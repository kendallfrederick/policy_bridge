import argparse
import weaviate
from weaviate.classes.query import MetadataQuery
import ollama
from langchain_ollama import OllamaLLM
import webbrowser
import warnings

from langchain_community.agent_toolkits.load_tools import load_tools
from langchain.agents import initialize_agent
from dotenv import load_dotenv
load_dotenv()

llm = OllamaLLM(model="my-llama") #this is the custom model name made with Modelfile
#make sure to run ollama create my-llama -f Modelfile

# Load tools for the agent

tools = load_tools(["llm-math"], llm=llm) 
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

warnings.filterwarnings("ignore", category=ResourceWarning)

# Create command line argument parser.
parser = argparse.ArgumentParser()
parser.add_argument('prompt', type=str, help='The query.')
args = parser.parse_args()
prompt = args.prompt

client = weaviate.connect_to_local()
try:

    collection = client.collections.get('xmls')

    prompt_emb = ollama.embeddings(
        model = 'nomic-embed-text',
        prompt = prompt
    )

    
    results = collection.query.hybrid(
        query = prompt,
        vector = prompt_emb['embedding'],
        alpha = 0.5,
        return_metadata = MetadataQuery(score=True, explain_score=True),
        limit = 3)
    
    filtered = []
    raw_data = []
    num = 1
    for o in results.objects:
        score = o.metadata.score
        if score > 0.8:
            filtered.append(o)
            print(f'\nArticle {num}: ')
            print(o.properties['title'])
            print(f'Score: {o.metadata.score}')
            print(f'Score Details: {o.metadata.explain_score}')
            o_string = ' '.join(o.properties['text'])
            raw_data.append(o_string)
            num = num + 1

    data = ' '.join(raw_data)

    #raw_data = results.objects[0]
    #data = raw_data.properties['text']
    
    '''
    for o in results.objects:
        data = data + '\n\n' + o.properties['text']
    '''


    #prompt_template = f'Using the data: {data}. Respond to this prompt: {prompt}'
    PROMPT_TEMPLATE = f'Using the data: {data}. Succinctly respond to this prompt and give a brief analysis of policy implications: {prompt}'
    #output = model.invoke(PROMPT_TEMPLATE)

    output = agent.invoke(PROMPT_TEMPLATE)

    print('\n\nResponse\n--------')
    print(output)
    
    
    print('\nCited from:')
    addrs = []
    count = 1
    for obj in filtered:
        title = obj.properties['title']
        author = obj.properties['authors'][0]
        doi = obj.properties['doi']
        doi_addr = f'https://doi.org/{doi}'
        addrs.append(doi_addr)
        print(f'{count}. "{title}" by {author}\n{doi_addr}')
        count = count + 1

    print('Would you like to view the relevant articles? (Y/N)')
    choice = input()
    if choice.capitalize() == 'Y':
        for a in addrs:
            webbrowser.open(a)
    
finally:
    client.close()