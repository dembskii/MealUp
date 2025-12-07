"use client";

import Link from "next/link";

export default function Home() {
  const pages = [
    { href: "/recipes", label: "📖 View Recipes" },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-slate-900 dark:to-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
            Welcome to MealUp
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-400 mb-12">
            Your personal meal planning companion
          </p>

          <div className="space-y-3">
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-6">
              Testing Pages
            </h2>
            {pages.map((page) => (
              <Link
                key={page.href}
                href={page.href}
                className="block px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold"
              >
                {page.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}