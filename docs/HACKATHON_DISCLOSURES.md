# BrandShield AI — Hackathon Disclosures & AI Declarations

## 1. External APIs & AI Model Disclosures

| Technology | Role | Provider / Library | Execution Mode |
| :--- | :--- | :--- | :--- |
| **Sentence Transformers (`all-MiniLM-L6-v2`)** | Embedding generation for brand guideline document chunks | HuggingFace / Local PyTorch | 100% Local (Runs on CPU/GPU offline) |
| **ChromaDB** | Semantic vector storage and similarity retrieval | Chroma Core Client | 100% Local Persistent Storage |
| **Google Gemini API (`gemini-1.5-flash`)** | Contextual multimodal visual inspection & editorial copy refinement | Google Cloud GenAI | Cloud API (With offline deterministic fallbacks) |
| **OpenCV (`opencv-python-headless`)** | K-Means color quantization, dominant color clustering | Open Source Computer Vision | 100% Local Deterministic Computation |
| **PyMuPDF (`fitz`) & python-docx** | Document extraction (PDF, DOCX, TXT) | Open Source Libraries | 100% Local File Processing |

### Offline Graceful Degradation:
BrandShield AI does **NOT** crash if external API keys or cloud connections are absent:
- If `GEMINI_API_KEY` is not provided, the platform executes deterministic rule-based correction synthesis, OpenCV color delta calculations, and WCAG contrast algorithms.
- 100% of automated unit, integration, and scenario tests run offline without paid API dependencies.

---

## 2. Reused Libraries & Open-Source Disclosures
- **FastAPI / Starlette:** Backend REST API routing and middleware
- **Streamlit:** Frontend presentation and reactive UI components
- **SQLAlchemy:** Relational ORM for SQLite
- **Pydantic V2:** Request/response schema validation
- **PyJWT & Bcrypt:** Secure cryptographic hashing and bearer token lifecycle
- **Pytest & Pytest-Asyncio:** Test automation runner

---

## 3. Synthetic Data Declaration
All demonstration data for the fictional enterprise **"NovaTech Global"** (including product specifications for the *NovaBook Pro*, mock warranty documents, and synthetic logos) is strictly synthetic and created solely for hackathon testing and evaluation. No proprietary or confidential corporate data was used.
