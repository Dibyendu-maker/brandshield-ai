# CodeZen India 2026 Round 2: Final Submission Answers

**Project Name:** BrandShield AI  
**Tagline:** *Every piece of content. One trusted brand identity.*  
**Track/Category:** AI-Powered Brand Governance & Content Compliance  
**Author:** Sole Developer Submission  
**Latest Verified Commit:** `25fba6581a2b8cc2c2efe76b45d447a284f650dc`  
**Test Suite Status:** 29/29 Passed (100% Pass Rate)

---

## 1. Project Submission Links

- **Functioning Project Link (Public Web Application):**  
  `[INSERT DEPLOYED APPLICATION URL HERE — e.g., https://brandshield-ai.streamlit.app]`

- **Public Source-Code Repository Link:**  
  `[INSERT PUBLIC GITHUB REPOSITORY URL HERE — e.g., https://github.com/your-username/brandshield-ai]`

- **Google Drive Project PDF Link:**  
  `[INSERT GOOGLE DRIVE PDF URL HERE — e.g., https://drive.google.com/file/d/your-pdf-id/view?usp=sharing]`  
  *(Generated PDF is available locally in the repository at `docs/BrandShield_AI_Round2_Submission.pdf`)*

---

## 2. What You Built

BrandShield AI is an enterprise-grade brand governance and pre-publication compliance platform that protects corporate identity across decentralized, multi-channel marketing workflows. As marketing teams, agencies, and generative AI tools produce content at scale, enterprises face severe brand risks: factual contradictions (inaccurate hardware specs, wrong prices, conflicting warranties), prohibited superlatives ("world's number one", "100% guaranteed"), tone inconsistency, and visual/accessibility violations.

BrandShield AI acts as an intelligent pre-publication checkpoint coupling deterministic ground-truth verification with modular AI auditing and human-in-the-loop review governance:

1. **Multiformat Ingestion:** Ingests direct plain text, Markdown, documents (PDF, DOCX, TXT), and visual brand assets (PNG, JPG, WEBP).
2. **Hybrid Brand Knowledge Engine:** Combines verified relational specifications (exact numbers, units, and dates stored in SQLite) with an unstructured vector vault (ChromaDB + `all-MiniLM-L6-v2` embeddings) for semantic guideline search.
3. **Modular Compliance Engine:** Evaluates submissions across 5 distinct linguistic and factual analyzers (Factual Spec Matcher, Prohibited Terminology Linter, Superlative Claim Classifier, Tone/Voice Analyzer, and Mandatory Messaging Alignment), generating structured, explainable findings cited to approved source documents and calculating a transparent weighted compliance score.
4. **Multimodal Computer Vision & Accessibility:** Uses OpenCV K-Means clustering (k=5) to extract dominant colors, computes Delta-E distance to approved brand palettes, calculates WCAG 2.1 AA relative luminance contrast ratios (4.5:1 text, 3:1 components), and runs readability heuristics.
5. **AI Correction Studio:** Non-destructive revision environment providing side-by-side comparisons, word-level visual diff analysis (equal, deleted, inserted), and intent-preserving rewrite synthesis that surgically fixes violations while preserving the creator's promotional tone.
6. **Human-Controlled Review Workflow:** 7-state governance lifecycle (`Draft` → `Submitted` → `Under Review` → `Changes Requested` → `Resubmitted` → `Approved` / `Rejected`) with role-based action gating (Reviewers/Admins approve; Creators submit and edit) and an immutable collaborative comment ledger.
7. **Governance Analytics & Policy Advice:** Aggregated trend analytics highlighting recurring organizational mistakes, category distributions, and automated clarity recommendations for brand leadership.
8. **Resilience & Tenant Isolation:** Multi-tenant organization boundaries strictly isolated at the database layer, active submission restoration across browser reloads via URL query parameters (`?sub_id=...`), and graceful offline backend detection.

---

## 3. Technology and Implementation Details

- **Backend Architecture:**  
  Built with **Python 3.12** and **FastAPI** (`/api/v1`), structured into modular routers (`auth`, `brand`, `content`, `compliance`, `workflow`, `analytics`). Request/response contracts are strictly validated using **Pydantic V2** schemas.
- **Frontend Presentation Layer:**  
  Engineered with **Streamlit** featuring a dark navy SaaS theme (`#0B132B`, `#1E293B`, `#0284C7`), responsive custom CSS components (status badges, severity pills, score meters, diff visualizers), and a 1-click Role Persona Switcher for effortless evaluator inspection.
- **Database & Persistence:**  
  Relational schema managed via **SQLAlchemy 2.0** ORM over **SQLite**, storing tenants (`Organization`), identities (`User`), guidelines (`BrandGuideline`), verified specifications (`BrandFact`), submissions (`ContentSubmission`), structured findings (`ComplianceFinding`), versioned edits (`ContentRevision`), and governance discussions (`ReviewComment`).
- **Semantic Retrieval (Vector Vault):**  
  Powered by **ChromaDB** using local `sentence-transformers/all-MiniLM-L6-v2` embeddings (384-dimensional dense vectors), partitioned into tenant-isolated collections (`org_{id}_vault`).
- **Computer Vision & Multimodal Inspection:**  
  - Local deterministic color extraction: **OpenCV** (`opencv-python-headless`) K-Means clustering in CIE-Lab space and Euclidean Delta-E distance calculation.
  - Accessibility: WCAG 2.1 AA relative luminance ($L_1 / L_2$) contrast ratio computation.
  - Contextual AI: **Google Gemini 1.5 Flash** (`google-genai` SDK) for layout and semantic visual critique, paired with 100% offline rule-based fallbacks.
