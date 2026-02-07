'use client';

import { useState, useMemo } from 'react';
import {
  Plus, Sparkles, ChevronRight, Utensils, Dumbbell, AlertCircle,
  Search, X, Camera, Clock, ChevronLeft, Save, Trash2, ChevronDown, Check
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Initial Mock Database
const INITIAL_FOOD_DATABASE = [
  { id: 1, name: 'Grilled Chicken Breast', kcal: 165, p: 31, c: 0, f: 3.6, image: 'https://picsum.photos/200?random=1' },
  { id: 2, name: 'Avocado Toast', kcal: 250, p: 6, c: 18, f: 16, image: 'https://picsum.photos/200?random=2' },
  { id: 3, name: 'Greek Yogurt Bowl', kcal: 120, p: 15, c: 8, f: 0, image: 'https://picsum.photos/200?random=3' },
  { id: 4, name: 'Salmon Fillet', kcal: 208, p: 20, c: 0, f: 13, image: 'https://picsum.photos/200?random=4' },
  { id: 5, name: 'Oatmeal with Berries', kcal: 150, p: 5, c: 27, f: 2.5, image: 'https://picsum.photos/200?random=5' },
  { id: 6, name: 'Protein Shake', kcal: 110, p: 24, c: 2, f: 1, image: 'https://picsum.photos/200?random=6' },
];

export default function Dashboard() {
  const [selectedDate, setSelectedDate] = useState(2);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeSection, setActiveSection] = useState(null);

  const [foodDatabase, setFoodDatabase] = useState(INITIAL_FOOD_DATABASE);

  const [dailyMeals, setDailyMeals] = useState({
    breakfast: [],
    lunch: [{ id: 101, name: 'Grilled Chicken Salad', kcal: 450, p: 45, c: 10, f: 20, image: '' }],
    dinner: [],
    snack: [{ id: 102, name: 'Greek Yogurt', kcal: 120, p: 15, c: 8, f: 0, image: '' }],
    workout: []
  });

  const [newRecipe, setNewRecipe] = useState({
    name: '', time: '', ingredientName: '', ingredientAmount: '100',
    ingredientUnit: 'grams (g)', ingredients: [], currentStep: '', steps: []
  });

  const macros = useMemo(() => {
    let total = { calories: 0, protein: 0, carbs: 0, fat: 0 };
    Object.values(dailyMeals).flat().forEach((item) => {
      total.calories += item.kcal;
      total.protein += item.p;
      total.carbs += item.c;
      total.fat += item.f;
    });
    return {
      calories: { current: Math.round(total.calories), target: 2200, unit: 'kcal', color: 'bg-orange-500', bg: 'bg-orange-100' },
      protein: { current: Math.round(total.protein), target: 140, unit: 'g', color: 'bg-green-500', bg: 'bg-green-100' },
      fat: { current: Math.round(total.fat), target: 70, unit: 'g', color: 'bg-purple-500', bg: 'bg-purple-100' },
      carbs: { current: Math.round(total.carbs), target: 280, unit: 'g', color: 'bg-blue-500', bg: 'bg-blue-100' },
    };
  }, [dailyMeals]);

  const weekDays = [
    { day: 'M', date: 10, full: 'Mon' },
    { day: 'T', date: 11, full: 'Tue' },
    { day: 'W', date: 12, full: 'Wed' },
    { day: 'T', date: 13, full: 'Thu' },
    { day: 'F', date: 14, full: 'Fri' },
    { day: 'S', date: 15, full: 'Sat' },
    { day: 'S', date: 16, full: 'Sun' },
  ];

  const mealSections = [
    { id: 'breakfast', label: 'Breakfast', recommended: '400-600 kcal', icon: Utensils },
    { id: 'lunch', label: 'Lunch', recommended: '600-800 kcal', icon: Utensils },
    { id: 'dinner', label: 'Dinner', recommended: '500-700 kcal', icon: Utensils },
    { id: 'snack', label: 'Snacks', recommended: '100-300 kcal', icon: Utensils },
    { id: 'workout', label: 'Training', recommended: 'Burn 400 kcal', icon: Dumbbell },
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.05 } }
  };
  const itemVariants = {
    hidden: { y: 10, opacity: 0 },
    visible: { y: 0, opacity: 1 }
  };

  const openAddModal = (sectionId) => {
    setActiveSection(sectionId);
    setViewMode('search');
    setIsAddModalOpen(true);
  };

  const handleAddFoodToMeal = (food) => {
    if (activeSection) {
      setDailyMeals(prev => ({
        ...prev,
        [activeSection]: [...prev[activeSection], food]
      }));
      setIsAddModalOpen(false);
    }
  };

  const handleAddIngredient = () => {
    if (newRecipe.ingredientName.trim()) {
      setNewRecipe(prev => ({
        ...prev,
        ingredients: [...prev.ingredients, {
          name: prev.ingredientName,
          amount: prev.ingredientAmount,
          unit: prev.ingredientUnit
        }],
        ingredientName: '', ingredientAmount: '100'
      }));
    }
  };

  const handleAddStep = () => {
    if (newRecipe.currentStep.trim()) {
      setNewRecipe(prev => ({
        ...prev,
        steps: [...prev.steps, prev.currentStep],
        currentStep: ''
      }));
    }
  };

  const handleSaveRecipe = () => {
    if (!newRecipe.name) return;
    const customFood = {
      id: `custom-${Date.now()}`,
      name: newRecipe.name,
      kcal: Math.floor(Math.random() * 500) + 200,
      p: Math.floor(Math.random() * 30) + 10,
      c: Math.floor(Math.random() * 50) + 20,
      f: Math.floor(Math.random() * 20) + 5,
      image: 'https://picsum.photos/200?grayscale&blur=2'
    };
    setFoodDatabase(prev => [customFood, ...prev]);
    setNewRecipe({
      name: '', time: '', ingredientName: '', ingredientAmount: '100',
      ingredientUnit: 'grams (g)', ingredients: [], currentStep: '', steps: []
    });
    setViewMode('search');
  };

  return (
    <motion.div
      className="p-4 md:p-8 space-y-6 max-w-3xl mx-auto"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Date Navigation Strip */}
      <motion.div variants={itemVariants} className="glass-panel p-4 rounded-3xl flex flex-col gap-4">
        <div className="flex justify-between items-center px-2">
          <h2 className="font-bold text-slate-800 dark:text-white text-lg flex items-center gap-2 drop-shadow-sm">
            October 2023 <ChevronRight className="w-4 h-4 text-slate-400" />
          </h2>
          <div className="bg-brand-500/10 dark:bg-brand-500/20 text-brand-700 dark:text-brand-300 px-3 py-1 rounded-full text-xs font-bold border border-brand-500/20 backdrop-blur-sm">
            Today
          </div>
        </div>
        <div className="flex justify-between items-center text-center">
          {weekDays.map((d, index) => (
            <button
              key={index}
              onClick={() => setSelectedDate(index)}
              className={`flex flex-col items-center justify-center w-10 h-14 rounded-2xl transition-all duration-300 ${
                index === selectedDate
                  ? 'bg-slate-900 dark:bg-white text-white dark:text-slate-900 shadow-xl scale-110 border border-white/20'
                  : 'text-slate-400 hover:bg-white/40 dark:hover:bg-slate-700/40'
              }`}
            >
              <span className="text-[10px] font-medium mb-1 opacity-80">{d.day}</span>
              <span className={`text-sm font-bold ${index === selectedDate ? 'text-white dark:text-slate-900' : 'text-slate-700 dark:text-slate-300'}`}>
                {d.date}
              </span>
            </button>
          ))}
        </div>
      </motion.div>

      {/* Banners */}
      <motion.div variants={itemVariants} className="space-y-3">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white p-6 shadow-lg shadow-cyan-500/20">
          <div className="absolute inset-0 bg-gradient-to-b from-white/20 to-transparent pointer-events-none"></div>
          <div className="relative z-10 flex justify-between items-center">
            <div>
              <h3 className="font-bold text-lg mb-1 drop-shadow-sm">Summer Body Challenge! 🏖️</h3>
              <p className="text-cyan-50 text-sm font-medium opacity-90">Less than 90 days until summer.</p>
            </div>
            <div className="bg-white/20 backdrop-blur-md px-4 py-2 rounded-2xl border border-white/30 shadow-inner">
              <span className="font-mono font-bold text-xl drop-shadow-sm">89</span>
              <span className="text-xs ml-1 opacity-80 font-medium">Days</span>
            </div>
          </div>
        </div>
        <div className="glass-panel bg-rose-50/50 dark:bg-rose-900/10 border-rose-200/50 dark:border-rose-500/20 p-4 rounded-3xl flex gap-3 items-start">
          <AlertCircle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
          <div>
            <p className="text-rose-700 dark:text-rose-400 font-bold text-sm">Profile Incomplete</p>
            <p className="text-rose-600 dark:text-rose-300 text-xs mt-1">
              Complete your profile to get personalized AI recommendations.
              <span className="underline font-bold ml-1 cursor-pointer hover:text-rose-800">Complete now</span>
            </p>
          </div>
        </div>
      </motion.div>

      {/* Meal Diary List */}
      <div className="space-y-4">
        {mealSections.map((section) => {
          const items = dailyMeals[section.id] || [];
          return (
            <motion.div
              key={section.id}
              variants={itemVariants}
              className="glass-panel rounded-3xl p-1 hover:bg-white/80 dark:hover:bg-slate-900/80 transition-colors"
            >
              <div className="p-4">
                <div className="flex justify-between items-center mb-3">
                  <div>
                    <h3 className="font-bold text-slate-800 dark:text-white text-lg drop-shadow-sm">{section.label}</h3>
                    <p className="text-slate-400 text-xs font-medium">{section.recommended}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button className="flex items-center justify-center w-10 h-10 rounded-full bg-brand-50/50 dark:bg-brand-500/10 text-brand-600 dark:text-brand-400 hover:bg-brand-100 dark:hover:bg-brand-500/20 transition-colors border border-brand-200/30" title="AI Suggestions">
                      <Sparkles className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => openAddModal(section.id)}
                      className="liquid-btn liquid-btn-secondary w-10 h-10 rounded-full flex items-center justify-center"
                      title="Add Item"
                    >
                      <Plus className="w-5 h-5" />
                    </button>
                  </div>
                </div>
                {items.length > 0 ? (
                  <div className="space-y-2 mt-2">
                    <AnimatePresence>
                      {items.map((item, i) => (
                        <motion.div
                          key={`${item.id}-${i}`}
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          className="flex justify-between items-center py-3 px-4 bg-white/40 dark:bg-slate-800/40 rounded-2xl border border-white/40 dark:border-white/5 backdrop-blur-sm group"
                        >
                          <span className="font-medium text-slate-700 dark:text-slate-200 text-sm">{item.name}</span>
                          <div className="flex items-center gap-4">
                            <span className="font-bold text-slate-500 dark:text-slate-400 text-sm">{item.kcal} kcal</span>
                            <button
                              onClick={() => {
                                const newItems = [...items];
                                newItems.splice(i, 1);
                                setDailyMeals({ ...dailyMeals, [section.id]: newItems });
                              }}
                              className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-500 transition-opacity"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </div>
                ) : (
                  <div className="py-2 flex items-center gap-2 opacity-50 pl-1">
                    <div className="w-1 h-8 bg-slate-200/50 dark:bg-slate-700/50 rounded-full"></div>
                    <span className="text-slate-400 text-sm italic">No items added yet</span>
                  </div>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Macro Summary Footer */}
      <motion.div variants={itemVariants} className="glass-panel p-6 rounded-3xl sticky bottom-4 z-20 backdrop-blur-2xl">
        <div className="grid grid-cols-4 gap-4 text-center divide-x divide-slate-200/50 dark:divide-slate-700/50">
          {Object.entries(macros).map(([key, data]) => (
            <div key={key} className="px-2 first:pl-0 last:pr-0">
              <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-1">
                {key === 'calories' ? 'Kcal' : key}
              </p>
              <div className="flex items-baseline justify-center gap-[2px] mb-2">
                <span className="font-bold text-slate-800 dark:text-white text-sm md:text-base">{data.current}</span>
                <span className="text-[10px] text-slate-400">/ {data.target}</span>
              </div>
              <div className="h-2 w-full bg-slate-100 dark:bg-slate-700/50 rounded-full overflow-hidden shadow-inner">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min((data.current / data.target) * 100, 100)}%` }}
                  transition={{ duration: 0.5, type: 'spring' }}
                  className={`h-full rounded-full ${data.color} shadow-[0_0_10px_rgba(0,0,0,0.2)]`}
                />
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Add Item Modal */}
      <AnimatePresence>
        {isAddModalOpen && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setIsAddModalOpen(false)}
              className="absolute inset-0 bg-slate-900/40 backdrop-blur-md"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 30 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 30 }}
              className="w-full max-w-2xl glass-panel bg-white/90 dark:bg-slate-900/90 backdrop-blur-3xl rounded-[2rem] relative z-10 overflow-hidden flex flex-col max-h-[85vh] shadow-2xl border border-white/50 dark:border-white/10"
            >
              <div className="flex justify-between items-center p-6 border-b border-slate-200/50 dark:border-slate-700/50 sticky top-0 z-20 bg-white/50 dark:bg-slate-900/50 backdrop-blur-md">
                <h3 className="text-xl font-bold text-slate-800 dark:text-white drop-shadow-sm">
                  {viewMode === 'search' ? 'Add Food' : 'Create Recipe'}
                </h3>
                <button onClick={() => setIsAddModalOpen(false)} className="p-2 hover:bg-black/5 dark:hover:bg-white/10 rounded-full transition-colors">
                  <X className="w-5 h-5 text-slate-400" />
                </button>
              </div>

              {viewMode === 'search' ? (
                <div className="flex flex-col h-full overflow-hidden">
                  <div className="p-6 space-y-4">
                    <div className="flex gap-3">
                      <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
                        <input
                          type="text" placeholder="Search for food..."
                          value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                          className="w-full pl-10 pr-4 py-3.5 liquid-input rounded-2xl text-slate-800 dark:text-white placeholder-slate-400 outline-none"
                        />
                      </div>
                      <button onClick={() => setViewMode('create')}
                        className="liquid-btn liquid-btn-primary px-5 py-3 rounded-2xl font-semibold text-sm flex items-center gap-2 whitespace-nowrap">
                        <Plus className="w-4 h-4" /> Create Custom
                      </button>
                    </div>
                  </div>
                  <div className="flex-1 overflow-y-auto p-6 pt-0 space-y-3">
                    {foodDatabase
                      .filter(item => item.name.toLowerCase().includes(searchQuery.toLowerCase()))
                      .map((item) => (
                        <div key={item.id} onClick={() => handleAddFoodToMeal(item)}
                          className="group flex items-center gap-4 p-3 rounded-3xl border border-transparent hover:border-brand-200/50 hover:bg-white/50 dark:hover:bg-white/5 transition-all cursor-pointer">
                          <img src={item.image} alt={item.name} className="w-16 h-16 rounded-2xl object-cover shadow-md group-hover:scale-105 transition-transform" />
                          <div className="flex-1 min-w-0">
                            <div className="flex justify-between items-start mb-1">
                              <h4 className="font-bold text-slate-800 dark:text-white truncate pr-2">{item.name}</h4>
                              <button className="p-1.5 bg-brand-100 text-brand-600 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                                <Plus className="w-4 h-4" />
                              </button>
                            </div>
                            <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
                              <span className="font-semibold text-slate-700 dark:text-slate-300">{item.kcal} kcal <span className="text-slate-400 font-normal">/ 100g</span></span>
                              <div className="w-px h-3 bg-slate-300 dark:bg-slate-600"></div>
                              <div className="flex gap-2">
                                <span className="text-green-600 dark:text-green-400 font-medium">P: {item.p}</span>
                                <span className="text-blue-600 dark:text-blue-400 font-medium">C: {item.c}</span>
                                <span className="text-purple-600 dark:text-purple-400 font-medium">F: {item.f}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    <div className="text-center py-8 text-slate-400 text-sm">End of results</div>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col h-full overflow-hidden">
                  <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    <button onClick={() => setViewMode('search')}
                      className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-800 dark:hover:text-white font-medium transition-colors">
                      <ChevronLeft className="w-4 h-4" /> Back to Search
                    </button>
                    <div className="glass-panel bg-rose-50/50 dark:bg-rose-900/10 border-rose-200/50 dark:border-rose-500/20 p-4 rounded-2xl flex gap-3 items-start border-dashed">
                      <AlertCircle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
                      <div>
                        <p className="text-rose-700 dark:text-rose-400 font-bold text-sm">Profile Incomplete</p>
                        <p className="text-rose-600 dark:text-rose-300 text-xs mt-1">
                          Complete your profile to get personalized AI recommendations.
                          <span className="underline font-bold ml-1 cursor-pointer hover:text-rose-800">Complete now</span>
                        </p>
                      </div>
                    </div>
                    <div className="w-full h-32 border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-3xl flex flex-col items-center justify-center gap-2 text-slate-400 hover:border-brand-400 hover:text-brand-500 hover:bg-brand-50/10 transition-all cursor-pointer bg-white/30 dark:bg-black/20">
                      <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-full shadow-inner">
                        <Camera className="w-5 h-5" />
                      </div>
                      <span className="text-sm font-medium">Add Recipe Photo</span>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="col-span-2 space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Recipe Name</label>
                        <input type="text" placeholder="e.g. Grandma&apos;s Apple Pie"
                          value={newRecipe.name} onChange={e => setNewRecipe({...newRecipe, name: e.target.value})}
                          className="w-full p-3.5 liquid-input rounded-xl text-slate-800 dark:text-white outline-none" />
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Prep Time</label>
                        <div className="relative">
                          <Clock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                          <input type="text" placeholder="30 min"
                            value={newRecipe.time} onChange={e => setNewRecipe({...newRecipe, time: e.target.value})}
                            className="w-full pl-9 pr-3 py-3.5 liquid-input rounded-xl text-slate-800 dark:text-white outline-none" />
                        </div>
                      </div>
                    </div>
                    {/* Ingredients Builder */}
                    <div className="space-y-3">
                      <label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Ingredients</label>
                      <div className="glass-panel p-5 rounded-3xl space-y-3 bg-slate-50/50 dark:bg-slate-800/30">
                        <input type="text" placeholder="Select ingredient..."
                          value={newRecipe.ingredientName} onChange={e => setNewRecipe({...newRecipe, ingredientName: e.target.value})}
                          className="w-full p-3.5 bg-white dark:bg-slate-800 text-slate-800 dark:text-white border border-slate-200 dark:border-white/10 rounded-xl focus:border-brand-500 outline-none shadow-sm transition-all" />
                        <div className="flex gap-3">
                          <input type="number" placeholder="100"
                            value={newRecipe.ingredientAmount} onChange={e => setNewRecipe({...newRecipe, ingredientAmount: e.target.value})}
                            className="flex-1 p-3.5 bg-white dark:bg-slate-800 text-slate-800 dark:text-white border border-slate-200 dark:border-white/10 rounded-xl focus:border-brand-500 outline-none shadow-sm transition-all" />
                          <div className="relative w-1/2 sm:w-1/3">
                            <select value={newRecipe.ingredientUnit} onChange={e => setNewRecipe({...newRecipe, ingredientUnit: e.target.value})}
                              className="w-full p-3.5 bg-white dark:bg-slate-800 text-slate-800 dark:text-white border border-slate-200 dark:border-white/10 rounded-xl focus:border-brand-500 outline-none appearance-none shadow-sm transition-all">
                              <option value="grams (g)">grams (g)</option>
                              <option value="kilograms (kg)">kilograms (kg)</option>
                              <option value="milliliters (ml)">milliliters (ml)</option>
                              <option value="liters (l)">liters (l)</option>
                              <option value="cup">cup</option>
                              <option value="tbsp">tbsp</option>
                              <option value="tsp">tsp</option>
                              <option value="pcs">pieces</option>
                            </select>
                            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                          </div>
                        </div>
                        <button onClick={handleAddIngredient}
                          className="w-full py-3.5 bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-bold rounded-xl hover:scale-[1.01] transition-all flex items-center justify-center gap-2 shadow-lg">
                          <Plus className="w-4 h-4" /> Add Ingredient
                        </button>
                      </div>
                      <div className="space-y-2 mt-4">
                        <AnimatePresence>
                          {newRecipe.ingredients.map((ing, i) => (
                            <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 10 }}
                              className="flex justify-between items-center p-3 bg-white dark:bg-slate-800 rounded-xl border border-slate-100 dark:border-white/5 shadow-sm">
                              <div className="flex items-center gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-brand-500"></div>
                                <span className="font-medium text-slate-700 dark:text-slate-200 text-sm">{ing.name}</span>
                              </div>
                              <div className="flex items-center gap-3">
                                <span className="text-xs font-bold text-slate-400 bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded-lg">{ing.amount} {ing.unit}</span>
                                <button onClick={() => setNewRecipe(prev => ({...prev, ingredients: prev.ingredients.filter((_, idx) => idx !== i)}))}
                                  className="text-slate-300 hover:text-red-500 transition-colors">
                                  <X className="w-4 h-4" />
                                </button>
                              </div>
                            </motion.div>
                          ))}
                        </AnimatePresence>
                        {newRecipe.ingredients.length === 0 && <span className="text-sm text-slate-400 italic px-2">No ingredients added yet.</span>}
                      </div>
                    </div>
                    {/* Instructions Builder */}
                    <div className="space-y-3">
                      <label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Instructions</label>
                      <div className="flex gap-2 items-start">
                        <textarea placeholder="Describe the step..."
                          value={newRecipe.currentStep} onChange={e => setNewRecipe({...newRecipe, currentStep: e.target.value})}
                          className="flex-1 p-3.5 liquid-input rounded-xl text-slate-800 dark:text-white outline-none resize-none h-20" />
                        <button onClick={handleAddStep}
                          className="p-3 bg-brand-50 dark:bg-brand-900/20 text-brand-600 dark:text-brand-400 rounded-xl hover:bg-brand-100 dark:hover:bg-brand-900/40 h-20 flex items-center justify-center border border-brand-200 dark:border-brand-700/30">
                          <Plus className="w-5 h-5" />
                        </button>
                      </div>
                      <div className="space-y-2">
                        <AnimatePresence>
                          {newRecipe.steps.map((step, i) => (
                            <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                              className="flex gap-3 text-sm text-slate-600 dark:text-slate-300 bg-white/50 dark:bg-white/5 p-3 rounded-xl border border-slate-100 dark:border-slate-700">
                              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 flex items-center justify-center font-bold text-xs">{i + 1}</div>
                              <p className="flex-1 pt-0.5">{step}</p>
                              <button onClick={() => setNewRecipe(prev => ({...prev, steps: prev.steps.filter((_, idx) => idx !== i)}))}
                                className="text-slate-400 hover:text-red-500"><Trash2 className="w-4 h-4" /></button>
                            </motion.div>
                          ))}
                        </AnimatePresence>
                      </div>
                    </div>
                  </div>
                  <div className="p-5 border-t border-slate-200/50 dark:border-slate-700/50 bg-white/50 dark:bg-slate-900/50 backdrop-blur-md flex justify-end gap-3">
                    <button onClick={() => setViewMode('search')}
                      className="px-5 py-2.5 text-slate-600 dark:text-slate-300 font-semibold hover:bg-black/5 dark:hover:bg-white/10 rounded-xl transition-colors">Cancel</button>
                    <button onClick={handleSaveRecipe}
                      className="liquid-btn liquid-btn-primary px-6 py-2.5 rounded-xl font-semibold flex items-center gap-2">
                      <Save className="w-4 h-4" /> Save Recipe
                    </button>
                  </div>
                </div>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
