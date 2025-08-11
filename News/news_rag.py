import sys
import weaviate
from weaviate.classes.query import MetadataQuery, QueryReference
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
    article_meta = client.collections.get('article_meta')
    article_chunks = client.collections.get('article_chunks')

    prompt_emb = ollama.embeddings(
        model = 'nomic-embed-text',
        prompt = claims_prompt
    )

    results = article_chunks.query.hybrid(
        query = claims_prompt,
        vector = prompt_emb['embedding'],
        alpha = 0.5,
        return_metadata = MetadataQuery(score=True, explain_score=False),
        return_references = QueryReference(
            link_on='hasArticle',
            return_properties=['title', 'author', 'doi']
        ),
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
            print(o.references['hasArticle'].__dict__['_CrossReference__objects'][0].properties['title'])
            print(f"https://doi.org/{o.references['hasArticle'].__dict__['_CrossReference__objects'][0].properties['doi']}")
            print(f'Score: {o.metadata.score}')
            o_string = o.properties['text']
            print(o_string)
            raw_data.append(o_string)
            num = num + 1

    #chunk reordering here
    data = '\n'.join(raw_data)

    DECISION = (f'''
    You must pick exactly 1 of the 3 following options
    - Supported
    - Refuted
    - Not Enough Context to Evaluate (use if there is no mention of the claim in the articles)
    ''')

    SOURCE_FORMAT = (f'''
    Use this in-line citation format:
    (Author Name(s), Year, Title's first 3 words)

    Based on the source:
                   "Grady, J. S., Her, M., Moreno, G., Perez, C., & Yelinek, J. (2019).
                   Emotions in storybooks: A comparison of storybooks that represent ethnic and racial groups in the United States. Psychology of Popular Media Culture, 8(3), 207–217.
                   https://doi.org/10.1037/ppm0000185"

    Here is an example of the in-line citation:
                   (Grady et al., 2019, Emotions in storybooks...)               
                      
    ''')

    ANSWER_FORMAT = (f'''
    Based on your assessed factual validity of the claim, make a {DECISION} then answer in the following format:
    Claim 1: claim.
    Decision: decision made.
    Explanation: explain why you made your decision based on the scientific data provided and also cite the article source used to answer in the format ###{SOURCE_FORMAT}###.
    ''')

    PROMPT_TEMPLATE = f'''
    Think critically about the individual factual validity of these claims.
    Using only the scientific research ###{data}### to critically analyze each of the semi-colon separated claims in ###{separate_claims}###.
    Please answer in this format ###{ANSWER_FORMAT}###.
    '''
    output = model.invoke(PROMPT_TEMPLATE)

    print('\n\nNews Claim Analysis\n-------------------')
    print(output)
    

    print('\nCited from:')
    addrs = []
    count = 1
    for obj in filtered:
        doi = obj.references['hasArticle'].__dict__['_CrossReference__objects'][0].properties['doi']
        doi_addr = f'https://doi.org/{doi}'
        if doi_addr not in addrs:
            addrs.append(doi_addr)
            title = obj.references['hasArticle'].__dict__['_CrossReference__objects'][0].properties['title']
            #authors_list = obj.references['hasArticle'].__dict__['_CrossReference__objects'][0].properties['authors']
            #authors = ', '.join(authors_list)
            print(f'{count}. "{title}" \n{doi_addr}')
            count = count + 1

    print('Would you like to view the relevant articles? (Y/N)')
    choice = input()
    if choice.capitalize() == 'Y':
        for a in addrs:
            webbrowser.open(a)

finally:
    client.close()