# import openai

# def get_embedding(text, model="text-embedding-3-small"):
#     response = openai.embeddings.create(
#         input=text,
#         model=model
#     )
#     embedding = response.data[0].embedding
#     return embedding

from llama_index.embeddings.ollama import OllamaEmbedding

# Initialize the Ollama embedding model
embedding_model = OllamaEmbedding()

def get_embedding(text):
    # Generate embedding using Ollama's embedding model
    embedding = embedding_model.embed(text)
    return embedding
