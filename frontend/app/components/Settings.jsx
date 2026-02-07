'use client';

import { useState } from 'react';
import {
  Bell, Moon, Sun, Monitor, Shield, Globe,
  Ruler, ChevronRight, LogOut, Trash2, User
} from 'lucide-react';
import { motion } from 'framer-motion';

export default function Settings({ currentTheme, setTheme }) {
  const [notifications, setNotifications] = useState({
    email: true, push: true, digest: false, marketing: false
  });
  const [units, setUnits] = useState('metric');

  const toggleNotification = (key) => {
    setNotifications(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-6 md:p-10 max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-800 dark:text-white drop-shadow-sm">Settings</h2>
        <p className="text-slate-500 dark:text-slate-400 mt-1">Manage your account preferences and app experience.</p>
      </div>

      {/* Account Section */}
      <div className="glass-panel rounded-3xl p-6 mb-6 flex items-center justify-between transition-colors">
        <div className="flex items-center gap-4">
          <div className="relative">
            <img src="https://i.pravatar.cc/150?u=a042581f4e29026704d" alt="Profile" className="w-16 h-16 rounded-full object-cover border-4 border-white/50 shadow-md" />
            <button className="absolute bottom-0 right-0 bg-brand-500 text-white p-1 rounded-full border border-white shadow-sm hover:bg-brand-600 transition-colors"><User className="w-3 h-3" /></button>
          </div>
          <div>
            <h3 className="text-xl font-bold text-slate-800 dark:text-white">Sarah Jenkins</h3>
            <p className="text-slate-400 text-sm">sarah.j@example.com</p>
          </div>
        </div>
        <button className="liquid-btn liquid-btn-secondary px-5 py-2.5 rounded-xl text-sm font-semibold">Edit Profile</button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column */}
        <div className="space-y-6">
          {/* Appearance */}
          <section className="glass-panel rounded-3xl p-6 transition-colors">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2.5 bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 rounded-xl shadow-inner"><Sun className="w-5 h-5" /></div>
              <h3 className="font-bold text-slate-800 dark:text-white text-lg">Appearance</h3>
            </div>
            <div className="grid grid-cols-3 gap-3">
              {[
                { id: 'light', label: 'Light', icon: Sun },
                { id: 'dark', label: 'Dark', icon: Moon },
                { id: 'system', label: 'System', icon: Monitor }
              ].map((item) => (
                <button key={item.id} onClick={() => setTheme(item.id)}
                  className={`flex flex-col items-center justify-center p-3 rounded-2xl border-2 transition-all ${currentTheme === item.id ? 'liquid-card border-brand-500/50 text-brand-700 dark:text-brand-400 shadow-md' : 'border-transparent hover:bg-white/40 text-slate-500 dark:text-slate-400'}`}>
                  <item.icon className="w-6 h-6 mb-2" /><span className="text-sm font-medium">{item.label}</span>
                </button>
              ))}
            </div>
          </section>

          {/* Preferences */}
          <section className="glass-panel rounded-3xl p-6 transition-colors">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2.5 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-xl shadow-inner"><Globe className="w-5 h-5" /></div>
              <h3 className="font-bold text-slate-800 dark:text-white text-lg">Preferences</h3>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3.5 bg-white/40 dark:bg-slate-800/40 rounded-2xl border border-white/20 dark:border-white/5 transition-colors">
                <div className="flex items-center gap-3"><Ruler className="w-5 h-5 text-slate-400" /><span className="font-medium text-slate-700 dark:text-slate-200">Units</span></div>
                <div className="flex bg-white/50 dark:bg-slate-700/50 rounded-xl p-1 shadow-inner border border-white/10">
                  <button onClick={() => setUnits('metric')}
                    className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all ${units === 'metric' ? 'bg-white dark:bg-slate-600 text-slate-800 dark:text-white shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700'}`}>Metric</button>
                  <button onClick={() => setUnits('imperial')}
                    className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all ${units === 'imperial' ? 'bg-white dark:bg-slate-600 text-slate-800 dark:text-white shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700'}`}>Imperial</button>
                </div>
              </div>
              <button className="w-full flex items-center justify-between p-3.5 bg-white/40 dark:bg-slate-800/40 rounded-2xl border border-white/20 dark:border-white/5 hover:bg-white/60 dark:hover:bg-slate-800/60 transition-colors">
                <div className="flex items-center gap-3"><Globe className="w-5 h-5 text-slate-400" /><span className="font-medium text-slate-700 dark:text-slate-200">Language</span></div>
                <div className="flex items-center gap-2 text-slate-400 text-sm font-medium">English<ChevronRight className="w-4 h-4" /></div>
              </button>
            </div>
          </section>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Notifications */}
          <section className="glass-panel rounded-3xl p-6 transition-colors">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2.5 bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 rounded-xl shadow-inner"><Bell className="w-5 h-5" /></div>
              <h3 className="font-bold text-slate-800 dark:text-white text-lg">Notifications</h3>
            </div>
            <div className="space-y-5">
              {[
                { id: 'push', label: 'Push Notifications', desc: 'Receive alerts on your device' },
                { id: 'email', label: 'Email Notifications', desc: 'Get important updates via email' },
                { id: 'digest', label: 'Weekly Digest', desc: 'Summary of your progress' },
                { id: 'marketing', label: 'Marketing', desc: 'News and special offers' }
              ].map((item) => (
                <div key={item.id} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-slate-700 dark:text-slate-200">{item.label}</p>
                    <p className="text-xs text-slate-400">{item.desc}</p>
                  </div>
                  <button onClick={() => toggleNotification(item.id)}
                    className={`relative w-14 h-8 rounded-full transition-all duration-300 border ${notifications[item.id] ? 'bg-brand-500 border-brand-400 shadow-[inset_0_1px_4px_rgba(0,0,0,0.2),0_2px_8px_rgba(27,211,132,0.4)]' : 'bg-slate-200/50 dark:bg-slate-700/50 border-slate-300/50 dark:border-white/10 shadow-inner'}`}>
                    <div className="absolute inset-0 rounded-full bg-gradient-to-b from-white/20 to-transparent pointer-events-none"></div>
                    <motion.div className="absolute top-1 left-1 w-6 h-6 rounded-full bg-white shadow-md flex items-center justify-center"
                      animate={{ x: notifications[item.id] ? 24 : 0 }} transition={{ type: "spring", stiffness: 500, damping: 30 }}>
                      <div className="w-4 h-2 bg-gradient-to-b from-white to-slate-100 rounded-full blur-[1px] opacity-80" />
                    </motion.div>
                  </button>
                </div>
              ))}
            </div>
          </section>

          {/* Privacy & Security */}
          <section className="glass-panel rounded-3xl p-6 transition-colors">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2.5 bg-teal-100 dark:bg-teal-900/30 text-teal-600 dark:text-teal-400 rounded-xl shadow-inner"><Shield className="w-5 h-5" /></div>
              <h3 className="font-bold text-slate-800 dark:text-white text-lg">Privacy & Security</h3>
            </div>
            <div className="space-y-2">
              <button className="w-full flex items-center justify-between p-3.5 hover:bg-white/40 dark:hover:bg-slate-700/40 rounded-2xl transition-colors text-left">
                <span className="font-medium text-slate-700 dark:text-slate-200">Change Password</span><ChevronRight className="w-4 h-4 text-slate-300" />
              </button>
              <button className="w-full flex items-center justify-between p-3.5 hover:bg-white/40 dark:hover:bg-slate-700/40 rounded-2xl transition-colors text-left">
                <span className="font-medium text-slate-700 dark:text-slate-200">Connected Apps</span><ChevronRight className="w-4 h-4 text-slate-300" />
              </button>
            </div>
            <div className="mt-6 pt-6 border-t border-slate-200/50 dark:border-slate-700/50 space-y-3">
              <button className="w-full flex items-center gap-3 p-3.5 text-slate-600 dark:text-slate-400 hover:bg-white/40 dark:hover:bg-slate-700/40 rounded-2xl transition-colors">
                <LogOut className="w-5 h-5" /><span className="font-medium">Log Out</span>
              </button>
              <button className="w-full flex items-center gap-3 p-3.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-2xl transition-colors">
                <Trash2 className="w-5 h-5" /><span className="font-medium">Delete Account</span>
              </button>
            </div>
          </section>
        </div>
      </div>
    </motion.div>
  );
}
