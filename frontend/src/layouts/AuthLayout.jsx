import React from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { ROUTES } from '../constants';
import { BookOpen } from 'lucide-react';

const AuthLayout = () => {
  const { user } = useAuth();

  // If already logged in, redirect straight to dashboard
  if (user) {
    return <Navigate to={ROUTES.DASHBOARD} replace />;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-dark-950 px-4 py-12 sm:px-6 lg:px-8 font-sans">
      <div className="w-full max-w-md space-y-8">
        <div className="flex flex-col items-center">
          {/* Logo Icon */}
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary-600 shadow-xl shadow-primary-600/30">
            <BookOpen className="h-6 w-6 text-white" />
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold tracking-tight text-white">
            Study<span className="text-primary-500">AI</span>
          </h2>
          <p className="mt-2 text-center text-sm text-dark-400">
            Your intelligent academic study assistant
          </p>
        </div>

        {/* Center Card Content */}
        <div className="rounded-2xl border border-dark-850 bg-dark-900/90 p-8 shadow-2xl backdrop-blur-sm">
          <Outlet />
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;
