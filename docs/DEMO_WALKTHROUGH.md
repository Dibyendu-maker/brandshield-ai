# BrandShield AI — Hackathon Judge Demonstration Walkthrough

This guide provides a 5-minute step-by-step walkthrough for evaluating BrandShield AI against the official Round 2 judging criteria.

---

## Step 1: Launch Application
Run the launcher from the project directory:
```bash
python run_servers.py
```
Open your browser to: **http://localhost:8501**

---

## Step 2: The NovaTech 1-Click Demonstration
1. In the **Executive Dashboard**, locate the quickstart banner.
2. Click **"🚀 Load NovaTech Demo"**.
3. The platform automatically:
   - Submits the canonical flawed advertisement copy:
     > *"Introducing NovaBook Pro! The world's number one laptop with 24 hours of battery life and a 5-year warranty. Guaranteed success for every user!"*
   - Executes the modular compliance audit.
   - Calculates the penalized compliance score (~26%).
   - Generates the evidence-backed findings.

---

## Step 3: Inspect Evidence & Violations (Improvement 1)
1. In the sidebar, select **"🔍 Compliance Inspector"**.
2. Expand the detected findings to see:
   - **Finding 1 [CRITICAL] FACTUAL:** Battery claim of 24 hours conflicts with approved 12 hours (*Source: NovaBook Pro Hardware Spec Sheet 2026, Section 3.2*).
   - **Finding 2 [CRITICAL] FACTUAL:** 5-year warranty contradicts approved 1-year warranty (*Source: Global Warranty Policy 2026*).
   - **Finding 3 [HIGH] CLAIM:** *"world's number one laptop"* is flagged as an unsupported superiority superlative under FTC advertising standards.
   - **Finding 4 [HIGH] TERMINOLOGY:** *"Guaranteed success"* is flagged as an explicitly prohibited phrase.
   - **Finding 5 [MEDIUM] TONE:** Multiple exclamation points violate calm enterprise tone.

---

## Step 4: Test the AI Correction Studio
1. Select **"🛠️ AI Correction Studio"** in the sidebar.
2. Review the **Interactive Side-by-Side Comparison**:
   - Original flawed copy vs BrandShield AI's compliant rewrite:
     > *"Introducing NovaBook Pro, an AI-powered productivity laptop offering up to 12 hours of battery life and backed by a 1-year warranty."*
3. Inspect the **Word-Level Diff Analysis** (deletions in red strikethrough, approved additions in green).
4. Click **"💾 Save as New Revision"**.
5. Notice that the compliance score immediately updates from ~26% to **95%+ (Compliant)**!

---

## Step 5: Test the Human Review Workflow (Improvement 3)
1. In the sidebar, select **"⚖️ Human Review Workflow"**.
2. Click **"📤 Submit for Review"** (Status changes to `Submitted`).
3. Switch Persona in the sidebar to **"Reviewer (Sarah)"**.
4. Review Sarah's dashboard and notice the **"✅ Approve for Publication"** button is now enabled.
5. Add a reviewer comment: *"Reviewed specifications against Q4 catalog. Copy is verified and approved."*
6. Click **"✅ Approve for Publication"**.
7. The status permanently updates to `Approved`, logging the transition in the audit trail.

---

## Step 6: Multimodal Visual Brand Inspection (Improvement 2)
1. Go to **"✍️ Content Submission"** &rarr; **"📁 Document / Image Upload"**.
2. Title: *"Q4 Media Kit Banner"*.
3. Upload `sample_data/unapproved_promo_banner.png`.
4. Run Audit. Notice the engine detects:
   - **[HIGH] VISUAL:** Dominant color deviation (bright red #DC2626 deviates from approved navy/teal palette).
   - **[MEDIUM] ACCESSIBILITY:** Color contrast ratio failure (< 3:1).
5. Now test `sample_data/novatech_logo_compliant.png`—notice that dominant colors pass alignment with #0B132B.

---

## Step 7: Governance Analytics & Policy Advice
1. Select **"📈 Governance Analytics"** in the sidebar.
2. View the organizational trends:
   - Violations by category (Factual, Claim, Terminology)
   - Repeated terminology mistakes
   - Approval vs rejection rates
3. Review the **Automated Brand Guideline Clarity Suggestions** advising marketing leaders where guidelines need clarification.
