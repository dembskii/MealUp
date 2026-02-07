"use client";

import { useState, useEffect } from "react";
import { NavItem } from "./data/types";
import Navigation from "./components/Navigation";
import Dashboard from "./components/Dashboard";
import RecipesView from "./components/RecipesView";
import WorkoutsView from "./components/WorkoutsView";
import Community from "./components/Community";
import Settings from "./components/Settings";
import Profile from "./components/Profile";
import { Menu, X } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

export default function Home() {
  const [activeTab, setActiveTab] = useState(NavItem.DASHBOARD);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [theme, setTheme] = useState("light");

  // Apply Theme Effect
  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove("light", "dark");

    if (theme === "system") {
      const systemTheme = window.matchMedia("(prefers-color-scheme: dark)")
        .matches
        ? "dark"
        : "light";
      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }
  }, [theme]);

  const renderContent = () => {
    switch (activeTab) {
      case NavItem.DASHBOARD:
        return <Dashboard />;
      case NavItem.RECIPES:
        return <RecipesView />;
      case NavItem.WORKOUTS:
        return <WorkoutsView />;
      case NavItem.COMMUNITY:
        return <Community />;
      case NavItem.SETTINGS:
        return <Settings currentTheme={theme} setTheme={setTheme} />;
      case NavItem.PROFILE:
        return <Profile />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen text-slate-800 dark:text-slate-100 font-sans selection:bg-brand-500 selection:text-white transition-colors duration-300">
      {/* Mobile Header */}
      <div className="md:hidden glass-panel p-4 flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center gap-2">
          <div className="liquid-btn-primary p-1.5 rounded-lg shadow-lg shadow-brand-500/30">
            <div className="w-5 h-5 border-2 border-white rounded-full"></div>
          </div>
          <span className="font-bold text-lg text-slate-800 dark:text-white">
            MealUp
          </span>
        </div>
        <button
          onClick={() => setMobileMenuOpen(true)}
          className="liquid-btn liquid-btn-secondary p-2 rounded-lg"
        >
          <Menu className="w-6 h-6" />
        </button>
      </div>

      {/* Mobile Navigation Drawer */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            key="mobile-nav"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 md:hidden"
          >
            <div
              className="absolute inset-0 bg-slate-900/30 backdrop-blur-sm"
              onClick={() => setMobileMenuOpen(false)}
            />
            <motion.div
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="absolute inset-y-0 left-0 w-72 h-full"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="h-full glass-panel border-r-0 rounded-r-3xl overflow-hidden">
                <Navigation
                  activeTab={activeTab}
                  setActiveTab={(tab) => {
                    setActiveTab(tab);
                    setMobileMenuOpen(false);
                  }}
                  currentTheme={theme}
                  setTheme={setTheme}
                />
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="absolute top-4 right-4 p-2 liquid-btn liquid-btn-secondary rounded-full"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Desktop Navigation */}
      <div className="hidden md:block w-72 h-[96vh] fixed left-4 top-[2vh] z-50">
        <div className="h-full glass-panel rounded-3xl overflow-hidden">
          <Navigation
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            currentTheme={theme}
            setTheme={setTheme}
          />
        </div>
      </div>

      {/* Main Content */}
      <main className="md:pl-80 min-h-screen transition-all duration-300 pt-4 md:pt-8 pr-4 md:pr-8 pb-8">
        <div className="max-w-7xl mx-auto w-full">{renderContent()}</div>
      </main>
    </div>
  );
}