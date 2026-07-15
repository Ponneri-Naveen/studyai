import React from 'react';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { ROUTES } from '../constants';
import { User, Mail, Calendar, LogOut, ShieldAlert } from 'lucide-react';
import toast from 'react-hot-toast';

const Profile = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    toast.success('Logged out successfully.');
    navigate(ROUTES.LOGIN);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8 animate-fadeIn">
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
          Your Profile
        </h1>
        <p className="text-dark-300 mt-1.5 text-sm">
          Manage your personal account information and app configurations.
        </p>
      </div>

      <div className="bg-dark-900 border border-dark-850 rounded-2xl p-6 md:p-8 space-y-6">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-primary-650 flex items-center justify-center text-white text-xl font-bold uppercase shadow-lg shadow-primary-600/10">
            {user?.name ? user.name[0] : 'U'}
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">{user?.name || 'Academic Student'}</h2>
            <p className="text-xs text-dark-400">Student Account</p>
          </div>
        </div>

        <div className="border-t border-dark-850 my-6 pt-6 space-y-4">
          <div className="flex items-center gap-3 text-sm">
            <Mail className="w-5 h-5 text-dark-500" />
            <div>
              <p className="text-xs text-dark-400 font-semibold uppercase tracking-wider">Email Address</p>
              <p className="text-white mt-0.5">{user?.email || 'N/A'}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 text-sm">
            <Calendar className="w-5 h-5 text-dark-500" />
            <div>
              <p className="text-xs text-dark-400 font-semibold uppercase tracking-wider">Member Since</p>
              <p className="text-white mt-0.5">
                {user?.createdAt ? new Date(user.createdAt).toLocaleDateString(undefined, { dateStyle: 'long' }) : 'July 15, 2026'}
              </p>
            </div>
          </div>
        </div>

        <div className="border-t border-dark-850 pt-6 flex flex-col sm:flex-row gap-4 justify-between">
          <div className="flex items-center gap-2 text-xs text-dark-400 bg-dark-950 px-3 py-2 rounded-lg border border-dark-850">
            <ShieldAlert className="w-4 h-4 text-primary-400" />
            <span>Local stub session storage active.</span>
          </div>

          <button
            onClick={handleLogout}
            className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-red-650 hover:bg-red-500 text-white font-semibold text-sm transition-colors cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out of StudyAI</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Profile;
