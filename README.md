# StudyAI 🎓💡

StudyAI is a production-grade, AI-powered web application designed to supercharge student learning. By leverage cutting-edge LLMs (Llama 3.3 70B via Groq API) and active-recall learning methodologies, StudyAI transforms passive reading materials (PDFs, Word documents, text sheets) into interactive study plans, detailed outlines, space-repetition flashcards, and testing quizzes.

---

## 🚀 Tech Stack

### Frontend
* **Core Framework:** React.js (bootstrapped with Vite)
* **Routing:** React Router v6
* **HTTP Client:** Axios with centralized interceptors
* **Styling:** Tailwind CSS
* **Visualization:** Chart.js & React-Chartjs-2
* **Formatting:** React Markdown
* **Notifications:** React Hot Toast

### Backend
* **API Framework:** Python Flask
* **Cross-Origin Resource Sharing (CORS):** Flask-CORS
* **LLM Engine:** Groq SDK (Llama 3.3 70B Versatile)
* **Authentication & DB SDK:** Firebase Admin SDK
* **File Extractors:** PyPDF2 (PDFs), python-docx (Word Documents)
* **Testing:** Pytest

### Database
* **Primary:** Firebase Firestore
* **Fallback:** Local JSON Storage for offline resilience

---

## 📂 Folder Structure

```
studyai/
├── docs/                      # Project documentation and assets
├── backend/
│   ├── app.py                 # Application entry point / Flask Factory
│   ├── config.py              # Environment configuration loader
│   ├── requirements.txt       # Python dependency manifest
│   ├── .env                   # Local backend secrets (git-ignored)
│   ├── .env.example           # Shared backend environment templates
│   ├── routes/                # Flask Blueprints
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentication routes (register, login, logout stubs)
│   │   └── health.py          # Api status checker
│   ├── services/              # Core business logic
│   │   ├── __init__.py
│   │   └── auth_service.py    # Firebase Auth interface (stub)
│   ├── models/                # Database models & schemas
│   ├── storage/               # File system database fallbacks
│   ├── utils/                 # Utilities and error formatters
│   │   ├── __init__.py
│   │   └── error_handler.py   # Global HTTP exception interceptors
│   ├── tests/                 # Integration and unit tests
│   │   ├── __init__.py
│   │   └── test_health.py     # Health endpoint validation
│   ├── uploads/               # Temporary uploads directory (git-ignored)
│   └── logs/                  # Application runtime logs (git-ignored)
└── frontend/
    ├── package.json           # Frontend dependency manifest
    ├── index.html             # HTML entry point
    ├── vite.config.js         # Vite custom configuration
    ├── tailwind.config.js     # Tailwind CSS theme configuration
    ├── postcss.config.js      # PostCSS configurations
    ├── .env                   # Local frontend variables (git-ignored)
    ├── .env.example           # Shared frontend configuration templates
    └── src/
        ├── main.jsx           # App wrapper with contexts and boundaries
        ├── App.jsx            # React router definitions
        ├── assets/            # Static assets
        ├── components/        # Shared components
        │   ├── ErrorBoundary.jsx   # Visual crash recovery wrapper
        │   ├── ProtectedRoute.jsx  # Auth guard wrapper
        │   └── Navbar.jsx          # Responsive viewport header navigation
        ├── constants/         # Globally available string/route mappings
        │   └── index.js
        ├── contexts/          # React context modules
        │   └── AuthContext.jsx     # Global login/logout session state
        ├── hooks/             # Custom react hooks
        │   └── useAuth.js          # Auth Context consumption shortcut
        ├── layouts/           # Page layouts
        │   ├── MainLayout.jsx      # Navigation grid layout
        │   └── AuthLayout.jsx      # Centered card layout for signup/signin
        ├── pages/             # View pages
        │   ├── Dashboard.jsx
        │   ├── Upload.jsx
        │   ├── Summary.jsx
        │   ├── Flashcards.jsx
        │   ├── Quiz.jsx
        │   ├── Schedule.jsx
        │   ├── Analytics.jsx
        │   ├── Login.jsx
        │   ├── Register.jsx
        │   └── Profile.jsx
        ├── services/          # External api communication files
        │   ├── api.js              # Standardized Axios Client
        │   ├── authService.js
        │   └── healthService.js
        ├── styles/            # CSS entry points
        │   └── index.css           # Tailwind custom setups and keyframes
        ├── types/             # Optional JS type documentation
        └── utils/             # Helper utilities
            └── errorParser.js      # Axios error extractor
```

---

## 🛠️ Getting Started

### Prerequisites
* **Node.js:** v18.x or v20.x
* **Python:** v3.9+

### Backend Setup
1. Open a terminal in `studyai/backend`
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in local values.
5. Run the server:
   ```bash
   python app.py
   ```
   *The server runs by default on `http://localhost:5000`.*

### Frontend Setup
1. Open a terminal in `studyai/frontend`
2. Install the package dependencies:
   ```bash
   npm install
   ```
3. Copy `.env.example` to `.env`.
4. Run the development server:
   ```bash
   npm run dev
   ```
   *The client application launches at `http://localhost:5173`.*

---

## 📡 API Reference

### Health Check
* **Endpoint:** `GET /api/health`
* **Response:**
  ```json
  {
    "status": "running",
    "version": "1.0.0",
    "service": "StudyAI API"
  }
  ```

### Authentication (Stubs)
* **Register:** `POST /api/auth/register` (Body: `{ name, email, password }`)
* **Login:** `POST /api/auth/login` (Body: `{ email, password }`)
* **Logout:** `POST /api/auth/logout`

---

## ⚠️ Global Error Handling Strategy

### Backend
* Uncaught exceptions and standard status errors are captured globally by `utils/error_handler.py`.
* All API error responses return structured JSON:
  ```json
  {
    "error": "Error description text message",
    "code": 404
  }
  ```

### Frontend
* An `ErrorBoundary` wraps the application tree, capturing visual crashes and showing a premium recovery view.
* The centralized Axios interceptor (`services/api.js`) triggers automated logging of unauthorized responses.
* `utils/errorParser.js` converts raw network exceptions or bad status response data into customer-friendly notifications rendered via `react-hot-toast`.

---

## 📍 Git Commit Workflow Guidelines

To maintain history clarity, adhere to the following incremental commits sequentially as you proceed through development:

| Phase | Target Scope | Suggested Commit Message |
| :--- | :--- | :--- |
| **Phase 1** | Scaffolding, stubs, and configuration | `feat: initial project setup` |
| **Phase 2** | Connection and health pinging | `feat: frontend-backend connection` |
| **Phase 3** | PDF/Word file uploads | `feat: study material upload` |
| **Phase 4** | Groq SDK integration | `feat: Groq API integration` |
| **Phase 5** | Outlining and Markdown summaries | `feat: summary generator` |
| **Phase 6** | Deck generation and recall view | `feat: flashcard system` |
| **Phase 7** | Questions/answers game engine | `feat: quiz system` |
| **Phase 8** | Metric statistics and Chart.js | `feat: analytics dashboard` |
| **Phase 9** | Cloud hosting configuration | `chore: production deployment` |