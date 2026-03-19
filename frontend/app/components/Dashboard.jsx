'use client';

import { useState, useMemo, useEffect, useRef, useCallback } from 'react';
import {
  Plus, Sparkles, Utensils,
  Search, X, Camera, Clock, ChevronLeft, Save, Trash2, ChevronDown,
  CalendarDays, ChevronRight
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { getRecipes, getIngredients } from '../services/recipeService';
import {
  getDailyLog,
  getDailyLogsRange,
  createMealEntry,
  deleteMealEntry,
} from '../services/analyticsService';

const CACHE_TTL_MS = 60 * 1000;
let cachedFoodDatabase = null;
let cachedFoodDatabasePromise = null;
const inFlightDailyLogRequests = new Map();
const dailyLogCache = new Map();
const inFlightMonthSummaryRequests = new Map();
const monthSummaryCache = new Map();

// ---- Date helpers ----
const DAY_SHORT = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

function isSameDay(a, b) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

function startOfWeek(date) {
  const d = new Date(date);
  const day = d.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  d.setDate(d.getDate() + diff);
  d.setHours(0, 0, 0, 0);
  return d;
}

function getWeekDays(anchorDate) {
  const start = startOfWeek(anchorDate);
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(start);
    d.setDate(d.getDate() + i);
    return d;
  });
}

function getCalendarGrid(year, month) {
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const startDay = firstDay.getDay() === 0 ? 6 : firstDay.getDay() - 1;
  const days = [];
  for (let i = 0; i < startDay; i++) days.push(null);
  for (let d = 1; d <= lastDay.getDate(); d++) days.push(new Date(year, month, d));
  return days;
}

