'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Bell, Moon, Sun, Monitor, Shield, Globe, Ruler, ChevronRight,
  LogOut, Trash2, User, X, Save, Loader2, Check, Edit3,
  Heart, Calendar, Weight, ArrowUpDown, Mail, Clock
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { getUserById, updateUser } from '../services/userService';

export default function Settings({ currentTheme, setTheme }) {
  const { user: authUser, handleLogout } = useAuth();
  const [notifications, setNotifications] = useState({ email: true, push: true, digest: false, marketing: false });
  const [units, setUnits] = useState('metric');

  // Profile state
  const [profile, setProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Edit form state
  const [form, setForm] = useState({
    username: '', first_name: '', last_name: '', date_of_birth: '',
    sex: '', age: '',
    weight: '', weight_unit: 'kg', height: '', height_unit: 'cm',
  });

  const fetchProfile = useCallback(async () => {
    if (!authUser?.internal_uid) return;
    setProfileLoading(true);
    try {
      const data = await getUserById(authUser.internal_uid);
      if (data) {
        setProfile(data);
        setForm({
          username: data.username || '',
          first_name: data.first_name || '',
          last_name: data.last_name || '',
          date_of_birth: data.date_of_birth || '',
          sex: data.sex || '',
          age: data.age ?? '',
          weight: data.body_params?.weight ?? '',
          weight_unit: data.body_params?.weight_unit || 'kg',
          height: data.body_params?.height ?? '',
          height_unit: data.body_params?.height_unit || 'cm',
        });
      }
    } catch (err) {
      console.error('Failed to load profile:', err);
    } finally {
      setProfileLoading(false);
    }
  }, [authUser?.internal_uid]);

  useEffect(() => { fetchProfile(); }, [fetchProfile]);

  const toggleNotification = (key) => setNotifications(prev => ({ ...prev, [key]: !prev[key] }));

  const handleFormChange = (field, value) => setForm(prev => ({ ...prev, [field]: value }));

  const handleSave = async () => {
    if (!authUser?.internal_uid) return;
    setSaving(true);
    try {
      // Ensure date_of_birth is in YYYY-MM-DD format for the backend
      let dateValue = form.date_of_birth || undefined;
      if (dateValue) {
        const parsed = new Date(dateValue);
        if (!isNaN(parsed.getTime())) {
          dateValue = parsed.toISOString().split('T')[0]; // "YYYY-MM-DD"
        } else {
          dateValue = undefined;
        }
      }

      const payload = {
        username: form.username || undefined,
        first_name: form.first_name || undefined,
        last_name: form.last_name || undefined,
        date_of_birth: dateValue,
        sex: form.sex || undefined,
        age: form.age ? parseInt(form.age) : undefined,
        body_params: {
          weight: form.weight ? parseFloat(form.weight) : undefined,
          weight_unit: form.weight_unit,
          height: form.height ? parseFloat(form.height) : undefined,
          height_unit: form.height_unit,
        },
      };
      // Remove undefined keys from body_params
      Object.keys(payload.body_params).forEach(k => payload.body_params[k] === undefined && delete payload.body_params[k]);
      if (Object.keys(payload.body_params).length === 0) delete payload.body_params;
      Object.keys(payload).forEach(k => payload[k] === undefined && delete payload[k]);

      await updateUser(authUser.internal_uid, payload);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2000);
      await fetchProfile();
      setEditModalOpen(false);
    } catch (err) {
      console.error('Failed to save profile:', err);
      const msg = err?.message || '';
      const detail = msg.includes(':') ? msg.split(':').slice(1).join(':').trim() : msg;
      alert(`Failed to save profile: ${detail || 'Unknown error. Please try again.'}`);
    } finally {
      setSaving(false);
    }
  };

  // Display helpers
  const displayName = profile
    ? (profile.first_name && profile.last_name ? `${profile.first_name} ${profile.last_name}` : profile.username || authUser?.name || 'User')
    : authUser?.name || 'User';
  const displayEmail = profile?.email || authUser?.email || '';
  const avatarUrl = authUser?.picture;
  const initials = displayName.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);

  const formatDate = (d) => {
    if (!d) return '—';
    try { return new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }); } catch { return d; }
  };

  // Profile data rows
  const personalInfo = [
    { label: 'Username', value: profile?.username || '—', icon: User },
    { label: 'First Name', value: profile?.first_name || '—', icon: User },
    { label: 'Last Name', value: profile?.last_name || '—', icon: User },
    { label: 'Email', value: displayEmail || '—', icon: Mail },
    { label: 'Date of Birth', value: formatDate(profile?.date_of_birth), icon: Calendar },
    { label: 'Role', value: profile?.role || authUser?.role || '—', icon: Shield },
    { label: 'Member Since', value: formatDate(profile?.created_at), icon: Clock },
  ];

  const healthInfo = [
    { label: 'Sex', value: profile?.sex ? profile.sex.charAt(0).toUpperCase() + profile.sex.slice(1) : '—', icon: Heart },
    { label: 'Age', value: profile?.age ?? '—', icon: Calendar },
    { label: 'Weight', value: profile?.body_params?.weight ? `${profile.body_params.weight} ${profile.body_params.weight_unit || 'kg'}` : '—', icon: Weight },
    { label: 'Height', value: profile?.body_params?.height ? `${profile.body_params.height} ${profile.body_params.height_unit || 'cm'}` : '—', icon: ArrowUpDown },
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-6 md:p-10 max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-800 dark:text-white drop-shadow-sm">Settings</h2>
        <p className="text-slate-500 dark:text-slate-400 mt-1">Manage your account preferences and app experience.</p>
      </div>

      {/* ── Account Card ── */}
      <div className="glass-panel rounded-3xl p-6 mb-6 transition-colors">
        {profileLoading ? (
          <div className="flex items-center gap-4 animate-pulse">
            <div className="w-16 h-16 rounded-full bg-slate-200 dark:bg-slate-700" />
            <div className="space-y-2 flex-1"><div className="h-5 w-40 bg-slate-200 dark:bg-slate-700 rounded-lg" /><div className="h-4 w-56 bg-slate-200 dark:bg-slate-700 rounded-lg" /></div>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center gap-4">
                <div className="relative">
                  {avatarUrl ? (
                    <img src={avatarUrl} alt="Profile" className="w-16 h-16 rounded-full object-cover border-4 border-white/50 shadow-md" />
                  ) : (
                    <div className="w-16 h-16 rounded-full bg-brand-500 flex items-center justify-center text-white font-bold text-xl border-4 border-white/50 shadow-md">{initials}</div>
                  )}
                  <div className="absolute bottom-0 right-0 bg-brand-500 text-white p-1 rounded-full border-2 border-white shadow-sm"><User className="w-3 h-3" /></div>
                </div>
                <div>
                  <h3 className="text-xl font-bold text-slate-800 dark:text-white">{displayName}</h3>
                  <p className="text-slate-400 text-sm">{displayEmail}</p>
                  {profile?.role && <span className="inline-block mt-1 text-[10px] font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-900/20 px-2 py-0.5 rounded-full">{profile.role}</span>}
                </div>
              </div>
              <button onClick={() => setEditModalOpen(true)}
                className="liquid-btn liquid-btn-secondary px-5 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2"><Edit3 className="w-4 h-4" />Edit Profile</button>
            </div>

            {/* Personal Info */}
            <div className="mt-6 pt-6 border-t border-slate-200/30 dark:border-slate-700/30">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Personal Information</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {personalInfo.map(item => (
                  <div key={item.label} className="flex items-center gap-3 p-3 bg-slate-50/90 dark:bg-slate-800/30 rounded-2xl border border-slate-200/60 dark:border-white/5">
                    <div className="p-2 bg-slate-100 dark:bg-slate-700/50 rounded-xl"><item.icon className="w-4 h-4 text-slate-400" /></div>
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{item.label}</p>
                      <p className="text-sm font-medium text-slate-700 dark:text-slate-200">{item.value}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Health Info */}
            <div className="mt-6 pt-6 border-t border-slate-200/30 dark:border-slate-700/30">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Health & Body</h4>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {healthInfo.map(item => (
                  <div key={item.label} className="flex flex-col items-center p-4 bg-slate-50/90 dark:bg-slate-800/30 rounded-2xl border border-slate-200/60 dark:border-white/5 text-center">
                    <div className="p-2 bg-brand-50 dark:bg-brand-900/20 rounded-xl mb-2"><item.icon className="w-4 h-4 text-brand-500" /></div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{item.label}</p>
                    <p className="text-base font-bold text-slate-800 dark:text-white mt-1">{item.value}</p>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
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
                  className={`flex flex-col items-center justify-center p-3 rounded-2xl border-2 transition-all ${currentTheme === item.id ? 'liquid-card border-brand-500/50 text-brand-700 dark:text-brand-400 shadow-md' : 'border-transparent hover:bg-slate-100/80 dark:hover:bg-white/40 text-slate-500 dark:text-slate-400'}`}>
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
                <div className="flex items-center justify-between p-3.5 bg-slate-50/90 dark:bg-slate-800/40 rounded-2xl border border-slate-200/60 dark:border-white/5 transition-colors">
                <div className="flex items-center gap-3"><Ruler className="w-5 h-5 text-slate-400" /><span className="font-medium text-slate-700 dark:text-slate-200">Units</span></div>
                <div className="flex bg-white/50 dark:bg-slate-700/50 rounded-xl p-1 shadow-inner border border-white/10">
                  <button onClick={() => setUnits('metric')}
                    className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all ${units === 'metric' ? 'bg-white dark:bg-slate-600 text-slate-800 dark:text-white shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700'}`}>Metric</button>
                  <button onClick={() => setUnits('imperial')}
                    className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all ${units === 'imperial' ? 'bg-white dark:bg-slate-600 text-slate-800 dark:text-white shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700'}`}>Imperial</button>
                </div>
              </div>
              <button className="w-full flex items-center justify-between p-3.5 bg-slate-50/90 dark:bg-slate-800/40 rounded-2xl border border-slate-200/60 dark:border-white/5 hover:bg-slate-100/80 dark:hover:bg-slate-800/60 transition-colors">
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
                    className={`relative w-14 h-8 rounded-full transition-all duration-300 border ${notifications[item.id] ? 'bg-brand-500 border-brand-400 shadow-[inset_0_1px_4px_rgba(0,0,0,0.2),0_2px_8px_rgba(27,211,132,0.4)]' : 'bg-slate-200/80 dark:bg-slate-700/50 border-slate-300/60 dark:border-white/10 shadow-inner'}`}>
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
              <button onClick={handleLogout}
                className="w-full flex items-center gap-3 p-3.5 text-slate-600 dark:text-slate-400 hover:bg-white/40 dark:hover:bg-slate-700/40 rounded-2xl transition-colors">
                <LogOut className="w-5 h-5" /><span className="font-medium">Log Out</span>
              </button>
              <button className="w-full flex items-center gap-3 p-3.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-2xl transition-colors">
                <Trash2 className="w-5 h-5" /><span className="font-medium">Delete Account</span>
              </button>
            </div>
          </section>
        </div>
      </div>

      {/* ── Edit Profile Modal ── */}
      <AnimatePresence>
        {editModalOpen && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setEditModalOpen(false)} className="absolute inset-0 bg-slate-900/40 backdrop-blur-md" />
            <motion.div initial={{ opacity: 0, scale: 0.9, y: 30 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.9, y: 30 }}
              className="w-full max-w-xl glass-panel bg-white/90 dark:bg-slate-900/90 backdrop-blur-3xl rounded-[2rem] relative z-10 overflow-hidden flex flex-col max-h-[85vh] shadow-2xl border border-white/50 dark:border-white/10">

              {/* Header */}
              <div className="flex justify-between items-center p-6 border-b border-slate-200/50 dark:border-slate-700/50 sticky top-0 z-20 bg-white/50 dark:bg-slate-900/50 backdrop-blur-md">
                <h3 className="text-xl font-bold text-slate-800 dark:text-white drop-shadow-sm">Edit Profile</h3>
                <button onClick={() => setEditModalOpen(false)} className="p-2 hover:bg-black/5 dark:hover:bg-white/10 rounded-full transition-colors"><X className="w-5 h-5 text-slate-400" /></button>
              </div>

              {/* Form body */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">

                {/* Personal Information */}
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2"><User className="w-4 h-4" />Personal Information</h4>
                  <div className="space-y-4">
                    <div>
                      <label className="text-xs font-bold text-slate-500 mb-1 block ml-1">Username</label>
                      <input type="text" value={form.username} onChange={e => handleFormChange('username', e.target.value)}
                        placeholder="Enter username" maxLength={40}
                        className="w-full p-3.5 liquid-input rounded-xl text-slate-800 dark:text-white outline-none" />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs font-bold text-slate-500 mb-1 block ml-1">First Name</label>
                        <input type="text" value={form.first_name} onChange={e => handleFormChange('first_name', e.target.value)}
                          placeholder="First name" maxLength={50}
                          className="w-full p-3.5 liquid-input rounded-xl text-slate-800 dark:text-white outline-none" />
                      </div>
                      <div>
                        <label className="text-xs font-bold text-slate-500 mb-1 block ml-1">Last Name</label>
                        <input type="text" value={form.last_name} onChange={e => handleFormChange('last_name', e.target.value)}
                          placeholder="Last name" maxLength={50}
                          className="w-full p-3.5 liquid-input rounded-xl text-slate-800 dark:text-white outline-none" />
                      </div>
                    </div>
                    <div>
                      <label className="text-xs font-bold text-slate-500 mb-1 block ml-1">Date of Birth</label>
                      <input type="date" value={form.date_of_birth} onChange={e => handleFormChange('date_of_birth', e.target.value)}
                        className="w-full p-3.5 liquid-input rounded-xl text-slate-800 dark:text-white outline-none" />
                    </div>
                  </div>
                </div>

                {/* Divider */}
                <div className="border-t border-slate-200/30 dark:border-slate-700/30" />

                {/* Health & Body */}
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2"><Heart className="w-4 h-4" />Health & Body</h4>
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs font-bold text-slate-500 mb-1 block ml-1">Sex</label>
                        <select value={form.sex} onChange={e => handleFormChange('sex', e.target.value)}
                          className="w-full p-3.5 liquid-input rounded-xl text-slate-800 dark:text-white outline-none appearance-none">
                          <option value="">Select...</option>
                          <option value="male">Male</option>
                          <option value="female">Female</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-xs font-bold text-slate-500 mb-1 block ml-1">Age</label>
                        <input type="number" value={form.age} onChange={e => handleFormChange('age', e.target.value)}
                          placeholder="e.g. 25" min={1} max={150}
                          className="w-full p-3.5 liquid-input rounded-xl text-slate-800 dark:text-white outline-none" />
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-3">
                      <div className="col-span-2">
                        <label className="text-xs font-bold text-slate-500 mb-1 block ml-1">Weight</label>
                        <input type="number" step="0.1" value={form.weight} onChange={e => handleFormChange('weight', e.target.value)}
                          placeholder="e.g. 70"
                          className="w-full p-3.5 liquid-input rounded-xl text-slate-800 dark:text-white outline-none" />
                      </div>
                      <div>
                        <label className="text-xs font-bold text-slate-500 mb-1 block ml-1">Unit</label>
                        <select value={form.weight_unit} onChange={e => handleFormChange('weight_unit', e.target.value)}
                          className="w-full p-3.5 liquid-input rounded-xl text-slate-800 dark:text-white outline-none appearance-none">
                          <option value="kg">kg</option>
                          <option value="lb">lb</option>
                        </select>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-3">
                      <div className="col-span-2">
                        <label className="text-xs font-bold text-slate-500 mb-1 block ml-1">Height</label>
                        <input type="number" step="0.1" value={form.height} onChange={e => handleFormChange('height', e.target.value)}
                          placeholder="e.g. 175"
                          className="w-full p-3.5 liquid-input rounded-xl text-slate-800 dark:text-white outline-none" />
                      </div>
                      <div>
                        <label className="text-xs font-bold text-slate-500 mb-1 block ml-1">Unit</label>
                        <select value={form.height_unit} onChange={e => handleFormChange('height_unit', e.target.value)}
                          className="w-full p-3.5 liquid-input rounded-xl text-slate-800 dark:text-white outline-none appearance-none">
                          <option value="cm">cm</option>
                          <option value="m">m</option>
                          <option value="ft">ft</option>
                        </select>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Read-only info */}
                <div className="border-t border-slate-200/30 dark:border-slate-700/30 pt-4">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Read-only</p>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between p-3 bg-slate-50/50 dark:bg-slate-800/30 rounded-xl">
                      <span className="text-slate-400">Email</span>
                      <span className="text-slate-600 dark:text-slate-300 font-medium">{displayEmail}</span>
                    </div>
                    <div className="flex justify-between p-3 bg-slate-50/50 dark:bg-slate-800/30 rounded-xl">
                      <span className="text-slate-400">Role</span>
                      <span className="text-slate-600 dark:text-slate-300 font-medium">{profile?.role || authUser?.role || '—'}</span>
                    </div>
                    <div className="flex justify-between p-3 bg-slate-50/50 dark:bg-slate-800/30 rounded-xl">
                      <span className="text-slate-400">Member Since</span>
                      <span className="text-slate-600 dark:text-slate-300 font-medium">{formatDate(profile?.created_at)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="p-5 border-t border-slate-200/50 dark:border-slate-700/50 bg-white/50 dark:bg-slate-900/50 backdrop-blur-md flex justify-end gap-3">
                <button onClick={() => setEditModalOpen(false)}
                  className="px-5 py-2.5 text-slate-600 dark:text-slate-300 font-semibold hover:bg-black/5 dark:hover:bg-white/10 rounded-xl transition-colors">Cancel</button>
                <button onClick={handleSave} disabled={saving}
                  className="liquid-btn liquid-btn-primary px-6 py-2.5 rounded-xl font-semibold flex items-center gap-2 disabled:opacity-50">
                  {saving ? <><Loader2 className="w-4 h-4 animate-spin" />Saving...</> : saveSuccess ? <><Check className="w-4 h-4" />Saved!</> : <><Save className="w-4 h-4" />Save Changes</>}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
