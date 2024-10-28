import logging
from embeddings.embedding_service import get_embedding
from pinecone_service.pinecone_utils import query_pinecone
from config.__init__ import pinecone_init, openai

from nltk.translate.bleu_score import sentence_bleu
from sklearn.metrics import precision_score

SIMILARITY_THRESHOLD = 0.6
messages = []
index_name = "rag-project"

def process_query(query, top_k=5, similarity_threshold=SIMILARITY_THRESHOLD):
    query_embedding = get_embedding(query)
    if query_embedding is None:
        return {"error": "Failed to generate embedding for the query."}

    results = retrieve_documents(query_embedding)
    if not results['matches']:
        return {"error": "No documents were retrieved."}

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

def generate_follow_up_questions(documents, original_query, num_questions=1):
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

def summerize_messages(messages):
    return " ".join([msg['content'] for msg in messages[-5:] ] )

def get_follow_up_questions(prompt):

    summary=summerize_messages(messages)
    combined_prompt=f"{summary}\n user's query:{prompt}"

    messages.append({"role": "user", "content": combined_prompt})
    logging.info(f"messages: {messages}")
    response = openai.chat.completions.create(
        model='gpt-4',
        messages=messages,
        max_tokens=150,
        n=1,
        temperature=0.7,
    )
    questions = response.choices[0].message.content
    messages.append({"role": "assistant", "content": questions})
    return questions

def evaluate_response(generated_response, expected_response):
    # BLEU score calculation
    bleu_score = sentence_bleu([expected_response.split()], generated_response.split())
    
    # Precision calculation
    expected_tokens = set(expected_response.split())
    generated_tokens = set(generated_response.split())
    true_positives = len(expected_tokens.intersection(generated_tokens))
    precision = true_positives / len(generated_tokens) if len(generated_tokens) > 0 else 0
    
    # Faithfulness evaluation
    faithful_score = 1 if bleu_score > 0.5 else 0

    return bleu_score, precision, faithful_score

def terminal_interaction():
    while True:
        # Get the user input from the terminal
        query = input("\nEnter your query (or type 'exit' to quit): ")
        
        if query.lower() == 'exit':
            print("Exiting the application.")
            break
        
        # Process the query
        response = process_query(query)
        
        if 'error' in response:
            print(f"Error: {response['error']}")
        elif response['status'] == 'relevant':
            print("\nDocuments retrieved:")
            generated_response = " ".join([doc['description'] for doc in response['documents']])
            for doc in response['documents']:
                print(f"Score: {doc['score']}, Topic: {doc['topic']}, URL: {doc['url']}, Description: {doc['description']}")
            
            # Evaluation
            expected_response = input("\nEnter the expected response to evaluate: ")
            bleu, precision, faithful = evaluate_response(generated_response, expected_response)
            print(f"\nEvaluation Results:\nBLEU Score: {bleu}\nPrecision: {precision}\nFaithfulness: {faithful}")
        else:
            print("\nThe documents are not sufficiently relevant.")
            print(f"Follow-up questions: {response['follow_up_questions']}")

if __name__ == "__main__":
    terminal_interaction()

