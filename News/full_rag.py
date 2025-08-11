import sys
import weaviate
from weaviate.classes.query import MetadataQuery
import ollama
from langchain_ollama import OllamaLLM
import webbrowser
import warnings

warnings.filterwarnings("ignore", category=ResourceWarning)

# Create command line argument parser.
# Processes arguments passed to program
if len(sys.argv) < 2:
    # If wrong number of arguments given, prints an error message and exits with an error code
    print("Error: Improper number of arguments. Expected at least one claim.\n")
    sys.exit(1)
else:
    # Parses and stores valid keyword arguments
    claims = [sys.argv[c].strip() for c in range(1, len(sys.argv))]

claims_prompt = '. '.join(claims)
separate_claims = '; '.join(claims)

model = OllamaLLM(model="anews-llama") #this is the custom model name made with aModelfile
#make sure to run ollama create anews-llama -f aModelfile

client = weaviate.connect_to_local()

try:
    articles= client.collections.get('articles')

    prompt_emb = ollama.embeddings(
        model = 'nomic-embed-text',
        prompt = claims_prompt
    )

    results = articles.query.hybrid(
        query = claims_prompt,
        vector = prompt_emb['embedding'],
        alpha = 0.5,
        return_metadata = MetadataQuery(score=True, explain_score=False),
        limit = 10
    )

    filtered = []
    raw_data = []
    num = 1
    for o in results.objects:
        score = o.metadata.score
        if score > 0.5:
            filtered.append(o)
            print(f'\nSource {num}: ')
            print(o.properties['doi'])
            print(f'Score: {o.metadata.score}')
            o_string = o.properties['text']
            raw_data.append(o_string)
            num = num + 1

    #chunk reordering here
    data = '\n'.join(raw_data)

    PROMPT_TEMPLATE = f'''
    Using only this scientific research: {data}. 
    Critically analyze whether each of the following semi-colon separated claims is supported or refuted by the scientific research.
    If you can find no relevant context within that scientific research, state that and do not try to use any other sources.
    Answer in the format of a numbered list where each element is a claim followed by the associated fact-checking analysis.
    Here are the claims: {separate_claims}
    '''
    output = model.invoke(PROMPT_TEMPLATE)

    print('\n\nNews Claim Analysis\n-------------------')
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