'use client';

import Link from "next/link";
import { useUser } from "@auth0/nextjs-auth0/client";

export default function Navbar() {
  const { user, isLoading } = useUser();

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
                  {user.name}
                </span>
                <a
                  href="/auth/logout"
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded hover:bg-red-700"
                >
                  Sign Out
                </a>
              </>
            ) : (
              <>
                <a
                  href="/auth/login"
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700"
                >
                  Sign In
                </a>
                <a
                  href="/auth/login?screen_hint=signup"
                  className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-600 rounded hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  Sign Up
                </a>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}