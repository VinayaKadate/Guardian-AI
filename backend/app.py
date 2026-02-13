import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import pandas as pd

from rag import RAGPipeline
from database import Database
from compliance import ComplianceChecker

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

db = Database()
rag = RAGPipeline(
    qdrant_host=os.getenv("QDRANT_HOST", "qdrant"),
    qdrant_port=int(os.getenv("QDRANT_PORT", "6333")),
    ollama_host=os.getenv("OLLAMA_HOST", "http://ollama:11434")
)
compliance = ComplianceChecker(db)

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        ext = file.filename.lower().split('.')[-1]
        
        if ext == 'pdf':
            chunks = rag.load_pdf(file_path, file.filename)
            rag.index_chunks(chunks)
        elif ext in ['xlsx', 'xls']:
            chunks = rag.load_excel(file_path, file.filename)
            rag.index_chunks(chunks)
            
            if 'ban' in file.filename.lower():
                xl_file = pd.ExcelFile(file_path)
                banned_entities = []
                for sheet_name in xl_file.sheet_names:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    for idx, row in df.iterrows():
                        for col in df.columns:
                            if 'entity' in col.lower() or 'name' in col.lower():
                                entity = str(row[col]).strip()
                                if entity and entity.lower() != 'nan':
                                    banned_entities.append({
                                        'entity': entity,
                                        'source_file': file.filename,
                                        'sheet_name': sheet_name,
                                        'row_number': idx + 2
                                    })
                if banned_entities:
                    db.add_banned_entities(banned_entities)
                    compliance.refresh_banned_list()
        elif ext == 'csv':
            chunks = rag.load_csv(file_path, file.filename)
            rag.index_chunks(chunks)
            
            if 'ban' in file.filename.lower():
                df = pd.read_csv(file_path)
                banned_entities = []
                for idx, row in df.iterrows():
                    for col in df.columns:
                        if 'entity' in col.lower() or 'name' in col.lower():
                            entity = str(row[col]).strip()
                            if entity and entity.lower() != 'nan':
                                banned_entities.append({
                                    'entity': entity,
                                    'source_file': file.filename,
                                    'sheet_name': 'N/A',
                                    'row_number': idx + 2
                                })
                if banned_entities:
                    db.add_banned_entities(banned_entities)
                    compliance.refresh_banned_list()
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        return {"message": f"File {file.filename} uploaded and indexed successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask_question(question: str = Form(...)):
    try:
        is_compliant, entity, info = compliance.check_text(question)
        if not is_compliant:
            return JSONResponse({
                "answer": None,
                "sources": [],
                "refused": True,
                "reason": f"Question contains banned entity: '{entity}'",
                "ban_info": info
            })
        
        docs = rag.search(question, top_k=3)
        
        context_texts = [d['content'] for d in docs]
        is_compliant, entity, info = compliance.check_documents(context_texts)
        if not is_compliant:
            return JSONResponse({
                "answer": None,
                "sources": [],
                "refused": True,
                "reason": f"Retrieved context contains banned entity: '{entity}'",
                "ban_info": info
            })
        
        answer = rag.generate_answer(question, docs)
        
        sources = []
        for doc in docs:
            meta = doc['metadata']
            if meta['type'] == 'pdf':
                sources.append({
                    'source': meta['source'],
                    'page': meta['page'],
                    'type': 'pdf'
                })
            elif meta['type'] in ['excel', 'csv']:
                sources.append({
                    'source': meta['source'],
                    'sheet': meta.get('sheet', 'N/A'),
                    'row': meta['row'],
                    'type': meta['type']
                })
        
        return JSONResponse({
            "answer": answer,
            "sources": sources,
            "refused": False
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}