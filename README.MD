# CVAlyze Prototype - POC Documentation

> **Proof of Concept experiments for CV text extraction and AI-powered data extraction**

[![Repository](https://img.shields.io/badge/GitHub-CVAlyze--Prototype-blue?logo=github)](https://github.com/me-Afzal/CVAlyze-Prototype)

---

## 📋 Project Context

**CVAlyze** is an AI-powered CV analysis platform designed to extract structured data from unstructured resumes (PDF, DOCX, TXT) with speed and accuracy for streamlined recruitment processes.

This repository documents the experimental approaches tested to identify the optimal solution for production deployment.

---

## 🧪 POC Experiments

### 1️⃣ Text Extraction Layer

#### ❌ Initial Approach: Docling
**Experiment File:** [`Docling.ipynb`](https://github.com/me-Afzal/CVAlyze-Prototype/blob/main/Docling.ipynb)

**Issues Identified:**
- Slow processing due to neural network architecture
- Failed to extract hyperlinks from documents
- Not suitable for real-time processing

**Verdict:** Rejected

---

#### ✅ Final Approach: Dedicated Libraries

**Tools Used:**
- **PyMuPDF** - Fast PDF text extraction
- **pdfplumber** - Enhanced PDF parsing with table support
- **python-docx** - DOCX file handling

**Advantages:**
- ⚡ Fast extraction (< 1 second)
- 🔗 Hyperlink support
- 🪶 Lightweight and efficient
- 🧹 Post-processing: Token cleaning to reduce LLM request size

**Verdict:** ✅ Adopted for production

---

### 2️⃣ Structured Data Extraction

#### ❌ Approach 1: Regex Patterns

**Issues:**
- Low accuracy due to dynamic CV formats across professions
- Hard to maintain and scale

**Verdict:** Outdated approach

---

#### ❌ Approach 2: Local LLMs
**Experiment File:** [`Q-model.ipynb`](https://github.com/me-Afzal/CVAlyze-Prototype/blob/main/Q-model.ipynb)

**Models Tested (Quantized):**

| Model | Response Time | Issues |
|-------|--------------|--------|
| Mistral-7B-Instruct | 1:40 min | Too slow |
| Ministral-3b-Instruct | 1:34 min | Hallucinations + slow |
| LLaMA 2/3 | ~1:40 min | Similar to Mistral-7B |

**Root Cause:** Infrastructure limitations (CPU-only Kubernetes nodes; GPU instances required)

**Verdict:** ❌ Not viable for production without GPU infrastructure

---

#### ❌ Approach 3: Chunk-Based RAG
**Experiment File:** [`RAG-ext.ipynb`](https://github.com/me-Afzal/CVAlyze-Prototype/blob/main/RAG-ext.ipynb) (Chunking section)

**Setup:**
- Text chunking → Embeddings → Gemini API requests

**Issues:**
- ⏱️ Slow due to embedding overhead
- 📊 High token count from chunk redundancy
- 💰 Increased API costs and complexity

**Verdict:** ❌ Inefficient for single-document extraction

---

#### ✅ Approach 4: Custom RAG (No Chunking)
**Experiment File:** [`RAG-ext.ipynb`](https://github.com/me-Afzal/CVAlyze-Prototype/blob/main/RAG-ext.ipynb) (No-chunking section)

**Configuration:**
- **LLM:** Gemini API 2.5 Flash
- **Strategy:** Single API request per CV with structured JSON output
- **Prompt Engineering:** Custom system prompt to extract all fields in one call

**Constraints Addressed:**
| Constraint | Solution |
|------------|----------|
| API Rate Limit (200 req/day) | Batch extraction strategy |
| Token Limit | No chunking = reduced tokens |
| Processing Speed | Single-pass extraction |

**Performance:**
- ⚡ **3-4 seconds** per CV
- 🎯 High accuracy (LLM-based understanding)
- 💰 Token-efficient

**Verdict:** ✅ Production-ready

---

## 🏗️ Implementation

### Custom RAG Class

**Purpose:** Reusable extraction logic for ETL microservice

**Pipeline:**
```
CV Upload → Text Extraction → Token Cleaning → Custom RAG → JSON Output
```

**Input:** Cleaned CV text  
**Output:** Structured JSON
```json
{
  "name": "...",
  "email": "...",
  "phone": "...",
  "skills": [...],
  "experience": [...],
  "education": [...]
}
```

**Features:**
- Single-pass extraction
- Token-efficient prompting
- Rate-limit aware design
- Reusable across ETL microservice

---

## 📊 Key Outcomes

| Metric | Result |
|--------|--------|
| **Text Extraction Speed** | < 1 second |
| **Data Extraction Speed** | 3-4 seconds |
| **Accuracy** | High (LLM-based) |
| **Token Efficiency** | Optimized (no chunking) |
| **Scalability** | Rate-limit conscious |
| **Production Readiness** | ✅ Ready |

---

## 🛠️ Technical Stack
```
Text Extraction: PyMuPDF + pdfplumber + python-docx
LLM: Gemini API 2.5 Flash
Architecture: Custom RAG without chunking
Deployment Target: GCP Kubernetes (ETL Microservice)
```

---

## 💡 Lessons Learned

1. **Local LLMs:** Not viable without GPU infrastructure in production environments
2. **Chunking:** Adds unnecessary overhead for single-document structured extraction
3. **Single-pass extraction:** Most efficient approach for CV parsing
4. **API rate limits:** Design for batch processing from day one
5. **Specialized libraries:** Purpose-built tools (PyMuPDF) outperform general-purpose solutions (Docling) for speed-critical tasks

---

## 📁 Repository Structure
```
CVAlyze-Prototype/
├── Docling.ipynb          # Docling text extraction testing
├── Q-model.ipynb          # Local LLM quantized model testing
├── RAG-ext.ipynb          # RAG with/without chunking experiments
└── README.md              # This file
```

---

## 🚀 Next Steps

- [ ] Integrate Custom RAG class into ETL microservice
- [ ] Implement rate-limiting queue for bulk CV uploads
- [ ] Monitor token usage and optimize prompts
- [ ] Add error handling and retry logic
- [ ] Performance benchmarking with real-world CV datasets

---

## 🔗 Related Links

- **Main Project:** [CVAlyze Platform](https://github.com/me-Afzal/CVAlyze)
- **Documentation:** [Full System Architecture](#)
- **API Documentation:** [ETL Microservice API](#)

---

## 📄 License

This is a proof-of-concept repository for the CVAlyze project.

---

## 👤 Author

**Afzal**  
[![GitHub](https://img.shields.io/badge/GitHub-me--Afzal-black?logo=github)](https://github.com/me-Afzal)

---

**Last Updated:** October 2025