function formatDateKey(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function emptyMealsState() {
  return { breakfast: [], lunch: [], dinner: [], snack: [] };
}

function convertToGrams(quantity, unit) {
  const q = Number(quantity) || 0;
  switch (unit) {
    case 'kg': return q * 1000;
    case 'ml': return q;
    case 'l': return q * 1000;
    case 'tsp': return q * 5;
    case 'tbsp': return q * 15;
    case 'cup': return q * 240;
    // Keep conversion identical to the Nutrition tab implementation.
    case 'oz': return q * 28.35;
    case 'lb': return q * 453.6;
    case 'pcs': return q * 100;
    case 'g':
    default:
      return q;
  }
}

function computeRecipeBaseGrams(ingredients) {
  return (ingredients || []).reduce(
    (sum, ing) => sum + convertToGrams(ing.quantity, ing.capacity),
    0,
  );
}

function computeRecipeMacrosPer100(recipe, ingredientMap) {
  let calories = 0;
  let protein = 0;
  let carbs = 0;
  let fat = 0;
  let totalWeight = 0;

  for (const item of recipe.ingredients || []) {
    const ing = ingredientMap[item.ingredient_id];
    const weightG = convertToGrams(item.quantity || 0, item.capacity);
    totalWeight += weightG;

    if (ing?.macro_per_hundred) {
      const factor = weightG / 100;
      calories += (ing.macro_per_hundred.calories || 0) * factor;
      protein += (ing.macro_per_hundred.proteins || 0) * factor;
      carbs += (ing.macro_per_hundred.carbs || 0) * factor;
      fat += (ing.macro_per_hundred.fats || 0) * factor;
    }
  }

  if (totalWeight <= 0) {
    return { kcal: 0, p: 0, c: 0, f: 0 };
  }

  const norm = 100 / totalWeight;
  return {
    kcal: Math.round(calories * norm),
    p: Math.round(protein * norm),
    c: Math.round(carbs * norm),
    f: Math.round(fat * norm),
  };
}

function mapDailyLogToMeals(log) {
  const meals = emptyMealsState();

  for (const entry of log?.meals || []) {
    const section = entry.meal_type;
    if (!meals[section]) continue;
    meals[section].push({
      entryId: entry._id || entry.id,
      id: entry.recipe_id || entry._id || entry.id,
      recipeId: entry.recipe_id,
      name: entry.recipe_name || (entry.ingredients || []).map((i) => i.name).join(', ') || 'Meal entry',
      kcal: Math.round(entry.total_macros?.calories || 0),
      p: Math.round(entry.total_macros?.proteins || 0),
      c: Math.round(entry.total_macros?.carbs || 0),
      f: Math.round(entry.total_macros?.fats || 0),
      grams: Math.round((entry.ingredients || []).reduce((sum, ing) => sum + (Number(ing.quantity) || 0), 0)),
    });
  }

  meals._totalMacro = log?.total_macros || null;
  return meals;
}

function isFresh(entry) {
  return !!entry && Date.now() - entry.ts < CACHE_TTL_MS;
}

async function fetchDailyLogDedup(dateToLoad, force = false) {
  const cached = dailyLogCache.get(dateToLoad);
  if (!force && isFresh(cached)) {
    return cached.data;
  }

  if (!force && inFlightDailyLogRequests.has(dateToLoad)) {
    return inFlightDailyLogRequests.get(dateToLoad);
  }

  const request = (async () => {
    const dailyLog = await getDailyLog(dateToLoad);
    dailyLogCache.set(dateToLoad, { data: dailyLog, ts: Date.now() });
    return dailyLog;
  })().finally(() => {
    inFlightDailyLogRequests.delete(dateToLoad);
  });

  inFlightDailyLogRequests.set(dateToLoad, request);
  return request;
}

async function fetchMonthSummaryDedup(from, to, force = false) {
  const key = `${from}:${to}`;
  const cached = monthSummaryCache.get(key);

  if (!force && isFresh(cached)) {
    return cached.data;
  }

  if (!force && inFlightMonthSummaryRequests.has(key)) {
    return inFlightMonthSummaryRequests.get(key);
  }

  const request = (async () => {
    const logs = await getDailyLogsRange(from, to);
    monthSummaryCache.set(key, { data: logs || [], ts: Date.now() });
    return logs || [];
  })().finally(() => {
    inFlightMonthSummaryRequests.delete(key);
  });

  inFlightMonthSummaryRequests.set(key, request);
  return request;
}

async function fetchFoodDatabaseDedup() {
  if (cachedFoodDatabase) {
    return cachedFoodDatabase;
  }

  if (cachedFoodDatabasePromise) {
    return cachedFoodDatabasePromise;
  }

  cachedFoodDatabasePromise = (async () => {
    const limit = 100;
    let skip = 0;
    const recipes = [];

    const ingredients = await getIngredients({ skip: 0, limit: 500 });
    const map = {};
    (ingredients || []).forEach((ing) => {
      const key = ing.id || ing._id;
      if (key) map[key] = ing;
    });

    // Recipe API enforces limit <= 100, so fetch in pages.
    while (true) {
      const page = await getRecipes({ skip, limit });
      if (!page?.length) break;
      recipes.push(...page);
      if (page.length < limit) break;
      skip += limit;
    }

    const mappedRecipes = (recipes || []).map((recipe) => ({
      ...computeRecipeMacrosPer100(recipe, map),
      id: recipe._id || recipe.id,
      recipeId: recipe._id || recipe.id,
      name: recipe.name,
      ingredients: recipe.ingredients || [],
      baseTotalGrams: computeRecipeBaseGrams(recipe.ingredients || []),
      image: recipe.image || `https://picsum.photos/seed/${recipe._id || recipe.id}/200/200`,
    }));

    cachedFoodDatabase = mappedRecipes;
    return mappedRecipes;
  })().finally(() => {
    cachedFoodDatabasePromise = null;
  });

  return cachedFoodDatabasePromise;
}

export default function Dashboard() {
  const { user: authUser } = useAuth();
  const today = useMemo(() => { const d = new Date(); d.setHours(0, 0, 0, 0); return d; }, []);
  const [selectedDate, setSelectedDate] = useState(today);
  const [calendarOpen, setCalendarOpen] = useState(false);
  const [calMonth, setCalMonth] = useState(today.getMonth());
  const [calYear, setCalYear] = useState(today.getFullYear());
  const weekDays = useMemo(() => getWeekDays(selectedDate), [selectedDate]);
  const calendarRef = useRef(null);

  // Close calendar on click outside
  useEffect(() => {
    if (!calendarOpen) return;
    const handleClickOutside = (e) => {
      if (calendarRef.current && !calendarRef.current.contains(e.target)) {
        setCalendarOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [calendarOpen]);

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [portionGrams, setPortionGrams] = useState('100');
  const [activeSection, setActiveSection] = useState(null);
  const [foodDatabase, setFoodDatabase] = useState([]);

  const [allMeals, setAllMeals] = useState({});
  const [recordedDateKeys, setRecordedDateKeys] = useState(new Set());
  const [isSavingMeal, setIsSavingMeal] = useState(false);

  const dateKey = useMemo(() => formatDateKey(selectedDate), [selectedDate]);
  const dailyMeals = allMeals[dateKey] || { ...emptyMealsState(), _totalMacro: null };

  const refreshDateData = useCallback(async (dateToLoad, force = false) => {
    try {
      const dailyLog = await fetchDailyLogDedup(dateToLoad, force);
      const mapped = mapDailyLogToMeals(dailyLog);
      const hasMeals = ['breakfast', 'lunch', 'dinner', 'snack'].some((section) => (mapped[section] || []).length > 0);

      setAllMeals(prev => ({ ...prev, [dateToLoad]: mapped }));
      setRecordedDateKeys(prev => {
        const next = new Set(prev);
        if (hasMeals) next.add(dateToLoad);
        else next.delete(dateToLoad);
        return next;
      });
    } catch (err) {
      console.error(`Failed to load daily log for ${dateToLoad}:`, err);
      setAllMeals(prev => ({ ...prev, [dateToLoad]: { ...emptyMealsState(), _totalMacro: null } }));
    }
  }, []);

  const refreshMonthSummary = useCallback(async (year, month, force = false) => {
    const monthStart = new Date(year, month, 1);
    const monthEnd = new Date(year, month + 1, 0);
    const from = formatDateKey(monthStart);
    const to = formatDateKey(monthEnd);

    try {
      const logs = await fetchMonthSummaryDedup(from, to, force);
      setRecordedDateKeys(new Set((logs || []).map((log) => log.date)));
    } catch (err) {
      console.error('Failed to load date markers:', err);
      setRecordedDateKeys(new Set());
    }
  }, []);

  // Load recipes for search list
  useEffect(() => {
    if (!authUser?.internal_uid) return;
    let cancelled = false;

    (async () => {
      try {
        const mappedRecipes = await fetchFoodDatabaseDedup();
        if (!cancelled) {
          setFoodDatabase(mappedRecipes);
        }
      } catch (err) {
        console.error('Failed to load recipes for dashboard:', err);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [authUser?.internal_uid]);

  // Load selected date meals from analytics
  useEffect(() => {
    if (!authUser?.internal_uid) return;
    let cancelled = false;

    (async () => {
      if (cancelled) return;
      await refreshDateData(dateKey);
    })();

    return () => {
      cancelled = true;
    };
  }, [authUser?.internal_uid, dateKey, refreshDateData]);

  // Load calendar markers for visible month
  useEffect(() => {
    if (!authUser?.internal_uid) return;
    let cancelled = false;

    (async () => {
      if (cancelled) return;
      await refreshMonthSummary(calYear, calMonth);
    })();

    return () => {
      cancelled = true;
    };
  }, [authUser?.internal_uid, calYear, calMonth, refreshMonthSummary]);

  const filteredFoodDatabase = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return foodDatabase;
    return foodDatabase.filter((item) => item.name.toLowerCase().includes(query));
  }, [foodDatabase, searchQuery]);

  const [newRecipe, setNewRecipe] = useState({
    name: '', time: '', ingredientName: '', ingredientAmount: '100',
    ingredientUnit: 'grams (g)', ingredients: [], currentStep: '', steps: []
  });

  const macros = useMemo(() => {
    if (dailyMeals._totalMacro) {
      const tm = dailyMeals._totalMacro;
      return {
        calories: { current: Math.round(tm.calories || 0), target: 2200, unit: 'kcal', color: 'bg-orange-500' },
        protein: { current: Math.round(tm.proteins || 0), target: 140, unit: 'g', color: 'bg-green-500' },
        fat: { current: Math.round(tm.fats || 0), target: 70, unit: 'g', color: 'bg-purple-500' },
        carbs: { current: Math.round(tm.carbs || 0), target: 280, unit: 'g', color: 'bg-blue-500' },
      };
    }
    let total = { calories: 0, protein: 0, carbs: 0, fat: 0 };
    ['breakfast', 'lunch', 'dinner', 'snack'].forEach((s) => {
      (dailyMeals[s] || []).forEach((item) => {
        total.calories += item.kcal || 0;
        total.protein += item.p || 0;
        total.carbs += item.c || 0;
        total.fat += item.f || 0;
      });
    });
    return {
      calories: { current: Math.round(total.calories), target: 2200, unit: 'kcal', color: 'bg-orange-500' },
      protein: { current: Math.round(total.protein), target: 140, unit: 'g', color: 'bg-green-500' },
      fat: { current: Math.round(total.fat), target: 70, unit: 'g', color: 'bg-purple-500' },
      carbs: { current: Math.round(total.carbs), target: 280, unit: 'g', color: 'bg-blue-500' },
    };
  }, [dailyMeals]);

  const mealSections = [
    { id: 'breakfast', label: 'Breakfast', recommended: '400-600 kcal', icon: Utensils },
    { id: 'lunch', label: 'Lunch', recommended: '600-800 kcal', icon: Utensils },
    { id: 'dinner', label: 'Dinner', recommended: '500-700 kcal', icon: Utensils },
    { id: 'snack', label: 'Snacks', recommended: '100-300 kcal', icon: Utensils },
  ];

  const containerVariants = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.05 } } };
  const itemVariants = { hidden: { y: 10, opacity: 0 }, visible: { y: 0, opacity: 1 } };

  const openAddModal = (sectionId) => { setActiveSection(sectionId); setViewMode('search'); setIsAddModalOpen(true); };

  const buildIngredientsForPortion = (food, targetGrams) => {
    const recipeIngredients = food.ingredients || [];
    if (!recipeIngredients.length) return [];

    const baseTotalGrams = food.baseTotalGrams || computeRecipeBaseGrams(recipeIngredients);
    if (!baseTotalGrams || baseTotalGrams <= 0) return [];

    const scale = targetGrams / baseTotalGrams;
    return recipeIngredients
      .map((ing) => {
        const grams = convertToGrams(ing.quantity, ing.capacity) * scale;
        return {
          ingredient_id: ing.ingredient_id,
          quantity: Math.round(grams * 100) / 100,
        };
      })
      .filter((ing) => ing.ingredient_id && ing.quantity > 0);
  };

  const handleAddFoodToMeal = async (food) => {
    if (!activeSection || isSavingMeal) return;

    const recipeId = food.recipeId || food.id;
    if (!recipeId) return;

    const parsedPortion = Number(portionGrams);
    const targetGrams = Number.isFinite(parsedPortion) && parsedPortion > 0 ? parsedPortion : 100;
    const ingredients = buildIngredientsForPortion(food, targetGrams);

    try {
      setIsSavingMeal(true);
      const payload = {
        date: dateKey,
        meal_type: activeSection,
        recipe_name: food.name,
      };

      // Prefer manual ingredient quantities in grams so macros match chosen portion.
      if (ingredients.length) {
        payload.ingredients = ingredients;
      } else {
        payload.recipe_id = String(recipeId);
      }

      await createMealEntry(payload);
      await refreshDateData(dateKey, true);
      await refreshMonthSummary(calYear, calMonth, true);
      setIsAddModalOpen(false);
      setPortionGrams('100');
    } catch (err) {
      console.error('Failed to add meal entry:', err);
    } finally {
      setIsSavingMeal(false);
    }
  };

  const handleRemoveFood = async (sectionId, index) => {
    const item = (dailyMeals[sectionId] || [])[index];
    if (!item?.entryId || isSavingMeal) return;

    try {
      setIsSavingMeal(true);
      await deleteMealEntry(item.entryId);
      await refreshDateData(dateKey, true);
      await refreshMonthSummary(calYear, calMonth, true);
    } catch (err) {
      console.error('Failed to delete meal entry:', err);
    } finally {
      setIsSavingMeal(false);
    }
  };

  const handleAddIngredient = () => {
    if (newRecipe.ingredientName.trim()) {
      setNewRecipe(prev => ({
        ...prev,
        ingredients: [...prev.ingredients, { name: prev.ingredientName, amount: prev.ingredientAmount, unit: prev.ingredientUnit }],
        ingredientName: '', ingredientAmount: '100'
      }));
    }
  };

  const handleAddStep = () => {
    if (newRecipe.currentStep.trim()) {
      setNewRecipe(prev => ({ ...prev, steps: [...prev.steps, prev.currentStep], currentStep: '' }));
    }
  };

  const handleSaveRecipe = () => {
    if (!newRecipe.name) return;
    const customFood = {
      id: `custom-${Date.now()}`, name: newRecipe.name,
      kcal: Math.floor(Math.random() * 500) + 200, p: Math.floor(Math.random() * 30) + 10,
      c: Math.floor(Math.random() * 50) + 20, f: Math.floor(Math.random() * 20) + 5,
      image: 'https://picsum.photos/200?grayscale&blur=2'
    };
    setFoodDatabase(prev => [customFood, ...prev]);
    setNewRecipe({ name: '', time: '', ingredientName: '', ingredientAmount: '100', ingredientUnit: 'grams (g)', ingredients: [], currentStep: '', steps: [] });
    setViewMode('search');
  };

  // Calendar navigation
  const prevMonth = () => { if (calMonth === 0) { setCalMonth(11); setCalYear(y => y - 1); } else setCalMonth(m => m - 1); };
  const nextMonth = () => { if (calMonth === 11) { setCalMonth(0); setCalYear(y => y + 1); } else setCalMonth(m => m + 1); };
  const selectCalDay = (d) => { setSelectedDate(d); setCalendarOpen(false); };
  const calDays = useMemo(() => getCalendarGrid(calYear, calMonth), [calYear, calMonth]);
  const recordedDates = useMemo(() => {
    const merged = new Set(recordedDateKeys);

    Object.entries(allMeals).forEach(([key, meals]) => {
      const hasMeals = ['breakfast', 'lunch', 'dinner', 'snack'].some((section) => (meals?.[section] || []).length > 0);
      if (hasMeals) merged.add(key);
    });

    return merged;
  }, [allMeals, recordedDateKeys]);

  return (
    <motion.div className="p-4 md:p-8 space-y-6 max-w-3xl mx-auto" variants={containerVariants} initial="hidden" animate="visible">

      {/* ── Date Navigation Strip ── */}
      <motion.div variants={itemVariants} className="glass-panel p-4 rounded-3xl flex flex-col gap-4 relative z-40">
        <div className="flex justify-between items-center px-2">
          <button onClick={() => { setCalMonth(selectedDate.getMonth()); setCalYear(selectedDate.getFullYear()); setCalendarOpen(!calendarOpen); }}
            className="font-bold text-slate-800 dark:text-white text-lg flex items-center gap-2 drop-shadow-sm hover:text-brand-600 dark:hover:text-brand-400 transition-colors">
            {MONTH_NAMES[selectedDate.getMonth()]} {selectedDate.getFullYear()}
            <CalendarDays className="w-4 h-4 text-slate-400" />
          </button>
          {isSameDay(selectedDate, today) ? (
            <div className="bg-brand-500/10 dark:bg-brand-500/20 text-brand-700 dark:text-brand-300 px-3 py-1 rounded-full text-xs font-bold border border-brand-500/20 backdrop-blur-sm">Today</div>
          ) : (
            <button onClick={() => setSelectedDate(today)}
              className="bg-brand-500/10 dark:bg-brand-500/20 text-brand-700 dark:text-brand-300 px-3 py-1 rounded-full text-xs font-bold border border-brand-500/20 backdrop-blur-sm hover:bg-brand-500/20 transition-colors">Today</button>
          )}
        </div>

        {/* Week strip */}
        <div className="flex justify-between items-center text-center">
          <button onClick={() => setSelectedDate(d => { const n = new Date(d); n.setDate(n.getDate() - 7); return n; })}
            className="p-1 text-slate-400 hover:text-slate-700 dark:hover:text-white transition-colors"><ChevronLeft className="w-4 h-4" /></button>
          {weekDays.map((d, i) => {
            const isToday = isSameDay(d, today);
            const isSelected = isSameDay(d, selectedDate);
            const hasData = recordedDates.has(formatDateKey(d));
            return (
              <button key={i} onClick={() => setSelectedDate(d)}
                className={`flex flex-col items-center justify-center w-10 h-14 rounded-2xl transition-all duration-300 relative ${
                  isSelected ? 'bg-slate-900 dark:bg-white text-white dark:text-slate-900 shadow-xl scale-110 border border-white/20'
                    : isToday ? 'ring-2 ring-brand-500/40 text-slate-700 dark:text-slate-200'
                    : 'text-slate-400 hover:bg-white/40 dark:hover:bg-slate-700/40'
                }`}>
                <span className={`text-[10px] font-medium mb-1 opacity-80`}>{DAY_SHORT[d.getDay()]}</span>
                <span className={`text-sm font-bold ${isSelected ? 'text-white dark:text-slate-900' : 'text-slate-800 dark:text-slate-300'}`}>{d.getDate()}</span>
                {hasData && !isSelected && <div className="absolute bottom-1 w-1 h-1 rounded-full bg-brand-500" />}
              </button>
            );
          })}
          <button onClick={() => setSelectedDate(d => { const n = new Date(d); n.setDate(n.getDate() + 7); return n; })}
            className="p-1 text-slate-400 hover:text-slate-700 dark:hover:text-white transition-colors"><ChevronRight className="w-4 h-4" /></button>
        </div>

        {/* ── Calendar dropdown ── */}
        <AnimatePresence>
          {calendarOpen && (
            <motion.div ref={calendarRef} initial={{ opacity: 0, y: -8, scale: 0.96 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -8, scale: 0.96 }}
              transition={{ duration: 0.2 }} className="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-[100] w-60 glass-panel bg-white/95 dark:bg-slate-900/95 rounded-2xl p-3 shadow-2xl border border-slate-200/60 dark:border-white/10">
              <div className="flex items-center justify-between mb-2">
                <button onClick={prevMonth} className="p-1 hover:bg-slate-100 dark:hover:bg-white/10 rounded-lg transition-colors"><ChevronLeft className="w-3.5 h-3.5 text-slate-600 dark:text-slate-300" /></button>
                <span className="font-bold text-slate-800 dark:text-white text-xs">{MONTH_NAMES[calMonth]} {calYear}</span>
                <button onClick={nextMonth} className="p-1 hover:bg-slate-100 dark:hover:bg-white/10 rounded-lg transition-colors"><ChevronRight className="w-3.5 h-3.5 text-slate-600 dark:text-slate-300" /></button>
              </div>
              <div className="grid grid-cols-7 gap-0.5 mb-0.5">
                {['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'].map(d => (
                  <div key={d} className="text-center text-[8px] font-bold text-slate-400 uppercase py-0.5">{d}</div>
                ))}
              </div>
              <div className="grid grid-cols-7 gap-0.5">
                {calDays.map((d, i) => {
                  if (!d) return <div key={`b-${i}`} />;
                  const sel = isSameDay(d, selectedDate);
                  const isT = isSameDay(d, today);
                  const hasData = recordedDates.has(formatDateKey(d));
                  const isFuture = d > today;
                  return (
                    <button key={i} onClick={() => selectCalDay(d)} disabled={isFuture}
                      className={`relative w-full aspect-square rounded-md text-[10px] font-medium flex items-center justify-center transition-all
                        ${sel ? 'bg-brand-500 text-white shadow-md shadow-brand-500/30'
                          : isT ? 'ring-1.5 ring-brand-500/40 text-brand-600 dark:text-brand-400 font-bold'
                          : isFuture ? 'text-slate-300 dark:text-slate-600 cursor-not-allowed'
                          : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-white/10'}`}>
                      {d.getDate()}
                      {hasData && !sel && <div className="absolute bottom-0.5 w-1 h-1 rounded-full bg-brand-500" />}
                    </button>
                  );
                })}
              </div>
              <button onClick={() => selectCalDay(today)}
                className="mt-1.5 w-full py-1 text-[10px] font-semibold text-brand-600 dark:text-brand-400 hover:bg-brand-50 dark:hover:bg-brand-900/20 rounded-lg transition-colors">Go to Today</button>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* ── Meal Diary ── */}
      <div className="space-y-4">
        {mealSections.map((section) => {
          const items = dailyMeals[section.id] || [];
          return (
            <motion.div key={section.id} variants={itemVariants} className="glass-panel rounded-3xl p-1 hover:shadow-lg transition-all">
              <div className="p-4">
                <div className="flex justify-between items-center mb-3">
                  <div>
                    <h3 className="font-bold text-slate-800 dark:text-white text-lg drop-shadow-sm">{section.label}</h3>
                    <p className="text-slate-500 dark:text-slate-400 text-xs font-medium">{section.recommended}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button className="flex items-center justify-center w-10 h-10 rounded-full bg-brand-50/50 dark:bg-brand-500/10 text-brand-600 dark:text-brand-400 hover:bg-brand-100 dark:hover:bg-brand-500/20 transition-colors border border-brand-200/30" title="AI Suggestions">
                      <Sparkles className="w-5 h-5" />
                    </button>
                    <button onClick={() => openAddModal(section.id)} disabled={isSavingMeal} className="liquid-btn liquid-btn-secondary w-10 h-10 rounded-full flex items-center justify-center disabled:opacity-60" title="Add Item">
                      <Plus className="w-5 h-5" />
                    </button>
                  </div>
                </div>
                {items.length > 0 ? (
                  <div className="space-y-2 mt-2">
                    <AnimatePresence>
                      {items.map((item, i) => (
                        <motion.div key={`${item.id}-${i}`} initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
                          className="flex justify-between items-center py-3 px-4 bg-slate-50/90 dark:bg-slate-800/40 rounded-2xl border border-slate-200/50 dark:border-white/5 backdrop-blur-sm group">
                          <span className="font-medium text-slate-700 dark:text-slate-200 text-sm">{item.name}</span>
                          <div className="flex items-center gap-4">
                            <span className="font-bold text-slate-500 dark:text-slate-400 text-sm">{item.kcal} kcal{item.grams ? ` • ${item.grams} g` : ''}</span>
                            <button onClick={() => handleRemoveFood(section.id, i)} disabled={isSavingMeal}
                              className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-500 transition-opacity"><Trash2 className="w-4 h-4" /></button>
                          </div>
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </div>
                ) : (
                  <div className="py-2 flex items-center gap-2 opacity-50 pl-1">
                    <div className="w-1 h-8 bg-slate-300/80 dark:bg-slate-700/50 rounded-full"></div>
                    <span className="text-slate-500 dark:text-slate-400 text-sm italic">No items added yet</span>
                  </div>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* ── Macro Summary Footer ── */}
      <motion.div variants={itemVariants} className="glass-panel p-6 rounded-3xl sticky bottom-4 z-20 backdrop-blur-2xl">
        <div className="grid grid-cols-4 gap-4 text-center divide-x divide-slate-200/60 dark:divide-slate-700/50">
          {Object.entries(macros).map(([key, data]) => (
            <div key={key} className="px-2 first:pl-0 last:pr-0">
              <p className="text-[10px] uppercase font-bold text-slate-500 dark:text-slate-400 tracking-wider mb-1">{key === 'calories' ? 'Kcal' : key}</p>
              <div className="flex items-baseline justify-center gap-[2px] mb-2">
                <span className="font-bold text-slate-800 dark:text-white text-sm md:text-base">{data.current}</span>
                <span className="text-[10px] text-slate-500 dark:text-slate-400">/ {data.target}</span>
              </div>
              <div className="h-2 w-full bg-slate-200/80 dark:bg-slate-700/50 rounded-full overflow-hidden shadow-inner">
                <motion.div initial={{ width: 0 }} animate={{ width: `${Math.min((data.current / data.target) * 100, 100)}%` }}
                  transition={{ duration: 0.5, type: 'spring' }} className={`h-full rounded-full ${data.color} shadow-[0_0_10px_rgba(0,0,0,0.2)]`} />
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* ── Add Item Modal ── */}
      <AnimatePresence>
        {isAddModalOpen && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setIsAddModalOpen(false)} className="absolute inset-0 bg-slate-900/40 backdrop-blur-md" />
            <motion.div initial={{ opacity: 0, scale: 0.9, y: 30 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.9, y: 30 }}
              className="w-full max-w-2xl glass-panel bg-white/90 dark:bg-slate-900/90 backdrop-blur-3xl rounded-[2rem] relative z-10 overflow-hidden flex flex-col max-h-[85vh] shadow-2xl border border-white/50 dark:border-white/10">
              <div className="flex justify-between items-center p-6 border-b border-slate-200/50 dark:border-slate-700/50 sticky top-0 z-20 bg-white/50 dark:bg-slate-900/50 backdrop-blur-md">
                <h3 className="text-xl font-bold text-slate-800 dark:text-white drop-shadow-sm">{viewMode === 'search' ? 'Add Food' : 'Create Recipe'}</h3>
                <button onClick={() => setIsAddModalOpen(false)} className="p-2 hover:bg-black/5 dark:hover:bg-white/10 rounded-full transition-colors"><X className="w-5 h-5 text-slate-400" /></button>
              </div>

              {viewMode === 'search' ? (
                <div className="flex flex-col h-full overflow-hidden">
                  <div className="p-6 space-y-4">
                    <div className="flex gap-3">
                      <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
                        <input type="text" placeholder="Search for food..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                          className="w-full pl-10 pr-4 py-3.5 liquid-input rounded-2xl text-slate-800 dark:text-white placeholder-slate-400 outline-none" />
                      </div>
                      <div className="w-28">
                        <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wide mb-1 ml-1">Portion (g)</label>
                        <input
                          type="number"
                          min="1"
                          value={portionGrams}
                          onChange={(e) => setPortionGrams(e.target.value)}
                          className="w-full px-3 py-3.5 liquid-input rounded-2xl text-slate-800 dark:text-white outline-none"
                        />
                      </div>
                    </div>
                  </div>
                  <div className="flex-1 overflow-y-auto p-6 pt-0 space-y-3">
                    {filteredFoodDatabase.map((item) => (
                      <div key={item.id} onClick={() => handleAddFoodToMeal(item)}
                        className="group flex items-center gap-4 p-3 rounded-3xl border border-transparent hover:border-brand-200/50 hover:bg-white/50 dark:hover:bg-white/5 transition-all cursor-pointer">
                        <img src={item.image} alt={item.name} className="w-16 h-16 rounded-2xl object-cover shadow-md group-hover:scale-105 transition-transform" />
                        <div className="flex-1 min-w-0">
                          <div className="flex justify-between items-start mb-1">
                            <h4 className="font-bold text-slate-800 dark:text-white truncate pr-2">{item.name}</h4>
                            <button className="p-1.5 bg-brand-100 text-brand-600 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"><Plus className="w-4 h-4" /></button>
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
                    <button onClick={() => setViewMode('search')} className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-800 dark:hover:text-white font-medium transition-colors">
                      <ChevronLeft className="w-4 h-4" /> Back to Search
                    </button>
                    <div className="w-full h-32 border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-3xl flex flex-col items-center justify-center gap-2 text-slate-400 hover:border-brand-400 hover:text-brand-500 hover:bg-brand-50/10 transition-all cursor-pointer bg-white/30 dark:bg-black/20">
                      <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-full shadow-inner"><Camera className="w-5 h-5" /></div>
                      <span className="text-sm font-medium">Add Recipe Photo</span>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="col-span-2 space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Recipe Name</label>
                        <input type="text" placeholder="e.g. Grandma&apos;s Apple Pie" value={newRecipe.name} onChange={e => setNewRecipe({...newRecipe, name: e.target.value})}
                          className="w-full p-3.5 liquid-input rounded-xl text-slate-800 dark:text-white outline-none" />
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Prep Time</label>
                        <div className="relative">
                          <Clock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                          <input type="text" placeholder="30 min" value={newRecipe.time} onChange={e => setNewRecipe({...newRecipe, time: e.target.value})}
                            className="w-full pl-9 pr-3 py-3.5 liquid-input rounded-xl text-slate-800 dark:text-white outline-none" />
                        </div>
                      </div>
                    </div>
                    <div className="space-y-3">
                      <label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Ingredients</label>
                      <div className="glass-panel p-5 rounded-3xl space-y-3 bg-slate-50/50 dark:bg-slate-800/30">
                        <input type="text" placeholder="Select ingredient..." value={newRecipe.ingredientName} onChange={e => setNewRecipe({...newRecipe, ingredientName: e.target.value})}
                          className="w-full p-3.5 bg-white dark:bg-slate-800 text-slate-800 dark:text-white border border-slate-200 dark:border-white/10 rounded-xl focus:border-brand-500 outline-none shadow-sm transition-all" />
                        <div className="flex gap-3">
                          <input type="number" placeholder="100" value={newRecipe.ingredientAmount} onChange={e => setNewRecipe({...newRecipe, ingredientAmount: e.target.value})}
                            className="flex-1 p-3.5 bg-white dark:bg-slate-800 text-slate-800 dark:text-white border border-slate-200 dark:border-white/10 rounded-xl focus:border-brand-500 outline-none shadow-sm transition-all" />
                          <div className="relative w-1/2 sm:w-1/3">
                            <select value={newRecipe.ingredientUnit} onChange={e => setNewRecipe({...newRecipe, ingredientUnit: e.target.value})}
                              className="w-full p-3.5 bg-white dark:bg-slate-800 text-slate-800 dark:text-white border border-slate-200 dark:border-white/10 rounded-xl focus:border-brand-500 outline-none appearance-none shadow-sm transition-all">
                              <option value="grams (g)">grams (g)</option><option value="kilograms (kg)">kilograms (kg)</option>
                              <option value="milliliters (ml)">milliliters (ml)</option><option value="liters (l)">liters (l)</option>
                              <option value="cup">cup</option><option value="tbsp">tbsp</option><option value="tsp">tsp</option><option value="pcs">pieces</option>
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
                              <div className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-brand-500"></div>
                                <span className="font-medium text-slate-700 dark:text-slate-200 text-sm">{ing.name}</span></div>
                              <div className="flex items-center gap-3">
                                <span className="text-xs font-bold text-slate-400 bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded-lg">{ing.amount} {ing.unit}</span>
                                <button onClick={() => setNewRecipe(prev => ({...prev, ingredients: prev.ingredients.filter((_, idx) => idx !== i)}))}
                                  className="text-slate-300 hover:text-red-500 transition-colors"><X className="w-4 h-4" /></button>
                              </div>
                            </motion.div>
                          ))}
                        </AnimatePresence>
                        {newRecipe.ingredients.length === 0 && <span className="text-sm text-slate-400 italic px-2">No ingredients added yet.</span>}
                      </div>
                    </div>
                    <div className="space-y-3">
                      <label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Instructions</label>
                      <div className="flex gap-2 items-start">
                        <textarea placeholder="Describe the step..." value={newRecipe.currentStep} onChange={e => setNewRecipe({...newRecipe, currentStep: e.target.value})}
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
                    <button onClick={() => setViewMode('search')} className="px-5 py-2.5 text-slate-600 dark:text-slate-300 font-semibold hover:bg-black/5 dark:hover:bg-white/10 rounded-xl transition-colors">Cancel</button>
                    <button onClick={handleSaveRecipe} className="liquid-btn liquid-btn-primary px-6 py-2.5 rounded-xl font-semibold flex items-center gap-2"><Save className="w-4 h-4" /> Save Recipe</button>
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
