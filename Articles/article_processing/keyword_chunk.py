import os
import sys
import requests
import json
from lxml import etree as et
import ollama
import weaviate
from weaviate.classes.config import Property, DataType, ReferenceProperty
from langchain_text_splitters import RecursiveCharacterTextSplitter
import warnings

warnings.filterwarnings("ignore", category=ResourceWarning)

# Processes arguments passed to program
if len(sys.argv) < 2:
    # If wrong number of arguments given, prints an error message and exits with an error code
    print("Error: Improper number of arguments. Expected at least one keyword.\n")
    sys.exit(1)
else:
    # Parses and stores valid keyword arguments
    keywords = [sys.argv[k].strip() for k in range(1, len(sys.argv))]


# Query CORE API
# Set up access and authentication
api_endpoint = "https://api.core.ac.uk/v3/search/works"
api_key = ""

# Retrieve CORE API key from local file
# Update absolute path based on system
api_key_path = "/Users/law/Policy_Project/policy_ai/Articles/article_processing/api_key.txt"
try:
    with open (api_key_path, "r") as key_file:
        api_key = key_file.readline().strip()
except FileNotFoundError:
    # If key file is not found, prints an error message and exits with an error code
    print("Error: API key file could not be found.\n")
    sys.exit(1)

# Set up request header to authenticate with key
headers = {"Authorization": "Bearer " + api_key}

# Format query
separated_keywords = '"' + '" OR "'.join(keywords) + '"'
query_text = f"({separated_keywords}) AND _exists_:title AND _exists_:authors AND _exists_:doi AND _exists_:fullText"
query = {"q": query_text, "limit": 50}

# Perform query
response = requests.post(api_endpoint, data = json.dumps(query), headers=headers)

#Add API error catching probably with try catch here
#Clean up beneath key retrieval

if response.status_code == 200:
    works = response.json()["results"]
    dois = [work["doi"] for work in works]
    '''
    # Print out titles of all returned Articles
    print("********** ARTICLE TITLES **********")
    titles = [work["title"] for work in works]
    count = 1
    for title in titles:
        print(f"{count}. {title}\n")
        count = count + 1
    '''
else:
    print(f"Error: Query returned with status code {response.status_code}. {response.text}\n")
    print("Remaining requests:", response.headers.get("X-RateLimit-Remaining"))
    print("Reset Time (epoch):", response.headers.get("X-RateLimit-Reset"))
    sys.exit(1)

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
        Property(name='authors', data_type=DataType.TEXT_ARRAY),
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


# Get doi list and process articles
# Update absolute path based on system
doi_list_path = "/Users/law/Policy_Project/doi.txt"
try:
    with open(doi_list_path, "a+") as doi_file:
        doi_file.seek(0)
        doi_list = [d.strip() for d in doi_file.readlines()]

        added = 0
        existed = 0
        chunks = 0
        num_works = len(works)
        added_dois = []
        for work in works:
            doi = work["doi"]
            if (doi not in doi_list) and (doi not in added_dois):
                raw_text =  work["fullText"].replace("\n", "")

                parent_record = {
                    "title": work["title"],
                    "authors": [author["name"] for author in work["authors"]],
                    "doi": doi
                }

                parent_id = article_meta.data.insert(
                    properties=parent_record
                )

                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1850,
                    chunk_overlap=250,
                    length_function=len,
                    is_separator_regex=True,
                    separators=['\n\n', '\n', ' ', '']
                )
                text = text_splitter.split_text(raw_text)

                print(f"Chunking -> {work["title"]}... ({added + existed}/{num_works} done)\n")
                with article_chunks.batch.fixed_size(batch_size=len(text)) as batch:
                    for t in text:
                        embedding = ollama.embeddings(model='nomic-embed-text',
                                                prompt = t)
                        batch.add_object(
                            properties = {'text': t},
                            references={'hasArticle': parent_id},
                            vector = embedding['embedding']
                        )
                doi_file.write(f"{doi}\n")
                added_dois.append(doi)
                hunks = chunks + len(text)
                added = added + 1
            else:
                existed = existed + 1

except FileNotFoundError:
    # If key file is not found, prints an error message and exits with an error code
    print("Error: API key file could not be found.\n")
    sys.exit(1)

print(f"Articles added: {added}")
print(f"Chunks created: {chunks}")
print(f"({existed} articles found already existed in the database)")

client.close()