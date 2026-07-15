# StudyAI — Developer Guide

Welcome to the StudyAI developer guide. This document explains the codebase layout, patterns, and style conventions used in the project.

---

## 📂 Folder Structure

The project is structured into two main directories:
```
studyai/
├── .github/workflows/   # CI/CD pipelines runner workflows
├── docs/                # Project documentation and guides
├── backend/             # Flask Backend Application
│   ├── routes/          # REST API endpoints blueprints controllers
│   ├── services/        # Business logic services & AI wrappers
│   │   └── repositories/# Repository interfaces and DB adapters
│   ├── storage/         # Local fallback JSON DB registry
│   ├── tests/           # Pytest unit testing suite
│   ├── utils/           # Utilities (logger, security, orjson)
│   └── app.py           # Application Factory entrypoint
└── frontend/            # React + Vite Frontend Application
    ├── src/
    │   ├── components/  # Shared layouts, errors bounds components
    │   ├── context/     # React state Context (Auth)
    │   ├── pages/       # Page views (Dashboard, Analytics, Quiz)
    │   ├── services/    # API Axios bindings
    │   └── App.jsx      # Route-level lazy loading router
    └── vite.config.js   # Rollup build chunking configurations
```

---

## 🔄 Repository Pattern Abstraction

StudyAI uses the Repository Pattern to switch databases dynamically:
1.  **Interface (`StorageRepository`)**: Outlines the standard database methods.
2.  **JSON Database Driver (`JSONRepository`)**: Local sandbox files driver for fast dev configurations.
3.  **Cloud Database Driver (`FirestoreRepository`)**: Google Firestore production adapter.
4.  **Factory Selector (`RepositoryFactory`)**: Resolves active database engine on startup.

### How to Retrieve Data in Services
Always import from the factory class:
```python
from services.repositories.repository_factory import RepositoryFactory

repo = RepositoryFactory.get_repository()
# Operations execute automatically against active database provider
materials = repo.get_all_materials(user_id)
```

---

## 🧪 Running Tests
To run unit and integration tests:
```bash
cd backend
.\venv\Scripts\pytest.exe tests/ -v
```

---

## 🎨 Coding Conventions
*   **Backend (Python)**: Code should adhere to PEP 8 standards. Use type annotations on functions where possible.
*   **Frontend (JavaScript)**: Use React hooks (`useMemo`, `useCallback`) strategically to minimize rendering overhead. Always wrap page routes in `lazy()` imports.
