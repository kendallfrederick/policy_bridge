import os
from lxml import etree as et
import ollama
import weaviate
from weaviate.classes.config import Property, DataType, ReferenceProperty
from langchain_text_splitters import RecursiveCharacterTextSplitter
import warnings

warnings.filterwarnings("ignore", category=ResourceWarning)


# Connect to local Weaviate vector database on Docker
client = weaviate.connect_to_local()

'''
client.collections.delete('xmls')

client.collections.delete('article_meta')
client.collections.delete('article_chunks')

article_meta = client.collections.create(
    name = 'article_meta',
    properties = [
        Property(name='title', data_type=DataType.TEXT),
        Property(name='author', data_type=DataType.TEXT),
        Property(name='doi', data_type=DataType.TEXT)
    ]
)

article_chunks = client.collections.create(
    name = 'article_chunks',
    properties = [
        Property(name='text', data_type=DataType.TEXT),
    ],
    references = [
        ReferenceProperty(name='hasArticle', target_collection='article_meta')
    ]
)
'''

article_meta = client.collections.get('article_meta')
article_chunks = client.collections.get('article_chunks')

data_path = '/Users/law/Policy_Project/policy_ai/weav/Colorado River Salinity Articles'


chunks = 0
papers = 0
    
for xml_path in (path for path in os.scandir(data_path) if not path.name.startswith('.')):
    if (papers % 100) == 0:
        print(f'*Update: Reached {papers} papers*')
    full_path = data_path + '/' + xml_path.name
    
    try:
        tree = et.parse(full_path)
        root = tree.getroot()

        # Parse article metadata from xml to add parent object to article_meta collection
        meta = root.find('front/article-meta')
        title_el = meta.find('title-group/article-title')
        title = title_el.xpath('string()')
        doi = meta.findtext('article-id[@pub-id-type="doi"]')

        author_el = meta.find('contrib-group/contrib[@contrib-type="author"]')
        first = author_el.findtext('name/given-names')
        last = author_el.findtext('name/surname')
        if first is not None:
            author = last + ', ' + first
        else:
            author = author_el.xpath('string()')

        parent_record = {
            'title': title,
            'author': author,
            'doi': doi
        }

        parent_id = article_meta.data.insert(
            properties=parent_record
        )


        # Parse, clean, and chunk article text from xml to add embeddings to Weaviate vector DB
        body = root.find('body')
        for st in body.findall('.//title'):
            par = st.getparent()
            if par is not None:
                par.remove(st)

        for table in body.findall('.//table-wrap'):
            par = table.getparent()
            if par is not None:
                par.remove(table)

        for image in body.findall('.//img'):
            par = image.getparent()
            if par is not None:
                par.remove(image)

        for fig in body.findall('.//fig'):
            par = fig.getparent()
            if par is not None:
                par.remove(fig)

        for form in body.findall('.//disp-formula'):
            par = form.getparent()
            if par is not None:
                par.remove(form)

        for sup in body.findall('.//supplementary-material'):
            par = sup.getparent()
            if par is not None:
                par.remove(sup)

        raw_text = body.xpath('string()')
        text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1850,
                chunk_overlap=250,
                length_function=len,
                is_separator_regex=False,
                separators=['\n', '\n\n']
            )
        text = text_splitter.split_text(raw_text)
        if text[-1].lower() == 'supporting information':
            text = text[:-1]

        with article_chunks.batch.fixed_size(batch_size=len(text)) as batch:
            for t in text:
                embedding = ollama.embeddings(model='nomic-embed-text',
                                              prompt = t)
                batch.add_object(
                    properties = {'text': t},
                    references={'hasArticle': parent_id},
                    vector = embedding['embedding']
                )

        chunks = chunks + len(text)
        papers = papers + 1

    except et.ParseError as e:
        print(f'Error: Could not parse xml file: {e} from path {full_path}')
    except FileNotFoundError:
        print(f'Error: Could not find the file at path {full_path}')

print(f'Chunks added: {chunks}\nPapers added: {papers}')

client.close()