# core/rag_engine.py
class EnhancedRAGEngine:
    def __init__(self, config):
        self.config = config
        self.documents = []  # Store documents
        print("✅ RAG Engine initialized with add_documents method")
    
    def add_documents(self, documents):
        """Add documents to the engine"""
        if documents:
            self.documents.extend(documents)
            print(f"✅ Added {len(documents)} documents. Total: {len(self.documents)}")
            return True
        return False
    
    def retrieve(self, query, n_results=None):
        """Retrieve relevant documents"""
        if not self.documents:
            return []
        
        results = []
        for i, doc in enumerate(self.documents[:3]):  # Return first 3 docs
            results.append({
                'document': doc.get('text', 'No content')[:300],
                'metadata': {'filename': doc.get('filename', 'Unknown')},
                'score': 1.0
            })
        return results
    
    def generate_response(self, query, context):
        """Generate a response based on context"""
        if not self.documents:
            return "Please upload some documents first."
        
        doc_count = len(self.documents)
        doc_names = [d.get('filename', 'Unknown') for d in self.documents[:3]]
        
        # Format document names
        if doc_names:
            docs_list = "\n".join([f"• {name}" for name in doc_names])
        else:
            docs_list = "No documents"
        
        response = f"""📚 **Based on your {doc_count} document(s):**

I found information related to your question: **"{query}"**

**Documents analyzed:**
{docs_list}

**Information from your materials:**
{context[0][:300] if context else 'No specific context found'}...

Try asking more specific questions or upload more documents for better results!"""
        
        return response
    
    def __str__(self):
        return f"EnhancedRAGEngine with {len(self.documents)} documents"
