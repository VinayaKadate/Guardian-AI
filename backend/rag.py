import os
from typing import List, Dict
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from pypdf import PdfReader
import pandas as pd
import ollama

class RAGPipeline:
    def __init__(self, qdrant_host: str, qdrant_port: int, ollama_host: str):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.collection_name = "documents"
        self.ollama_host = ollama_host
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        self._ensure_collection()
    
    def _ensure_collection(self):
        collections = self.qdrant_client.get_collections().collections
        if not any(c.name == self.collection_name for c in collections):
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "size": 384,
                    "distance": "Cosine"
                }
            )
    
    def load_pdf(self, file_path: str, filename: str) -> List[Dict]:
        reader = PdfReader(file_path)
        chunks = []
        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            page_chunks = self.text_splitter.split_text(text)
            for chunk in page_chunks:
                chunks.append({
                    'content': chunk,
                    'metadata': {
                        'source': filename,
                        'page': page_num,
                        'type': 'pdf'
                    }
                })
        return chunks
    
    def load_excel(self, file_path: str, filename: str) -> List[Dict]:
        chunks = []
        xl_file = pd.ExcelFile(file_path)
        for sheet_name in xl_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            for idx, row in df.iterrows():
                row_text = " | ".join([f"{col}: {val}" for col, val in row.items()])
                chunks.append({
                    'content': row_text,
                    'metadata': {
                        'source': filename,
                        'sheet': sheet_name,
                        'row': idx + 2,
                        'type': 'excel'
                    }
                })
        return chunks
    
    def load_csv(self, file_path: str, filename: str) -> List[Dict]:
        chunks = []
        df = pd.read_csv(file_path)
        for idx, row in df.iterrows():
            row_text = " | ".join([f"{col}: {val}" for col, val in row.items()])
            chunks.append({
                'content': row_text,
                'metadata': {
                    'source': filename,
                    'row': idx + 2,
                    'type': 'csv'
                }
            })
        return chunks
    
    def index_chunks(self, chunks: List[Dict]):
        texts = [c['content'] for c in chunks]
        metadatas = [c['metadata'] for c in chunks]
        
        Qdrant.from_texts(
            texts=texts,
            embedding=self.embeddings,
            metadatas=metadatas,
            collection_name=self.collection_name,
            url=f"http://{os.getenv('QDRANT_HOST')}:{os.getenv('QDRANT_PORT')}"
        )
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        vectorstore = Qdrant(
            client=self.qdrant_client,
            collection_name=self.collection_name,
            embeddings=self.embeddings
        )
        results = vectorstore.similarity_search(query, k=top_k)
        return [{
            'content': doc.page_content,
            'metadata': doc.metadata
        } for doc in results]
    
    def generate_answer(self, query: str, context_docs: List[Dict]) -> str:
        context = "\n\n".join([f"[{d['metadata']['source']}] {d['content']}" 
                               for d in context_docs])
        
        prompt = f"""Based on the following context, answer the question. If the answer is not in the context, say so.

Context:
{context}

Question: {query}

Answer:"""
        
        response = ollama.chat(
            model='llama3',
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0.3}
        )
        
        return response['message']['content']