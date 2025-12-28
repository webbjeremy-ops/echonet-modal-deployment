# echonet-modal-deployment
Official implementation for 'A Serverless, Dual-Model Architecture for Automated Echocardiography Feedback'

# Serverless Echocardiography: Dual-Model Architecture for Educational Feedback

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Powered by Modal](https://img.shields.io/badge/Compute-Modal-green)](https://modal.com)

**Official Code Repository for the Manuscript:**
> *"Democratizing Deliberate Practice: Development and Validation of a Serverless, Dual-Model AI Tool for Automated Echocardiography Feedback"*

---

## 📋 Overview
This repository contains the reference implementation of a **Scale-to-Zero** deep learning architecture designed to democratize access to advanced echocardiography analysis. 

Unlike traditional deployments that require expensive, always-on GPU servers ($400+/mo), this system runs on **Modal**, a serverless platform that provisions NVIDIA T4 GPUs only during active inference. This results in an idle cost of **$0.00/mo**, making clinical-grade AI accessible to residency programs and educational workshops.

### Key Features
* **💡 Zero-Cost Idle:** Auto-scaling infrastructure ensures you only pay for the seconds the GPU is running.
* **🛡️ Dual-Model Safety:** A Multimodal LLM (Gemini 2.5 Flash) acts as a "Triage Nurse," verifying the anatomical view (Apical 4-Chamber) before the CNN runs.
* **🎓 Blinded Feedback Loop:** Designed for "Deliberate Practice," requiring trainees to estimate LVEF visually before seeing the AI quantification.
* **🔄 Universal Ingestion:** Automatically handles transcoding for MP4, AVI, and GIF formats.

---

## 🏗️ System Architecture

The system utilizes a decoupled microservices approach.

```text
[ USER / TRAINEE ]
       │
       ▼
[ REACT FRONTEND ] ──────────────┐
       │                         │
       ▼                         │
[ SUPABASE STORAGE ]             │
       │                         │ (Feedback Loop)
       ▼                         │
┌─────────────────────────────┐  │
│ SERVERLESS BACKEND (MODAL)  │  │
│                             │  │
│  1. TRIAGE LAYER (LLM)      │  │
│     (Gemini 2.5 Flash)      │  │
│          │                  │  │
│          ▼                  │  │
│     Is View Valid? ──NO────►│──┘
│          │                  │
│          YES                │
│          ▼                  │
│  2. QUANTIFICATION (CNN)    │
│     (EchoNet-Dynamic)       │
│          │                  │
└──────────┼──────────────────┘
           │
           ▼
[ RESULT DATABASE ] ─────────────► [ DELTA DISPLAY ]

The inference backend is defined entirely as code using Python and Modal.

---

## 🛠️ Deployment Guide (Backend)

The inference backend is defined entirely as code using Python and Modal.

### Prerequisites
* Python 3.12+
* A [Modal.com](https://modal.com) account
* A [Supabase](https://supabase.com) project (for storage/auth)

### 1. Installation
Clone the repository and install dependencies:
```bash
git clone [https://github.com/YOUR_USERNAME/serverless-echo-edu.git](https://github.com/YOUR_USERNAME/serverless-echo-edu.git)
cd serverless-echo-edu
pip install -r backend/requirements.txt

### 2. Configure Secrets
Set up your cloud credentials securely using Modal's secret manager. This prevents sensitive API keys from being hardcoded in your scripts.

modal secret create my-app-secrets \
    SUPABASE_URL=your_supabase_url \
    SUPABASE_KEY=your_supabase_key \
    GEMINI_API_KEY=your_google_api_key

### 3. Deploy to Cloud
Push the serverless function to the cloud with a single command.

modal deploy backend/app.py

Note: The system will automatically build the container, download the model weights, and provision the endpoint.

### Next Step
This completes the setup for your GitHub repository. Now that your "Digital Appendix" is ready, we can move back to the manuscript itself.

Shall I write the full text for the **Introduction** section of the paper now, focusing on the "Competency-Based Medical Education" narrative we discussed?
