import sys
import weaviate
from weaviate.classes.query import MetadataQuery, QueryReference
import ollama
from langchain_ollama import OllamaLLM
import webbrowser
import warnings

import streamlit as st

def analyze_claims(claims):

    print("ENTERED ANALYZE CLAIMS")
    for claim in claims:
        print(claim)

    warnings.filterwarnings("ignore", category=ResourceWarning)

    if len(claims) == 1:
        claims_prompt = claims[0] + ('.')
        separate_claims = claims[0]
    else:
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

        print("Chosen Sources")

        for o in results.objects:
            score = o.metadata.score
            if score > 0.5:
                filtered.append(o)
                print(f'\nSource {num}: ')
                print(o.references['hasArticle'].__dict__['_CrossReference__objects'][0].properties['title'])
                print(f'Score: {o.metadata.score}')

                print(o.references['hasArticle'].__dict__['_CrossReference__objects'][0].properties['title'])

                o_string = o.properties['text']
                print(o_string)
                raw_data.append(o_string)
                num = num + 1

        #chunk reordering here
        data = '\n'.join(raw_data)

        PROMPT_TEMPLATE = f'''
        Using only this scientific research: {data}. 
        Critically analyze whether each of the following semi-colon separated claims is supported or refuted by the scientific research. (There may only be one claim!)
        If you can find no relevant context within that scientific research, state only Not Enough Relevant Information in the Context.
        Answer in the format of a numbered list where each element is a claim followed by the associated fact-checking analysis.
        Here are the claims: {separate_claims}
        '''
        output = model.invoke(PROMPT_TEMPLATE)

        print('\n\nClaim Analysis\n-------------------')
        st.subheader("Claim Analysis")

        print(output)
        st.write(output)
        

        print('\nCited from:')
        st.subheader("Sources: ")

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

                st.write(f'{count}. "{title}" \n{doi_addr}')
                count = count + 1


    finally:
        client.close()