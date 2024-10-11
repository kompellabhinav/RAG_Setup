from embeddings.embedding_service import get_embedding
from pinecone_service.pinecone_utils import query_pinecone
from config.__init__ import pinecone_init, openai
import logging

SIMILARITY_THRESHOLD = 0.6
messages = []
index_name = "rag-project"

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
        prompt = generate_follow_up_questions(results, query)
        follow_up_questions = get_follow_up_questions(prompt)
        response_data = {
            "status": "not_relevant",
            "follow_up_questions": follow_up_questions
        }
        return response_data

def retrieve_documents(query_embedding):
    pc = pinecone_init()
    index = pc.Index(index_name)
    # Query Pinecone index
    results = index.query(
        vector=query_embedding,
        top_k=5,
        include_metadata=True
    )
    return results

def is_score_above_threshold(results, threshold=SIMILARITY_THRESHOLD):
    if not results['matches']:
        return False
    top_score = results['matches'][0]['score']
    return top_score >= threshold

def generate_follow_up_questions(documents, original_query, num_questions=3):
    document_texts = []
    for i, match in enumerate(documents['matches'][:3]):
        doc_text = match['metadata'].get('Description', '')
        document_texts.append(f"Document {i+1}: {doc_text}")

    prompt = (
        f"The user's query is: '{original_query}'\n\n"
        "The retrieved documents are not sufficiently relevant.\n"
        "Based on the following documents, generate follow-up questions to help clarify the user's intent.\n\n" +
        "\n".join(document_texts) +
        f"\n\nPlease provide {num_questions} follow-up questions."
    )
    return prompt

def get_follow_up_questions(prompt):
    messages.append({"role": "user", "content": prompt})
    logging.info(f"messages: {messages}")
    response = openai.chat.completions.create(
        model='gpt-4',  # Or another suitable model
        messages=messages,
        max_tokens=150,
        n=1,
        temperature=0.7,
    )
    questions = response.choices[0].message.content
    messages.append({"role": "assistant", "content": questions})
    return questions