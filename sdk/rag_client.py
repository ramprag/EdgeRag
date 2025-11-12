import httpx
import json
from typing import Dict, List, Optional
from pathlib import Path


class RAGClient:
    """Python SDK for Edge RAG MVP"""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = ""):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key} if api_key else {}
        self.client = httpx.Client(timeout=300.0)  # 5 min timeout for long operations

    def upload_doc(self, file_path: str) -> str:
        """
        Upload a document to the RAG system

        Args:
            file_path: Path to PDF or image file

        Returns:
            doc_id: Unique document identifier
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/octet-stream')}
            response = self.client.post(
                f"{self.base_url}/upload",
                headers=self.headers,
                files=files
            )

        response.raise_for_status()
        data = response.json()
        return data['doc_id']

    def build_index(self) -> Dict:
        """
        Build the FAISS index for all uploaded documents

        Returns:
            Dict with index building results
        """
        response = self.client.post(
            f"{self.base_url}/build-index",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def query(self, query: str, top_k: int = 5) -> Dict:
        """
        Query the RAG system

        Args:
            query: Question to ask
            top_k: Number of relevant chunks to retrieve

        Returns:
            Dict with answer and sources
        """
        response = self.client.post(
            f"{self.base_url}/query",
            headers=self.headers,
            json={"query": query, "top_k": top_k}
        )
        response.raise_for_status()
        return response.json()

    def list_docs(self) -> List[Dict]:
        """
        List all uploaded documents

        Returns:
            List of document metadata
        """
        response = self.client.get(
            f"{self.base_url}/docs-list",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()['documents']

    def export_json(self, data: Dict, output_path: str):
        """
        Export query results to JSON file

        Args:
            data: Query response data
            output_path: Path to save JSON file
        """
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Results exported to {output_path}")

    def close(self):
        """Close the HTTP client"""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = RAGClient(api_key="your-secret-api-key-here")

    # Upload documents
    doc_id = client.upload_doc("sample.pdf")
    print(f"Uploaded document: {doc_id}")

    # Build index
    result = client.build_index()
    print(f"Index built: {result['total_chunks']} chunks indexed")

    # Query
    response = client.query("What are the main findings?")
    print(f"\nAnswer: {response['answer']}\n")

    for source in response['sources']:
        print(f"Source: {source['filename']} (page {source['page']}, score: {source['score']:.3f})")

    # Export results
    client.export_json(response, "query_result.json")