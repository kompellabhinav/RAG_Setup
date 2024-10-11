from embeddings.embedding_service import get_embedding
from pinecone_service.pinecone_utils import query_pinecone
from config.__init__ import pinecone_init, openai

SIMILARITY_THRESHOLD = 0.6
messages = []
index_name = "rag-project"

def process_query(query, top_k=5, similarity_threshold=SIMILARITY_THRESHOLD):
    # Generate query embedding
    query_embedding = get_embedding(query)
    if query_embedding is None:
        print("Failed to generate embedding for the query.")
        return

    # Retrieve documents from Pinecone
    results = retrieve_documents(query_embedding)
    if not results['matches']:
        print("No documents were retrieved.")
        return

    # Check if the top score meets the threshold
    if is_score_above_threshold(results, threshold=similarity_threshold):
        print("Documents are relevant. Proceeding with the response.")
        # Here you would proceed to generate an answer using the retrieved documents
        # For demonstration, we'll print the documents
        for match in results['matches']:
            print(f"Score: {match['score']}")
            print(f"Topic: {match['metadata'].get('Topic', 'N/A')}")
            print(f"URL: {match['metadata'].get('Video URL', 'N/A')}")
            print(f"Description: {match['metadata'].get('Description', 'N/A')}\n")
    else:
        print("Documents are not sufficiently relevant. Generating follow-up questions.")
        prompt = generate_follow_up_questions(results, query)
        follow_up_questions = get_follow_up_questions(prompt)
        print("Please help us better understand your query by answering the following questions:")
        print(follow_up_questions)
        # Optionally, get user input to refine the query

def retrieve_documents(query_embedding):
    pc = pinecone_init()
    index = pc.Index(index_name)
    # Query Pinecone index
    results = index.query(
    vector=query_embedding,
    top_k=5,
    include_metadata=True
    )

    # Display the results
    for match in results['matches']:
        print(f"Score: {match['score']}")
        print(f"Topic: {match['metadata']['Topic']}")
        print(f"URL: {match['metadata']['Video URL']}")
        print(f"Description: {match['metadata']['Description']}\n")
    
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