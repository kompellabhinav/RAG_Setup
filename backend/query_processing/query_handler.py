# query_handle.py

from embeddings.embedding_service import get_embedding
from pinecone_service.pinecone_utils import query_pinecone, get_pinecone_index
import logging

# Define similarity threshold and initialize messages array
SIMILARITY_THRESHOLD = 0.6
index_name = "rag-project"
messages = []  # Used to store conversation context

def process_query(query, top_k=5, similarity_threshold=SIMILARITY_THRESHOLD):
    # Generate query embedding
    query_embedding = get_embedding(query)
    if query_embedding is None:
        return {"error": "Failed to generate embedding for the query."}

    # Retrieve documents from Pinecone
    results = retrieve_documents(query_embedding)
    if not results['matches']:
        return {"error": "No documents were retrieved."}

    # Check if the top score meets the threshold
    if is_score_above_threshold(results, threshold=similarity_threshold):
        response_data = {
            "status": "relevant",
            "documents": []
        }
        for match in results['matches']:
            document = {
                "score": match['score'],
                "topic": match['metadata'].get('Topic', 'N/A'),
                "url": match['metadata'].get('Video URL', 'N/A'),
                "description": match['metadata'].get('Description', 'N/A')
            }
            response_data["documents"].append(document)
        return response_data
    else:
        follow_up_questions = generate_follow_up_questions(results, query)
        response_data = {
            "status": "not_relevant",
            "follow_up_questions": follow_up_questions
        }
        return response_data

# Retrieve documents from Pinecone
def retrieve_documents(query_embedding):
    index = get_pinecone_index(index_name)
    results = index.query(
        vector=query_embedding,
        top_k=5,
        include_metadata=True
    )
    return results

# Check if the top score is above the threshold
def is_score_above_threshold(results, threshold=SIMILARITY_THRESHOLD):
    if not results['matches']:
        return False
    top_score = results['matches'][0]['score']
    return top_score >= threshold

# Generate follow-up questions based on the retrieved documents
def generate_follow_up_questions(documents, original_query, num_questions=3):
    document_texts = []
    for i, match in enumerate(documents['matches'][:3]):
        doc_text = match['metadata'].get('Description', '')
        document_texts.append(f"Document {i+1}: {doc_text}")

    # Create a prompt for generating follow-up questions
    prompt = (
        f"The user's query is: '{original_query}'\n\n"
        "The retrieved documents are not sufficiently relevant.\n"
        "Based on the following documents, generate follow-up questions to help clarify the user's intent.\n\n" +
        "\n".join(document_texts) +
        f"\n\nPlease provide {num_questions} follow-up questions."
    )

    # Add this prompt to the conversation history in messages array
    messages.append({"role": "user", "content": prompt})
    logging.info(f"messages: {messages}")

    follow_up_questions = generate_with_llama(messages)
    return follow_up_questions

# Custom function to generate follow-up questions using Ollama's model
def generate_with_llama(messages):
    # Implement the response generation with Ollama's Llama model here
    # This should be adapted to work with Ollama, using the messages array as context
    conversation_history = "\n".join([msg["content"] for msg in messages])
    response = ollama_model.generate(conversation_history)  # Replace with actual Ollama generation function
    
    # Add the model's response to the messages array
    messages.append({"role": "assistant", "content": response})
    return response
