class RAGEngine:
    def __init__(self, config=None):
        self.config = config
        self.documents = []
        print("RAG Engine initialized")

    def add_documents(self, documents):
        if documents:
            self.documents.extend(documents)
            return True
        return False

    def retrieve(self, query, n_results=None):
        if not self.documents:
            return []

        results = []
        for doc in self.documents[:3]:
            results.append({
                "document": doc.get("text", ""),
                "metadata": {"filename": doc.get("filename", "Unknown")},
                "score": 1.0
            })
        return results

    def generate_response(self, query, context):
        if not self.documents:
            return "Please upload documents first."

        return f"Answer for: {query}"
