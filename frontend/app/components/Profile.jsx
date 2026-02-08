'use client';

import { useState, useEffect, useMemo, useRef } from 'react';
import { createPortal } from 'react-dom';
import axios from 'axios';
import { ENDPOINTS } from '../config/network';
import {
  User, MapPin, Calendar, Heart, Clock, Flame, Award, Settings, Loader2, ChefHat, ArrowRight,
  CheckCircle2, X, Dumbbell, Activity, Layers, Search, Filter, Edit3, Save, Trash2,
  ChevronDown, Plus, Minus
} from 'lucide-react';
import {
  getMyWorkoutPlans, getTrainings, getExercises,
  updateTraining, deleteTraining, updateWorkoutPlan, deleteWorkoutPlan,
} from '../services/workoutService';
import {
  getLikedWorkouts, unlikeWorkout,
  getLikedRecipes, unlikeRecipe,
} from '../services/userService';
import { TrainingType, SetUnit, BodyPart, Advancement } from '../data/types';
import { motion, AnimatePresence } from 'framer-motion';

const buildExerciseMap = (exercisesArr) => {
  const map = {};
  for (const ex of exercisesArr) map[ex._id || ex.id] = ex;
  return map;
};

const populateTraining = (training, exercisesMap) => ({
  ...training,
  exercises: training.exercises.map(ex => ({
    ...ex,
    _exerciseDetails: exercisesMap[ex.exercise_id] || {
      _id: ex.exercise_id, name: 'Unknown Exercise',
      body_part: BodyPart.FULL_BODY, advancement: Advancement.BEGINNER, category: 'custom'
    }
  }))
});

const authApi = axios.create({ baseURL: ENDPOINTS.AUTH, withCredentials: true });
const userApi = axios.create({ baseURL: ENDPOINTS.USERS, withCredentials: true });
const recipeApi = axios.create({ baseURL: ENDPOINTS.RECIPES, withCredentials: true });

function CustomSelect({ value, onChange, options, placeholder }) {
  const [open, setOpen] = useState(false);
  const btnRef = useRef(null);
  const menuRef = useRef(null);
  const [pos, setPos] = useState({ top: 0, left: 0, width: 0 });

  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (btnRef.current?.contains(e.target) || menuRef.current?.contains(e.target)) return;
      setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  useEffect(() => {
    if (!open || !btnRef.current) return;
    const update = () => {
      const rect = btnRef.current.getBoundingClientRect();
      setPos({ top: rect.bottom + 4, left: rect.left, width: rect.width });
    };
    update();
    window.addEventListener('scroll', update, true);
    window.addEventListener('resize', update);
    return () => { window.removeEventListener('scroll', update, true); window.removeEventListener('resize', update); };
  }, [open]);

  const selected = options.find(o => o.value === value);
  return (
    <div ref={btnRef}>
      <button type="button" onClick={() => setOpen(!open)}
        className="w-full p-3 rounded-xl liquid-input text-sm font-medium outline-none cursor-pointer flex items-center justify-between gap-2 text-slate-800 dark:text-white hover:bg-white/50 dark:hover:bg-white/10 transition-colors">
        <span className="truncate">{selected?.label || placeholder || 'Select...'}</span>
        <ChevronDown className={`w-4 h-4 text-slate-400 shrink-0 transition-transform duration-200 ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && typeof document !== 'undefined' && createPortal(
        <div ref={menuRef} style={{ position: 'fixed', top: pos.top, left: pos.left, width: pos.width, zIndex: 9999 }}>
          <div className="bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl rounded-xl shadow-xl border border-white/50 dark:border-white/10 overflow-hidden">
            {options.map(opt => (
              <button key={opt.value} type="button"
                onClick={() => { onChange(opt.value); setOpen(false); }}
                className={`w-full px-4 py-2.5 text-left text-sm font-medium transition-colors flex items-center justify-between
                  ${value === opt.value
                    ? 'bg-brand-500/10 text-brand-600 dark:text-brand-400'
                    : 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-white/5'}`}>
                <span>{opt.label}</span>
                {value === opt.value && <CheckCircle2 className="w-3.5 h-3.5 text-brand-500" />}
              </button>
            ))}
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}

