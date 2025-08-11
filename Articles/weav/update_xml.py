import os
import xml.etree.ElementTree as et
import ollama
import weaviate
from weaviate.classes.config import Property, DataType
import warnings

warnings.filterwarnings("ignore", category=ResourceWarning)

# Connect to local Weaviate vector database on Docker
client = weaviate.connect_to_local()


collection = client.collections.get('xmls')
# Provide location of tempdir from allofplos update
#data_path = ''
xml_objs = []
    
for xml_path in (path for path in os.scandir(data_path) if not path.name.startswith('.')):
    full_path = data_path + '/' + xml_path.name
    tree = et.parse(full_path)
    root = tree.getroot()

    meta = root.find('.//front/article-meta')
    title = meta.findtext('title-group/article-title')



    doi = meta.findtext('article-id[@pub-id-type="doi"]')
    authors = []
    for a in meta.findall('contrib-group/contrib[@contrib-type="author"]'):
        first = a.findtext('name/given-names')
        last = a.findtext('name/surname')
        authors.append(f'{first} {last}')
    keywords = []
    for k in meta.findall('kwd-group/kwd'):
        keyword = k.text
        keywords.append(keyword)
    abstract = []
    for ap in meta.findall('abstract/p'):
        abstract_par = ''.join(ap.itertext())
        abstract.append(abstract_par)
    text = []
    for s in root.findall('body/sec'):
        heading = s.findtext('title')
        text.append(heading)
        for p in s.iter('p'):
            paragraph = ''.join(p.itertext())
            text.append(paragraph)

    record = {
        'title': title,
        'doi': doi,
        'authors': authors,
        'keywords': keywords,
        'abstract': abstract,
        'text': text
    }
    xml_objs.append(record)

with collection.batch.fixed_size(batch_size=len(xml_objs)) as batch:
    for i, x in enumerate(xml_objs):
        xml_text = f'{x['title']}\n\n{x['abstract']}\n\n{x['text']}'
        
        embedding = ollama.embeddings(model='nomic-embed-text',
                                     prompt = xml_text)
    
        batch.add_object(
            properties = {'title': x['title'],
                          'doi': x['doi'],
                        'authors': x['authors'],
                        'keywords': x['keywords'],
                        'abstract': x['abstract'],
                        'text': x['text']},
            vector = embedding['embedding']
        )
        

client.close()