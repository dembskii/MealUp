import Navbar from "./components/Navbar";

export default function Home() {
  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-slate-900 dark:to-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
              Welcome to MealUp
            </h1>
            <p className="text-lg text-slate-600 dark:text-slate-400 mb-8">
              Your personal meal planning companion
            </p>
            <div className="inline-block bg-white dark:bg-slate-800 rounded-lg shadow p-6">
              <p className="text-slate-700 dark:text-slate-300">
                Sign in to get started with meal planning and recipes
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}