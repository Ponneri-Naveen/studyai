# StudyAI — Troubleshooting Guide

This guide compiles common issues encountered during local development or production deployment and details their solutions.

---

## 🛑 Backend Server Startup Issues

### 1. AttributeError: 'Config' object has no attribute 'BASE_DIR'
*   **Cause**: Legacy `config.py` did not declare a base path directory attribute.
*   **Solution**: Verify that `BASE_DIR` is declared at the top of the Config base class in `config.py`:
    ```python
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ```

### 2. ConfigurationError: Missing GROQ_API_KEY
*   **Cause**: Backend startup validations failed because environment parameters are missing.
*   **Solution**: Configure `.env` in the `backend/` directory and check that the key matches:
    ```env
    GROQ_API_KEY=gsk_your_key_here
    ```

### 3. Port 5000 Already In Use
*   **Cause**: Another process or background server is listening on port 5000.
*   **Solution**:
    *   **Windows (PowerShell)**:
        ```powershell
        Get-Process -Id (Get-NetTCPConnection -LocalPort 5000).OwningProcess | Stop-Process -Force
        ```
    *   **macOS/Linux**:
        ```bash
        kill -9 $(lsof -t -i:5000)
        ```

---

## 🌐 Network & API Integration Issues

### 1. CORS Block Warnings
*   **Cause**: The request Origin does not match the backend server configuration.
*   **Solution**: Check `FRONTEND_URL` in `backend/.env` and `VITE_API_BASE_URL` in `frontend/.env`. They must explicitly point to each other.

### 2. Firebase App Already Exists Crash
*   **Cause**: Multi-initializations on RepositoryFactory calls.
*   **Solution**: Ensure that `firebase_admin.initialize_app` is only called if no application apps list exists:
    ```python
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    ```

---

## ⚡ React Frontend & Bundling Issues

### 1. Circular Chunk Warnings
*   **Cause**: ManualRollup splitting in `vite.config.js` generated circular links between React modules and Axios helper libraries.
*   **Solution**: Merge helper libraries and react dependencies in a single `vendor-core` chunk inside `vite.config.js`.
