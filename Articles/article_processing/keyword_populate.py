import sys
import json
import requests
from lxml import etree as et
import weaviate
from weaviate.classes.config import Property, DataType, ReferenceProperty
import ollama
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
api_key_path = "/Users/intern7/Policy_Project/policy_ai/Articles/article_processing/api_key.txt"
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
query = {"q": query_text, "limit": 3}

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


# Parse and embed

# Access dB
client = weaviate.connect_to_local()
'''
client.collections.delete("articles")
articles = client.collections.create(
    name = "articles",
    properties = [
        Property(name="title", data_type=DataType.TEXT),
        Property(name="authors", data_type=DataType.TEXT_ARRAY),
        Property(name="doi", data_type=DataType.TEXT),
        Property(name="text", data_type=DataType.TEXT)
    ]
)
'''
articles = client.collections.get("articles")

# Get doi list and process articles
# Update absolute path based on system
doi_list_path = "/Users/intern7/Policy_Project/policy_ai/Articles/article_processing/doi.txt"
try:
    with open(doi_list_path, "a+") as doi_file:
        doi_file.seek(0)
        doi_list = [d.strip() for d in doi_file.readlines()]

        added = 0
        added_dois = []
        for work in works:
            doi = work["doi"]
            if (doi not in doi_list) and (doi not in added_dois):
                text =  work["fullText"].replace("\n", "")
                article_record = {
                    "title": work["title"],
                    "authors": [author["name"] for author in work["authors"]],
                    "doi": doi,
                    "text": text
                }
                embedding = ollama.embeddings(model="nomic-embed-text",
                                              prompt = text)
                articles.data.insert(
                    properties=article_record,
                    vector = embedding['embedding']
                )
                doi_file.write(f"{doi}\n")
                added_dois.append(doi)
                added = added + 1

except FileNotFoundError:
    # If key file is not found, prints an error message and exits with an error code
    print("Error: API key file could not be found.\n")
    sys.exit(1)

print(f"Articles added: {added}")

client.close()
'''
#q = keywords with dashses between and without dashes between (check quality of results from each)

Extend to collect and show all authors

Check how many strict responses before getting relaxed responses,
only do second search if not enough from first (how to ensure no duplicates?)
Maybe track some attribute from strict responses (how to isolate and extract attributes like title and doi?) (how to compare against to exclude these while searching or filter after searching?)
(are relaxed responses sorted at all by relevance? otherwise maybe do searches on each keyword, track appearances of each article about all and take top hits?)

'''
