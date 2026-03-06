# core/rag_engine.py
class EnhancedRAGEngine:
    def __init__(self, config):
        self.config = config
        self.documents = []  # Store documents
        self.document_texts = []  # Store just the texts for searching
        print("✅ RAG Engine initialized with document storage")
    
    def add_documents(self, documents):
        """Add documents to the engine"""
        if documents:
            self.documents.extend(documents)
            # Also store just the texts for simple searching
            for doc in documents:
                if doc.get('text'):
                    self.document_texts.append({
                        'filename': doc.get('filename', 'Unknown'),
                        'text': doc.get('text', '')
                    })
            print(f"✅ Added {len(documents)} documents. Total: {len(self.documents)}")
            return True
        return False
    
    def retrieve(self, query, n_results=None):
        """Retrieve relevant documents based on simple keyword matching"""
        if not self.documents:
            return []
        
        if n_results is None:
            n_results = 3
        
        # Simple keyword search
        query_words = set(query.lower().split())
        scored_docs = []
        
        for doc in self.documents:
            text = doc.get('text', '').lower()
            filename = doc.get('filename', 'Unknown')
            
            # Count how many query words appear in the text
            score = 0
            for word in query_words:
                if word in text and len(word) > 3:  # Only count meaningful words
                    score += 1
            
            # Normalize score
            if query_words:
                score = score / len(query_words)
            
            scored_docs.append({
                'document': text[:500] + "..." if len(text) > 500 else text,
                'metadata': {'filename': filename},
                'score': score,
                'full_text': text
            })
        
        # Sort by score (highest first) and return top results
        scored_docs.sort(key=lambda x: x['score'], reverse=True)
        return scored_docs[:n_results]
    
    def generate_response(self, query, context):
        """Generate a response based on context"""
        if not self.documents:
            return "📁 **No documents uploaded yet.** Please upload some files first."
        
        # Get document info
        doc_count = len(self.documents)
        doc_names = [d.get('filename', 'Unknown') for d in self.documents]
        
        # Search for relevant content
        relevant_docs = self.retrieve(query, n_results=2)
        
        if relevant_docs and relevant_docs[0]['score'] > 0:
            # Found relevant content
            best_match = relevant_docs[0]
            filename = best_match['metadata']['filename']
            content = best_match['document']
            score = best_match['score']
            
            response = f"""📚 **Found information in your documents!**

**Question:** {query}

**Relevant content from** `{filename}`:
> {content}

**Confidence:** {score:.1%} match

**All documents searched:** {', '.join(doc_names[:3])}{'...' if len(doc_names) > 3 else ''}

*You can ask follow-up questions or upload more documents for better results.*"""
        else:
            # No relevant content found
            response = f"""🔍 **No specific information found for:** "{query}"

I searched through {doc_count} document(s):
{chr(10).join(['• ' + name for name in doc_names[:5]])}

**Suggestions:**
• Try rephrasing your question
• Ask about a different topic
• Upload more relevant documents
• Make sure your PDF contains searchable text (not scanned images)

**Your uploaded files contain text - I can see them, but couldn't find exact matches for your query.**"""
        
        return response
    
    def get_document_list(self):
        """Return list of uploaded documents"""
        return [doc.get('filename', 'Unknown') for doc in self.documents]