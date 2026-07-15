import React, { useState } from 'react';
import { NavLink, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { ROUTES } from '../constants';
import { 
  Menu, X, BookOpen, LayoutDashboard, UploadCloud, 
  FileText, CreditCard, BrainCircuit, Calendar, 
  BarChart3, User, LogOut 
} from 'lucide-react';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate(ROUTES.LOGIN);
  };

  const navItems = [
    { name: 'Dashboard', path: ROUTES.DASHBOARD, icon: LayoutDashboard },
    { name: 'Upload', path: ROUTES.UPLOAD, icon: UploadCloud },
    { name: 'Summary', path: ROUTES.SUMMARY, icon: FileText },
    { name: 'Flashcards', path: ROUTES.FLASHCARDS, icon: CreditCard },
    { name: 'Quiz', path: ROUTES.QUIZ, icon: BrainCircuit },
    { name: 'Schedule', path: ROUTES.SCHEDULE, icon: Calendar },
    { name: 'Weak Topics', path: ROUTES.ANALYTICS, icon: BarChart3 },
  ];

  return (
    <nav className="bg-dark-900 border-b border-dark-800 text-white sticky top-0 z-50 backdrop-blur-md bg-opacity-80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link to={ROUTES.DASHBOARD} className="flex items-center gap-2 font-bold text-xl tracking-tight text-white">
              <div className="p-1.5 rounded-lg bg-primary-600">
                <BookOpen className="w-5 h-5 text-white" />
              </div>
              <span>Study<span className="text-primary-400">AI</span></span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          {user && (
            <div className="hidden xl:flex items-center space-x-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) => 
                    `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                      isActive 
                        ? 'bg-primary-600/10 text-primary-400 border border-primary-500/20' 
                        : 'text-dark-300 hover:text-white hover:bg-dark-800 border border-transparent'
                    }`
                  }
                >
                  <item.icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </NavLink>
              ))}
            </div>
          )}

          {/* User Account / Auth Actions */}
          <div className="hidden md:flex items-center gap-4">
            {user ? (
              <div className="flex items-center gap-3">
                <NavLink
                  to={ROUTES.PROFILE}
                  className={({ isActive }) => 
                    `flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                      isActive 
                        ? 'bg-primary-600/15 text-primary-400' 
                        : 'text-dark-300 hover:text-white hover:bg-dark-800'
                    }`
                  }
                >
                  <User className="w-4 h-4" />
                  <span>{user.name || 'Account'}</span>
                </NavLink>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-red-400 hover:text-red-300 hover:bg-red-950/20 transition-all duration-200 cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <Link to={ROUTES.LOGIN} className="text-sm font-medium text-dark-300 hover:text-white px-3 py-2">
                  Sign In
                </Link>
                <Link 
                  to={ROUTES.REGISTER} 
                  className="bg-primary-600 hover:bg-primary-500 px-4 py-2 rounded-lg text-sm font-medium shadow-lg hover:shadow-primary-600/20 transition-all duration-200"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>

          {/* Hamburger button (Mobile) */}
          <div className="xl:hidden flex items-center">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="inline-flex items-center justify-center p-2 rounded-lg text-dark-300 hover:text-white hover:bg-dark-800 focus:outline-none"
            >
              {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="xl:hidden border-t border-dark-800 bg-dark-900 px-2 pt-2 pb-3 space-y-1">
          {user && navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setIsOpen(false)}
              className={({ isActive }) => 
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-base font-medium transition-all duration-200 ${
                  isActive 
                    ? 'bg-primary-600/10 text-primary-400' 
                    : 'text-dark-300 hover:text-white hover:bg-dark-800'
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              <span>{item.name}</span>
            </NavLink>
          ))}
          <div className="border-t border-dark-850 my-2 pt-2">
            {user ? (
              <div className="space-y-1">
                <NavLink
                  to={ROUTES.PROFILE}
                  onClick={() => setIsOpen(false)}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-base font-medium text-dark-300 hover:text-white hover:bg-dark-800"
                >
                  <User className="w-5 h-5" />
                  <span>Profile ({user.name})</span>
                </NavLink>
                <button
                  onClick={() => {
                    setIsOpen(false);
                    handleLogout();
                  }}
                  className="flex w-full items-center gap-3 px-3 py-2.5 rounded-lg text-base font-medium text-red-400 hover:text-red-300 hover:bg-red-950/20"
                >
                  <LogOut className="w-5 h-5" />
                  <span>Logout</span>
                </button>
              </div>
            ) : (
              <div className="px-3 py-2 space-y-2">
                <Link
                  to={ROUTES.LOGIN}
                  onClick={() => setIsOpen(false)}
                  className="block text-center text-dark-300 hover:text-white py-2 font-medium"
                >
                  Sign In
                </Link>
                <Link
                  to={ROUTES.REGISTER}
                  onClick={() => setIsOpen(false)}
                  className="block text-center bg-primary-600 hover:bg-primary-500 py-2 rounded-lg font-medium shadow-lg"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
