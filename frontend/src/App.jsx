import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ROUTES } from './constants';

// Layouts
import MainLayout from './layouts/MainLayout';
import AuthLayout from './layouts/AuthLayout';

// Components
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Summary from './pages/Summary';
import Flashcards from './pages/Flashcards';
import Quiz from './pages/Quiz';
import StudyPlanner from './pages/StudyPlanner';
import WeakTopics from './pages/WeakTopics';
import Profile from './pages/Profile';
import Login from './pages/Login';
import Register from './pages/Register';

function App() {
  return (
    <Routes>
      {/* Protected Main Routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path={ROUTES.UPLOAD} element={<Upload />} />
        <Route path={ROUTES.SUMMARY} element={<Summary />} />
        <Route path={ROUTES.FLASHCARDS} element={<Flashcards />} />
        <Route path={ROUTES.QUIZ} element={<Quiz />} />
        <Route path={ROUTES.SCHEDULE} element={<StudyPlanner />} />
        <Route path={ROUTES.ANALYTICS} element={<WeakTopics />} />
        <Route path={ROUTES.PROFILE} element={<Profile />} />
      </Route>

      {/* Public Auth Routes */}
      <Route element={<AuthLayout />}>
        <Route path={ROUTES.LOGIN} element={<Login />} />
        <Route path={ROUTES.REGISTER} element={<Register />} />
      </Route>

      {/* Fallback to Dashboard/Login */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