export default function Profile() {
  const [activeTab, setActiveTab] = useState('my_recipes');

  const [authUser, setAuthUser] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [myRecipes, setMyRecipes] = useState([]);
  const [ingredientMap, setIngredientMap] = useState({});
  const [allIngredients, setAllIngredients] = useState([]);
  const [selectedRecipe, setSelectedRecipe] = useState(null);
  const [editingRecipe, setEditingRecipe] = useState(null);
  const [myPlans, setMyPlans] = useState([]);
  const [myTrainings, setMyTrainings] = useState([]);
  const [allPopulatedTrainings, setAllPopulatedTrainings] = useState([]);
  const [workoutsLoading, setWorkoutsLoading] = useState(true);
  const [exercisesDB, setExercisesDB] = useState({});
  const [allExercises, setAllExercises] = useState([]);
  const [likedTrainings, setLikedTrainings] = useState([]);
  const [unlikingInProgress, setUnlikingInProgress] = useState(new Set());
  const [likedRecipes, setLikedRecipes] = useState([]);
  const [unlikingRecipeInProgress, setUnlikingRecipeInProgress] = useState(new Set());

  // Search & filter state for profile tabs
  const [planSearchQuery, setPlanSearchQuery] = useState('');
  const [workoutSearchQuery, setWorkoutSearchQuery] = useState('');
  const [showWorkoutFilters, setShowWorkoutFilters] = useState(false);
  const [filterTrainingType, setFilterTrainingType] = useState('ALL');
  const [filterBodyPart, setFilterBodyPart] = useState('ALL');
  const [filterMaxTime, setFilterMaxTime] = useState(120);

  // Recipe filter state
  const [recipeSearchQuery, setRecipeSearchQuery] = useState('');
  const [showRecipeFilters, setShowRecipeFilters] = useState(false);
  const [recipeFilters, setRecipeFilters] = useState({ time: 'All', maxCalories: 'All', minProtein: 'All', sort: 'newest' });

  // Detail / edit modals
  const [selectedTraining, setSelectedTraining] = useState(null);
  const [editingTraining, setEditingTraining] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [editingPlan, setEditingPlan] = useState(null);
  const [expandedPlanTrainings, setExpandedPlanTrainings] = useState({});
  const [isEditLoading, setIsEditLoading] = useState(false);
  const [showExercisePicker, setShowExercisePicker] = useState(false);
  const [pickerSearch, setPickerSearch] = useState('');
  const [pickerBodyPart, setPickerBodyPart] = useState('ALL');
  const [planPickerSearch, setPlanPickerSearch] = useState('');

  // Recipe edit ingredient picker state
  const [editIngDropdownOpen, setEditIngDropdownOpen] = useState({});
  const [editIngSearchTerms, setEditIngSearchTerms] = useState({});
  const editIngDropdownRefs = useRef({});

  // Close ingredient dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      const openKeys = Object.keys(editIngDropdownOpen).filter(k => editIngDropdownOpen[k]);
      if (openKeys.length === 0) return;
      for (const key of openKeys) {
        if (editIngDropdownRefs.current[key] && !editIngDropdownRefs.current[key].contains(e.target)) {
          setEditIngDropdownOpen(prev => ({ ...prev, [key]: false }));
        }
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [editIngDropdownOpen]);

  const [loading, setLoading] = useState(true);
  const [recipesLoading, setRecipesLoading] = useState(true);
  const [error, setError] = useState(null);

  const dayNames = ['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const emptySchedule = () => ({ 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [] });
  const [pickingForPlanDay, setPickingForPlanDay] = useState(null);

  const editPlanTrainingIds = useMemo(() => {
    if (!editingPlan?.schedule) return [];
    return [1,2,3,4,5,6,7].flatMap(d => editingPlan.schedule[d] || []);
  }, [editingPlan?.schedule]);

  useEffect(() => {
    fetchProfileData();
  }, []);

  const fetchProfileData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Get current auth user
      const { data: auth } = await authApi.get('/me');
      setAuthUser(auth);

      // 2. Get full user profile from user-service
      let profile = null;
      if (auth.internal_uid) {
        try {
          const { data } = await userApi.get(`/users/${auth.internal_uid}`);
          profile = data;
        } catch (err) {
          console.warn('Could not fetch user profile by uid:', err);
        }
      }
      if (!profile && auth.user_id) {
        try {
          const { data } = await userApi.get(`/users/auth0/${auth.user_id}`);
          profile = data;
        } catch (err) {
          console.warn('Could not fetch user profile by auth0_sub:', err);
        }
      }
      setUserProfile(profile);

      // 3. Fetch recipes and ingredients in parallel
      const authorId = auth.internal_uid || profile?.uid;
      const [recipesRes, ingredientsRes] = await Promise.all([
        authorId ? recipeApi.get('/', { params: { author_id: authorId, limit: 100 } }) : Promise.resolve({ data: [] }),
        recipeApi.get('/ingredients?limit=500'),
      ]);
      setMyRecipes(recipesRes.data);

      const map = {};
      ingredientsRes.data.forEach(ing => {
        map[ing.id || ing._id] = ing;
      });
      setIngredientMap(map);


      setAllIngredients(ingredientsRes.data);

      // Fetch liked recipes
      const uid0 = auth.internal_uid || profile?.uid;
      if (uid0) {
        try {
          const likedRecipesRes = await getLikedRecipes(uid0, { limit: 500 });
          const likedRecipeItems = likedRecipesRes.items || likedRecipesRes || [];
          const likedRecipeIds = likedRecipeItems.map(item => item.recipe_id);
          if (likedRecipeIds.length > 0) {
            // Fetch all recipes (not just author's) to find liked ones
            const allRecipesRes = await recipeApi.get('/', { params: { limit: 100 } });
            const allRecipes = allRecipesRes.data || [];
            const likedRecipesData = allRecipes.filter(r => likedRecipeIds.includes(r._id));
            setLikedRecipes(likedRecipesData);
          }
        } catch (likedRecipeErr) {
          console.warn('Could not fetch liked recipes:', likedRecipeErr);
        }
      }

      // 4. Fetch workout plans, trainings, and exercises (independently so one failure doesn't block others)

      setWorkoutsLoading(true);
      try {
        // Fetch exercises first — build the map before populating trainings
        const exercisesRes = await getExercises({ limit: 500 });
        const exMap = buildExerciseMap(exercisesRes);
        setExercisesDB(exMap);
        setAllExercises(exercisesRes);

        // Then fetch trainings + my plans in parallel
        const [trainingsData, plansRes] = await Promise.all([
          getTrainings({ limit: 500 }),
          getMyWorkoutPlans({ limit: 100 }),
        ]);

        setMyPlans(plansRes);

        // Populate all trainings for plan detail lookups
        const allPopulated = trainingsData.map(t => populateTraining(t, exMap));
        setAllPopulatedTrainings(allPopulated);

        // Filter trainings by creator_id to show only MY own trainings
        const uid = auth.internal_uid || profile?.uid;
        const myTrainingsData = trainingsData.filter(t => t.creator_id === uid);

        setMyTrainings(myTrainingsData.map(t => populateTraining(t, exMap)));

        // 5. Fetch liked workouts
        if (uid) {
          try {
            const likedRes = await getLikedWorkouts(uid, { limit: 500 });
            const likedItems = likedRes.items || likedRes || [];
            const likedIds = likedItems.map(item => item.workout_id);
            if (likedIds.length > 0) {
              const likedTrainingsData = trainingsData.filter(t => likedIds.includes(t._id));
              setLikedTrainings(likedTrainingsData.map(t => populateTraining(t, exMap)));
            }
          } catch (likedErr) {
            console.warn('Could not fetch liked workouts:', likedErr);
          }
        }
      } catch (workoutErr) {
        console.warn('Could not fetch workout data:', workoutErr);
      } finally {
        setWorkoutsLoading(false);
      }
    } catch (err) {
      console.error('Error fetching profile data:', err);
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
      setRecipesLoading(false);
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '? min';
    return `${Math.floor(seconds / 60)} min`;
  };

  const getDifficultyColor = (type) => {
    switch (type) {
      case TrainingType.HIIT: return 'text-orange-700 dark:text-orange-300 bg-orange-100 dark:bg-orange-900/30 border-orange-200 dark:border-orange-700/50';
      case TrainingType.STRENGTH: return 'text-red-700 dark:text-red-300 bg-red-100 dark:bg-red-900/30 border-red-200 dark:border-red-700/50';
      case TrainingType.CARDIO: return 'text-sky-700 dark:text-sky-300 bg-sky-100 dark:bg-sky-900/30 border-sky-200 dark:border-sky-700/50';
      case TrainingType.YOGA: return 'text-emerald-700 dark:text-emerald-300 bg-emerald-100 dark:bg-emerald-900/30 border-emerald-200 dark:border-emerald-700/50';
      case TrainingType.PUSH: return 'text-violet-700 dark:text-violet-300 bg-violet-100 dark:bg-violet-900/30 border-violet-200 dark:border-violet-700/50';
      case TrainingType.PULL: return 'text-indigo-700 dark:text-indigo-300 bg-indigo-100 dark:bg-indigo-900/30 border-indigo-200 dark:border-indigo-700/50';
      case TrainingType.LEGS: return 'text-amber-700 dark:text-amber-300 bg-amber-100 dark:bg-amber-900/30 border-amber-200 dark:border-amber-700/50';
      case TrainingType.UPPER: return 'text-cyan-700 dark:text-cyan-300 bg-cyan-100 dark:bg-cyan-900/30 border-cyan-200 dark:border-cyan-700/50';
      case TrainingType.LOWER: return 'text-teal-700 dark:text-teal-300 bg-teal-100 dark:bg-teal-900/30 border-teal-200 dark:border-teal-700/50';
      case TrainingType.FULL_BODY: return 'text-fuchsia-700 dark:text-fuchsia-300 bg-fuchsia-100 dark:bg-fuchsia-900/30 border-fuchsia-200 dark:border-fuchsia-700/50';
      case TrainingType.HYPERTROPHY: return 'text-rose-700 dark:text-rose-300 bg-rose-100 dark:bg-rose-900/30 border-rose-200 dark:border-rose-700/50';
      case TrainingType.ENDURANCE: return 'text-lime-700 dark:text-lime-300 bg-lime-100 dark:bg-lime-900/30 border-lime-200 dark:border-lime-700/50';
      case TrainingType.FLEXIBILITY: return 'text-pink-700 dark:text-pink-300 bg-pink-100 dark:bg-pink-900/30 border-pink-200 dark:border-pink-700/50';
      default: return 'text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700';
    }
  };

  // ---------- Filtered lists ----------
  const filteredMyPlans = useMemo(() => {
    return myPlans.filter(p => {
      if (planSearchQuery && !p.name.toLowerCase().includes(planSearchQuery.toLowerCase())) return false;
      return true;
    });
  }, [myPlans, planSearchQuery]);

  const filteredMyTrainings = useMemo(() => {
    return myTrainings.filter(t => {
      if (workoutSearchQuery && !t.name.toLowerCase().includes(workoutSearchQuery.toLowerCase())) return false;
      if (filterTrainingType !== 'ALL' && t.training_type !== filterTrainingType) return false;
      if (filterMaxTime < 120 && t.est_time > filterMaxTime * 60) return false;
      if (filterBodyPart !== 'ALL') {
        const hasBodyPart = t.exercises.some(ex => ex._exerciseDetails?.body_part === filterBodyPart);
        if (!hasBodyPart) return false;
      }
      return true;
    });
  }, [myTrainings, workoutSearchQuery, filterTrainingType, filterMaxTime, filterBodyPart]);

  const toGrams = (quantity, capacity) => {
    switch (capacity) {
      case 'kg': return quantity * 1000;
      case 'ml': return quantity;
      case 'l': return quantity * 1000;
      case 'oz': return quantity * 28.35;
      case 'lb': return quantity * 453.6;
      case 'tsp': return quantity * 5;
      case 'tbsp': return quantity * 15;
      case 'cup': return quantity * 240;
      case 'pcs': return quantity * 100;
      default: return quantity;
    }
  };

  const calculateMacros = (recipe) => {
    let calories = 0, protein = 0, carbs = 0, fat = 0, totalWeight = 0;
    if (recipe.ingredients) {
      recipe.ingredients.forEach(item => {
        const ing = ingredientMap[item.ingredient_id];
        const weightG = toGrams(item.quantity || 0, item.capacity);
        totalWeight += weightG;
        if (ing?.macro_per_hundred) {
          const factor = weightG / 100;
          calories += (ing.macro_per_hundred.calories || 0) * factor;
          protein += (ing.macro_per_hundred.proteins || 0) * factor;
          carbs += (ing.macro_per_hundred.carbs || 0) * factor;
          fat += (ing.macro_per_hundred.fats || 0) * factor;
        }
      });
    }
    if (totalWeight > 0) {
      const norm = 100 / totalWeight;
      return { calories: Math.round(calories * norm), protein: Math.round(protein * norm), carbs: Math.round(carbs * norm), fat: Math.round(fat * norm) };
    }
    return { calories: 0, protein: 0, carbs: 0, fat: 0 };
  };

  const filteredMyRecipes = useMemo(() => {
    let filtered = myRecipes.filter(recipe => {
      if (recipeSearchQuery && !recipe.name?.toLowerCase().includes(recipeSearchQuery.toLowerCase())) return false;
      if (recipeFilters.time !== 'All') {
        const limitSeconds = parseInt(recipeFilters.time) * 60;
        if (!recipe.time_to_prepare || recipe.time_to_prepare > limitSeconds) return false;
      }
      if (recipeFilters.maxCalories !== 'All') {
        const macros = calculateMacros(recipe);
        if (macros.calories > parseInt(recipeFilters.maxCalories)) return false;
      }
      if (recipeFilters.minProtein !== 'All') {
        const macros = calculateMacros(recipe);
        if (macros.protein < parseInt(recipeFilters.minProtein)) return false;
      }
      return true;
    });
    if (recipeFilters.sort === 'newest') {
      filtered.sort((a, b) => new Date(b._created_at || 0) - new Date(a._created_at || 0));
    } else if (recipeFilters.sort === 'popular') {
      filtered.sort((a, b) => (b.total_likes || 0) - (a.total_likes || 0));
    } else if (recipeFilters.sort === 'fastest') {
      filtered.sort((a, b) => (a.time_to_prepare || 9999) - (b.time_to_prepare || 9999));
    } else if (recipeFilters.sort === 'calories_low') {
      filtered.sort((a, b) => calculateMacros(a).calories - calculateMacros(b).calories);
    } else if (recipeFilters.sort === 'protein_high') {
      filtered.sort((a, b) => calculateMacros(b).protein - calculateMacros(a).protein);
    }
    return filtered;
  }, [myRecipes, recipeSearchQuery, recipeFilters, ingredientMap]);

  const recipeActiveFilterCount = [recipeFilters.time, recipeFilters.maxCalories, recipeFilters.minProtein].filter(v => v !== 'All').length;

  const filteredExercisesForPicker = useMemo(() => {
    return allExercises.filter(ex => {
      if (pickerBodyPart !== 'ALL' && ex.body_part !== pickerBodyPart) return false;
      if (pickerSearch && !ex.name.toLowerCase().includes(pickerSearch.toLowerCase())) return false;
      return true;
    });
  }, [allExercises, pickerBodyPart, pickerSearch]);

  // ---------- Training handlers ----------
  const handleStartEditTraining = (training) => {
    setEditingTraining({
      _id: training._id,
      name: training.name,
      description: training.description || '',
      training_type: training.training_type,
      est_time: training.est_time,
      exercises: training.exercises.map(ex => ({
        exercise_id: ex.exercise_id,
        sets: ex.sets,
        rest_between_sets: ex.rest_between_sets || 60,
        notes: ex.notes || '',
      })),
    });
    setSelectedTraining(null);
  };

  const handleSaveEditTraining = async () => {
    if (!editingTraining || !editingTraining.name || !editingTraining.exercises?.length) return;
    setIsEditLoading(true);
    try {
      const payload = {
        name: editingTraining.name,
        exercises: editingTraining.exercises.map(ex => ({
          exercise_id: ex.exercise_id,
          sets: ex.sets,
          rest_between_sets: ex.rest_between_sets || 60,
          notes: ex.notes || null,
        })),
        est_time: editingTraining.est_time,
        training_type: editingTraining.training_type,
        description: editingTraining.description || null,
      };
      const saved = await updateTraining(editingTraining._id, payload);
      setMyTrainings(prev => prev.map(t => t._id === saved._id ? populateTraining(saved, exercisesDB) : t));
      setEditingTraining(null);
    } catch (err) {
      console.error('Failed to update training:', err);
    } finally {
      setIsEditLoading(false);
    }
  };

  const handleDeleteTraining = async (trainingId) => {
    if (!confirm('Delete this workout?')) return;
    try {
      await deleteTraining(trainingId);
      setMyTrainings(prev => prev.filter(t => t._id !== trainingId));
      setSelectedTraining(null);
    } catch (err) {
      console.error('Failed to delete training:', err);
    }
  };

  const handleUnlikeWorkout = async (e, trainingId) => {
    e.stopPropagation();
    const uid = authUser?.internal_uid || userProfile?.uid;
    if (!uid || unlikingInProgress.has(trainingId)) return;
    setUnlikingInProgress(prev => new Set(prev).add(trainingId));
    try {
      await unlikeWorkout(uid, trainingId);
      setLikedTrainings(prev => prev.filter(t => t._id !== trainingId));
    } catch (err) {
      console.error('Failed to unlike workout:', err);
    } finally {
      setUnlikingInProgress(prev => { const s = new Set(prev); s.delete(trainingId); return s; });
    }
  };

  const handleUnlikeRecipe = async (e, recipeId) => {
    e.stopPropagation();
    const uid = authUser?.internal_uid || userProfile?.uid;
    if (!uid || unlikingRecipeInProgress.has(recipeId)) return;
    setUnlikingRecipeInProgress(prev => new Set(prev).add(recipeId));
    try {
      await unlikeRecipe(uid, recipeId);
      setLikedRecipes(prev => prev.filter(r => r._id !== recipeId));
      // Also decrement total_likes in recipe-service
      try { await recipeApi.post(`/${recipeId}/unlike`); } catch {}
    } catch (err) {
      console.error('Failed to unlike recipe:', err);
    } finally {
      setUnlikingRecipeInProgress(prev => { const s = new Set(prev); s.delete(recipeId); return s; });
    }
  };

  const handleEditUpdateSet = (exIndex, setIndex, field, value) => {
    setEditingTraining(prev => {
      const exercises = [...(prev.exercises || [])];
      const sets = [...exercises[exIndex].sets];
      sets[setIndex] = { ...sets[setIndex], [field]: value };
      exercises[exIndex] = { ...exercises[exIndex], sets };
      return { ...prev, exercises };
    });
  };
  const handleEditAddSet = (exIndex) => {
    setEditingTraining(prev => {
      const exercises = [...(prev.exercises || [])];
      const ex = exercises[exIndex];
      exercises[exIndex] = { ...ex, sets: [...ex.sets, { volume: 10, units: SetUnit.REPS }] };
      return { ...prev, exercises };
    });
  };
  const handleEditRemoveSet = (exIndex, setIndex) => {
    setEditingTraining(prev => {
      const exercises = [...(prev.exercises || [])];
      const ex = exercises[exIndex];
      if (ex.sets.length <= 1) return prev;
      exercises[exIndex] = { ...ex, sets: ex.sets.filter((_, i) => i !== setIndex) };
      return { ...prev, exercises };
    });
  };

  const handleAddExerciseToEditing = (exerciseId) => {
    const newEx = {
      exercise_id: exerciseId,
      sets: [{ volume: 10, units: SetUnit.REPS }, { volume: 10, units: SetUnit.REPS }, { volume: 10, units: SetUnit.REPS }],
      rest_between_sets: 60, notes: ''
    };
    setEditingTraining(prev => ({ ...prev, exercises: [...(prev.exercises || []), newEx] }));
    setShowExercisePicker(false);
  };

  // ---------- Plan handlers ----------
  const handleStartEditPlan = (plan) => {
    let schedule;
    if (plan.schedule && typeof plan.schedule === 'object') {
      schedule = emptySchedule();
      Object.entries(plan.schedule).forEach(([day, tids]) => {
        schedule[parseInt(day)] = [...(tids || [])];
      });
    } else {
      schedule = emptySchedule();
      (plan.trainings || []).forEach((tid, idx) => {
        const day = (idx % 7) + 1;
        schedule[day] = [...(schedule[day] || []), tid];
      });
    }
    setEditingPlan({
      _id: plan._id,
      name: plan.name,
      description: plan.description || '',
      schedule,
      is_public: plan.is_public,
    });
    setSelectedPlan(null);
  };

  const handleSaveEditPlan = async () => {
    if (!editingPlan || !editingPlan.name) return;
    setIsEditLoading(true);
    try {
      const flatTrainings = [1,2,3,4,5,6,7].flatMap(d => editingPlan.schedule?.[d] || []);
      const payload = {
        name: editingPlan.name,
        description: editingPlan.description || null,
        trainings: flatTrainings,
        schedule: editingPlan.schedule,
        is_public: editingPlan.is_public,
      };
      const saved = await updateWorkoutPlan(editingPlan._id, payload);
      setMyPlans(prev => prev.map(p => p._id === saved._id ? saved : p));
      setEditingPlan(null);
    } catch (err) {
      console.error('Failed to update plan:', err);
    } finally {
      setIsEditLoading(false);
    }
  };

  const handleDeletePlan = async (planId) => {
    if (!confirm('Delete this plan?')) return;
    try {
      await deleteWorkoutPlan(planId);
      setMyPlans(prev => prev.filter(p => p._id !== planId));
      setSelectedPlan(null);
    } catch (err) {
      console.error('Failed to delete plan:', err);
    }
  };

  const CAPACITY_UNITS = [
    { value: 'g', label: 'g' }, { value: 'kg', label: 'kg' }, { value: 'ml', label: 'ml' },
    { value: 'l', label: 'l' }, { value: 'tsp', label: 'tsp' }, { value: 'tbsp', label: 'tbsp' },
    { value: 'cup', label: 'cup' }, { value: 'oz', label: 'oz' }, { value: 'lb', label: 'lb' }, { value: 'pcs', label: 'pcs' },
  ];



  const formatTime = (seconds) => {
    if (!seconds) return '? min';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes} min`;
  };

  const getIngredientName = (ingredientId) => {
    return ingredientMap[ingredientId]?.name || 'Unknown';
  };

  const handleLike = async (recipeId) => {
    try {
      const { data } = await recipeApi.post(`/${recipeId}/like`);
      setMyRecipes(prev => prev.map(r => (r._id === recipeId ? data : r)));
      if (selectedRecipe?._id === recipeId) setSelectedRecipe(data);
    } catch (err) {
      console.error('Error liking recipe:', err);
    }
  };

  const handleDelete = async (recipeId) => {
    if (!confirm('Are you sure you want to delete this recipe?')) return;
    try {
      await recipeApi.delete(`/${recipeId}`);
      setMyRecipes(prev => prev.filter(r => r._id !== recipeId));
      if (selectedRecipe?._id === recipeId) setSelectedRecipe(null);
    } catch (err) {
      console.error('Error deleting recipe:', err);
      alert(err.response?.data?.detail || 'Failed to delete recipe.');
    }
  };

  const handleStartEditRecipe = (recipe) => {
    setEditingRecipe({
      _id: recipe._id,
      prepare_instruction: recipe.prepare_instruction || [],
      time_to_prepare: recipe.time_to_prepare || 1800,
      ingredients: recipe.ingredients?.map(i => ({ ...i })) || [],
      images: recipe.images ? [...recipe.images] : [],
    });
    setEditIngDropdownOpen({});
    setEditIngSearchTerms({});
    setSelectedRecipe(null);
  };

  const handleSaveEditRecipe = async () => {
    if (!editingRecipe) return;
    setIsEditLoading(true);
    try {
      const payload = {
        prepare_instruction: editingRecipe.prepare_instruction,
        time_to_prepare: editingRecipe.time_to_prepare,
        ingredients: editingRecipe.ingredients.filter(i => i.ingredient_id && i.quantity > 0),
        images: editingRecipe.images,
      };
      const { data } = await recipeApi.put(`/${editingRecipe._id}`, payload);
      setMyRecipes(prev => prev.map(r => r._id === data._id ? data : r));
      setEditingRecipe(null);
    } catch (err) {
      console.error('Error updating recipe:', err);
      alert(err.response?.data?.detail || 'Failed to update recipe.');
    } finally {
      setIsEditLoading(false);
    }
  };

  // Derive display info from real data
  const displayName = userProfile
    ? `${userProfile.first_name || ''} ${userProfile.last_name || ''}`.trim() || userProfile.username
    : authUser?.name || 'User';
  const displayUsername = userProfile?.username ? `@${userProfile.username}` : authUser?.email || '';
  const displayAvatar = authUser?.picture || '';
  const displayRole = userProfile?.role || authUser?.role || 'user';
  const displayEmail = userProfile?.email || authUser?.email || '';
  const joinedDate = userProfile?.created_at
    ? new Date(userProfile.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    : '';

  if (loading) {
    return (
      <div className="flex justify-center items-center py-24">
        <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
        <span className="ml-3 text-slate-500 dark:text-slate-400">Loading profile...</span>
      </div>
    );
  }

  if (error && !authUser) {
    return (
      <div className="text-center py-24">
        <p className="text-red-500 mb-4">You need to be logged in to view your profile.</p>
        <button onClick={fetchProfileData} className="px-5 py-2.5 liquid-btn liquid-btn-primary rounded-2xl font-semibold">Retry</button>
      </div>
    );
  }

  function RecipeGridItem({ recipe }) {
    const macros = calculateMacros(recipe);
    const imageUrl = recipe.images?.[0] || `https://picsum.photos/seed/${recipe._id}/400/300`;
    return (
      <div
        onClick={() => setSelectedRecipe(recipe)}
        className="glass-panel rounded-3xl overflow-hidden hover:shadow-xl hover:scale-[1.02] transition-all duration-300 group cursor-pointer flex flex-col h-full"
      >
        <div className="relative h-40 overflow-hidden">
          <img src={imageUrl} alt={recipe.name} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            onError={(e) => { e.target.src = 'https://picsum.photos/400/300?grayscale'; }} />
          <div className="absolute inset-0 bg-black/10 group-hover:bg-transparent transition-colors"></div>
          <div className="absolute bottom-3 left-3 flex gap-1">
            <span className="px-2 py-0.5 bg-black/40 backdrop-blur-md text-white text-[10px] font-medium rounded-full border border-white/20">
              {recipe.ingredients?.length || 0} ing.
            </span>
            {recipe.total_likes > 0 && (
              <span className="px-2 py-0.5 bg-black/40 backdrop-blur-md text-white text-[10px] font-medium rounded-full border border-white/20">
                {recipe.total_likes} likes
              </span>
            )}
          </div>
        </div>
        <div className="p-4 flex-1">
          <h4 className="font-bold text-slate-800 dark:text-white text-sm mb-3 line-clamp-1">{recipe.name}</h4>
          <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
            <div className="flex items-center gap-1"><Clock className="w-3 h-3 text-brand-500" /><span>{formatTime(recipe.time_to_prepare)}</span></div>
            <div className="flex items-center gap-1"><Flame className="w-3 h-3 text-orange-500" /><span>{macros.calories} kcal/100g</span></div>
          </div>
          <div className="mt-2 grid grid-cols-3 gap-1 text-[10px] text-slate-400">
            <span>P: {macros.protein}g</span>
            <span>C: {macros.carbs}g</span>
            <span>F: {macros.fat}g</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-4xl mx-auto p-4 md:p-8">
      {/* Profile Header */}
      <div className="glass-panel rounded-3xl p-6 md:p-8 mb-8 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-r from-brand-400/20 to-brand-600/20 blur-3xl"></div>
        <div className="relative flex flex-col md:flex-row gap-6 items-start md:items-end">
          <div className="relative -mt-4 md:mt-0">
            <div className="w-28 h-28 rounded-full border-4 border-white dark:border-slate-800 shadow-xl overflow-hidden bg-slate-100 dark:bg-slate-700">
              {displayAvatar ? (
                <img src={displayAvatar} alt="Profile" className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-3xl font-bold text-slate-400">
                  {displayName.charAt(0).toUpperCase()}
                </div>
              )}
            </div>
            {displayRole !== 'user' && (
              <div className="absolute bottom-1 right-1 bg-brand-500 text-white text-xs px-2 py-0.5 rounded-full font-bold border-2 border-white dark:border-slate-800 flex items-center gap-1 shadow-md">
                <Award className="w-3 h-3" />{displayRole}
              </div>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-slate-800 dark:text-white drop-shadow-sm">{displayName}</h1>
            <p className="text-slate-500 dark:text-slate-400 font-medium text-sm mb-1">{displayUsername}</p>
            {displayEmail && displayEmail !== displayUsername?.replace('@', '') && (
              <p className="text-slate-400 dark:text-slate-500 text-xs mb-3">{displayEmail}</p>
            )}
            {userProfile && (
              <div className="flex flex-wrap gap-4 text-xs text-slate-500 dark:text-slate-400">
                {userProfile.sex && (
                  <div className="flex items-center gap-1"><User className="w-3.5 h-3.5" />{userProfile.sex}</div>
                )}
                {userProfile.age && (
                  <div className="flex items-center gap-1"><User className="w-3.5 h-3.5" />{userProfile.age} years</div>
                )}
                {userProfile.body_params?.weight && (
                  <div className="flex items-center gap-1">
                    {userProfile.body_params.weight} {userProfile.body_params.weight_unit || 'kg'}
                  </div>
                )}
                {userProfile.body_params?.height && (
                  <div className="flex items-center gap-1">
                    {userProfile.body_params.height} {userProfile.body_params.height_unit || 'cm'}
                  </div>
                )}
                {joinedDate && (
                  <div className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" />Joined {joinedDate}</div>
                )}
              </div>
            )}
          </div>
          <div className="flex gap-6 md:gap-8 bg-white/40 dark:bg-black/20 p-4 rounded-2xl border border-white/20 dark:border-white/5 min-w-[240px] justify-between backdrop-blur-sm">
            <div className="text-center">
              <p className="font-bold text-slate-800 dark:text-white text-lg">{myRecipes.length}</p>
              <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">Recipes</p>
            </div>
            <div className="text-center">
              <p className="font-bold text-slate-800 dark:text-white text-lg">{myPlans.length}</p>
              <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">Plans</p>
            </div>
            <div className="text-center">
              <p className="font-bold text-slate-800 dark:text-white text-lg">{myTrainings.length}</p>
              <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">Workouts</p>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex gap-6 border-b border-white/20 dark:border-white/10 mb-6 overflow-x-auto pb-1 scrollbar-hide">
        {[
          { id: 'my_recipes', label: `My Recipes (${myRecipes.length})` },
          { id: 'my_plans', label: `My Plans (${myPlans.length})` },
          { id: 'my_workouts', label: `My Workouts (${myTrainings.length})` },
        ].map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`pb-3 text-sm font-bold relative whitespace-nowrap transition-colors ${activeTab === tab.id ? 'text-brand-600 dark:text-brand-400' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'}`}>
            {tab.label}
            {activeTab === tab.id && (
              <motion.div layoutId="activeTab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-brand-500 rounded-full shadow-[0_0_8px_rgba(27,211,132,0.8)]" />
            )}
          </button>
        ))}
      </div>

      {/* Content Area */}
      <AnimatePresence mode="wait">
        <motion.div key={activeTab} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }}>
          {activeTab === 'my_recipes' && (
            <div>
              {/* Search & Filter Bar */}
              <div className="flex flex-col gap-4 mb-6">
                <div className="flex flex-col sm:flex-row gap-3">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
                    <input type="text" value={recipeSearchQuery} onChange={(e) => setRecipeSearchQuery(e.target.value)} placeholder="Search your recipes..."
                      className="w-full pl-10 pr-4 py-3 liquid-input rounded-2xl text-slate-800 dark:text-white placeholder-slate-400 outline-none" />
                  </div>
                  <button onClick={() => setShowRecipeFilters(!showRecipeFilters)}
                    className={`px-4 py-3 rounded-2xl flex items-center gap-2 font-semibold transition-all liquid-btn ${showRecipeFilters ? 'bg-slate-800 text-white shadow-lg' : 'liquid-btn-secondary'}`}>
                    <Filter className="w-4 h-4" /><span>Filters</span>
                    {recipeActiveFilterCount > 0 && (<span className="min-w-[18px] h-[18px] rounded-full bg-brand-500 text-white text-[10px] font-bold flex items-center justify-center">{recipeActiveFilterCount}</span>)}
                  </button>
                </div>
                <AnimatePresence>
                  {showRecipeFilters && (
                    <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }}>
                      <div className="glass-panel rounded-2xl p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div className="space-y-1.5">
                          <label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Max Prep Time</label>
                          <CustomSelect value={recipeFilters.time} onChange={(v) => setRecipeFilters({...recipeFilters, time: v})}
                            options={[
                              { value: 'All', label: 'Any Time' },
                              { value: '15', label: 'Under 15 min' },
                              { value: '30', label: 'Under 30 min' },
                              { value: '60', label: 'Under 60 min' },
                              { value: '120', label: 'Under 2 hours' },
                            ]} />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Max Calories / 100g</label>
                          <CustomSelect value={recipeFilters.maxCalories} onChange={(v) => setRecipeFilters({...recipeFilters, maxCalories: v})}
                            options={[
                              { value: 'All', label: 'Any' },
                              { value: '100', label: 'Under 100 kcal' },
                              { value: '200', label: 'Under 200 kcal' },
                              { value: '300', label: 'Under 300 kcal' },
                              { value: '500', label: 'Under 500 kcal' },
                            ]} />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Min Protein / 100g</label>
                          <CustomSelect value={recipeFilters.minProtein} onChange={(v) => setRecipeFilters({...recipeFilters, minProtein: v})}
                            options={[
                              { value: 'All', label: 'Any' },
                              { value: '10', label: '10g+' },
                              { value: '20', label: '20g+' },
                              { value: '30', label: '30g+' },
                              { value: '40', label: '40g+' },
                            ]} />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Sort By</label>
                          <CustomSelect value={recipeFilters.sort} onChange={(v) => setRecipeFilters({...recipeFilters, sort: v})}
                            options={[
                              { value: 'newest', label: 'Newest' },
                              { value: 'popular', label: 'Most Popular' },
                              { value: 'fastest', label: 'Fastest' },
                              { value: 'calories_low', label: 'Lowest Calories' },
                              { value: 'protein_high', label: 'Highest Protein' },
                            ]} />
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {filteredMyRecipes.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                  {filteredMyRecipes.map(recipe => <RecipeGridItem key={recipe._id} recipe={recipe} />)}
                </div>
              ) : (
                <p className="text-center text-slate-400 py-10">{myRecipes.length > 0 ? 'No recipes match your filters.' : "You haven't created any recipes yet."}</p>
              )}

              {/* LIKED RECIPES SECTION */}
              <div className="mt-10">
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2 bg-red-100 dark:bg-red-900/20 rounded-xl">
                    <Heart className="w-5 h-5 text-red-500" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-slate-800 dark:text-white">Liked recipes</h3>
                    <p className="text-xs text-slate-400">{likedRecipes.length} liked</p>
                  </div>
                </div>
                {likedRecipes.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    {likedRecipes.map(recipe => {
                      const macros = calculateMacros(recipe);
                      const imageUrl = recipe.images?.[0] || `https://picsum.photos/seed/${recipe._id}/400/300`;
                      return (
                        <motion.div key={`liked-recipe-${recipe._id}`} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} whileHover={{ scale: 1.02 }}
                          onClick={() => setSelectedRecipe(recipe)}
                          className="glass-panel rounded-3xl overflow-hidden group cursor-pointer flex flex-col h-full">
                          <div className="relative h-40 overflow-hidden">
                            <img src={imageUrl} alt={recipe.name} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                              onError={(e) => { e.target.src = 'https://picsum.photos/400/300?grayscale'; }} />
                            <div className="absolute inset-0 bg-black/10 group-hover:bg-transparent transition-colors"></div>
                            <div className="absolute top-3 right-3">
                              <button
                                onClick={(e) => handleUnlikeRecipe(e, recipe._id)}
                                disabled={unlikingRecipeInProgress.has(recipe._id)}
                                className={`p-1.5 bg-red-500/80 backdrop-blur-md rounded-full shadow-sm border border-red-400/30 hover:bg-red-600 transition-colors ${unlikingRecipeInProgress.has(recipe._id) ? 'opacity-50' : ''}`}
                                title="Unlike"
                              >
                                <Heart className="w-3.5 h-3.5 text-white fill-current" />
                              </button>
                            </div>
                            <div className="absolute bottom-3 left-3 flex gap-1">
                              <span className="px-2 py-0.5 bg-black/40 backdrop-blur-md text-white text-[10px] font-medium rounded-full border border-white/20">
                                {recipe.ingredients?.length || 0} ing.
                              </span>
                              {recipe.total_likes > 0 && (
                                <span className="px-2 py-0.5 bg-black/40 backdrop-blur-md text-white text-[10px] font-medium rounded-full border border-white/20">
                                  {recipe.total_likes} likes
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="p-4 flex-1">
                            <h4 className="font-bold text-slate-800 dark:text-white text-sm mb-3 line-clamp-1">{recipe.name}</h4>
                            <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
                              <div className="flex items-center gap-1"><Clock className="w-3 h-3 text-brand-500" /><span>{formatTime(recipe.time_to_prepare)}</span></div>
                              <div className="flex items-center gap-1"><Flame className="w-3 h-3 text-orange-500" /><span>{macros.calories} kcal/100g</span></div>
                            </div>
                            <div className="mt-2 grid grid-cols-3 gap-1 text-[10px] text-slate-400">
                              <span>P: {macros.protein}g</span>
                              <span>C: {macros.carbs}g</span>
                              <span>F: {macros.fat}g</span>
                            </div>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-center text-slate-400 py-10">You haven&apos;t liked any recipes yet.</p>
                )}
              </div>
            </div>
          )}

          {activeTab === 'my_plans' && (
            <div className="space-y-6">
              <div className="glass-panel p-2 rounded-2xl flex flex-col md:flex-row gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
                  <input type="text" value={planSearchQuery} onChange={(e) => setPlanSearchQuery(e.target.value)} placeholder="Search your plans..."
                    className="w-full pl-12 pr-4 py-3 bg-transparent text-slate-800 dark:text-white placeholder-slate-400 outline-none font-medium" />
                </div>
              </div>
              {workoutsLoading ? (
                <div className="flex items-center justify-center py-16"><Loader2 className="w-6 h-6 animate-spin text-brand-500" /></div>
              ) : filteredMyPlans.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {filteredMyPlans.map(plan => {
                    const workoutCount = plan.trainings?.length || 0;
                    const uniqueWorkoutIds = Array.from(new Set(plan.trainings || []));
                    return (
                      <motion.div key={plan._id} layoutId={`prof-plan-${plan._id}`} onClick={() => { setExpandedPlanTrainings({}); setSelectedPlan(plan); }}
                        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} whileHover={{ scale: 1.02 }}
                        className="glass-panel rounded-3xl p-6 relative overflow-hidden group cursor-pointer">
                        <div className="absolute top-0 left-0 w-2 h-full bg-brand-500"></div>
                        <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-2 ml-2 group-hover:text-brand-600 transition-colors">{plan.name}</h3>
                        <p className="text-sm text-slate-500 mb-4 ml-2 line-clamp-2">{plan.description || 'Personal goal plan.'}</p>
                        <div className="flex gap-2 mb-4 ml-2">
                          <span className="bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-full text-xs font-bold text-slate-600 dark:text-slate-300 border border-slate-200">{workoutCount} Trainings</span>
                          {plan.total_likes > 0 && <span className="bg-red-50 dark:bg-red-900/20 px-3 py-1 rounded-full text-xs font-bold text-red-500 border border-red-200">{plan.total_likes} Likes</span>}
                          {plan.is_public && <span className="bg-green-50 dark:bg-green-900/20 px-3 py-1 rounded-full text-xs font-bold text-green-600 border border-green-200">Public</span>}
                        </div>
                        <div className="ml-2 space-y-2">
                          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-2">Trainings:</p>
                          {uniqueWorkoutIds.slice(0, 3).map(tid => {
                            const t = allPopulatedTrainings.find(tr => tr._id === tid);
                            return t ? <div key={tid} className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400"><Dumbbell className="w-3.5 h-3.5 text-brand-500" />{t.name}</div> : null;
                          })}
                          {uniqueWorkoutIds.length > 3 && <p className="text-xs text-slate-400 ml-5">+{uniqueWorkoutIds.length - 3} more</p>}
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-center text-slate-400 py-10">{myPlans.length > 0 ? 'No plans match your search.' : "You haven't created any workout plans yet."}</p>
              )}
            </div>
          )}

          {activeTab === 'my_workouts' && (
            <div className="space-y-6">
              <div className="space-y-4">
                <div className="glass-panel p-2 rounded-2xl flex flex-col md:flex-row gap-2">
                  <div className="relative flex-1">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
                    <input type="text" value={workoutSearchQuery} onChange={(e) => setWorkoutSearchQuery(e.target.value)} placeholder="Search your workouts..."
                      className="w-full pl-12 pr-4 py-3 bg-transparent text-slate-800 dark:text-white placeholder-slate-400 outline-none font-medium" />
                  </div>
                  <button onClick={() => setShowWorkoutFilters(!showWorkoutFilters)}
                    className={`px-6 py-3 rounded-xl flex items-center gap-2 font-bold transition-all ${showWorkoutFilters ? 'bg-slate-800 text-white shadow-lg' : 'bg-white/50 dark:bg-white/5 text-slate-600 hover:bg-white/80'}`}>
                    <Filter className="w-4 h-4" /> Filters
                  </button>
                </div>
                <AnimatePresence>
                  {showWorkoutFilters && (
                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                      <div className="glass-panel rounded-2xl p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 border-dashed">
                        <div className="space-y-3">
                          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2 ml-1"><Layers className="w-3 h-3" /> Training Type</label>
                          <div className="flex flex-wrap gap-2">
                            {['ALL', ...Object.values(TrainingType)].map(tt => (
                              <button key={tt} onClick={() => setFilterTrainingType(tt)}
                                className={`px-3 py-1.5 rounded-xl text-xs font-bold border transition-all ${filterTrainingType === tt ? 'bg-brand-500 text-white border-brand-400 shadow-md' : 'bg-white/50 dark:bg-white/5 text-slate-500 border-transparent hover:border-slate-200'}`}>
                                {tt === 'ALL' ? 'All' : tt.replace('_', ' ')}
                              </button>
                            ))}
                          </div>
                        </div>
                        <div className="space-y-3">
                          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2 ml-1"><Dumbbell className="w-3 h-3" /> Body Part</label>
                          <div className="flex flex-wrap gap-2">
                            {['ALL', ...Object.values(BodyPart)].map(bp => (
                              <button key={bp} onClick={() => setFilterBodyPart(bp)}
                                className={`px-3 py-1.5 rounded-xl text-xs font-bold border transition-all ${filterBodyPart === bp ? 'bg-brand-500 text-white border-brand-400 shadow-md' : 'bg-white/50 dark:bg-white/5 text-slate-500 border-transparent hover:border-slate-200'}`}>
                                {bp === 'ALL' ? 'All' : bp.replace('_', ' ')}
                              </button>
                            ))}
                          </div>
                        </div>
                        <div className="space-y-3">
                          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center justify-between ml-1">
                            <span className="flex items-center gap-2"><Clock className="w-3 h-3" /> Max Duration</span>
                            <span className="text-brand-500">{filterMaxTime} min</span>
                          </label>
                          <input type="range" min="5" max="180" step="5" value={filterMaxTime} onChange={(e) => setFilterMaxTime(parseInt(e.target.value))}
                            className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-brand-500" />
                          <div className="flex justify-between text-[9px] text-slate-400 font-bold px-1"><span>5m</span><span>180m</span></div>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
              {workoutsLoading ? (
                <div className="flex items-center justify-center py-16"><Loader2 className="w-6 h-6 animate-spin text-brand-500" /></div>
              ) : filteredMyTrainings.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {filteredMyTrainings.map(training => (
                    <motion.div key={training._id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} whileHover={{ scale: 1.02 }}
                      onClick={() => setSelectedTraining(training)}
                      className="glass-panel rounded-3xl p-6 relative overflow-hidden group cursor-pointer">
                      <div className="flex justify-between items-start mb-4">
                        <h3 className="text-lg font-bold text-slate-800 dark:text-white group-hover:text-brand-600 transition-colors">{training.name}</h3>
                        <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getDifficultyColor(training.training_type)}`}>{training.training_type?.replace('_', ' ')}</span>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-slate-500 mb-4">
                        <div className="flex items-center gap-1"><Clock className="w-4 h-4 text-brand-500" /><span>{formatDuration(training.est_time)}</span></div>
                        <div className="flex items-center gap-1"><Activity className="w-4 h-4 text-orange-500" /><span>{training.exercises.length} exercises</span></div>
                      </div>
                      <div className="space-y-2">
                        {training.exercises.slice(0, 3).map((ex, i) => (
                          <div key={i} className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                            <div className="w-1.5 h-1.5 rounded-full bg-brand-500"></div>
                            <span>{ex._exerciseDetails?.name || 'Unknown'}</span>
                            <span className="text-slate-400 text-xs ml-auto">{ex.sets.length} x {ex.sets[0]?.volume} {ex.sets[0]?.units}</span>
                          </div>
                        ))}
                        {training.exercises.length > 3 && <p className="text-xs text-slate-400 ml-3">+{training.exercises.length - 3} more</p>}
                      </div>
                    </motion.div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-slate-400 py-10">{myTrainings.length > 0 ? 'No workouts match your filters.' : "You haven't created any workouts yet."}</p>
              )}

              {/* LIKED WORKOUTS SECTION */}
              <div className="mt-10">
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2 bg-red-100 dark:bg-red-900/20 rounded-xl">
                    <Heart className="w-5 h-5 text-red-500" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-slate-800 dark:text-white">Liked trainings</h3>
                    <p className="text-xs text-slate-400">{likedTrainings.length} liked</p>
                  </div>
                </div>
                {likedTrainings.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {likedTrainings.map(training => (
                      <motion.div key={`liked-${training._id}`} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} whileHover={{ scale: 1.02 }}
                        onClick={() => setSelectedTraining(training)}
                        className="glass-panel rounded-3xl p-6 relative overflow-hidden group cursor-pointer">
                        <div className="flex justify-between items-start mb-4">
                          <h3 className="text-lg font-bold text-slate-800 dark:text-white group-hover:text-brand-600 transition-colors pr-2">{training.name}</h3>
                          <div className="flex items-center gap-2 shrink-0">
                            <button
                              onClick={(e) => handleUnlikeWorkout(e, training._id)}
                              disabled={unlikingInProgress.has(training._id)}
                              className={`p-1.5 rounded-xl transition-all text-red-500 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30 ${unlikingInProgress.has(training._id) ? 'opacity-50' : ''}`}
                              title="Unlike"
                            >
                              <Heart className="w-4 h-4 fill-current" />
                            </button>
                            <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getDifficultyColor(training.training_type)}`}>{training.training_type?.replace('_', ' ')}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-slate-500 mb-4">
                          <div className="flex items-center gap-1"><Clock className="w-4 h-4 text-brand-500" /><span>{formatDuration(training.est_time)}</span></div>
                          <div className="flex items-center gap-1"><Activity className="w-4 h-4 text-orange-500" /><span>{training.exercises.length} exercises</span></div>
                        </div>
                        <div className="space-y-2">
                          {training.exercises.slice(0, 3).map((ex, i) => (
                            <div key={i} className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                              <div className="w-1.5 h-1.5 rounded-full bg-brand-500"></div>
                              <span>{ex._exerciseDetails?.name || 'Unknown'}</span>
                              <span className="text-slate-400 text-xs ml-auto">{ex.sets.length} x {ex.sets[0]?.volume} {ex.sets[0]?.units}</span>
                            </div>
                          ))}
                          {training.exercises.length > 3 && <p className="text-xs text-slate-400 ml-3">+{training.exercises.length - 3} more</p>}
                        </div>
                      </motion.div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-slate-400 py-10">You haven't liked any trainings yet.</p>
                )}
              </div>
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* TRAINING DETAIL MODAL */}
      <AnimatePresence>
        {selectedTraining && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setSelectedTraining(null)} className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" />
            <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="w-full max-w-2xl bg-white/95 dark:bg-slate-900/95 glass-panel rounded-[2.5rem] relative z-10 flex flex-col max-h-[88vh] shadow-2xl border border-white/40 overflow-hidden">
              <div className="p-5 border-b border-slate-100 dark:border-white/5 flex justify-between items-center bg-white/50 dark:bg-white/5 backdrop-blur-sm">
                <div className="pl-3 flex-1 min-w-0">
                  <h3 className="font-bold text-xl text-slate-800 dark:text-white drop-shadow-sm truncate">{selectedTraining.name}</h3>
                  <div className="flex items-center gap-3 mt-1">
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${getDifficultyColor(selectedTraining.training_type)}`}>{selectedTraining.training_type?.replace('_', ' ')}</span>
                    <span className="text-[10px] text-slate-400 font-bold">{formatDuration(selectedTraining.est_time)}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => handleStartEditTraining(selectedTraining)} className="p-2.5 hover:bg-brand-500/10 rounded-full transition-colors group" title="Edit"><Edit3 className="w-4 h-4 text-slate-400 group-hover:text-brand-500" /></button>
                  <button onClick={() => handleDeleteTraining(selectedTraining._id)} className="p-2.5 hover:bg-red-50 dark:hover:bg-red-900/10 rounded-full transition-colors group" title="Delete"><Trash2 className="w-4 h-4 text-slate-400 group-hover:text-red-500" /></button>
                  <button onClick={() => setSelectedTraining(null)} className="p-2.5 hover:bg-black/5 dark:hover:bg-white/10 rounded-full transition-colors"><X className="w-5 h-5 text-slate-400" /></button>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {selectedTraining.description && <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">{selectedTraining.description}</p>}
                {selectedTraining.exercises.map((ex, i) => (
                  <div key={i} className="p-5 bg-white/40 dark:bg-white/5 border border-white/50 dark:border-white/10 rounded-2xl">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="p-2 bg-brand-500/10 text-brand-500 rounded-xl"><Dumbbell className="w-5 h-5" /></div>
                      <div>
                        <h4 className="font-bold text-slate-800 dark:text-white">{ex._exerciseDetails?.name || 'Unknown'}</h4>
                        <p className="text-[9px] text-slate-400 font-bold uppercase tracking-widest mt-0.5">{(ex._exerciseDetails?.body_part || '').replace('_', ' ')} • {ex._exerciseDetails?.advancement || ''}</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                      {ex.sets.map((set, si) => (
                        <div key={si} className="flex items-center gap-2 p-2 bg-white/60 dark:bg-black/20 rounded-xl border border-white/40 dark:border-white/5">
                          <span className="w-6 h-6 rounded bg-slate-100 dark:bg-slate-800 text-[10px] font-bold text-slate-400 flex items-center justify-center">{si + 1}</span>
                          <span className="text-sm font-bold text-slate-800 dark:text-white">{set.volume}</span>
                          <span className="text-[10px] font-bold text-slate-400">{set.units}</span>
                        </div>
                      ))}
                    </div>
                    {ex.rest_between_sets > 0 && <p className="text-[10px] text-slate-400 mt-2 ml-1">Rest: {ex.rest_between_sets}s between sets</p>}
                    {ex.notes && <p className="text-xs text-slate-500 mt-2 ml-1 italic">{ex.notes}</p>}
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* TRAINING EDIT MODAL */}
      <AnimatePresence>
        {editingTraining && (
          <div className="fixed inset-0 z-[80] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setEditingTraining(null)} className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" />
            <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="w-full max-w-2xl bg-white/95 dark:bg-slate-900/95 glass-panel rounded-[2.5rem] relative z-10 flex flex-col max-h-[88vh] shadow-2xl border border-white/40 overflow-hidden">
              <div className="p-5 border-b border-slate-100 dark:border-white/5 flex justify-between items-center bg-white/50 dark:bg-white/5 backdrop-blur-sm">
                <div className="pl-3">
                  <h3 className="font-bold text-xl text-slate-800 dark:text-white drop-shadow-sm">Edit Workout</h3>
                  <p className="text-[10px] font-bold text-brand-600 dark:text-brand-400 uppercase tracking-[0.2em]">Modify Session Details</p>
                </div>
                <button onClick={() => setEditingTraining(null)} className="p-2.5 hover:bg-black/5 dark:hover:bg-white/10 rounded-full transition-colors"><X className="w-5 h-5 text-slate-400" /></button>
              </div>
              <div className="flex-1 overflow-y-auto p-8 space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">Title</label>
                    <input type="text" value={editingTraining.name} onChange={e => setEditingTraining({...editingTraining, name: e.target.value})}
                      className="w-full p-4 liquid-input rounded-2xl text-slate-800 dark:text-white outline-none font-medium" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">Type</label>
                    <div className="relative group">
                      <select value={editingTraining.training_type} onChange={e => setEditingTraining({...editingTraining, training_type: e.target.value})}
                        className="w-full p-4 liquid-input rounded-2xl text-slate-800 dark:text-white outline-none appearance-none font-medium cursor-pointer pr-10">
                        {Object.values(TrainingType).map(t => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}
                      </select>
                      <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">Est. Time (min)</label>
                    <div className="flex items-center gap-2">
                      <button type="button" onClick={() => setEditingTraining(prev => ({...prev, est_time: Math.max(60, prev.est_time - 60)}))}
                        className="w-10 h-10 flex items-center justify-center rounded-xl liquid-input text-slate-500 hover:text-brand-500 hover:bg-brand-500/10 transition-colors shrink-0"><Minus className="w-4 h-4" /></button>
                      <input type="text" inputMode="numeric" value={Math.floor(editingTraining.est_time / 60)} onChange={e => setEditingTraining({...editingTraining, est_time: (parseInt(e.target.value) || 1) * 60})}
                        className="flex-1 p-4 liquid-input rounded-2xl text-slate-800 dark:text-white outline-none font-medium text-center" />
                      <button type="button" onClick={() => setEditingTraining(prev => ({...prev, est_time: prev.est_time + 60}))}
                        className="w-10 h-10 flex items-center justify-center rounded-xl liquid-input text-slate-500 hover:text-brand-500 hover:bg-brand-500/10 transition-colors shrink-0"><Plus className="w-4 h-4" /></button>
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">Description</label>
                  <input type="text" value={editingTraining.description} onChange={e => setEditingTraining({...editingTraining, description: e.target.value})} placeholder="Optional description"
                    className="w-full p-4 liquid-input rounded-2xl text-slate-800 dark:text-white outline-none font-medium" />
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center px-1">
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2"><Activity className="w-4 h-4 text-brand-500" /> Exercises ({editingTraining.exercises?.length || 0})</label>
                    <button onClick={() => setShowExercisePicker(true)} className="flex items-center gap-2 text-brand-600 dark:text-brand-400 font-bold text-sm bg-brand-500/10 px-4 py-2 rounded-xl hover:bg-brand-500/20 transition-all active:scale-95"><Plus className="w-4 h-4" /> Add Exercise</button>
                  </div>
                  {editingTraining.exercises?.map((ex, exIdx) => (
                    <motion.div key={exIdx} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                      className="p-5 bg-white/40 dark:bg-white/5 border border-white/50 dark:border-white/10 rounded-3xl shadow-sm group backdrop-blur-sm">
                      <div className="flex justify-between items-center mb-4">
                        <div className="flex items-center gap-3">
                          <div className="p-2.5 bg-brand-500/10 text-brand-500 rounded-2xl"><Dumbbell className="w-5 h-5" /></div>
                          <div>
                            <span className="font-bold text-slate-800 dark:text-white">{exercisesDB[ex.exercise_id]?.name || 'Exercise'}</span>
                            <p className="text-[9px] text-slate-400 font-bold uppercase tracking-widest mt-0.5">{(exercisesDB[ex.exercise_id]?.body_part || '').replace('_', ' ')}</p>
                          </div>
                        </div>
                        <button onClick={() => setEditingTraining(prev => ({...prev, exercises: prev.exercises.filter((_, idx) => idx !== exIdx)}))}
                          className="p-2 text-slate-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 rounded-xl transition-all"><Trash2 className="w-4 h-4" /></button>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {ex.sets.map((set, setIdx) => (
                          <div key={setIdx} className="flex gap-2 items-center bg-white/60 dark:bg-black/20 p-2 rounded-2xl border border-white/40 dark:border-white/5 group/set">
                            <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800 text-[10px] font-bold text-slate-400">{setIdx + 1}</div>
                            <button type="button" onClick={() => handleEditUpdateSet(exIdx, setIdx, 'volume', Math.max(1, (set.volume || 1) - 1))}
                              className="w-7 h-7 flex items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-400 hover:text-brand-500 hover:bg-brand-500/10 transition-colors shrink-0"><Minus className="w-3 h-3" /></button>
                            <input type="text" inputMode="numeric" value={set.volume} onChange={e => handleEditUpdateSet(exIdx, setIdx, 'volume', parseInt(e.target.value) || 0)}
                              className="w-10 p-1 bg-transparent text-center text-sm font-bold text-slate-800 dark:text-white focus:outline-none" />
                            <button type="button" onClick={() => handleEditUpdateSet(exIdx, setIdx, 'volume', (set.volume || 0) + 1)}
                              className="w-7 h-7 flex items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-400 hover:text-brand-500 hover:bg-brand-500/10 transition-colors shrink-0"><Plus className="w-3 h-3" /></button>
                            <div className="relative flex-1">
                              <select value={set.units} onChange={e => handleEditUpdateSet(exIdx, setIdx, 'units', e.target.value)}
                                className="w-full p-2 bg-transparent text-[10px] font-bold text-slate-500 dark:text-slate-400 outline-none cursor-pointer appearance-none pr-6">
                                {Object.values(SetUnit).map(u => <option key={u} value={u}>{u}</option>)}
                              </select>
                              <ChevronDown className="absolute right-1 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-400 pointer-events-none" />
                            </div>
                            <button onClick={() => handleEditRemoveSet(exIdx, setIdx)} className="p-1 text-slate-300 hover:text-red-500 opacity-0 group-hover/set:opacity-100 transition-opacity"><X className="w-4 h-4" /></button>
                          </div>
                        ))}
                        <button onClick={() => handleEditAddSet(exIdx)}
                          className="w-full py-3 border-2 border-dashed border-slate-100 dark:border-white/5 rounded-2xl text-slate-300 text-[10px] font-bold hover:border-brand-500/50 hover:bg-brand-500/5 hover:text-brand-600 transition-all flex items-center justify-center gap-2">
                          <Plus className="w-3.5 h-3.5" /> Add Set
                        </button>
                      </div>
                      <div className="mt-3 grid grid-cols-2 gap-3">
                        <div className="flex items-center gap-2">
                          <label className="text-[10px] font-bold text-slate-400 whitespace-nowrap">Rest (s)</label>
                          <div className="flex items-center gap-1">
                            <button type="button" onClick={() => setEditingTraining(prev => {
                              const exercises = [...prev.exercises]; exercises[exIdx] = { ...exercises[exIdx], rest_between_sets: Math.max(0, (exercises[exIdx].rest_between_sets || 0) - 5) }; return { ...prev, exercises };
                            })} className="w-7 h-7 flex items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-400 hover:text-brand-500 hover:bg-brand-500/10 transition-colors shrink-0"><Minus className="w-3 h-3" /></button>
                            <input type="text" inputMode="numeric" value={ex.rest_between_sets || 0} onChange={e => setEditingTraining(prev => {
                              const exercises = [...prev.exercises]; exercises[exIdx] = { ...exercises[exIdx], rest_between_sets: parseInt(e.target.value) || 0 }; return { ...prev, exercises };
                            })} className="w-12 p-1 bg-transparent text-sm text-slate-800 dark:text-white outline-none text-center font-medium" />
                            <button type="button" onClick={() => setEditingTraining(prev => {
                              const exercises = [...prev.exercises]; exercises[exIdx] = { ...exercises[exIdx], rest_between_sets: (exercises[exIdx].rest_between_sets || 0) + 5 }; return { ...prev, exercises };
                            })} className="w-7 h-7 flex items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-400 hover:text-brand-500 hover:bg-brand-500/10 transition-colors shrink-0"><Plus className="w-3 h-3" /></button>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <label className="text-[10px] font-bold text-slate-400 whitespace-nowrap">Notes</label>
                          <input type="text" value={ex.notes || ''} onChange={e => setEditingTraining(prev => {
                            const exercises = [...prev.exercises]; exercises[exIdx] = { ...exercises[exIdx], notes: e.target.value }; return { ...prev, exercises };
                          })} className="flex-1 p-2 liquid-input rounded-xl text-xs text-slate-800 dark:text-white outline-none font-medium" placeholder="Optional" />
                        </div>
                      </div>
                    </motion.div>
                  ))}
                  {(!editingTraining.exercises || editingTraining.exercises.length === 0) && (
                    <div className="text-center py-12 border-2 border-dashed border-slate-100 dark:border-white/5 rounded-[2rem] flex flex-col items-center gap-3 group hover:border-brand-500/30 transition-all cursor-pointer" onClick={() => setShowExercisePicker(true)}>
                      <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-full text-slate-300 group-hover:text-brand-500 transition-colors"><Activity className="w-8 h-8" /></div>
                      <p className="text-xs font-bold text-slate-400">Click to add exercises</p>
                    </div>
                  )}
                </div>
              </div>
              <div className="p-6 bg-slate-50/80 dark:bg-black/20 backdrop-blur-md flex justify-end gap-3 border-t border-slate-100 dark:border-white/5">
                <button onClick={() => setEditingTraining(null)} className="px-6 py-2.5 text-slate-500 dark:text-slate-400 font-bold hover:text-slate-800 dark:hover:text-white transition-colors">Cancel</button>
                <button onClick={handleSaveEditTraining} disabled={!editingTraining.name || !editingTraining.exercises?.length}
                  className="liquid-btn liquid-btn-primary px-10 py-2.5 rounded-2xl font-bold flex items-center gap-2 shadow-lg shadow-brand-500/20 disabled:opacity-50 disabled:grayscale transition-all">
                  {isEditLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Save Changes
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* EXERCISE PICKER MODAL */}
      <AnimatePresence>
        {showExercisePicker && (
          <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setShowExercisePicker(false)} className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" />
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-lg bg-white/95 dark:bg-slate-900/95 glass-panel rounded-[2rem] relative z-10 flex flex-col max-h-[70vh] shadow-2xl border border-white/40 overflow-hidden">
              <div className="p-5 border-b border-slate-100 dark:border-white/5 flex justify-between items-center">
                <h3 className="font-bold text-lg text-slate-800 dark:text-white pl-2">Pick Exercise</h3>
                <button onClick={() => setShowExercisePicker(false)} className="p-2.5 hover:bg-black/5 dark:hover:bg-white/10 rounded-full transition-colors"><X className="w-5 h-5 text-slate-400" /></button>
              </div>
              <div className="p-4 space-y-3">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input type="text" value={pickerSearch} onChange={(e) => setPickerSearch(e.target.value)} placeholder="Search exercises..."
                    className="w-full pl-10 pr-4 py-3 liquid-input rounded-xl text-slate-800 dark:text-white outline-none" />
                </div>
                <div className="flex gap-2 flex-wrap">
                  {['ALL', ...Object.values(BodyPart)].map(bp => (
                    <button key={bp} onClick={() => setPickerBodyPart(bp)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${pickerBodyPart === bp ? 'bg-brand-500 text-white' : 'bg-slate-100 dark:bg-white/5 text-slate-500'}`}>
                      {bp === 'ALL' ? 'All' : bp.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-2">
                {filteredExercisesForPicker.map(ex => (
                  <div key={ex._id} onClick={() => handleAddExerciseToEditing(ex._id)}
                    className="p-4 rounded-2xl border border-slate-100 dark:border-white/5 hover:border-brand-500/30 hover:bg-brand-500/5 cursor-pointer flex justify-between items-center group transition-all">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-slate-50 dark:bg-slate-800 rounded-xl flex items-center justify-center text-slate-400 group-hover:text-brand-500 transition-colors">
                        <Dumbbell className="w-5 h-5" />
                      </div>
                      <div>
                        <h4 className="font-bold text-sm text-slate-800 dark:text-white">{ex.name}</h4>
                        <p className="text-[9px] text-slate-500 mt-1 uppercase font-bold tracking-[0.2em]">{ex.body_part.replace('_', ' ')} • {ex.advancement}</p>
                      </div>
                    </div>
                    <div className="w-9 h-9 rounded-xl bg-brand-500/10 text-brand-500 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all scale-75 group-hover:scale-100"><Plus className="w-5 h-5" /></div>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* PLAN DETAIL MODAL */}
      <AnimatePresence>
        {selectedPlan && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setSelectedPlan(null)} className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" />
            <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="w-full max-w-2xl bg-white/95 dark:bg-slate-900/95 glass-panel rounded-[2.5rem] relative z-10 flex flex-col max-h-[88vh] shadow-2xl border border-white/40 overflow-hidden">
              <div className="p-5 border-b border-slate-100 dark:border-white/5 flex justify-between items-center bg-white/50 dark:bg-white/5 backdrop-blur-sm">
                <div className="pl-3 flex-1 min-w-0">
                  <h3 className="font-bold text-xl text-slate-800 dark:text-white drop-shadow-sm truncate">{selectedPlan.name}</h3>
                  <div className="flex items-center gap-3 mt-1 flex-wrap">
                    <span className="text-[10px] text-slate-400 font-bold">{selectedPlan.trainings?.length || 0} trainings</span>
                    {selectedPlan.total_likes > 0 && <span className="text-[10px] text-red-500 font-bold">{selectedPlan.total_likes} likes</span>}
                    {selectedPlan.is_public && <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-green-100 dark:bg-green-900/20 text-green-600 border border-green-200 dark:border-green-800">Public</span>}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => handleStartEditPlan(selectedPlan)} className="p-2.5 hover:bg-brand-500/10 rounded-full transition-colors group" title="Edit"><Edit3 className="w-4 h-4 text-slate-400 group-hover:text-brand-500" /></button>
                  <button onClick={() => handleDeletePlan(selectedPlan._id)} className="p-2.5 hover:bg-red-50 dark:hover:bg-red-900/10 rounded-full transition-colors group" title="Delete"><Trash2 className="w-4 h-4 text-slate-400 group-hover:text-red-500" /></button>
                  <button onClick={() => setSelectedPlan(null)} className="p-2.5 hover:bg-black/5 dark:hover:bg-white/10 rounded-full transition-colors"><X className="w-5 h-5 text-slate-400" /></button>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {selectedPlan.description && <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">{selectedPlan.description}</p>}
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2"><Calendar className="w-3 h-3 text-brand-500" /> Weekly Breakdown</label>
                {(() => {
                  const schedule = (() => {
                    if (selectedPlan.schedule && typeof selectedPlan.schedule === 'object') {
                      const s = {};
                      for (let d = 1; d <= 7; d++) s[d] = selectedPlan.schedule[String(d)] || selectedPlan.schedule[d] || [];
                      return s;
                    }
                    const s = { 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [] };
                    (selectedPlan.trainings || []).forEach((tid, idx) => { s[(idx % 7) + 1].push(tid); });
                    return s;
                  })();
                  return [1, 2, 3, 4, 5, 6, 7].map(day => {
                    const dayTids = schedule[day] || [];
                    return (
                      <div key={day} className="bg-white/40 dark:bg-white/5 border border-white/50 dark:border-white/10 rounded-2xl overflow-hidden">
                        <div className="px-4 py-3 flex items-center gap-3 border-b border-white/30 dark:border-white/5 bg-white/30 dark:bg-white/[0.02]">
                          <span className="w-8 h-8 rounded-xl bg-brand-500/10 text-brand-500 flex items-center justify-center text-[11px] font-black">{dayNames[day].slice(0, 2).toUpperCase()}</span>
                          <h4 className="font-bold text-sm text-slate-700 dark:text-slate-200">{dayNames[day]}</h4>
                          <span className="text-[10px] text-slate-400 font-bold ml-auto">{dayTids.length > 0 ? `${dayTids.length} training${dayTids.length > 1 ? 's' : ''}` : 'Rest day'}</span>
                        </div>
                        {dayTids.length > 0 ? (
                          <div className="p-3 space-y-2">
                            {dayTids.map((tid, i) => {
                              const t = allPopulatedTrainings.find(tr => tr._id === tid);
                              const key = `plan-${day}-${tid}-${i}`;
                              const isExpanded = expandedPlanTrainings[key];
                              return t ? (
                                <div key={key} className="bg-white/50 dark:bg-black/10 rounded-xl border border-white/40 dark:border-white/5 overflow-hidden">
                                  <div onClick={() => setExpandedPlanTrainings(prev => ({ ...prev, [key]: !prev[key] }))}
                                    className="p-3 flex items-center justify-between cursor-pointer hover:bg-white/40 dark:hover:bg-white/[0.03] transition-colors">
                                    <div className="flex items-center gap-3">
                                      <div className="p-1.5 bg-brand-500/10 text-brand-500 rounded-lg"><Activity className="w-4 h-4" /></div>
                                      <div>
                                        <h5 className="font-bold text-sm text-slate-800 dark:text-white">{t.name}</h5>
                                        <p className="text-[9px] text-slate-400 font-bold uppercase tracking-widest mt-0.5">{formatDuration(t.est_time)} &bull; {t.exercises.length} exercises</p>
                                      </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                      <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold border ${getDifficultyColor(t.training_type)}`}>{t.training_type?.replace('_', ' ')}</span>
                                      <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`} />
                                    </div>
                                  </div>
                                  <AnimatePresence>
                                    {isExpanded && (
                                      <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                                        <div className="px-3 pb-3 space-y-2 border-t border-white/30 dark:border-white/5 pt-3">
                                          {t.description && <p className="text-xs text-slate-500 dark:text-slate-400 italic mb-2">{t.description}</p>}
                                          {t.exercises.map((ex, ei) => (
                                            <div key={ei} className="p-3 bg-white/50 dark:bg-black/20 rounded-xl border border-white/40 dark:border-white/5">
                                              <div className="flex items-center gap-2 mb-2">
                                                <Dumbbell className="w-3.5 h-3.5 text-brand-500" />
                                                <span className="font-bold text-sm text-slate-800 dark:text-white">{ex._exerciseDetails?.name || 'Unknown'}</span>
                                                <span className="text-[9px] text-slate-400 font-bold uppercase ml-auto">{(ex._exerciseDetails?.body_part || '').replace('_', ' ')}</span>
                                              </div>
                                              <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                                                {ex.sets.map((set, si) => (
                                                  <div key={si} className="flex items-center gap-1.5 p-1.5 bg-white/60 dark:bg-black/20 rounded-lg border border-white/40 dark:border-white/5">
                                                    <span className="w-5 h-5 rounded bg-slate-100 dark:bg-slate-800 text-[9px] font-bold text-slate-400 flex items-center justify-center">{si + 1}</span>
                                                    <span className="text-xs font-bold text-slate-800 dark:text-white">{set.volume}</span>
                                                    <span className="text-[9px] font-bold text-slate-400">{set.units}</span>
                                                  </div>
                                                ))}
                                              </div>
                                              {ex.rest_between_sets > 0 && <p className="text-[9px] text-slate-400 mt-1.5">Rest: {ex.rest_between_sets}s</p>}
                                              {ex.notes && <p className="text-[10px] text-slate-500 mt-1 italic">{ex.notes}</p>}
                                            </div>
                                          ))}
                                        </div>
                                      </motion.div>
                                    )}
                                  </AnimatePresence>
                                </div>
                              ) : (
                                <div key={key} className="p-2 bg-white/30 dark:bg-white/5 rounded-lg text-xs text-slate-400 italic">Training not found</div>
                              );
                            })}
                          </div>
                        ) : (
                          <div className="px-4 py-3 text-[10px] text-slate-400 italic flex items-center gap-2 ml-11">Rest day</div>
                        )}
                      </div>
                    );
                  });
                })()}
                {(!selectedPlan.trainings || selectedPlan.trainings.length === 0) && <p className="text-sm text-slate-400 text-center py-8">No trainings assigned to this plan.</p>}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* PLAN EDIT MODAL */}
      <AnimatePresence>
        {editingPlan && (
          <div className="fixed inset-0 z-[80] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setEditingPlan(null)} className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" />
            <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="w-full max-w-2xl bg-white/95 dark:bg-slate-900/95 glass-panel rounded-[2.5rem] relative z-10 flex flex-col max-h-[88vh] shadow-2xl border border-white/40 overflow-hidden">
              <div className="p-5 border-b border-slate-100 dark:border-white/5 flex justify-between items-center bg-white/50 dark:bg-white/5 backdrop-blur-sm">
                <div className="pl-3">
                  <h3 className="font-bold text-xl text-slate-800 dark:text-white drop-shadow-sm">Edit Plan</h3>
                  <p className="text-[10px] font-bold text-brand-600 dark:text-brand-400 uppercase tracking-[0.2em]">Modify Plan Details</p>
                </div>
                <button onClick={() => setEditingPlan(null)} className="p-2.5 hover:bg-black/5 dark:hover:bg-white/10 rounded-full transition-colors"><X className="w-5 h-5 text-slate-400" /></button>
              </div>
              <div className="flex-1 overflow-y-auto p-8 space-y-8">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 bg-brand-500/5 dark:bg-white/5 rounded-[2rem] border-2 border-dashed border-brand-500/10 backdrop-blur-sm">
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1 flex items-center gap-2"><Layers className="w-4 h-4 text-brand-500" /> Plan Name</label>
                    <input type="text" value={editingPlan.name} onChange={e => setEditingPlan({...editingPlan, name: e.target.value})}
                      className="w-full p-4 liquid-input rounded-2xl outline-none font-medium" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1 flex items-center gap-2"><Edit3 className="w-4 h-4 text-brand-500" /> Description</label>
                    <input type="text" value={editingPlan.description} onChange={e => setEditingPlan({...editingPlan, description: e.target.value})} placeholder="Optional"
                      className="w-full p-4 liquid-input rounded-2xl outline-none font-medium" />
                  </div>
                </div>
                <div className="flex items-center gap-3 px-1">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Public</label>
                  <button onClick={() => setEditingPlan({...editingPlan, is_public: !editingPlan.is_public})}
                    className={`w-12 h-6 rounded-full transition-all ${editingPlan.is_public ? 'bg-brand-500' : 'bg-slate-300 dark:bg-slate-700'}`}>
                    <div className={`w-5 h-5 rounded-full bg-white shadow-md transform transition-transform ${editingPlan.is_public ? 'translate-x-6' : 'translate-x-0.5'}`}></div>
                  </button>
                </div>
                <div className="space-y-4">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2 px-1"><Calendar className="w-4 h-4 text-brand-500" /> Weekly Schedule</label>
                  <div className="space-y-3">
                    {[1, 2, 3, 4, 5, 6, 7].map(day => {
                      const dayTrainings = editingPlan.schedule?.[day] || [];
                      return (
                        <div key={day} className="p-4 bg-white/40 dark:bg-white/5 rounded-2xl border border-white/50 dark:border-white/10 backdrop-blur-sm">
                          <div className="flex justify-between items-center mb-2">
                            <h4 className="font-bold text-sm text-slate-700 dark:text-slate-200 flex items-center gap-2">
                              <span className="w-7 h-7 rounded-lg bg-brand-500/10 text-brand-500 flex items-center justify-center text-[10px] font-black">{dayNames[day].slice(0, 2).toUpperCase()}</span>
                              {dayNames[day]}
                            </h4>
                            <button onClick={() => { setPickingForPlanDay(day); setPlanPickerSearch(''); }} className="flex items-center gap-1.5 text-brand-600 dark:text-brand-400 font-bold text-xs bg-brand-500/10 px-3 py-1.5 rounded-lg hover:bg-brand-500/20 transition-all active:scale-95"><Plus className="w-3.5 h-3.5" /> Add</button>
                          </div>
                          {dayTrainings.length > 0 ? (
                            <div className="space-y-2 mt-2">
                              {dayTrainings.map((tid, idx) => {
                                const t = allPopulatedTrainings.find(tr => tr._id === tid);
                                return t ? (
                                  <motion.div key={`${day}-${idx}`} initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                                    className="flex items-center justify-between p-3 bg-white/60 dark:bg-black/20 rounded-xl border border-white/40 dark:border-white/5 group">
                                    <div className="flex items-center gap-3">
                                      <div className="p-1.5 bg-brand-500/10 text-brand-500 rounded-lg"><Activity className="w-4 h-4" /></div>
                                      <div>
                                        <span className="font-bold text-sm text-slate-800 dark:text-white">{t.name}</span>
                                        <p className="text-[9px] text-slate-400 font-bold uppercase tracking-widest mt-0.5">{t.training_type} &bull; {formatDuration(t.est_time)}</p>
                                      </div>
                                    </div>
                                    <button onClick={() => setEditingPlan(prev => {
                                      if (!prev) return prev;
                                      const schedule = { ...prev.schedule };
                                      schedule[day] = schedule[day].filter((_, i) => i !== idx);
                                      return { ...prev, schedule };
                                    })} className="p-1.5 text-slate-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 rounded-lg transition-all opacity-0 group-hover:opacity-100"><Trash2 className="w-3.5 h-3.5" /></button>
                                  </motion.div>
                                ) : null;
                              })}
                            </div>
                          ) : (
                            <p className="text-[10px] text-slate-400 italic mt-1 ml-9">Rest day</p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
              <div className="p-6 bg-slate-50/80 dark:bg-black/20 backdrop-blur-md flex justify-end gap-3 border-t border-slate-100 dark:border-white/5">
                <button onClick={() => setEditingPlan(null)} className="px-6 py-2.5 text-slate-500 dark:text-slate-400 font-bold hover:text-slate-800 dark:hover:text-white transition-colors">Cancel</button>
                <button onClick={handleSaveEditPlan} disabled={!editingPlan.name}
                  className="liquid-btn liquid-btn-primary px-10 py-2.5 rounded-2xl font-bold flex items-center gap-2 shadow-lg shadow-brand-500/20 disabled:opacity-50 disabled:grayscale transition-all">
                  {isEditLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Save Changes
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* PLAN TRAINING PICKER MODAL */}
      <AnimatePresence>
        {pickingForPlanDay && editingPlan && (
          <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setPickingForPlanDay(null)} className="absolute inset-0 z-0 bg-slate-900/60 backdrop-blur-md" />
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-lg bg-white/95 dark:bg-slate-900/95 glass-panel rounded-[2rem] relative z-10 flex flex-col max-h-[70vh] shadow-2xl border border-white/40 overflow-hidden">
              <div className="p-5 border-b border-slate-100 dark:border-white/5 flex justify-between items-center bg-white/50 dark:bg-white/5 backdrop-blur-sm">
                <div className="pl-2">
                  <h3 className="font-bold text-lg text-slate-800 dark:text-white">Add Training — {dayNames[pickingForPlanDay]}</h3>
                  <p className="text-[10px] font-bold text-brand-600 dark:text-brand-400 uppercase tracking-[0.2em]">Select a workout to assign</p>
                </div>
                <button onClick={() => setPickingForPlanDay(null)} className="p-2.5 hover:bg-black/5 dark:hover:bg-white/10 rounded-full transition-colors"><X className="w-5 h-5 text-slate-400" /></button>
              </div>
              <div className="p-4 border-b border-slate-100 dark:border-white/5">
                <div className="relative">
                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input type="text" placeholder="Search workouts..." value={planPickerSearch} onChange={e => setPlanPickerSearch(e.target.value)}
                    className="w-full pl-11 pr-4 py-3 liquid-input rounded-xl outline-none font-medium text-sm" autoFocus />
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-2">
                {myTrainings
                  .filter(t => !planPickerSearch || t.name.toLowerCase().includes(planPickerSearch.toLowerCase()))
                  .map(training => (
                    <div key={training._id}
                      onClick={() => {
                        const day = pickingForPlanDay;
                        setEditingPlan(prev => {
                          if (!prev) return prev;
                          const schedule = { ...prev.schedule };
                          schedule[day] = [...(schedule[day] || []), training._id];
                          return { ...prev, schedule };
                        });
                        setPickingForPlanDay(null);
                      }}
                      className="p-4 rounded-2xl border border-slate-100 dark:border-white/5 hover:border-brand-500/30 hover:bg-brand-500/5 dark:hover:bg-brand-500/5 cursor-pointer flex justify-between items-center group transition-all">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-slate-50 dark:bg-slate-800 rounded-xl flex items-center justify-center text-slate-400 group-hover:text-brand-500 transition-colors"><Activity className="w-5 h-5" /></div>
                        <div>
                          <h4 className="font-bold text-sm text-slate-800 dark:text-white">{training.name}</h4>
                          <p className="text-[9px] text-slate-500 mt-1 uppercase font-bold tracking-[0.2em]">{formatDuration(training.est_time)} &bull; {training.training_type?.replace('_', ' ')}</p>
                        </div>
                      </div>
                      <div className="w-9 h-9 rounded-xl bg-brand-500/10 text-brand-500 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all scale-75 group-hover:scale-100"><Plus className="w-5 h-5" /></div>
                    </div>
                  ))}
                {myTrainings.filter(t => !planPickerSearch || t.name.toLowerCase().includes(planPickerSearch.toLowerCase())).length === 0 && (
                  <div className="text-center py-16 opacity-40">
                    <p className="text-xs font-bold uppercase tracking-widest">No workouts found</p>
                    <p className="text-[10px] mt-2">Create some workouts first to assign them to a plan.</p>
                  </div>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Recipe Detail Modal */}
      <AnimatePresence>
        {selectedRecipe && (() => {
          const macros = calculateMacros(selectedRecipe);
          const imageUrl = selectedRecipe.images?.[0] || `https://picsum.photos/seed/${selectedRecipe._id}/800/500`;
          return (
            <div className="fixed inset-0 z-[70] flex items-center justify-center p-4">
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setSelectedRecipe(null)}
                className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" />
              <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
                className="w-full max-w-4xl glass-panel bg-white/95 dark:bg-slate-900/95 backdrop-blur-3xl rounded-[2.5rem] relative z-10 flex flex-col max-h-[90vh] shadow-2xl overflow-hidden border border-white/50 dark:border-white/10">
                <div className="relative h-72 md:h-80 w-full shrink-0">
                  <img src={imageUrl} alt={selectedRecipe.name} className="w-full h-full object-cover"
                    onError={(e) => { e.target.src = 'https://picsum.photos/800/500?grayscale'; }} />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
                  <div className="absolute top-6 right-6 flex gap-2">
                    {myRecipes.some(r => r._id === selectedRecipe._id) && (
                    <>
                    <button onClick={() => handleStartEditRecipe(selectedRecipe)} className="p-2 bg-brand-500/70 hover:bg-brand-500 text-white rounded-full transition-colors backdrop-blur-md border border-white/10" title="Edit recipe">
                      <Edit3 className="w-5 h-5" />
                    </button>
                    <button onClick={() => handleDelete(selectedRecipe._id)} className="p-2 bg-red-500/70 hover:bg-red-500 text-white rounded-full transition-colors backdrop-blur-md border border-white/10" title="Delete recipe">
                      <Trash2 className="w-5 h-5" />
                    </button>
                    </>
                    )}
                    <button onClick={() => setSelectedRecipe(null)} className="p-2 bg-black/20 hover:bg-black/40 text-white rounded-full transition-colors backdrop-blur-md border border-white/10">
                      <X className="w-6 h-6" />
                    </button>
                  </div>
                  <div className="absolute bottom-0 left-0 w-full p-8 text-white">
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="flex flex-wrap gap-2 mb-3">
                      <span className="px-3 py-1 bg-white/20 backdrop-blur-md text-xs font-bold rounded-full border border-white/20">
                        {selectedRecipe.ingredients?.length || 0} ingredients
                      </span>
                      <span className="px-3 py-1 bg-white/20 backdrop-blur-md text-xs font-bold rounded-full border border-white/20">
                        {selectedRecipe.prepare_instruction?.length || 0} steps
                      </span>
                    </motion.div>
                    <h2 className="text-3xl md:text-4xl font-bold leading-tight drop-shadow-lg mb-2">{selectedRecipe.name}</h2>
                    {selectedRecipe._created_at && (
                      <p className="text-white/70 text-sm">Created {new Date(selectedRecipe._created_at).toLocaleDateString()}</p>
                    )}
                  </div>
                </div>
                <div className="flex-1 overflow-y-auto">
                  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="p-8 space-y-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="flex gap-4 p-4 bg-slate-50 dark:bg-white/5 rounded-2xl border border-slate-100 dark:border-white/5 items-center justify-around">
                        <div className="text-center"><p className="text-xs text-slate-400 font-bold uppercase mb-1">Cal/100g</p>
                          <div className="flex items-center gap-1.5 justify-center"><div className="p-1.5 bg-orange-100 dark:bg-orange-900/30 rounded-full text-orange-500"><Flame className="w-4 h-4" /></div><span className="text-lg font-bold text-slate-800 dark:text-white">{macros.calories}</span></div>
                        </div>
                        <div className="w-px h-10 bg-slate-200 dark:bg-white/10" />
                        <div className="text-center"><p className="text-xs text-slate-400 font-bold uppercase mb-1">Time</p>
                          <div className="flex items-center gap-1.5 justify-center"><div className="p-1.5 bg-brand-100 dark:bg-brand-900/30 rounded-full text-brand-500"><Clock className="w-4 h-4" /></div><span className="text-lg font-bold text-slate-800 dark:text-white">{formatTime(selectedRecipe.time_to_prepare)}</span></div>
                        </div>
                        <div className="w-px h-10 bg-slate-200 dark:bg-white/10" />
                        <div className="text-center"><p className="text-xs text-slate-400 font-bold uppercase mb-1">Likes</p>
                          <div className="flex items-center gap-1.5 justify-center">
                            <div className="p-1.5 bg-slate-100 dark:bg-slate-800 rounded-full text-slate-400"><Heart className="w-4 h-4" /></div>
                            <span className="text-lg font-bold text-slate-800 dark:text-white">{selectedRecipe.total_likes || 0}</span>
                          </div>
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-2">
                        <div className="p-3 bg-green-50 dark:bg-green-900/10 rounded-2xl border border-green-100 dark:border-green-500/10 text-center"><p className="text-[10px] text-green-600 dark:text-green-400 font-bold uppercase mb-1">Protein/100g</p><p className="text-xl font-bold text-slate-800 dark:text-white">{macros.protein}g</p></div>
                        <div className="p-3 bg-blue-50 dark:bg-blue-900/10 rounded-2xl border border-blue-100 dark:border-blue-500/10 text-center"><p className="text-[10px] text-blue-600 dark:text-blue-400 font-bold uppercase mb-1">Carbs/100g</p><p className="text-xl font-bold text-slate-800 dark:text-white">{macros.carbs}g</p></div>
                        <div className="p-3 bg-purple-50 dark:bg-purple-900/10 rounded-2xl border border-purple-100 dark:border-purple-500/10 text-center"><p className="text-[10px] text-purple-600 dark:text-purple-400 font-bold uppercase mb-1">Fat/100g</p><p className="text-xl font-bold text-slate-800 dark:text-white">{macros.fat}g</p></div>
                      </div>
                    </div>
                    <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
                      <div className="lg:col-span-2">
                        <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2"><ChefHat className="w-5 h-5 text-brand-500" /> Ingredients</h3>
                        <ul className="space-y-3">
                          {selectedRecipe.ingredients?.map((item, i) => (
                            <li key={i} className="flex items-start gap-3 p-3 bg-white/50 dark:bg-white/5 rounded-xl border border-slate-100 dark:border-white/5">
                              <div className="mt-0.5 p-0.5 bg-brand-500 rounded-full"><CheckCircle2 className="w-3 h-3 text-white" /></div>
                              <span className="text-sm text-slate-700 dark:text-slate-300 font-medium leading-relaxed">
                                {getIngredientName(item.ingredient_id)} — {item.quantity} {item.capacity}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="lg:col-span-3">
                        <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2"><ArrowRight className="w-5 h-5 text-brand-500" /> Instructions</h3>
                        <div className="space-y-6">
                          {selectedRecipe.prepare_instruction?.map((step, i) => (
                            <div key={i} className="flex gap-4 group">
                              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 font-bold flex items-center justify-center text-sm border border-slate-200 dark:border-white/10 group-hover:bg-brand-500 group-hover:text-white transition-colors duration-300">{i + 1}</div>
                              <p className="flex-1 text-slate-600 dark:text-slate-300 leading-relaxed pt-1 border-b border-slate-100 dark:border-white/5 pb-6 last:border-0 last:pb-0">{step}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                </div>
              </motion.div>
            </div>
          );
        })()}
      </AnimatePresence>

      {/* Recipe Edit Modal */}
      <AnimatePresence>
        {editingRecipe && (
          <div className="fixed inset-0 z-[80] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setEditingRecipe(null)}
              className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" />
            <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="w-full max-w-3xl glass-panel bg-white/95 dark:bg-slate-900/95 backdrop-blur-3xl rounded-[2.5rem] relative z-10 flex flex-col max-h-[90vh] shadow-2xl overflow-hidden border border-white/50 dark:border-white/10">
              <div className="p-8 border-b border-slate-200 dark:border-white/10 flex justify-between items-center">
                <h2 className="text-2xl font-bold text-slate-800 dark:text-white flex items-center gap-3"><Edit3 className="w-6 h-6 text-brand-500" /> Edit Recipe</h2>
                <button onClick={() => setEditingRecipe(null)} className="p-2 hover:bg-slate-100 dark:hover:bg-white/10 rounded-full transition-colors"><X className="w-5 h-5" /></button>
              </div>
              <div className="flex-1 overflow-y-auto p-8 space-y-6">
                {/* Prep time */}
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 block">Prep Time (minutes)</label>
                  <div className="flex items-center gap-2">
                    <button type="button" onClick={() => setEditingRecipe(prev => ({ ...prev, time_to_prepare: Math.max(60, (prev.time_to_prepare || 60) - 300) }))}
                      className="w-10 h-10 flex items-center justify-center rounded-xl liquid-input text-slate-500 hover:text-brand-500 hover:bg-brand-500/10 transition-colors shrink-0"><Minus className="w-4 h-4" /></button>
                    <input type="text" inputMode="numeric" value={Math.round((editingRecipe.time_to_prepare || 0) / 60)}
                      onChange={(e) => setEditingRecipe({ ...editingRecipe, time_to_prepare: Math.max(1, parseInt(e.target.value) || 1) * 60 })}
                      className="flex-1 p-3 liquid-input rounded-2xl text-slate-800 dark:text-white outline-none font-medium text-center" />
                    <button type="button" onClick={() => setEditingRecipe(prev => ({ ...prev, time_to_prepare: (prev.time_to_prepare || 0) + 300 }))}
                      className="w-10 h-10 flex items-center justify-center rounded-xl liquid-input text-slate-500 hover:text-brand-500 hover:bg-brand-500/10 transition-colors shrink-0"><Plus className="w-4 h-4" /></button>
                  </div>
                </div>

                {/* Ingredients */}
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3 block">
                    Ingredients ({editingRecipe.ingredients.length})
                  </label>
                  <div className="space-y-3">
                    {editingRecipe.ingredients.map((ing, i) => {
                      const selectedName = (() => {
                        if (!ing.ingredient_id) return null;
                        const found = allIngredients.find(a => (a.id || a._id) === ing.ingredient_id);
                        return found?.name || ingredientMap[ing.ingredient_id]?.name || null;
                      })();
                      const isOpen = editIngDropdownOpen[i] || false;
                      const searchTerm = editIngSearchTerms[i]?.toLowerCase() || '';
                      const filteredIngredients = searchTerm
                        ? allIngredients.filter(a => a.name.toLowerCase().includes(searchTerm))
                        : allIngredients;

                      return (
                        <div key={i} className="p-4 bg-white/40 dark:bg-white/5 rounded-2xl border border-white/50 dark:border-white/10 space-y-3">
                          {/* Ingredient Selector */}
                          <div className="relative" ref={(el) => (editIngDropdownRefs.current[i] = el)}>
                            <button type="button"
                              onClick={() => setEditIngDropdownOpen(prev => ({ ...prev, [i]: !isOpen }))}
                              className="w-full flex items-center justify-between p-3 liquid-input rounded-xl text-left">
                              <span className={`text-sm font-medium ${selectedName ? 'text-slate-800 dark:text-white' : 'text-slate-400'}`}>
                                {selectedName || 'Select ingredient...'}
                              </span>
                              <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
                            </button>

                            <AnimatePresence>
                              {isOpen && (
                                <motion.div initial={{ opacity: 0, y: -5 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -5 }}
                                  className="absolute top-full left-0 right-0 mt-1 z-20 glass-panel bg-white/95 dark:bg-slate-900/95 rounded-xl overflow-hidden shadow-xl border border-white/50 dark:border-white/10">
                                  <div className="p-2 border-b border-slate-100 dark:border-white/10">
                                    <div className="relative">
                                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
                                      <input type="text" placeholder="Search ingredients..."
                                        value={editIngSearchTerms[i] || ''}
                                        onChange={(e) => setEditIngSearchTerms(prev => ({ ...prev, [i]: e.target.value }))}
                                        className="w-full pl-9 pr-3 py-2 text-sm liquid-input rounded-lg outline-none"
                                        autoFocus />
                                    </div>
                                  </div>
                                  <div className="max-h-40 overflow-y-auto">
                                    {filteredIngredients.length > 0 ? (
                                      filteredIngredients.map((ingredient) => {
                                        const ingId = ingredient.id || ingredient._id;
                                        return (
                                          <button type="button" key={ingId}
                                            onClick={() => {
                                              const updated = [...editingRecipe.ingredients];
                                              updated[i] = { ...updated[i], ingredient_id: ingId };
                                              setEditingRecipe({ ...editingRecipe, ingredients: updated });
                                              setEditIngDropdownOpen(prev => ({ ...prev, [i]: false }));
                                              setEditIngSearchTerms(prev => ({ ...prev, [i]: '' }));
                                            }}
                                            className="w-full px-4 py-2.5 text-left hover:bg-brand-50 dark:hover:bg-brand-900/20 text-sm text-slate-700 dark:text-slate-300 font-medium transition-colors flex justify-between items-center">
                                            <span>{ingredient.name}</span>
                                            {ingredient.macro_per_hundred && (
                                              <span className="text-[10px] text-slate-400 font-bold">
                                                {Math.round(ingredient.macro_per_hundred.calories)} kcal
                                              </span>
                                            )}
                                          </button>
                                        );
                                      })
                                    ) : (
                                      <div className="px-4 py-3 text-sm text-slate-400 text-center">No ingredients found</div>
                                    )}
                                  </div>
                                </motion.div>
                              )}
                            </AnimatePresence>
                          </div>

                          {/* Quantity & Unit & Remove */}
                          <div className="flex items-center gap-2">
                            <button type="button" onClick={() => {
                              const updated = [...editingRecipe.ingredients];
                              updated[i] = { ...updated[i], quantity: Math.max(0.1, (ing.quantity || 0.1) - 1) };
                              setEditingRecipe({ ...editingRecipe, ingredients: updated });
                            }} className="w-8 h-8 flex items-center justify-center rounded-lg liquid-input text-slate-400 hover:text-brand-500 hover:bg-brand-500/10 transition-colors shrink-0"><Minus className="w-3 h-3" /></button>
                            <input type="text" inputMode="decimal" value={ing.quantity}
                              onChange={(e) => {
                                const updated = [...editingRecipe.ingredients];
                                updated[i] = { ...updated[i], quantity: parseFloat(e.target.value) || 0 };
                                setEditingRecipe({ ...editingRecipe, ingredients: updated });
                              }}
                              className="w-16 p-2.5 liquid-input rounded-xl text-sm text-slate-800 dark:text-white outline-none font-medium text-center"
                              placeholder="Qty" />
                            <button type="button" onClick={() => {
                              const updated = [...editingRecipe.ingredients];
                              updated[i] = { ...updated[i], quantity: (ing.quantity || 0) + 1 };
                              setEditingRecipe({ ...editingRecipe, ingredients: updated });
                            }} className="w-8 h-8 flex items-center justify-center rounded-lg liquid-input text-slate-400 hover:text-brand-500 hover:bg-brand-500/10 transition-colors shrink-0"><Plus className="w-3 h-3" /></button>
                            <div className="relative">
                              <select value={ing.capacity}
                                onChange={(e) => {
                                  const updated = [...editingRecipe.ingredients];
                                  updated[i] = { ...updated[i], capacity: e.target.value };
                                  setEditingRecipe({ ...editingRecipe, ingredients: updated });
                                }}
                                className="p-2.5 text-sm liquid-input rounded-xl text-slate-800 dark:text-white font-medium outline-none appearance-none cursor-pointer pr-7">
                                {CAPACITY_UNITS.map(u => <option key={u.value} value={u.value}>{u.label}</option>)}
                              </select>
                              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-400 pointer-events-none" />
                            </div>
                            <button type="button" onClick={() => {
                              const updated = editingRecipe.ingredients.filter((_, idx) => idx !== i);
                              setEditingRecipe({ ...editingRecipe, ingredients: updated });
                              const ns = { ...editIngSearchTerms }; delete ns[i];
                              const nd = { ...editIngDropdownOpen }; delete nd[i];
                              setEditIngSearchTerms(ns);
                              setEditIngDropdownOpen(nd);
                            }} className="p-2 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-full text-red-500 transition-colors">
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                    <button type="button"
                      onClick={() => setEditingRecipe({ ...editingRecipe, ingredients: [...editingRecipe.ingredients, { ingredient_id: '', capacity: 'g', quantity: 100 }] })}
                      className="w-full p-2.5 rounded-xl border-2 border-dashed border-slate-200 dark:border-white/10 text-slate-400 hover:border-brand-500 hover:text-brand-500 transition-colors text-sm font-bold flex items-center justify-center gap-2">
                      <Plus className="w-4 h-4" /> Add Ingredient
                    </button>
                  </div>
                </div>

                {/* Instructions */}
                <div>
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 block">Instructions</label>
                  <div className="space-y-3">
                    {editingRecipe.prepare_instruction.map((step, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <span className="flex-shrink-0 w-7 h-7 rounded-full bg-brand-500 text-white text-xs font-bold flex items-center justify-center mt-2">{i + 1}</span>
                        <textarea value={step} rows={2}
                          onChange={(e) => {
                            const updated = [...editingRecipe.prepare_instruction];
                            updated[i] = e.target.value;
                            setEditingRecipe({ ...editingRecipe, prepare_instruction: updated });
                          }}
                          className="flex-1 p-3 liquid-input rounded-xl text-sm text-slate-800 dark:text-white outline-none resize-none" />
                        <button onClick={() => {
                          const updated = editingRecipe.prepare_instruction.filter((_, idx) => idx !== i);
                          setEditingRecipe({ ...editingRecipe, prepare_instruction: updated });
                        }} className="p-1.5 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-full text-red-500 transition-colors mt-2">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                    <button onClick={() => setEditingRecipe({ ...editingRecipe, prepare_instruction: [...editingRecipe.prepare_instruction, ''] })}
                      className="w-full p-2.5 rounded-xl border-2 border-dashed border-slate-200 dark:border-white/10 text-slate-400 hover:border-brand-500 hover:text-brand-500 transition-colors text-sm font-bold flex items-center justify-center gap-2">
                      <Plus className="w-4 h-4" /> Add Step
                    </button>
                  </div>
                </div>
              </div>
              <div className="p-6 border-t border-slate-200 dark:border-white/10 flex justify-end gap-3">
                <button onClick={() => setEditingRecipe(null)} className="px-6 py-2.5 rounded-2xl font-bold text-slate-500 hover:bg-slate-100 dark:hover:bg-white/10 transition-colors">Cancel</button>
                <button onClick={handleSaveEditRecipe} disabled={isEditLoading}
                  className="liquid-btn liquid-btn-primary px-10 py-2.5 rounded-2xl font-bold flex items-center gap-2 shadow-lg shadow-brand-500/20 disabled:opacity-50 disabled:grayscale transition-all">
                  {isEditLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Save Changes
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
