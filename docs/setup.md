# Developer Environment Setup Guide

This guide describes how to configure dependencies, local blockchain nodes, IPFS daemons, and launch the backend and frontend services.

---

## 1. Prerequisites
- **Python**: Version 3.10+ (Tested on Python 3.13.5).
- **Node.js & npm** (Optional for Ganache CLI / hardhat): Node.js v18+.
- **Git**: Installed and configured.

---

## 2. Virtual Environment & Dependency Installation

1. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # Linux / macOS:
   source venv/bin/activate
   ```

2. Install project dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure Environment Variables:
   ```bash
   cp .env.example .env
   ```

---

## 3. Blockchain Setup (Ganache Local EVM)

### Option A: Ganache GUI
1. Download and run Ganache from Truffle Suite.
2. Create a workspace with RPC Server `HTTP://127.0.0.1:8545` and Port `8545`. Network ID: `1337` or `5777`.

### Option B: Ganache CLI
1. Run via npx:
   ```bash
   npx ganache --port 8545 --networkId 1337
   ```

### Option C: Simulated Local Provider
For unit testing and automated CI, tests use Ethereum Tester Provider or automated Ganache RPC mocks without requiring external dependencies.

---

## 4. IPFS Storage Setup

### Option A: Local Kubo Node
1. Install Kubo from [ipfs.tech](https://docs.ipfs.tech/install/).
2. Initialize and run daemon:
   ```bash
   ipfs init
   ipfs daemon
   ```
3. Default API endpoint: `http://127.0.0.1:5001/api/v0`.

### Option B: Remote Pinning Service (Pinata / Infura)
1. Set `IPFS_API_URL`, `IPFS_PROJECT_ID`, and `IPFS_PROJECT_SECRET` in `.env`.

---

## 5. Starting the Application Services

### 5.1 Run FastAPI Backend
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- Swagger API Docs: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/health`

### 5.2 Run Streamlit Frontend
```bash
python -m streamlit run frontend/app.py
```
- Web Application: `http://localhost:8501`

---

## 6. Running Test Suites
```bash
# Execute all test suites:
python -m pytest tests/ -v

# Run specific domain tests:
python -m pytest tests/test_encryption.py -v
python -m pytest tests/test_hashing.py -v
python -m pytest tests/test_blockchain.py -v
```
