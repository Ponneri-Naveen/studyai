import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ROUTES } from './constants';

// Layouts
import MainLayout from './layouts/MainLayout';
import AuthLayout from './layouts/AuthLayout';

// Components
import ProtectedRoute from './components/ProtectedRoute';

// Lazy Loaded Pages Chunks
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Upload = lazy(() => import('./pages/Upload'));
const Summary = lazy(() => import('./pages/Summary'));
const Flashcards = lazy(() => import('./pages/Flashcards'));
const Quiz = lazy(() => import('./pages/Quiz'));
const StudyPlanner = lazy(() => import('./pages/StudyPlanner'));
const WeakTopics = lazy(() => import('./pages/WeakTopics'));
const AnalyticsDashboard = lazy(() => import('./pages/AnalyticsDashboard'));
const Profile = lazy(() => import('./pages/Profile'));
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));

function App() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-dark-950 text-white">
        <div className="flex flex-col items-center gap-3">
          <div className="w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-xs font-mono text-dark-400 tracking-wider">Loading page assets...</span>
        </div>
      </div>
    }>
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
          <Route path={ROUTES.ANALYTICS} element={<AnalyticsDashboard />} />
          <Route path={ROUTES.WEAK_TOPICS} element={<WeakTopics />} />
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
    </Suspense>
  );
}

export default App;
