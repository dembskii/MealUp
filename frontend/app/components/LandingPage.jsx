'use client';

import { motion } from 'framer-motion';
import {
  Utensils, Dumbbell, Users, BarChart3,
  ChefHat, Sparkles, ArrowRight, LogIn, UserPlus,
  GraduationCap, Heart, TrendingUp, Shield
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.6, ease: [0.22, 1, 0.36, 1] },
  }),
};

const features = [
  {
    icon: Utensils,
    title: 'Smart Nutrition',
    desc: 'Browse and create recipes, track macros, and plan meals with AI-powered suggestions.',
    gradient: 'from-emerald-400 to-brand-500',
  },
  {
    icon: Dumbbell,
    title: 'Workout Builder',
    desc: 'Design custom training plans, track exercises, and follow structured workout schedules.',
    gradient: 'from-blue-400 to-indigo-500',
  },
  {
    icon: Users,
    title: 'Community',
    desc: 'Share progress, discuss nutrition tips, and connect with like-minded fitness enthusiasts.',
    gradient: 'from-purple-400 to-pink-500',
  },
  {
    icon: BarChart3,
    title: 'Progress Tracking',
    desc: 'Monitor your daily intake, workout consistency, and overall health goals in one dashboard.',
    gradient: 'from-orange-400 to-red-500',
  },
];

const stats = [
  { value: '500+', label: 'Recipes' },
  { value: '200+', label: 'Exercises' },
  { value: '24/7', label: 'AI Assistant' },
  { value: '100%', label: 'Free' },
];

