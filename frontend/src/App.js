import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const submitQuery = async () => {
    if (!query.trim()) {
      alert('Please enter a query.');
      return;
    }

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const res = await axios.post('http://127.0.0.1:5000/api/query', {
        query: query
      });

      setResponse(res.data);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.error || 'An error occurred.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center p-4">
      <h1 className="text-3xl font-bold mt-8 mb-4">RAG Project Query Interface</h1>
      <div className="w-full max-w-2xl bg-white p-6 rounded shadow">
        <div className="flex mb-4">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your query here"
            className="flex-grow p-2 border border-gray-300 rounded-l"
          />
          <button
            onClick={submitQuery}
            className="bg-blue-500 text-white px-4 py-2 rounded-r hover:bg-blue-600"
          >
            {loading ? 'Processing...' : 'Submit'}
          </button>
        </div>
        {error && <div className="text-red-500 mb-4">{error}</div>}
        {response && (
          <div className="mt-4">
            {response.status === 'relevant' && (
              <div>
                <h2 className="text-xl font-semibold mb-2">Relevant Documents:</h2>
                {response.documents.map((doc, index) => (
                  <div key={index} className="mb-4 p-4 border rounded">
                    <h3 className="font-bold">Document {index + 1}</h3>
                    <p><strong>Score:</strong> {doc.score}</p>
                    <p><strong>Topic:</strong> {doc.topic}</p>
                    <p>
                      <strong>URL:</strong>{' '}
                      <a href={doc.url} target="_blank" rel="noopener noreferrer" className="text-blue-500 underline">
                        {doc.url}
                      </a>
                    </p>
                    <p><strong>Description:</strong> {doc.description}</p>
                  </div>
                ))}
              </div>
            )}
            {response.status === 'not_relevant' && (
              <div>
                <h2 className="text-xl font-semibold mb-2">Follow-Up Questions:</h2>
                <p>{response.follow_up_questions}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;