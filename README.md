# Sentinel AI

Watch the full project walkthrough:  
https://youtu.be/kyne3G_owR4?si=TSCfTjFPft7LxTdB

---

# 🤖 Offline AI Assistant

A fully containerized **offline AI assistant** built using:

- FastAPI (Backend API)
- Ollama (Local LLM)
- Qdrant (Vector Database)
- LangChain (RAG Pipeline)
- Docker Compose (Service Orchestration)

This project enables document-based question answering using a local LLM without external APIs.

---

# 📁 Project Structure

```
offline-ai-assistant/
│
├── backend/
├── frontend/
├── data/
├── docker-compose.yml
└── README.md
```

---

# ⚙️ Requirements

- Docker Desktop
- WSL2 (for Windows)
- Minimum 8GB RAM recommended

---

# 🚀 Setup Instructions

## 1️⃣ Start Services

```bash
docker compose up -d
```

## 2️⃣ Pull LLM Model (Required)

```bash
docker exec -it ollama ollama pull llama3
```

Verify:

```bash
docker exec -it ollama ollama list
```

---

# 🌐 Access the Application

Frontend:
```
http://localhost:8080
```

Backend API Docs:
```
http://localhost:8000/docs
```

---

# 📄 How to Use

1. Open `http://localhost:8080`
2. Upload PDF / CSV / Excel documents
3. Ask questions based on uploaded documents
4. The system retrieves relevant context and generates answers locally

---

# 🐳 Services

- **ollama** – Local LLM inference  
- **qdrant** – Vector storage  
- **backend** – API and RAG logic  
- **frontend** – Web interface  

---

# 🔄 Reset (If Needed)

```bash
docker compose down -v
docker compose up -d --build
```

---

# 📌 Notes

- The system runs fully offline after the model is downloaded.
- Use quantized models for better CPU performance if needed.
