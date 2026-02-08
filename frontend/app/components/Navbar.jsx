'use client';

import Link from "next/link";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, isLoading, handleLogin, handleSignUp, handleLogout } = useAuth();

  return (
    <nav className="bg-white dark:bg-slate-900 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Link href="/" className="text-xl font-bold text-slate-900 dark:text-white">
              MealUp
            </Link>
          </div>

          <div className="flex items-center gap-4">
            {isLoading ? (
              <span className="text-sm text-slate-600 dark:text-slate-400">Loading...</span>
            ) : user ? (
              <>
                <span className="text-sm text-slate-700 dark:text-slate-300">
                  {user.name || user.email}
                </span>
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded hover:bg-red-700 transition"
                >
                  Sign Out
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={handleLogin}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700 transition"
                >
                  Sign In
                </button>
                <button
                  onClick={() => handleSignUp("user")}
                  className="px-4 py-2 text-sm font-medium text-blue-600 border border-blue-600 rounded hover:bg-blue-50 dark:text-blue-400 dark:border-blue-400 dark:hover:bg-slate-800 transition"
                >
                  Sign Up
                </button>
                <button
                  onClick={() => handleSignUp("trainer")}
                  className="px-4 py-2 text-sm font-medium text-green-600 border border-green-600 rounded hover:bg-green-50 dark:text-green-400 dark:border-green-400 dark:hover:bg-slate-800 transition"
                >
                  Become Trainer
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}