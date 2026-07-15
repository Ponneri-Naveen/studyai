# StudyAI 🎓💡

StudyAI is a production-grade, AI-powered web application designed to supercharge student learning. By leveraging cutting-edge LLMs (Llama 3.3 70B via Groq API) and active-recall learning methodologies, StudyAI transforms passive reading materials (PDFs, Word documents, text sheets) into interactive study plans, detailed outlines, spaced-repetition flashcards, and testing quizzes.

---

## 🚀 Tech Stack

### Frontend
*   **Core Framework:** React.js (bootstrapped with Vite)
*   **Routing:** React Router v6 (lazy loaded dynamic page routes)
*   **HTTP Client:** Axios with memory cache interceptors and AbortControllers
*   **Styling:** Tailwind CSS (premium dark-mode grid UI)
*   **Visualizations:** Recharts (responsive vector charts)
*   **Formatting:** React Markdown
*   **Notifications:** React Hot Toast

### Backend
*   **API Framework:** Python Flask
*   **Cross-Origin Resource Sharing (CORS):** Flask-CORS whitelisting
*   **LLM Engine:** Groq SDK (Llama 3.3 70B Versatile)
*   **Authentication & DB SDK:** Firebase Admin SDK
*   **JSON Serializer:** High-speed `orjson` bindings with monkey patching
*   **File Extractors:** PyPDF2 (PDFs), python-docx (Word Documents)
*   **Testing:** Pytest

### Database
*   **Primary:** Firebase Firestore (Google Cloud database)
*   **Fallback:** Local JSON Storage for offline resilience and development

---

## 🏛️ Production Deployment Architecture

```
Browser Client ──> Netlify CDN ──> React App Chunks (HTML/JS)
  │
  ├── [REST Requests / JWT Bearer Header] ──> Flask API Gateway (Render/Railway)
  │                                             │
  │                                             ├── [Token Validation] ──> Firebase Auth
  │                                             ├── [JSON Queries] ──> Firestore DB
  │                                             └── [Prompt templates] ──> Groq Cloud AI API
  │
  └── [Session Validation Claims] ──> Firebase Authentication Edge
```

---

## 📂 Folder Structure

```
studyai/
├── .github/workflows/         # CI/CD pipelines deployment configuration
│   └── deploy.yml             # GitHub Actions verify & release scripts
├── docs/                      # Unified project documentation
│   ├── INSTALLATION.md        # Sandbox installation guide
│   ├── DEVELOPER_GUIDE.md     # Code style & Repository abstraction guidelines
│   └── TROUBLESHOOTING.md     # Debugging guides
├── backend/
│   ├── app.py                 # Application entry point / Flask Factory
│   ├── config.py              # Environment configuration loader
│   ├── requirements.txt       # Python dependency manifest
│   ├── .env                   # Local backend secrets (git-ignored)
│   ├── routes/                # Flask Blueprints
│   ├── services/              # Core business logic
│   │   └── repositories/      # Repository abstractions (JSON/Firestore)
│   ├── storage/               # File system database fallbacks
│   ├── utils/                 # Utilities and error formatters
│   │   ├── error_handlers.py  # Global HTTP JSON exception interceptors
│   │   ├── logger_factory.py  # Rotating JSON logger
│   │   ├── orjson_compat.py   # High-speed JSON serialization driver
│   │   ├── security_headers.py# Flask-Talisman secure headers
│   │   └── startup_validator.py# Startup environment validation check
│   └── tests/                 # Integration and unit tests
└── frontend/
    ├── vite.config.js         # Rollup build chunking configurations
    └── src/
        ├── App.jsx            # Dynamic dynamic page loading routing
        ├── components/        # Shared component trees
        │   └── ErrorBoundary.jsx   # Crash recovery displays
        └── pages/             # Lazy-loaded router pages
```

---

## 🛠️ Getting Started

To launch StudyAI locally:

### 1. Prerequisites
*   Node.js: v20.x or higher
*   Python: v3.12 or higher

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install
npm run dev
```

---

## 📡 API Reference

### Health Status Check
*   **Endpoint:** `GET /api/health`
*   **Auth Required**: None
*   **Response (`200 OK`)**:
    ```json
    {
      "status": "healthy",
      "version": "1.0.0",
      "service": "StudyAI API",
      "environment": "development",
      "storage": {
        "writable": true
      },
      "groq": {
        "status": "connected"
      }
    }
    ```

---

## 📑 Unified Documentation Registry

For advanced configurations, reference the matching guides:
1.  **Detailed Sandbox Installation**: See [INSTALLATION.md](file:///d:/studyaiproject/studyai/docs/INSTALLATION.md).
2.  **Developer Guidelines & Abstractions**: See [DEVELOPER_GUIDE.md](file:///d:/studyaiproject/studyai/docs/DEVELOPER_GUIDE.md).
3.  **Troubleshooting & Debugging**: See [TROUBLESHOOTING.md](file:///d:/studyaiproject/studyai/docs/TROUBLESHOOTING.md).

---

## 📍 Git Commit Workflow Guidelines

Adhere to the following commits format:
*   `feat`: Adding new production services or UI views.
*   `perf`: Compiling speedups or API caching interceptors.
*   `chore`: Deployment setups and configs tweaks.

---

## 📄 License
This project is licensed under the MIT License.