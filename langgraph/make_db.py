#needed for langraph
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END

import os
import warnings

#needed for xml
import xml.etree.ElementTree as et

#needed for ollama and weaviate
import ollama
import weaviate
from weaviate.classes.config import Property, DataType

warnings.filterwarnings("ignore", category=ResourceWarning)

class State(TypedDict):
    data_path: str
    files: List[str]
    records: List[Dict[str, Any]]
    weaviate_client: Any
    collection: Any

def setup(state: State) -> State:
    weaviate_client = weaviate.connect_to_local()
    weaviate_client.collections.delete('database_xmls')
    collection = weaviate_client.collections.create(
        name='database_xmls',
        properties=[
            Property(name='title', data_type=DataType.TEXT),
            Property(name='authors', data_type=DataType.TEXT_ARRAY),
            Property(name='abstract', data_type=DataType.TEXT_ARRAY),
            Property(name='text', data_type=DataType.TEXT_ARRAY),
            Property(name='doi', data_type=DataType.TEXT),
            Property(name='keywords', data_type=DataType.TEXT_ARRAY),
        ]
    )
    return {**state, 'client': weaviate_client, 'collection': collection}

def find_files(state: State) -> State:
    files = [
        os.path.join(state['data_path'], f.name)
        for f in os.scandir(state['data_path'])
        if f.name.endswith('.xml')
    ]
    return {**state, 'files': files}

def parse_xml(state: State) -> State:
    records = []
    for file_path in state['files']:
        try:
            tree = et.parse(file_path)
            meta = tree.find('.//front/article-meta')
            
            title = meta.findtext('title-group/article-title', 'Untitled')
            
            authors = [
                f"{a.findtext('name/given-names', '')} {a.findtext('name/surname', '')}".strip()
                for a in meta.findall('contrib-group/contrib[@contrib-type="author"]')
            ]
            
            abstract = [p.text for p in meta.findall('abstract/p') if p.text]
            
            text = []
            for section in tree.findall('.//body/sec'):
                if section.findtext('title'):
                    text.append(section.findtext('title'))
                text.extend([p.text for p in section.findall('.//p') if p.text])

            doi = meta.findtext('article-id[@pub-id-type="doi"]', '')
            keywords = []
            for k in meta.findall('kwd-group/kwd'):
                keyword = k.text
                keywords.append(keyword)

            records.append({
                'title': title,
                'authors': authors,
                'abstract': abstract,
                'text': text,
                'doi': doi,
                'keywords': keywords
            })
        except:
            continue

    return {**state, 'records': records}

def add_and_save_embeddings(state: State) -> None:
    for record in state['records']:
        text = f"{record['title']} {' '.join(record['abstract'])} {' '.join(record['text'])}"
        embedding = ollama.embeddings(model='nomic-embed-text', prompt=text)
        record['embedding'] = embedding['embedding']

    with state['collection'].batch.fixed_size(len(state['records'])) as batch:
        for record in state['records']:
            batch.add_object(
                properties={k: v for k, v in record.items() if k != 'embedding'},
                vector=record['embedding']
            )

def create_workflow():
    workflow = StateGraph(State)
    
    workflow.add_node("setup", setup)
    workflow.add_node("find_files", find_files)
    workflow.add_node("parse_xml", parse_xml)
    workflow.add_node("add_and_save_embeddings", add_and_save_embeddings)
    
    workflow.set_entry_point("setup")
    workflow.add_edge("setup", "find_files")
    workflow.add_edge("find_files", "parse_xml")
    workflow.add_edge("parse_xml", "add_and_save_embeddings")
    workflow.add_edge("add_and_save_embeddings", END)
    
    return workflow.compile()

if __name__ == "__main__":
    app = create_workflow()
    result = app.invoke({
        'data_path': 'weav/xml_data',
        'files': [],
        'records': [],
        'client': None,
        'collection': None
    })
    print(f"Processed {len(result['records'])} records")
    