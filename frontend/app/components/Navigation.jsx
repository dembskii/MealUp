'use client';

import { NavItem } from '../data/types';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard, Utensils, Dumbbell, Users,
  Settings, UserCircle, Moon, Sun, LogIn, LogOut, UserPlus,
  GraduationCap, Loader2
} from 'lucide-react';

export default function Navigation({ activeTab, setActiveTab, currentTheme, setTheme }) {
  const { user, isLoading: isAuthLoading, handleLogin, handleSignUp, handleLogout } = useAuth();

  const navItems = [
    { id: NavItem.DASHBOARD, label: 'Dashboard', icon: LayoutDashboard },
    { id: NavItem.RECIPES, label: 'Nutrition', icon: Utensils },
    { id: NavItem.WORKOUTS, label: 'Workouts', icon: Dumbbell },
    { id: NavItem.COMMUNITY, label: 'Community', icon: Users },
    { id: NavItem.PROFILE, label: 'Profile', icon: UserCircle },
  ];

  const isDark =
    currentTheme === 'dark' ||
    (currentTheme === 'system' &&
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-color-scheme: dark)').matches);

  const toggleTheme = () => {
    setTheme(isDark ? 'light' : 'dark');
  };

  return (
    <div className="flex flex-col h-full bg-white/20 dark:bg-slate-900/20 backdrop-blur-sm transition-colors duration-300">
      {/* Logo */}
      <div className="p-8 flex items-center gap-3">
        <img src="/images/logo.png" alt="MealUp" className="w-8 h-8 drop-shadow-lg" />
        <h1 className="text-2xl font-bold text-slate-800 dark:text-white tracking-tight drop-shadow-sm">
          MealUp
        </h1>
      </div>

      {/* User info bar */}
      <div className="px-5 pb-4">
        {isAuthLoading ? (
          <div className="flex items-center gap-3 px-3 py-2.5 rounded-2xl bg-white/20 dark:bg-white/5 animate-pulse">
            <div className="w-9 h-9 rounded-full bg-slate-200 dark:bg-slate-700" />
            <div className="flex-1 space-y-1.5">
              <div className="h-3 w-24 bg-slate-200 dark:bg-slate-700 rounded" />
              <div className="h-2 w-16 bg-slate-200 dark:bg-slate-700 rounded" />
            </div>
          </div>
        ) : user ? (
          <div className="flex items-center gap-3 px-3 py-2.5 rounded-2xl bg-white/30 dark:bg-white/5 border border-white/30 dark:border-white/5">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-white font-bold text-sm shadow-md">
              {(user.name || user.email || '?').charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-bold text-slate-800 dark:text-white truncate">
                {user.name || user.email}
              </p>
              <p className="text-[10px] text-slate-400 truncate">{user.email}</p>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-3 px-3 py-2.5 rounded-2xl bg-white/20 dark:bg-white/5 border border-dashed border-slate-300/50 dark:border-white/10">
            <div className="w-9 h-9 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
              <UserCircle className="w-5 h-5 text-slate-400" />
            </div>
            <p className="text-xs text-slate-400 font-medium">Not signed in</p>
          </div>
        )}
      </div>

      {/* Navigation links */}
      <nav className="flex-1 px-4 space-y-3 mt-2">
        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-4 px-4 py-3.5 rounded-2xl transition-all duration-300 group relative overflow-hidden ${
                isActive
                  ? 'liquid-card text-brand-600 dark:text-brand-400 font-bold shadow-lg'
                  : 'text-slate-500 dark:text-slate-400 hover:bg-white/30 dark:hover:bg-slate-800/30 hover:text-slate-700 dark:hover:text-slate-200'
              }`}
            >
              <Icon
                className={`w-5 h-5 relative z-10 ${
                  isActive
                    ? 'text-brand-500 drop-shadow-sm'
                    : 'text-slate-400 group-hover:text-slate-600 dark:text-slate-500 dark:group-hover:text-slate-300'
                }`}
              />
              <span className="relative z-10">{item.label}</span>
              {isActive && (
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-brand-500 shadow-[0_0_10px_rgba(27,211,132,0.5)]"></div>
              )}
            </button>
          );
        })}
      </nav>

      {/* Bottom section */}
      <div className="p-4 border-t border-white/20 dark:border-white/5">
        {/* Auth actions */}
        {!isAuthLoading && (
          <div className="mb-4 space-y-2">
            {user ? (
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-semibold text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all border border-transparent hover:border-red-200 dark:hover:border-red-800/30"
              >
                <LogOut className="w-4 h-4" />
                Sign Out
              </button>
            ) : (
              <div className="space-y-2">
                <button
                  onClick={handleLogin}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-bold liquid-btn liquid-btn-primary shadow-lg shadow-brand-500/20"
                >
                  <LogIn className="w-4 h-4 text-white" />
                  <span>Sign In</span>
                </button>
                <button
                  onClick={() => handleSignUp('user')}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-semibold liquid-btn liquid-btn-secondary"
                >
                  <UserPlus className="w-4 h-4" />
                  Sign Up
                </button>
                <button
                  onClick={() => handleSignUp('trainer')}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-semibold text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20 hover:bg-orange-100 dark:hover:bg-orange-900/30 transition-all border border-orange-200 dark:border-orange-700/30"
                >
                  <GraduationCap className="w-4 h-4" />
                  Become Trainer
                </button>
              </div>
            )}
          </div>
        )}

        {/* Settings + Theme toggle */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveTab(NavItem.SETTINGS)}
            className={`flex-1 flex items-center gap-3 px-4 py-2.5 transition-all rounded-xl border ${
              activeTab === NavItem.SETTINGS
                ? 'liquid-card text-brand-600 border-white/50'
                : 'border-transparent text-slate-500 hover:bg-white/30 hover:text-slate-700'
            }`}
          >
            <Settings className={`w-5 h-5 ${activeTab === NavItem.SETTINGS ? 'text-brand-500' : ''}`} />
            <span className="text-sm font-medium">Settings</span>
          </button>

          <button
            onClick={toggleTheme}
            className={`p-2.5 rounded-xl transition-all duration-300 border ${
              isDark
                ? 'bg-slate-800/50 text-brand-400 border-white/10 shadow-inner'
                : 'bg-white/50 text-orange-400 border-white/40 shadow-sm hover:bg-white/80'
            }`}
            title="Toggle Theme"
          >
            {isDark ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
          </button>
        </div>
      </div>
    </div>
  );
}
