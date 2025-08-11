from langchain_ollama import OllamaEmbeddings

#uses ollama nomic embed-text model for embeddings (tested and found this is best)
def get_embedding_function():
    
    # Return the Ollama embeddings function.
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    return embeddings