export default function LandingPage() {
  const { handleLogin, handleSignUp } = useAuth();

  return (
    <div className="min-h-screen text-slate-800 dark:text-slate-100 font-sans selection:bg-brand-500 selection:text-white overflow-x-hidden">
      {/* ─── NAVBAR ─── */}
      <nav className="fixed top-0 inset-x-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/images/logo.png" alt="MealUp" className="w-9 h-9 drop-shadow-lg" />
            <span className="text-2xl font-bold text-slate-800 dark:text-white tracking-tight">
              MealUp
            </span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleLogin}
              className="px-5 py-2.5 rounded-2xl text-sm font-semibold liquid-btn liquid-btn-secondary"
            >
              <span className="flex items-center gap-2">
                <LogIn className="w-4 h-4" />
                Sign In
              </span>
            </button>
            <button
              onClick={() => handleSignUp('user')}
              className="px-5 py-2.5 rounded-2xl text-sm font-bold liquid-btn liquid-btn-primary shadow-lg shadow-brand-500/20"
            >
              <span className="flex items-center gap-2">
                <UserPlus className="w-4 h-4 text-white" />
                Get Started
              </span>
            </button>
          </div>
        </div>
      </nav>

      {/* ─── HERO ─── */}
      <section className="relative pt-32 pb-20 px-6">
        <div className="max-w-5xl mx-auto text-center">
          <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={0}>
            <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold bg-brand-100 dark:bg-brand-900/30 text-brand-700 dark:text-brand-300 border border-brand-200 dark:border-brand-700/30 mb-6">
              <Sparkles className="w-3.5 h-3.5" />
              AI-Powered Fitness & Nutrition
            </span>
          </motion.div>

          <motion.h1
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            custom={1}
            className="text-5xl sm:text-6xl lg:text-7xl font-extrabold leading-tight tracking-tight mb-6"
          >
            Your Health Journey
            <br />
            <span className="bg-gradient-to-r from-brand-400 to-brand-600 bg-clip-text text-transparent">
              Starts Here
            </span>
          </motion.h1>

          <motion.p
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            custom={2}
            className="text-lg sm:text-xl text-slate-500 dark:text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            Track nutrition, build workouts, discover recipes, and connect with a community
            of fitness enthusiasts — all in one beautiful app.
          </motion.p>

          <motion.div
            variants={fadeUp}
            initial="hidden"
            animate="visible"
            custom={3}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <button
              onClick={() => handleSignUp('user')}
              className="px-8 py-4 rounded-2xl text-base font-bold liquid-btn liquid-btn-primary shadow-xl shadow-brand-500/30 flex items-center gap-2"
            >
              Create Free Account
              <ArrowRight className="w-5 h-5 text-white" />
            </button>
            <button
              onClick={() => handleSignUp('trainer')}
              className="px-8 py-4 rounded-2xl text-base font-semibold text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20 hover:bg-orange-100 dark:hover:bg-orange-900/30 transition-all border border-orange-200 dark:border-orange-700/30 flex items-center gap-2"
            >
              <GraduationCap className="w-5 h-5" />
              Join as Trainer
            </button>
          </motion.div>
        </div>
      </section>

      {/* ─── STATS BAR ─── */}
      <section className="px-6 pb-16">
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-50px' }}
          custom={0}
          className="max-w-4xl mx-auto glass-panel rounded-3xl p-6 flex items-center justify-around"
        >
          {stats.map((s, i) => (
            <motion.div
              key={s.label}
              variants={fadeUp}
              custom={i + 1}
              className="text-center"
            >
              <p className="text-2xl sm:text-3xl font-extrabold bg-gradient-to-b from-brand-400 to-brand-600 bg-clip-text text-transparent">
                {s.value}
              </p>
              <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 font-medium mt-1">
                {s.label}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* ─── FEATURES ─── */}
      <section className="px-6 pb-24">
        <div className="max-w-6xl mx-auto">
          <motion.div
            variants={fadeUp}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-50px' }}
            custom={0}
            className="text-center mb-14"
          >
            <h2 className="text-3xl sm:text-4xl font-extrabold mb-4">
              Everything You Need
            </h2>
            <p className="text-slate-500 dark:text-slate-400 max-w-xl mx-auto">
              A complete toolkit to manage your nutrition, training, and wellness goals.
            </p>
          </motion.div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((f, i) => {
              const Icon = f.icon;
              return (
                <motion.div
                  key={f.title}
                  variants={fadeUp}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true, margin: '-30px' }}
                  custom={i}
                  className="glass-panel rounded-3xl p-6 hover:shadow-xl hover:scale-[1.03] transition-all duration-300 group cursor-default"
                >
                  <div
                    className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${f.gradient} flex items-center justify-center mb-4 shadow-lg group-hover:scale-110 transition-transform`}
                  >
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="font-bold text-lg mb-2 text-slate-800 dark:text-white">
                    {f.title}
                  </h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                    {f.desc}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ─── HIGHLIGHTS ─── */}
      <section className="px-6 pb-24">
        <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-6">
          {[
            {
              icon: Heart,
              title: 'Community Driven',
              text: 'Share recipes, workouts, and tips with a supportive community. Like, comment, and connect.',
              color: 'text-pink-500',
              bg: 'bg-pink-50 dark:bg-pink-900/20',
            },
            {
              icon: Shield,
              title: 'Trainer Profiles',
              text: 'Certified trainers can create and share professional workout plans and nutrition guides.',
              color: 'text-blue-500',
              bg: 'bg-blue-50 dark:bg-blue-900/20',
            },
            {
              icon: TrendingUp,
              title: 'Track Progress',
              text: 'Log your meals, monitor macro intake, and visualize your fitness journey over time.',
              color: 'text-orange-500',
              bg: 'bg-orange-50 dark:bg-orange-900/20',
            },
          ].map((item, i) => {
            const Icon = item.icon;
            return (
              <motion.div
                key={item.title}
                variants={fadeUp}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: '-30px' }}
                custom={i}
                className={`${item.bg} rounded-3xl p-6 border border-white/30 dark:border-white/5`}
              >
                <Icon className={`w-8 h-8 ${item.color} mb-4`} />
                <h3 className="font-bold text-lg mb-2 text-slate-800 dark:text-white">
                  {item.title}
                </h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                  {item.text}
                </p>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section className="px-6 pb-20">
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-50px' }}
          custom={0}
          className="max-w-3xl mx-auto text-center glass-panel rounded-3xl p-10"
        >
          <ChefHat className="w-12 h-12 text-brand-500 mx-auto mb-4" />
          <h2 className="text-3xl sm:text-4xl font-extrabold mb-4">
            Ready to Level Up?
          </h2>
          <p className="text-slate-500 dark:text-slate-400 max-w-lg mx-auto mb-8">
            Join MealUp today and take control of your nutrition and fitness with
            smart tools, a vibrant community, and AI-powered insights.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={() => handleSignUp('user')}
              className="px-8 py-4 rounded-2xl text-base font-bold liquid-btn liquid-btn-primary shadow-xl shadow-brand-500/30 flex items-center gap-2"
            >
              Get Started — It's Free
              <ArrowRight className="w-5 h-5 text-white" />
            </button>
            <button
              onClick={handleLogin}
              className="px-8 py-4 rounded-2xl text-base font-semibold liquid-btn liquid-btn-secondary flex items-center gap-2"
            >
              <LogIn className="w-5 h-5" />
              Sign In
            </button>
          </div>
        </motion.div>
      </section>

      {/* ─── FOOTER ─── */}
      <footer className="border-t border-white/20 dark:border-white/5 py-8 px-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <img src="/images/logo.png" alt="MealUp" className="w-6 h-6" />
            <span className="text-sm font-semibold text-slate-600 dark:text-slate-400">
              MealUp
            </span>
          </div>
          <p className="text-xs text-slate-400 dark:text-slate-500">
            &copy; {new Date().getFullYear()} MealUp. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
