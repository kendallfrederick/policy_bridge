import argparse
from langchain_chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM

from get_embedding_function import get_embedding_function

CHROMA_PATH = "chroma"

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""


def main():
    # Create command line argument parser.
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text.")
    args = parser.parse_args()
    query_text = args.query_text

    # Send the query to the RAG system.
    query_rag(query_text)


def query_rag(query_text: str):
   # Uses the same embedding function as the one used to populate the database.
   # This is important to ensure the embeddings match.
   embedding_function = get_embedding_function()
   
   # Call on database created with populate_database.py
   db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
   
   # Search the DB. K is the number of results to return.
   results = db.similarity_search_with_relevance_scores(query_text, k=8)
   
   # Send the context to the LLM to answer the question.
   context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
   prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
   prompt = prompt_template.format(context=context_text, question=query_text)
   
   # Print the prompt to see what is being sent to the LLM.
   print(prompt)

   #CHANGE MODEL AND PARAMS HERE

   model = OllamaLLM(model="my-llama") #this is the custom model name made with Modelfile
   
   #make sure to run ollama create my-llama -f Modelfile
   response_text = model.invoke(prompt)
   sources = [doc.metadata.get("id", None) for doc, _score in results]
   formatted_response = f"Response: {response_text}\nSources: {sources}"
   print(formatted_response)
   
   return response_text

if __name__ == "__main__":
    main()