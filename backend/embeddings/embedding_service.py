# import openai

# def get_embedding(text, model="text-embedding-3-small"):
#     response = openai.embeddings.create(
#         input=text,
#         model=model
#     )
#     embedding = response.data[0].embedding
#     return embedding

#from llama_index.embeddings.ollama import OllamaEmbedding
from langchain_ollama import OllamaEmbeddings

#model name
model_name="llama3.2"

# Initialize the Ollama embedding model
embedding_model = OllamaEmbeddings(model="llama3.2")

def get_embedding(text):
    # Generate embedding using Ollama's embedding model
    embedding = embedding_model.embed_query(text)
    print(f"The generated embedding dimension {len(embedding)}")
    return embedding
