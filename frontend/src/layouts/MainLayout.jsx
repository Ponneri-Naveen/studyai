import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from '../components/Navbar';

const MainLayout = () => {
  return (
    <div className="flex flex-col min-h-screen bg-dark-950 text-white font-sans selection:bg-primary-500/30 selection:text-primary-200">
      <Navbar />
      
      {/* Main Content Area */}
      <main className="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Premium minimal Footer */}
      <footer className="border-t border-dark-900 bg-dark-950/50 py-6 text-center text-xs text-dark-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p>© {new Date().getFullYear()} StudyAI. Built for high-performance student productivity.</p>
        </div>
      </footer>
    </div>
  );
};

export default MainLayout;