- **Security & Authentication:**  
  Cryptographic password hashing using **Bcrypt** with unique salts, stateless JWT Bearer token authentication (**PyJWT**), defense-in-depth file upload validation (25MB limit, UUID filename sanitization, MIME verification), and strict tenant-scoped data queries.
- **Testing & Code Quality:**  
  Comprehensive 29-test automated test suite (**Pytest** & **pytest-asyncio**) covering authentication, RBAC, document extraction, factual spec matching, image auditing, WCAG math, full workflow lifecycle, health endpoints, and multi-tenant isolation. 100% pass rate achieved in under 11 seconds.

---

## 4. What Changed from Original Plan, and Why?

1. **Self-Contained Local SQLite & ChromaDB Deployment:**  
   *Original Plan:* Multi-service infrastructure requiring external PostgreSQL and cloud vector database clusters (Milvus/Pinecone).  
   *Change & Rationale:* Adopted embedded SQLite via SQLAlchemy and a local ChromaDB vector client. This eliminated fragile cloud infrastructure dependencies for hackathon judges, allowed zero-friction 1-command startup (`python run_servers.py`), and guaranteed 100% offline verification while maintaining identical schema boundaries.
2. **Deterministic Rule-Based Retrieval Fallback:**  
   *Original Plan:* Exclusive reliance on cloud LLM APIs for all compliance decisions and copy synthesis.  
   *Change & Rationale:* Engineered a deterministic fallback engine (regex entity extractors, rule-based terminology linters, and local OpenCV color math) that executes in parallel with Gemini 1.5 Flash. This ensures the entire application runs reliably even in air-gapped or key-less environments with zero crashes.
3. **URL Query-Parameter Session Restoration:**  
   *Original Plan:* In-memory Streamlit session state.  
   *Change & Rationale:* Synchronized active submission IDs with browser URL parameters (`?sub_id=...`) with backend tenant authorization validation. When an evaluator refreshes their browser or switches views, the selected submission context is seamlessly restored without session loss.
4. **Direct Tab Navigation in Place of a Linear Stepper:**  
   *Original Plan:* Rigid multi-step wizard stepper forcing users through an artificial sequence.  
   *Change & Rationale:* Replaced the wizard with enterprise-standard navigation tabs and an instant Role Persona Switcher. This enables evaluators to jump directly between Executive Dashboard, Compliance Inspector, AI Correction Studio, and Human Review Workflow without synthetic progression friction.

---

## 5. What Does NOT Work Yet? (Known Limitations)

1. **Video & Rich Animation Compliance:**  
   Round 2 multimodal inspection evaluates static image formats (PNG, JPG, WEBP) and document formats (PDF, DOCX, TXT, MD). Video streams, animated GIF/MP4 assets, and interactive HTML5 display banners are not currently audited.
2. **Single-Node Embedded Relational Storage:**  
   The relational database currently runs on SQLite. While optimal for MVP demonstration, evaluation speed, and self-contained deployment, concurrent enterprise throughput across distributed cloud regions will require migration to clustered PostgreSQL (targeted for Round 3).
3. **Cloud API Dependency for Deep Contextual Image Critique:**  
   While deterministic computer vision (palette extraction, Delta-E distance, WCAG contrast) runs 100% locally on CPU without third-party services, deep semantic image critique requires an optional Google Gemini API key. If omitted, the platform gracefully executes local fallback scoring without raising errors.

---

## 6. Improvement 1: CI/CD & Automated Compliance Quality Gates (Proposed Round 3)

**Problem:** Marketers and developers currently have to manually upload assets to the web interface, which can be skipped or forgotten during fast-paced release cycles.  
**Proposed Solution:** Build automated CI/CD and Headless CMS integrations:
- **Pre-commit Git hooks and GitHub Actions:** Automatically audit markdown copy, static website assets, and documentation on pull request creation, posting inline compliance review comments and failing CI builds if Critical factual contradictions exist.
- **Headless CMS Webhooks:** Native webhook adapters for Contentful, Strapi, and Sanity that automatically intercept publication events, run the BrandShield audit asynchronously, and prevent publishing unapproved drafts until a certified Brand Reviewer signs off.

---

## 7. Improvement 2: Jurisdiction-Specific Regulatory Rulebooks (Proposed Round 3)

**Problem:** Global brands deploy campaigns across multiple countries, each governed by different legal and advertising standards (e.g. FTC in the US, ASCI in India, EU AI Act in Europe).  
**Proposed Solution:** Expand the modular compliance engine with dynamic regional regulatory rulebooks:
- **FTC Rulebook (USA):** Automated checks for mandatory influencer endorsement disclosures (`#ad`, `#sponsored`), substantiation requirements for objective claims, and dark-pattern detection.
- **ASCI Code (India):** Automated checking of comparative advertising fairness, mandatory disclaimers for financial/health claims, and font-size minimums for legal disclaimers.
- **EU AI Act Transparency Module:** Automatic labeling and audit validation for synthetic/AI-generated media, ensuring enterprise compliance with European transparency mandates.

---

## 8. Improvement 3: Active Learning & Guideline Auto-Tuning (Proposed Round 3)

**Problem:** Static corporate brand books quickly become outdated, and rigid compliance rules can produce repeated false positives that frustrate creative teams.  
**Proposed Solution:** Introduce an active learning feedback loop that learns from human governance interactions:
- **Reviewer Override Mining:** Analyze reviewer approval patterns, comment history, and creator revision diffs to identify guidelines that generate high false-positive rates or frequent overrides.
- **Automated Guideline Clarification Proposals:** When the system observes that human reviewers consistently approve a specific phrasing flagged by the AI, it automatically drafts a proposed guideline refinement for the Brand Administrator's review.
- **Adaptive Confidence Thresholds:** Dynamically calibrate severity weights and similarity thresholds based on historical organization-specific approval decisions.
