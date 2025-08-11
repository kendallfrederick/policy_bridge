#needed for langraph
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END

import os
import warnings
import argparse

#needed for xml
import xml.etree.ElementTree as et

#needed for ollama and weaviate
import ollama
from langchain_ollama import OllamaLLM
import weaviate
from weaviate.classes.config import Property, DataType
from weaviate.classes.query import MetadataQuery

warnings.filterwarnings("ignore", category=ResourceWarning)

################## CLASS DEFINITION ##############

class State(TypedDict):
    client: Any
    collection: Any

    # for rag
    prompt: Any
    prompt_emb: List[float]
    filtered: List[Any]
    rag_data: str
    addrs: List[str]

######################## RUN RAG ##########################

def get_and_embed_prompt(state: State) -> State:
    client = weaviate.connect_to_local()
    collection = client.collections.get('database')

    """Get the prompt from command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument('prompt', type=str, help='The query.')
    args = parser.parse_args()
    state['prompt'] = args.prompt
    
    prompt_emb = ollama.embeddings(
        model='nomic-embed-text',
        prompt=state['prompt']
    )
    state['prompt_emb'] = prompt_emb['embedding']

    state['collection'] = collection
    state['client'] = client
    return state

def get_rag_results(state: State) -> State:
    """Query the Weaviate collection and return results."""
    client = state['client']
    collection = state['collection']
    prompt = state['prompt']
    prompt_emb = state['prompt_emb']
    
    # Query the collection using hybrid search
    results = collection.query.hybrid(
        query = prompt,
        vector = state['prompt_emb'],
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

    state['rag_data'] = data
    state['filtered'] = filtered

    return state

def generate_response(state: State) -> State:
    data = state['rag_data']
    filtered = state['filtered']
    prompt = state['prompt']

    model = OllamaLLM(model="my-llama")
    PROMPT_TEMPLATE = f'Using the data: {data}. Succinctly respond to this prompt and give a brief analysis of policy implications: {prompt}'
    #print(PROMPT_TEMPLATE)
    output = model.invoke(PROMPT_TEMPLATE)

    print('\n\nResponse\n--------')
    print(output)
    
    print('\nCited from:')
    addrs = []
    count = 1
    for obj in state['filtered']:
        title = obj.properties['title']
        #author = obj.properties['authors'][0]
        #doi = obj.properties['doi']
        #doi_addr = f'https://doi.org/{doi}'
        #addrs.append(doi_addr)
        #print(f'{count}. "{title}" by {author}\n{doi_addr}')
        print(f'{count}. "{title}"')
        count = count + 1

    state['addrs'] = addrs

    return state

def view_relevant_articles(state: State) -> None:
    import webbrowser

    print('Would you like to view the relevant articles? (Y/N)')
    choice = input()
    if choice.capitalize() == 'Y':
        for a in state['addrs']:
            webbrowser.open(a)



######################## DEFINE STEPS TO RUN ##########################

def create_workflow():
    workflow = StateGraph(State)

    ### rag nodes
    workflow.add_node("get_and_embed_prompt", get_and_embed_prompt)
    workflow.add_node("get_rag_results", get_rag_results)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("view_relevant_articles", view_relevant_articles)

    ###TO RUN ALL STEPS
    workflow.set_entry_point("get_and_embed_prompt")
    workflow.add_edge("get_and_embed_prompt", "get_rag_results")
    workflow.add_edge("get_rag_results", "generate_response")
    workflow.add_edge("generate_response", END)
   #workflow.add_edge("generate_response", "view_relevant_articles")
    #workflow.add_edge("view_relevant_articles", END)

    
    return workflow.compile()

if __name__ == "__main__":
    app = create_workflow()
    result = app.invoke({
        'files': [],
        'client': None,
        'collection': None,

        'prompt': None,
        'prompt_emb': [],
        'filtered': [],
        'rag_data': None,
        'addrs': []

    })

    #not sure if this works...
    #from IPython.display import Image, display
    #display(Image(app.get_graph().draw_mermaid()))
    #app.get_graph().draw_ascii() 
    
    from IPython.display import Image, display
    import io

    # Get the mermaid string and save as PNG
    #mermaid_png = app.get_graph().draw_mermaid_png()
    #display(Image(mermaid_png))

    # Save the graph to a file
    with open("workflow_graph.png", "wb") as f:
        f.write(app.get_graph().draw_mermaid_png())
    print("Graph saved to workflow_graph.png")