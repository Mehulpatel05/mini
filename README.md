# Apex Sentinel: AI-Based Insider Threat Detection Pipeline

Apex Sentinel is a state-of-the-art corporate threat intelligence system that identifies anomalous employee behaviors (insider threats) using behavioral feature engineering and an unsupervised deep learning **Keras Autoencoder**.

The application aggregates raw daily logs, scales behavioral deviations, scores risk metrics (0-100), flags security violations, and provides a web-based administration console for compliance review.

---

## 🚀 Key Features

1. **Synthetic Data Generator (`generate_data.py`):** Simulates 60 employees over 120 days (~54,000 logs), injecting normal baselines and 3% realistic threat vectors (odd-hour bulk downloads, cross-department file snooping, travel coordinates anomaly, resignation-week USB dumps).
2. **Feature Engineering Pipeline (`feature_engineering.py`):** Aggregates raw logs into daily user profiles calculating circular login hour deviations, historical transfer z-scores, weekend access, role-boundary violations, 7-day rolling USB use, and 7-day location diversity.
3. **Deep Learning Model (`train_models.py`):** Trains a **Keras Autoencoder** (trained only on normal data) to flag anomalies using reconstruction Mean Squared Error (MSE), normalized to a calibrated 0-100 risk score (outperforms Isolation Forest baseline with **F1: 0.93** and **ROC-AUC: 0.99**).
4. **Real-time Risk Scoring Engine (`risk_engine.py`):** Evaluates live activity logs, recalculates historical baselines, maps scores to risk tiers (Low <40, Medium 40-70, High >70), and writes critical events to `alerts_log.csv`.
5. **FastAPI Backend Server (`backend/main.py`):** Exposes REST API endpoints for user directories, timeline history, alerts feed, interactive simulation, and dynamic PDF audit report generation.
6. **React Admin Dashboard (`frontend/`):** A premium, glassmorphic dark-themed UI built using Vite and Recharts to visualize threat parameters, filter directory logs, and simulate live threat injections.
7. **Compliance PDF Reports (`backend/pdf_generator.py`):** Generates audit-ready incident reports containing executive summaries, statistics, peak timeline logs, and sign-off blocks.

---

## 📂 Project Architecture

```text
AI-Based/
├── backend/
│   ├── main.py                 # FastAPI backend server
│   └── pdf_generator.py        # FPDF2 compliance PDF builder
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # React dashboard controller
│   │   ├── App.css             # Dashboard specific stylesheets
│   │   ├── index.css           # Global resets and CSS variables
│   │   └── main.jsx            # React entry point
│   ├── package.json            # Frontend dependency list
│   └── vite.config.js          # Vite config
├── data/
│   ├── synthetic_insider_logs.csv # Raw simulated logs database (Phase 1)
│   ├── features.csv            # Engineered daily features (Phase 3)
│   └── reports/                # Output folder for audit PDFs (Phase 8)
├── models/
│   ├── anomaly_model.pkl       # Scalers and model configs (Phase 4)
│   └── autoencoder_model.keras # Serialized Keras neural network weights
├── notebooks/
│   ├── eda_analysis.ipynb      # Jupyter Notebook for EDA (Phase 2)
│   └── eda_outputs/            # Saved EDA visualization plots
├── generate_data.py            # Simulated log generator script
├── feature_engineering.py      # Behavioral feature calculator script
├── train_models.py             # ML/DL training script
├── risk_engine.py              # Ingestion evaluator and alerter
├── alerts_log.csv              # High-risk audit logs
├── requirements.txt            # Python virtual environment freeze
├── dashboard_screenshot.jpg    # UI mockup screenshot for presentations
└── README.md                   # Setup and manual run guidelines
```

---

## 🛠️ Setup & Installation Instructions

Follow these steps to configure the virtual environment and initialize the pipeline datasets and models:

### 1. Configure the Python Virtual Environment
Open PowerShell/Command Prompt in the project directory:
```bash
# Create the virtual environment
python -m venv .venv

# Activate the virtual environment (Windows)
.venv\Scripts\activate

# Install all backend packages
pip install -r requirements.txt
```

### 2. Configure the React Frontend Node Packages
Open a terminal in the `frontend` subdirectory:
```bash
# Navigate to frontend and install
cd frontend
npm install
```

---

## 🔄 Initialize the Pipeline (Step-by-Step)

If you need to regenerate the data, features, and model from scratch, execute the scripts in order:

```bash
# Step 1: Generate the raw activity logs (generates data/synthetic_insider_logs.csv)
python generate_data.py

# Step 2: Compute behavioral daily aggregates (generates data/features.csv)
python feature_engineering.py

# Step 3: Train models & output scalers (generates models/autoencoder_model.keras)
python train_models.py
```

---

## 🚀 Running the Web Application

To run the complete system, you must start the backend API and the frontend dev server concurrently:

### A. Start the Backend API (FastAPI)
Run from the project root:
```bash
# Starts Uvicorn server on http://127.0.0.1:8000
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### B. Start the Frontend UI (React + Vite)
Run from the `frontend/` subdirectory:
```bash
# Starts React development server on http://localhost:5173/
npm run dev
```

---

## 🔑 Authentication Credentials

Log into the React dashboard via `http://localhost:5173/` using:
- **Security Administrator View (Full read/write rights + Live Simulator):**
  - **Username:** `admin` | **Password:** `admin`
- **Security Analyst View (Read-Only Directory + Alerts feed):**
  - **Username:** `analyst` | **Password:** `analyst`

---

## 📑 Generating PDF Compliance Reports

You can download an audit-ready compliance PDF report for any user:
- **Directly from the UI:** Select any employee in the Monitored Directory and click the **"Export PDF"** button in the header.
- **Directly via Endpoint:** Call the REST API directly:
  `GET http://localhost:8000/reports/{user_id}` (e.g., `http://localhost:8000/reports/EMP001`).
  *Reports are generated dynamically and saved to `data/reports/`.*

---

## 🖼️ Screenshots & Assets

We have generated and saved a premium high-resolution mockup image of the user interface at:
👉 **[`dashboard_screenshot.jpg`](file:///c:/Users/swatm/Desktop/AI-Based/dashboard_screenshot.jpg)** (located in the project root directory).
*You can copy this file directly into your PowerPoint slides or project report documents.*
