# StudyAI — Installation & Setup Guide

This guide details the step-by-step instructions to get your local environment running for the StudyAI project.

---

## 📋 Prerequisites
Make sure you have installed:
1.  **Python**: Version 3.12 or higher.
2.  **Node.js**: Version 20 or higher.
3.  **Groq API Account**: Get an API Key from the Groq Developer Console.
4.  **Firebase Project**: Optional for local fallback development, required for production Firestore deployments.

---

## 🛠️ Step-by-Step Local Setup

### 1. Clone the Codebase
```bash
git clone https://github.com/your-username/studyai.git
cd studyai
```

### 2. Configure the Backend (Flask)
Go to the backend folder, create a virtual environment, and install package dependencies:
```bash
cd backend
python -m venv venv

# Activate Virtual Environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Backend Environment Variables
Create a file named `.env` in the `backend/` directory:
```env
FLASK_ENV=development
PORT=5000
SECRET_KEY=<your_local_secret_key>
FRONTEND_URL=http://localhost:5173

# Groq AI Credentials
GROQ_API_KEY=<your_groq_api_key>

# Firebase Configuration (leave blank for local JSON fallback)
FIREBASE_PROJECT_ID=
FIREBASE_CREDENTIALS_PATH=
```

### 4. Configure the Frontend (React + Vite)
Go to the frontend directory and install node modules:
```bash
cd ../frontend
npm install
```

### 5. Setup Frontend Environment Variables
Create a file named `.env` in the `frontend/` directory:
```env
VITE_API_BASE_URL=http://localhost:5000/api

# Firebase Configuration (leave blank if backend is using JSON fallback)
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_PROJECT_ID=
VITE_FIREBASE_STORAGE_BUCKET=
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=
```

---

## 🚀 Running StudyAI Locally

### 1. Launch Backend Server
From the `backend/` directory with the virtual environment active:
```bash
python app.py
```

### 2. Launch Frontend Dev Server
From the `frontend/` directory:
```bash
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.
