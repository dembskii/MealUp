'use client';

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function Navbar() {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const checkAuth = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/auth/me", {
        credentials: "include"
      });
      
      console.log("Auth check response:", res.status);
      
      if (res.ok) {
        const data = await res.json();
        console.log("User authenticated:", data);
        setUser(data);
      } else {
        console.log("Not authenticated, clearing user");
        setUser(null);
        document.cookie = "session_id=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
      }
    } catch (error) {
      console.error("Auth check failed:", error);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const handleLogin = () => {
    window.location.href = "http://localhost:8000/api/v1/auth/login";
  };

  const handleSignUp = () => {
    window.location.href = "http://localhost:8000/api/v1/auth/login?prompt=signup";
  };

  const handleLogout = async () => {
    try {
      console.log("Starting logout...");
      
      const res = await fetch("http://localhost:8000/api/v1/auth/logout", {
        method: "GET",
        credentials: "include"
      });
      
      if (res.ok) {
        const data = await res.json();
        console.log("Logout successful");
        
        setUser(null);
        
        if (data.logout_url) {
            window.location.href = data.logout_url;
        } else {
            window.location.href = "/";
        }
      } else {
        console.error("Logout failed:", res.status);
        setUser(null);
        window.location.href = "/";
      }
    } catch (error) {
      console.error("Logout error:", error);
      setUser(null);
    }
  };

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
                  onClick={handleSignUp}
                  className="px-4 py-2 text-sm font-medium text-blue-600 border border-blue-600 rounded hover:bg-blue-50 dark:text-blue-400 dark:border-blue-400 dark:hover:bg-slate-800 transition"
                >
                  Sign Up
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}