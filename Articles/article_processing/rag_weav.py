import argparse
import weaviate
from weaviate.classes.query import MetadataQuery, QueryReference
import ollama
from langchain_ollama import OllamaLLM
import webbrowser
import warnings

warnings.filterwarnings("ignore", category=ResourceWarning)

# Create command line argument parser.
parser = argparse.ArgumentParser()
parser.add_argument('prompt', type=str, help='The query.')
args = parser.parse_args()
prompt = args.prompt

model = OllamaLLM(model="my-llama") #this is the custom model name made with Modelfile
#make sure to run ollama create my-llama -f Modelfile

client = weaviate.connect_to_local()
try:
    articles = client.collections.get('articles')

    prompt_emb = ollama.embeddings(
        model = 'nomic-embed-text',
        prompt = prompt
    )

    results = articles.query.hybrid(
        query = prompt,
        vector = prompt_emb['embedding'],
        alpha = 0.65,
        return_metadata = MetadataQuery(score=True, explain_score=False),
        limit = 10
    )


    filtered = []
    raw_data = []
    num = 1
    for o in results.objects:
        score = o.metadata.score
        if score > 0.8:
            filtered.append(o)
            print(f'\nSource {num}: ')
            print(o.properties['title'])
            print(f'Score: {o.metadata.score}')
            o_string = o.properties['text']
            raw_data.append(o_string)
            num = num + 1

    data = '\n'.join(raw_data)

    #raw_data = results.objects[0]
    #data = raw_data.properties['text']
    
    '''
    for o in results.objects:
        data = data + '\n\n' + o.properties['text']
    '''


    #prompt_template = f'Using the data: {data}. Respond to this prompt: {prompt}'
    PROMPT_TEMPLATE = f'Using the data: {data}. Succinctly respond to this prompt and give a brief analysis of policy implications: {prompt}'
    output = model.invoke(PROMPT_TEMPLATE)

    print('\n\nResponse\n--------')
    print(output)
    
    
    print('\nCited from:')
    addrs = []
    count = 1
    for obj in filtered:
        doi = obj.properties['doi']
        doi_addr = f'https://doi.org/{doi}'
        if doi_addr not in addrs:
            addrs.append(doi_addr)
            title = obj.properties['title']
            authors = ', '.join(obj.properties['authors'])
            print(f'{count}. "{title}" by {authors}\n{doi_addr}')
            count = count + 1

    print('Would you like to view the relevant articles? (Y/N)')
    choice = input()
    if choice.capitalize() == 'Y':
        for a in addrs:
            webbrowser.open(a)
    
finally:
    client.close()