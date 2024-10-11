from query_processing.query_handler import process_query

def main():
    while True:
        query = input("Enter your query (or 'exit' to quit): ")
        
        # Remove this to stop loop
        if query.lower() == 'exit':
            break
        process_query(query)

if __name__ == "__main__":
    main()