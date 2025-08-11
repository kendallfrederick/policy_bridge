#needed for langraph
from typing import TypedDict, List, Dict, Any, Optional, Literal
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
    data_path: str # set in main, called in find_files
    xml_files: List[str] # list of file paths made in find_files and used in parse_xml
    pdf_files: List[str] # list of file paths made in find_files and used in parse_pdf
    txt_files: List[str] # list of file paths made in find_files and used in parse_txt
    records: List[Dict[str, Any]] # list of dictionaries to hold parsed data from files, made in parse, used in add_and_save_embeddings
    weaviate_client: Any
    collection: Any 

def setup(state: State) -> State:
    weaviate_client = weaviate.connect_to_local()
    weaviate_client.collections.delete('database')

    collection = weaviate_client.collections.create(
        name='database',
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
    xml_files = [
        os.path.join(state['data_path'], f.name)
        for f in os.scandir(state['data_path'])
        if f.name.endswith('.xml')
    ]
    pdf_files = [
        os.path.join(state['data_path'], f.name)
        for f in os.scandir(state['data_path'])
        if f.name.endswith('.pdf')
    ]
    txt_files = [
        os.path.join(state['data_path'], f.name)
        for f in os.scandir(state['data_path'])
        if f.name.endswith('.txt')
    ]

    return {**state, 'xml_files': xml_files, 'pdf_files': pdf_files, 'txt_files': txt_files}

def parse_xml(state: State) -> State:
    records = [] #list of dictionaries to hold parsed data
    for file_path in state['xml_files']:
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

def parse_txt(state: State) -> State:
    records = []
    for file_path in state['txt_files']:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            title = os.path.basename(file_path)
            records.append({
                'title': title,
                'authors': [],
                'abstract': [],
                'text': [content],
                'doi': '',
                'keywords': []
            })
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue

    return {**state, 'records': records}

def parse_pdf(state: State) -> State:
    records = []
    for file_path in state['pdf_files']:
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text = []
            for page in reader.pages:
                text.append(page.extract_text() or '')
            title = os.path.basename(file_path)
            records.append({
                'title': title,
                'authors': [],
                'abstract': [],
                'text': text,
                'doi': '',
                'keywords': []
            })
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
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

#EDGE TO DECIDE FILE TYPE
def decide_parse(state: State) -> Literal['parse_xml', 'parse_txt', 'parse_pdf']:
    if state['xml_files']:
        return 'parse_xml'
    elif state['txt_files']:
       return 'parse_txt'
    elif state['pdf_files']:
       return 'parse_pdf'   

def create_workflow():
    workflow = StateGraph(State)
    
    workflow.add_node("setup", setup)
    workflow.add_node("find_files", find_files)
    workflow.add_node("parse_xml", parse_xml)
    workflow.add_node("parse_txt", parse_txt)
    workflow.add_node("parse_pdf", parse_pdf)
    workflow.add_node("decide_parse", decide_parse)
    workflow.add_node("add_and_save_embeddings", add_and_save_embeddings)
    
    workflow.set_entry_point("setup")
    workflow.add_edge("setup", "find_files")
    workflow.add_conditional_edges("find_files", decide_parse)
    workflow.add_edge("parse_pdf", "add_and_save_embeddings")
    workflow.add_edge("parse_txt", "add_and_save_embeddings")
    workflow.add_edge("parse_xml", "add_and_save_embeddings")
    workflow.add_edge("add_and_save_embeddings", END)
    
    return workflow.compile()

if __name__ == "__main__":
    app = create_workflow()
    result = app.invoke({
        'data_path': 'data',
        'files': [],
        'records': [],
        'client': None,
        'collection': None
    })
    print(f"Processed {len(result['records'])} records")

    from IPython.display import Image, display
    import io

    # Save the graph to a file
    with open("making_embeddings_graph.png", "wb") as f:
        f.write(app.get_graph().draw_mermaid_png())
    print("Graph saved to making_embeddings_graph.png")
    