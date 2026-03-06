# core/document_processor.py
class DocumentProcessor:
    def __init__(self, config=None):
        self.config = config
    
    def process_file(self, file_path):
        """Simple file processor"""
        import os
        filename = os.path.basename(file_path)
        
        # Try to read text file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()[:1000]  # First 1000 chars
        except:
            text = f"Sample content from {filename}"
        
        return {
            "doc_id": filename,
            "filename": filename,
            "text": text,
            "metadata": {"source": filename}
        }