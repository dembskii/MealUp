'use client';

import { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import {
  TrainingType, SetUnit, BodyPart, Advancement
} from '../data/types';
import { generateWorkout } from '../services/geminiService';
import {
  getExercises,
  getTrainings, createTraining, deleteTraining, updateTraining,
  getWorkoutPlans, createWorkoutPlan, deleteWorkoutPlan, updateWorkoutPlan,
  addTrainingToPlan, removeTrainingFromPlan,
  getTrainingWithExercises,
} from '../services/workoutService';
import {
  likeWorkout, unlikeWorkout, getLikedWorkouts, checkWorkoutsLikedBulk,
} from '../services/userService';
import {
  Dumbbell, Clock, Activity, Plus, Minus, Sparkles, X,
  Loader2, Search, Filter, ChevronDown, Edit3,
  Save, Trash2, Calendar, LayoutGrid, Layers, Info, Hash, Type, Heart, CheckCircle2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

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
        className="w-full p-4 rounded-2xl liquid-input text-sm font-medium outline-none cursor-pointer flex items-center justify-between gap-2 text-slate-800 dark:text-white hover:bg-white/50 dark:hover:bg-white/10 transition-colors">
        <span className="truncate">{selected?.label || placeholder || 'Select...'}</span>
        <ChevronDown className={`w-4 h-4 text-slate-400 shrink-0 transition-transform duration-200 ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && typeof document !== 'undefined' && createPortal(
        <div ref={menuRef} style={{ position: 'fixed', top: pos.top, left: pos.left, width: pos.width, zIndex: 9999 }}>
          <motion.div initial={{ opacity: 0, y: -4, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ duration: 0.15 }}
            className="bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl rounded-xl shadow-xl border border-white/50 dark:border-white/10 overflow-hidden">
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
          </motion.div>
        </div>,
        document.body
      )}
    </div>
  );
}

// Helper: build an exercisesMap lookup from an array of exercises
const buildExerciseMap = (exercisesArr) => {
  const map = {};
  for (const ex of exercisesArr) {
    map[ex._id || ex.id] = ex;
  }
  return map;
};

// Populate training exercises with details from the map
const populateTraining = (training, exercisesMap) => {
  return {
    ...training,
    exercises: training.exercises.map(ex => ({
      ...ex,
      _exerciseDetails: exercisesMap[ex.exercise_id] || {
        _id: ex.exercise_id, name: 'Unknown Exercise',
        body_part: BodyPart.FULL_BODY, advancement: Advancement.BEGINNER,
        category: 'custom'
      }
    }))
  };
};

export default function Workouts() {
  // ---------- exercises from API ----------
  const [exercisesDB, setExercisesDB] = useState({});
  const [allExercises, setAllExercises] = useState([]);
  const [exercisesLoaded, setExercisesLoaded] = useState(false);

  const [activeTab, setActiveTab] = useState('plans');
  const [trainings, setTrainings] = useState([]);
  const [plans, setPlans] = useState([]);
  const [currentUserId, setCurrentUserId] = useState(null);
  const [isAiModalOpen, setIsAiModalOpen] = useState(false);
  const [isWorkoutCreatorOpen, setIsWorkoutCreatorOpen] = useState(false);
  const [isPlanCreatorOpen, setIsPlanCreatorOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [selectedTraining, setSelectedTraining] = useState(null);
  const [editingTraining, setEditingTraining] = useState(null);
  const [editingPlan, setEditingPlan] = useState(null);
  const [expandedPlanTrainings, setExpandedPlanTrainings] = useState({});
  const [prompt, setPrompt] = useState('');
  const [workoutSearchQuery, setWorkoutSearchQuery] = useState('');
  const [planSearchQuery, setPlanSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [showPlanFilters, setShowPlanFilters] = useState(false);
  const [showWorkoutFilters, setShowWorkoutFilters] = useState(false);
  const [filterBodyPart, setFilterBodyPart] = useState('ALL');
  const [filterMaxTime, setFilterMaxTime] = useState(120);
  const [filterTrainingType, setFilterTrainingType] = useState('ALL');
  const [planFilterFrequency, setPlanFilterFrequency] = useState('ALL');
  const [planFilterDuration, setPlanFilterDuration] = useState(300);
  const [newTraining, setNewTraining] = useState({
    name: '', description: '',
    training_type: TrainingType.CUSTOM, est_time: 3600, exercises: []
  });
  const dayNames = ['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const emptySchedule = () => ({ 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [] });
  const [newPlan, setNewPlan] = useState({
    name: '', description: '', schedule: emptySchedule()
  });
  const [pickingForPlanDay, setPickingForPlanDay] = useState(null);
  const [showExercisePicker, setShowExercisePicker] = useState(false);
  const [pickerSearch, setPickerSearch] = useState('');
  const [pickerBodyPart, setPickerBodyPart] = useState('ALL');
  const [likedWorkoutIds, setLikedWorkoutIds] = useState(new Set());
  const [likingInProgress, setLikingInProgress] = useState(new Set());
  const [sessionCreatedIds, setSessionCreatedIds] = useState(new Set());

  // ===================== FETCH DATA ON MOUNT =====================
  const fetchExercises = useCallback(async () => {
    try {
      const data = await getExercises({ limit: 500 });
      setAllExercises(data);
      setExercisesDB(buildExerciseMap(data));
      setExercisesLoaded(true);
    } catch (err) {
      console.error('Failed to fetch exercises:', err);
    }
  }, []);

  const fetchTrainings = useCallback(async (exMap) => {
    try {
      const data = await getTrainings({ limit: 500 });
      const map = exMap || exercisesDB;
      setTrainings(data.map(t => populateTraining(t, map)));
    } catch (err) {
      console.error('Failed to fetch trainings:', err);
    }
  }, [exercisesDB]);

  const fetchPlans = useCallback(async () => {
    try {
      const data = await getWorkoutPlans({ limit: 500 });
      setPlans(data);
    } catch (err) {
      console.error('Failed to fetch workout plans:', err);
    }
  }, []);

  useEffect(() => {
    (async () => {
      setInitialLoading(true);
      try {
        // Fetch current user
        try {
          const res = await fetch('http://localhost:8000/api/v1/auth/me', { credentials: 'include' });
          if (res.ok) {
            const auth = await res.json();
            setCurrentUserId(auth.internal_uid || null);
          }
        } catch { /* not logged in */ }

        const exercises = await getExercises({ limit: 500 });
        setAllExercises(exercises);
        const map = buildExerciseMap(exercises);
        setExercisesDB(map);
        setExercisesLoaded(true);

        const [trainingsData, plansData] = await Promise.all([
          getTrainings({ limit: 500 }),
          getWorkoutPlans({ limit: 500 }),
        ]);
        setTrainings(trainingsData.map(t => populateTraining(t, map)));
        setPlans(plansData);

        // Fetch liked workout status
        try {
          const res = await fetch('http://localhost:8000/api/v1/auth/me', { credentials: 'include' });
          if (res.ok) {
            const auth = await res.json();
            const uid = auth.internal_uid;
            if (uid && trainingsData.length > 0) {
              const ids = trainingsData.map(t => t._id);
              const { results } = await checkWorkoutsLikedBulk(uid, ids);
              setLikedWorkoutIds(new Set(Object.entries(results).filter(([, v]) => v).map(([k]) => k)));
            }
          }
        } catch (e) {
          console.error('Failed to fetch liked workouts status:', e);
        }
      } catch (err) {
        console.error('Failed to load workout data:', err);
      } finally {
        setInitialLoading(false);
      }
    })();
  }, []);

  const handleGenerateAi = async () => {
    if (!prompt.trim()) return;
    setIsLoading(true);
    try {
      const generated = await generateWorkout(prompt);
      if (generated) {
        // Try to persist via API
        const payload = {
          name: generated.name,
          exercises: generated.exercises,
          est_time: generated.est_time || 3600,
          training_type: generated.training_type || TrainingType.CUSTOM,
          description: generated.description || null,
        };
        try {
          const saved = await createTraining(payload);
          setTrainings(prev => [populateTraining(saved, exercisesDB), ...prev]);
          if (saved._id) setSessionCreatedIds(prev => new Set(prev).add(saved._id));
        } catch {
          // Fallback: just show locally
          setTrainings(prev => [populateTraining(generated, exercisesDB), ...prev]);
        }
        setIsAiModalOpen(false);
        setPrompt('');
        setActiveTab('workouts');
      }
    } catch (err) {
      console.error('AI generation failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddExerciseToTraining = (exerciseId) => {
    const newEx = {
      exercise_id: exerciseId,
      sets: [{ volume: 10, units: SetUnit.REPS }, { volume: 10, units: SetUnit.REPS }, { volume: 10, units: SetUnit.REPS }],
      rest_between_sets: 60, notes: ''
    };
    if (editingTraining) {
      setEditingTraining(prev => ({ ...prev, exercises: [...(prev.exercises || []), newEx] }));
    } else {
      setNewTraining(prev => ({ ...prev, exercises: [...(prev.exercises || []), newEx] }));
    }
    setShowExercisePicker(false);
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

  const togglePlanTraining = (tid) => {
    setExpandedPlanTrainings(prev => ({ ...prev, [tid]: !prev[tid] }));
  };

  const handleRemoveExercise = (index) => {
    setNewTraining(prev => ({ ...prev, exercises: prev.exercises?.filter((_, i) => i !== index) }));
  };

  const handleUpdateSet = (exIndex, setIndex, field, value) => {
    setNewTraining(prev => {
      const exercises = [...(prev.exercises || [])];
      const sets = [...exercises[exIndex].sets];
      sets[setIndex] = { ...sets[setIndex], [field]: value };
      exercises[exIndex] = { ...exercises[exIndex], sets };
      return { ...prev, exercises };
    });
  };

  const handleAddSet = (exIndex) => {
    setNewTraining(prev => {
      const exercises = [...(prev.exercises || [])];
      const ex = exercises[exIndex];
      exercises[exIndex] = { ...ex, sets: [...ex.sets, { volume: 10, units: SetUnit.REPS }] };
      return { ...prev, exercises };
    });
  };

  const handleRemoveSet = (exIndex, setIndex) => {
    setNewTraining(prev => {
      const exercises = [...(prev.exercises || [])];
      const ex = exercises[exIndex];
      if (ex.sets.length <= 1) return prev;
      exercises[exIndex] = { ...ex, sets: ex.sets.filter((_, i) => i !== setIndex) };
      return { ...prev, exercises };
    });
  };

  const handleSaveTraining = async () => {
    if (!newTraining.name || !newTraining.exercises?.length) return;
    setIsLoading(true);
    try {
      const payload = {
        name: newTraining.name,
        exercises: newTraining.exercises.map(ex => ({
          exercise_id: ex.exercise_id,
          sets: ex.sets,
          rest_between_sets: ex.rest_between_sets || 60,
          notes: ex.notes || null,
        })),
        est_time: newTraining.est_time || 3600,
        training_type: newTraining.training_type || TrainingType.CUSTOM,
        description: newTraining.description || null,
      };
      const saved = await createTraining(payload);
      setTrainings(prev => [populateTraining(saved, exercisesDB), ...prev]);
      if (saved._id) setSessionCreatedIds(prev => new Set(prev).add(saved._id));
      setIsWorkoutCreatorOpen(false);
      setNewTraining({ name: '', description: '', training_type: TrainingType.CUSTOM, est_time: 3600, exercises: [] });
    } catch (err) {
      console.error('Failed to save training:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddToPlanSchedule = (trainingId) => {
    if (typeof pickingForPlanDay === 'string' && pickingForPlanDay.startsWith('edit-')) {
      const day = parseInt(pickingForPlanDay.split('-')[1]);
      setEditingPlan(prev => {
        if (!prev) return prev;
        const schedule = { ...prev.schedule };
        schedule[day] = [...(schedule[day] || []), trainingId];
        return { ...prev, schedule };
      });
      setPickingForPlanDay(null);
    } else if (pickingForPlanDay !== null) {
      setNewPlan(prev => {
        const schedule = { ...prev.schedule };
        schedule[pickingForPlanDay] = [...(schedule[pickingForPlanDay] || []), trainingId];
        return { ...prev, schedule };
      });
      setPickingForPlanDay(null);
    }
  };

  const handleRemoveFromSchedule = (day, index) => {
    setNewPlan(prev => {
      const schedule = { ...prev.schedule };
      schedule[day] = schedule[day].filter((_, i) => i !== index);
      return { ...prev, schedule };
    });
  };

  const scheduleTrainingIds = useMemo(() => {
    if (!newPlan.schedule) return [];
    return Object.values(newPlan.schedule).flat();
  }, [newPlan.schedule]);

  const handleSavePlan = async () => {
    if (!newPlan.name || !scheduleTrainingIds.length) return;
    setIsLoading(true);
    try {
      const payload = {
        name: newPlan.name,
        description: newPlan.description || null,
        trainings: scheduleTrainingIds,
        schedule: newPlan.schedule,
        is_public: false,
      };
      const saved = await createWorkoutPlan(payload);
      setPlans(prev => [saved, ...prev]);
      setIsPlanCreatorOpen(false);
      setNewPlan({ name: '', description: '', schedule: emptySchedule() });
    } catch (err) {
      console.error('Failed to save plan:', err);
    } finally {
      setIsLoading(false);
    }
  };

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
    setIsLoading(true);
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
      setTrainings(prev => prev.map(t => t._id === saved._id ? populateTraining(saved, exercisesDB) : t));
      setEditingTraining(null);
    } catch (err) {
      console.error('Failed to update training:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteTraining = async (trainingId) => {
    if (!confirm('Delete this workout?')) return;
    try {
      await deleteTraining(trainingId);
      setTrainings(prev => prev.filter(t => t._id !== trainingId));
      setSelectedTraining(null);
    } catch (err) {
      console.error('Failed to delete training:', err);
    }
  };

  const handleStartEditPlan = (plan) => {
    // Use saved schedule if available, otherwise distribute round-robin
    let schedule;
    if (plan.schedule && typeof plan.schedule === 'object') {
      schedule = { 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [] };
      Object.entries(plan.schedule).forEach(([day, tids]) => {
        schedule[parseInt(day)] = [...(tids || [])];
      });
    } else {
      schedule = { 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [] };
      const trainingsList = plan.trainings || [];
      trainingsList.forEach((tid, idx) => {
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

  const editPlanTrainingIds = useMemo(() => {
    if (!editingPlan?.schedule) return [];
    return Object.values(editingPlan.schedule).flat();
  }, [editingPlan?.schedule]);

  const handleSaveEditPlan = async () => {
    if (!editingPlan || !editingPlan.name) return;
    setIsLoading(true);
    try {
      const payload = {
        name: editingPlan.name,
        description: editingPlan.description || null,
        trainings: editPlanTrainingIds,
        schedule: editingPlan.schedule,
        is_public: editingPlan.is_public,
      };
      const saved = await updateWorkoutPlan(editingPlan._id, payload);
      setPlans(prev => prev.map(p => p._id === saved._id ? saved : p));
      setEditingPlan(null);
    } catch (err) {
      console.error('Failed to update plan:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeletePlan = async (planId) => {
    if (!confirm('Delete this plan?')) return;
    try {
      await deleteWorkoutPlan(planId);
      setPlans(prev => prev.filter(p => p._id !== planId));
      setSelectedPlan(null);
    } catch (err) {
      console.error('Failed to delete plan:', err);
    }
  };

  const handleToggleLike = async (e, trainingId) => {
    e.stopPropagation();
    if (!currentUserId || likingInProgress.has(trainingId)) return;
    setLikingInProgress(prev => new Set(prev).add(trainingId));
    try {
      const isLiked = likedWorkoutIds.has(trainingId);
      if (isLiked) {
        await unlikeWorkout(currentUserId, trainingId);
        setLikedWorkoutIds(prev => { const s = new Set(prev); s.delete(trainingId); return s; });
      } else {
        await likeWorkout(currentUserId, trainingId);
        setLikedWorkoutIds(prev => new Set(prev).add(trainingId));
      }
    } catch (err) {
      console.error('Failed to toggle like:', err);
    } finally {
      setLikingInProgress(prev => { const s = new Set(prev); s.delete(trainingId); return s; });
    }
  };

  const formatDuration = (seconds) => `${Math.floor(seconds / 60)} min`;

  // Own training IDs: trainings created by the current user (based on creator_id from API)
  const ownTrainingIds = useMemo(() => {
    if (!currentUserId) return new Set();
    const fromApi = trainings
      .filter(t => t.creator_id === currentUserId)
      .map(t => t._id);
    return new Set([...fromApi, ...sessionCreatedIds]);
  }, [trainings, currentUserId, sessionCreatedIds]);

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

  const filteredTrainings = useMemo(() => {
    return trainings.filter(t => {
      if (workoutSearchQuery && !t.name.toLowerCase().includes(workoutSearchQuery.toLowerCase())) return false;
      if (t.est_time / 60 > filterMaxTime) return false;
      if (filterBodyPart !== 'ALL' && !t.exercises.some(ex => ex._exerciseDetails?.body_part === filterBodyPart)) return false;
      if (filterTrainingType !== 'ALL' && t.training_type !== filterTrainingType) return false;
      return true;
    });
  }, [trainings, workoutSearchQuery, filterMaxTime, filterBodyPart, filterTrainingType]);

  const filteredPlans = useMemo(() => {
    return plans.filter(p => {
      if (planSearchQuery && !p.name.toLowerCase().includes(planSearchQuery.toLowerCase())) return false;
      const frequency = p.trainings?.length || 0;
      if (planFilterFrequency !== 'ALL' && frequency !== planFilterFrequency) return false;
      const totalDuration = (p.trainings || []).reduce((acc, tid) => {
        const t = trainings.find(tr => tr._id === tid);
        return acc + (t ? t.est_time / 60 : 0);
      }, 0);
      if (totalDuration > planFilterDuration) return false;
      return true;
    });
  }, [plans, planSearchQuery, planFilterFrequency, planFilterDuration, trainings]);

  const filteredExercisesForPicker = useMemo(() => {
    return allExercises.filter(ex => {
      const matchesName = ex.name.toLowerCase().includes(pickerSearch.toLowerCase());
      const matchesBody = pickerBodyPart === 'ALL' || ex.body_part === pickerBodyPart;
      return matchesName && matchesBody;
    });
  }, [allExercises, pickerSearch, pickerBodyPart]);

  return (
    <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="p-6 md:p-10">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h2 className="text-3xl font-bold text-slate-800 dark:text-white drop-shadow-sm">Training Hub</h2>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Manage plans and workouts.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => { if (activeTab === 'plans') setIsPlanCreatorOpen(true); else setIsWorkoutCreatorOpen(true); }}
            className="liquid-btn liquid-btn-secondary px-5 py-3 rounded-2xl flex items-center gap-2 font-semibold shadow-sm">
            <Plus className="w-4 h-4" /><span>Create {activeTab === 'plans' ? 'Plan' : 'Workout'}</span>
          </button>
          <button onClick={() => setIsAiModalOpen(true)}
            className="liquid-btn liquid-btn-primary px-5 py-3 rounded-2xl flex items-center gap-2 font-semibold shadow-lg shadow-brand-500/20">
            <Sparkles className="w-4 h-4 text-white" /><span>AI Trainer</span>
          </button>
        </div>
      </div>

      <div className="flex justify-center mb-8">
        <div className="bg-slate-200/50 dark:bg-slate-800/50 p-1.5 rounded-2xl flex gap-1 shadow-inner border border-white/20 dark:border-white/5">
          <button onClick={() => setActiveTab('plans')}
            className={`px-5 md:px-6 py-2.5 rounded-xl font-bold text-sm transition-all flex items-center gap-2 ${activeTab === 'plans' ? 'bg-white dark:bg-slate-700 text-brand-600 dark:text-brand-400 shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700'}`}>
            <Layers className="w-4 h-4" /> Plans
          </button>
          <button onClick={() => setActiveTab('workouts')}
            className={`px-5 md:px-6 py-2.5 rounded-xl font-bold text-sm transition-all flex items-center gap-2 ${activeTab === 'workouts' ? 'bg-white dark:bg-slate-700 text-brand-600 dark:text-brand-400 shadow-sm' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700'}`}>
            <LayoutGrid className="w-4 h-4" /> Workouts
          </button>
        </div>
      </div>

      {/* PLANS TAB */}
      {activeTab === 'plans' && (
        <div className="space-y-6">
          <div className="space-y-4">
            <div className="glass-panel p-2 rounded-2xl flex flex-col md:flex-row gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
                <input type="text" value={planSearchQuery} onChange={(e) => setPlanSearchQuery(e.target.value)} placeholder="Search workout plans..."
                  className="w-full pl-12 pr-4 py-3 bg-transparent text-slate-800 dark:text-white placeholder-slate-400 outline-none font-medium" />
              </div>
              <button onClick={() => setShowPlanFilters(!showPlanFilters)}
                className={`px-6 py-3 rounded-xl flex items-center gap-2 font-bold transition-all ${showPlanFilters ? 'bg-slate-800 text-white shadow-lg' : 'bg-white/50 dark:bg-white/5 text-slate-600 hover:bg-white/80'}`}>
                <Filter className="w-4 h-4" /> Filters
              </button>
            </div>
            <AnimatePresence>
              {showPlanFilters && (
                <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                  <div className="glass-panel rounded-2xl p-6 grid grid-cols-1 md:grid-cols-3 gap-8 border-dashed">
                    <div className="space-y-3">
                      <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2 ml-1"><Calendar className="w-3 h-3" /> Frequency (Days / Week)</label>
                      <div className="flex flex-wrap gap-2">
                        {['ALL', 1, 2, 3, 4, 5, 6, 7].map(f => (
                          <button key={f} onClick={() => setPlanFilterFrequency(f)}
                            className={`px-4 py-2 rounded-xl text-xs font-bold border transition-all ${planFilterFrequency === f ? 'bg-brand-500 text-white border-brand-400 shadow-md' : 'bg-white/50 dark:bg-white/5 text-slate-500 border-transparent hover:border-slate-200'}`}>
                            {f === 'ALL' ? 'Any' : `${f}d`}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="space-y-3">
                      <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center justify-between ml-1">
                        <span className="flex items-center gap-2"><Clock className="w-3 h-3" /> Max Weekly Effort</span>
                        <span className="text-brand-500">{planFilterDuration} min</span>
                      </label>
                      <input type="range" min="30" max="600" step="30" value={planFilterDuration} onChange={(e) => setPlanFilterDuration(parseInt(e.target.value))}
                        className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-brand-500" />
                      <div className="flex justify-between text-[9px] text-slate-400 font-bold px-1"><span>30m</span><span>600m</span></div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          {initialLoading ? (
            <div className="flex items-center justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-brand-500" /></div>
          ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredPlans.map((plan) => {
              const workoutCount = plan.trainings?.length || 0;
              const uniqueWorkoutIds = Array.from(new Set(plan.trainings || []));
              return (
                <motion.div key={plan._id} layoutId={`plan-${plan._id}`} onClick={() => setSelectedPlan(plan)}
                  initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} whileHover={{ scale: 1.02 }}
                  className="glass-panel rounded-3xl p-6 relative overflow-hidden group cursor-pointer">
                  <div className="absolute top-0 left-0 w-2 h-full bg-brand-500"></div>
                  <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-2 ml-2 group-hover:text-brand-600 transition-colors">{plan.name}</h3>
                  <p className="text-sm text-slate-500 mb-4 ml-2 line-clamp-2">{plan.description || "Personal goal plan."}</p>
                  <div className="flex gap-2 mb-4 ml-2">
                    <span className="bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-full text-xs font-bold text-slate-600 dark:text-slate-300 border border-slate-200">{workoutCount} Trainings</span>
                    {plan.total_likes > 0 && <span className="bg-red-50 dark:bg-red-900/20 px-3 py-1 rounded-full text-xs font-bold text-red-500 border border-red-200">{plan.total_likes} Likes</span>}
                  </div>
                  <div className="ml-2 space-y-2">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-2">Trainings:</p>
                    {uniqueWorkoutIds.slice(0, 3).map(tid => {
                      const t = trainings.find(tr => tr._id === tid);
                      return t ? <div key={tid} className="flex items-center gap-2 text-sm text-slate-600"><Dumbbell className="w-3.5 h-3.5 text-brand-500" />{t.name}</div> : null;
                    })}
                    {uniqueWorkoutIds.length > 3 && <p className="text-xs text-slate-400 ml-5">+{uniqueWorkoutIds.length - 3} more</p>}
                  </div>
                </motion.div>
              );
            })}
          </div>
          )}
        </div>
      )}

      {/* WORKOUTS TAB */}
      {activeTab === 'workouts' && (
        <div className="space-y-6">
          <div className="space-y-4">
            <div className="glass-panel p-2 rounded-2xl flex flex-col md:flex-row gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
                <input type="text" value={workoutSearchQuery} onChange={(e) => setWorkoutSearchQuery(e.target.value)} placeholder="Search workouts..."
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
                    {/* Training Type */}
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
                    {/* Body Part */}
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
                    {/* Max Duration */}
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
          {initialLoading ? (
            <div className="flex items-center justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-brand-500" /></div>
          ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredTrainings.map((training) => (
              <motion.div key={training._id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} whileHover={{ scale: 1.02 }}
                onClick={() => setSelectedTraining(training)}
                className="glass-panel rounded-3xl p-6 relative overflow-hidden group cursor-pointer">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-lg font-bold text-slate-800 dark:text-white group-hover:text-brand-600 transition-colors pr-2">{training.name}</h3>
                  <div className="flex items-center gap-2 shrink-0">
                    {currentUserId && !ownTrainingIds.has(training._id) && (
                      <button
                        onClick={(e) => handleToggleLike(e, training._id)}
                        disabled={likingInProgress.has(training._id)}
                        className={`p-1.5 rounded-xl transition-all ${likedWorkoutIds.has(training._id) ? 'text-red-500 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30' : 'text-slate-300 hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/10'} ${likingInProgress.has(training._id) ? 'opacity-50' : ''}`}
                        title={likedWorkoutIds.has(training._id) ? 'Unlike' : 'Like workout'}
                      >
                        <Heart className={`w-4 h-4 ${likedWorkoutIds.has(training._id) ? 'fill-current' : ''}`} />
                      </button>
                    )}
                    <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getDifficultyColor(training.training_type)}`}>{training.training_type}</span>
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
          )}
        </div>
      )}

      {/* WORKOUT CREATOR MODAL */}
      <AnimatePresence>
        {isWorkoutCreatorOpen && (
          <div className="fixed inset-0 z-[80] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setIsWorkoutCreatorOpen(false)} className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" />
            <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="w-full max-w-2xl bg-white/95 dark:bg-slate-900/95 glass-panel rounded-[2.5rem] relative z-10 flex flex-col max-h-[88vh] shadow-2xl border border-white/40 overflow-hidden">
              <div className="p-5 border-b border-slate-100 dark:border-white/5 flex justify-between items-center bg-white/50 dark:bg-white/5 backdrop-blur-sm">
                <div className="pl-3">
                  <h3 className="font-bold text-xl text-slate-800 dark:text-white drop-shadow-sm">Construct Workout</h3>
                  <p className="text-[10px] font-bold text-brand-600 dark:text-brand-400 uppercase tracking-[0.2em]">Crystalline Session Architect</p>
                </div>
                <button onClick={() => setIsWorkoutCreatorOpen(false)} className="p-2.5 hover:bg-black/5 dark:hover:bg-white/10 rounded-full transition-colors group"><X className="w-5 h-5 text-slate-400 group-hover:text-slate-600 dark:group-hover:text-white transition-colors" /></button>
              </div>
              <div className="flex-1 overflow-y-auto p-8 space-y-8">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1 flex items-center gap-1.5"><Hash className="w-3 h-3 text-brand-500" /> Workout Title</label>
                    <input type="text" value={newTraining.name} onChange={e => setNewTraining({...newTraining, name: e.target.value})} placeholder="e.g. Explosive Quads & Core"
                      className="w-full p-4 liquid-input rounded-2xl text-slate-800 dark:text-white outline-none font-medium" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1 flex items-center gap-1.5"><Layers className="w-3 h-3 text-brand-500" /> Category</label>
                    <CustomSelect value={newTraining.training_type} onChange={(v) => setNewTraining({...newTraining, training_type: v})}
                      options={Object.values(TrainingType).map(t => ({ value: t, label: t.replace('_', ' ') }))} />
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="flex justify-between items-center px-1">
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2"><Activity className="w-4 h-4 text-brand-500" /> Session Routine</label>
                    <button onClick={() => setShowExercisePicker(true)} className="flex items-center gap-2 text-brand-600 dark:text-brand-400 font-bold text-sm bg-brand-500/10 px-4 py-2 rounded-xl hover:bg-brand-500/20 transition-all active:scale-95"><Plus className="w-4 h-4" /> Add Exercise</button>
                  </div>
                  <div className="space-y-4">
                    {newTraining.exercises?.map((ex, exIdx) => (
                      <motion.div key={exIdx} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                        className="p-5 bg-white/40 dark:bg-white/5 border border-white/50 dark:border-white/10 rounded-3xl shadow-sm group backdrop-blur-sm">
                        <div className="flex justify-between items-center mb-5">
                          <div className="flex items-center gap-3">
                            <div className="p-2.5 bg-brand-500/10 text-brand-500 rounded-2xl"><Dumbbell className="w-5 h-5" /></div>
                            <div>
                              <span className="font-bold text-slate-800 dark:text-white">{exercisesDB[ex.exercise_id]?.name || 'Exercise'}</span>
                              <p className="text-[9px] text-slate-400 font-bold uppercase tracking-widest mt-0.5">{(exercisesDB[ex.exercise_id]?.body_part || '').replace('_', ' ')}</p>
                            </div>
                          </div>
                          <button onClick={() => handleRemoveExercise(exIdx)} className="p-2 text-slate-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 rounded-xl transition-all"><Trash2 className="w-4 h-4" /></button>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          {ex.sets.map((set, setIdx) => (
                            <div key={setIdx} className="flex gap-2 items-center bg-white/60 dark:bg-black/20 p-2 rounded-2xl border border-white/40 dark:border-white/5 group/set">
                              <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800 text-[10px] font-bold text-slate-400">{setIdx + 1}</div>
                              <button type="button" onClick={() => handleUpdateSet(exIdx, setIdx, 'volume', Math.max(1, (set.volume || 1) - 1))}
                                className="w-7 h-7 flex items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-400 hover:text-brand-500 hover:bg-brand-500/10 transition-colors shrink-0"><Minus className="w-3 h-3" /></button>
                              <input type="text" inputMode="numeric" value={set.volume} onChange={e => handleUpdateSet(exIdx, setIdx, 'volume', parseInt(e.target.value) || 0)}
                                className="w-10 p-1 bg-transparent text-center text-sm font-bold text-slate-800 dark:text-white focus:outline-none" />
                              <button type="button" onClick={() => handleUpdateSet(exIdx, setIdx, 'volume', (set.volume || 0) + 1)}
                                className="w-7 h-7 flex items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-400 hover:text-brand-500 hover:bg-brand-500/10 transition-colors shrink-0"><Plus className="w-3 h-3" /></button>
                              <div className="relative flex-1">
                                <select value={set.units} onChange={e => handleUpdateSet(exIdx, setIdx, 'units', e.target.value)}
                                  className="w-full p-2 bg-transparent text-[10px] font-bold text-slate-500 dark:text-slate-400 outline-none cursor-pointer appearance-none pr-6">
                                  {Object.values(SetUnit).map(u => <option key={u} value={u}>{u}</option>)}
                                </select>
                                <ChevronDown className="absolute right-1 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-400 pointer-events-none" />
                              </div>
                              <button onClick={() => handleRemoveSet(exIdx, setIdx)} className="p-1 text-slate-300 hover:text-red-500 opacity-0 group-hover/set:opacity-100 transition-opacity"><X className="w-4 h-4" /></button>
                            </div>
                          ))}
                          <button onClick={() => handleAddSet(exIdx)}
                            className="w-full py-3 border-2 border-dashed border-slate-100 dark:border-white/5 rounded-2xl text-slate-300 text-[10px] font-bold hover:border-brand-500/50 hover:bg-brand-500/5 hover:text-brand-600 transition-all flex items-center justify-center gap-2">
                            <Plus className="w-3.5 h-3.5" /> Add Set
                          </button>
                        </div>
                      </motion.div>
                    ))}
                    {(!newTraining.exercises || newTraining.exercises.length === 0) && (
                      <div className="text-center py-16 border-2 border-dashed border-slate-100 dark:border-white/5 rounded-[2rem] flex flex-col items-center gap-4 group hover:border-brand-500/30 transition-all cursor-pointer" onClick={() => setShowExercisePicker(true)}>
                        <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-full text-slate-300 group-hover:text-brand-500 transition-colors"><Activity className="w-8 h-8" /></div>
                        <p className="text-xs font-bold text-slate-400 group-hover:text-slate-500">Add movements to build your routine</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              <div className="p-6 bg-slate-50/80 dark:bg-black/20 backdrop-blur-md flex justify-end gap-3 border-t border-slate-100 dark:border-white/5">
                <button onClick={() => setIsWorkoutCreatorOpen(false)} className="px-6 py-2.5 text-slate-500 dark:text-slate-400 font-bold hover:text-slate-800 dark:hover:text-white transition-colors">Cancel</button>
                <button onClick={handleSaveTraining} disabled={!newTraining.name || !newTraining.exercises?.length}
                  className="liquid-btn liquid-btn-primary px-10 py-2.5 rounded-2xl font-bold flex items-center gap-2 shadow-lg shadow-brand-500/20 disabled:opacity-50 disabled:grayscale transition-all">
                  <Save className="w-4 h-4" /> Save Workout
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
                  <div key={ex._id} onClick={() => handleAddExerciseToTraining(ex._id)}
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

      {/* PLAN CREATOR MODAL */}
      <AnimatePresence>
        {isPlanCreatorOpen && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setIsPlanCreatorOpen(false)} className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" />
            <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="w-full max-w-2xl bg-white/95 dark:bg-slate-900/95 glass-panel rounded-[2.5rem] relative z-10 flex flex-col max-h-[88vh] shadow-2xl border border-white/40 overflow-hidden">
              <div className="p-5 border-b border-slate-100 dark:border-white/5 flex justify-between items-center bg-white/50 dark:bg-white/5 backdrop-blur-sm">
                <div className="pl-3">
                  <h3 className="font-bold text-xl text-slate-800 dark:text-white drop-shadow-sm">Workout Plan Architect</h3>
                  <p className="text-[10px] font-bold text-brand-600 dark:text-brand-400 uppercase tracking-[0.2em]">Build Your Training Program</p>
                </div>
                <button onClick={() => setIsPlanCreatorOpen(false)} className="p-2.5 hover:bg-black/5 dark:hover:bg-white/10 rounded-full transition-colors group"><X className="w-5 h-5 text-slate-400 group-hover:text-slate-600 dark:group-hover:text-white transition-colors" /></button>
              </div>
              <div className="flex-1 overflow-y-auto p-8 space-y-8">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 bg-brand-500/5 dark:bg-white/5 rounded-[2rem] border-2 border-dashed border-brand-500/10 backdrop-blur-sm">
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1 flex items-center gap-2"><Hash className="w-4 h-4 text-brand-500" /> Plan Name</label>
                    <input type="text" placeholder="e.g. Project Shred: Summer Edition" value={newPlan.name} onChange={(e) => setNewPlan({...newPlan, name: e.target.value})}
                      className="w-full p-4 liquid-input rounded-2xl outline-none font-medium" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1 flex items-center gap-2"><Type className="w-4 h-4 text-brand-500" /> Description</label>
                    <input type="text" placeholder="e.g. Focus on strength gain and fat loss" value={newPlan.description} onChange={(e) => setNewPlan({...newPlan, description: e.target.value})}
                      className="w-full p-4 liquid-input rounded-2xl outline-none font-medium" />
                  </div>
                </div>
                <div className="space-y-4">
                  <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2 px-1"><Calendar className="w-4 h-4 text-brand-500" /> Weekly Schedule</label>
                  <div className="space-y-3">
                    {[1, 2, 3, 4, 5, 6, 7].map(day => {
                      const dayTrainings = newPlan.schedule?.[day] || [];
                      return (
                        <div key={day} className="p-4 bg-white/40 dark:bg-white/5 rounded-2xl border border-white/50 dark:border-white/10 backdrop-blur-sm">
                          <div className="flex justify-between items-center mb-2">
                            <h4 className="font-bold text-sm text-slate-700 dark:text-slate-200 flex items-center gap-2">
                              <span className="w-7 h-7 rounded-lg bg-brand-500/10 text-brand-500 flex items-center justify-center text-[10px] font-black">{dayNames[day].slice(0, 2).toUpperCase()}</span>
                              {dayNames[day]}
                            </h4>
                            <button onClick={() => setPickingForPlanDay(day)} className="flex items-center gap-1.5 text-brand-600 dark:text-brand-400 font-bold text-xs bg-brand-500/10 px-3 py-1.5 rounded-lg hover:bg-brand-500/20 transition-all active:scale-95"><Plus className="w-3.5 h-3.5" /> Add</button>
                          </div>
                          {dayTrainings.length > 0 ? (
                            <div className="space-y-2 mt-2">
                              {dayTrainings.map((tid, idx) => {
                                const t = trainings.find(tr => tr._id === tid);
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
                                    <button onClick={() => handleRemoveFromSchedule(day, idx)} className="p-1.5 text-slate-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 rounded-lg transition-all opacity-0 group-hover:opacity-100"><Trash2 className="w-3.5 h-3.5" /></button>
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
                <button onClick={() => setIsPlanCreatorOpen(false)} className="px-6 py-2.5 text-slate-500 dark:text-slate-400 font-bold hover:text-slate-800 dark:hover:text-white transition-colors">Cancel</button>
                <button onClick={handleSavePlan} disabled={!newPlan.name || !scheduleTrainingIds.length}
                  className="liquid-btn liquid-btn-primary px-12 py-3 rounded-2xl font-bold flex items-center gap-2 shadow-lg shadow-brand-500/20 disabled:opacity-50 disabled:grayscale transition-all">
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Finalize Plan
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ASSIGN TRAINING PICKER MODAL */}
      <AnimatePresence>
        {pickingForPlanDay !== null && (
          <div className="fixed inset-0 z-[90] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setPickingForPlanDay(null)} className="absolute inset-0 z-0 bg-slate-900/60 backdrop-blur-md" />
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-lg bg-white/95 dark:bg-slate-900/95 glass-panel rounded-[2rem] relative z-10 flex flex-col max-h-[70vh] shadow-2xl border border-white/40 overflow-hidden">
              <div className="p-5 border-b border-slate-100 dark:border-white/5 flex justify-between items-center bg-white/50 dark:bg-white/5 backdrop-blur-sm">
                <div className="pl-2"><h3 className="font-bold text-lg text-slate-800 dark:text-white">{typeof pickingForPlanDay === 'string' && pickingForPlanDay.startsWith('edit-') ? `Assign Training — ${dayNames[parseInt(pickingForPlanDay.split('-')[1])]}` : `Assign Training — ${dayNames[pickingForPlanDay]}`}</h3></div>
                <button onClick={() => setPickingForPlanDay(null)} className="p-2.5 hover:bg-black/5 dark:hover:bg-white/10 rounded-full transition-colors"><X className="w-5 h-5 text-slate-400" /></button>
              </div>
              <div className="flex-1 overflow-y-auto p-5 space-y-3">
                {(() => {
                  const ownTrainings = trainings.filter(t => ownTrainingIds.has(t._id));
                  const likedOnly = trainings.filter(t => likedWorkoutIds.has(t._id) && !ownTrainingIds.has(t._id));
                  const available = [...ownTrainings, ...likedOnly];
                  if (available.length === 0) {
                    return (
                      <div className="text-center py-16 opacity-60">
                        <Dumbbell className="w-10 h-10 mx-auto text-slate-300 mb-4" />
                        <p className="text-sm font-bold text-slate-500 uppercase tracking-widest">No trainings available</p>
                        <p className="text-[11px] text-slate-400 mt-2 max-w-xs mx-auto">Create your own trainings or like other users' trainings to add them to plans.</p>
                      </div>
                    );
                  }
                  return (
                    <>
                      {ownTrainings.length > 0 && (
                        <>
                          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-1 pt-1">Your trainings</p>
                          {ownTrainings.map(training => (
                            <div key={training._id} onClick={() => handleAddToPlanSchedule(training._id)}
                              className="p-4 rounded-2xl border border-slate-100 dark:border-white/5 hover:border-brand-500/30 hover:bg-brand-500/5 dark:hover:bg-brand-500/5 cursor-pointer flex justify-between items-center group transition-all">
                              <div className="flex items-center gap-4">
                                <div className="w-10 h-10 bg-brand-500/10 rounded-xl flex items-center justify-center text-brand-500 group-hover:text-brand-600 transition-colors"><Dumbbell className="w-5 h-5" /></div>
                                <div>
                                  <h4 className="font-bold text-sm text-slate-800 dark:text-white">{training.name}</h4>
                                  <p className="text-[9px] text-slate-500 mt-1 uppercase font-bold tracking-[0.2em]">{formatDuration(training.est_time)} • {training.training_type}</p>
                                </div>
                              </div>
                              <div className="w-9 h-9 rounded-xl bg-brand-500/10 text-brand-500 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all scale-75 group-hover:scale-100"><Plus className="w-5 h-5" /></div>
                            </div>
                          ))}
                        </>
                      )}
                      {likedOnly.length > 0 && (
                        <>
                          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-1 pt-3 flex items-center gap-1.5"><Heart className="w-3 h-3 text-red-400" /> Liked</p>
                          {likedOnly.map(training => (
                            <div key={training._id} onClick={() => handleAddToPlanSchedule(training._id)}
                              className="p-4 rounded-2xl border border-slate-100 dark:border-white/5 hover:border-brand-500/30 hover:bg-brand-500/5 dark:hover:bg-brand-500/5 cursor-pointer flex justify-between items-center group transition-all">
                              <div className="flex items-center gap-4">
                                <div className="w-10 h-10 bg-red-50 dark:bg-red-900/20 rounded-xl flex items-center justify-center text-red-400 group-hover:text-red-500 transition-colors"><Heart className="w-5 h-5" /></div>
                                <div>
                                  <h4 className="font-bold text-sm text-slate-800 dark:text-white">{training.name}</h4>
                                  <p className="text-[9px] text-slate-500 mt-1 uppercase font-bold tracking-[0.2em]">{formatDuration(training.est_time)} • {training.training_type}</p>
                                </div>
                              </div>
                              <div className="w-9 h-9 rounded-xl bg-brand-500/10 text-brand-500 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all scale-75 group-hover:scale-100"><Plus className="w-5 h-5" /></div>
                            </div>
                          ))}
                        </>
                      )}
                    </>
                  );
                })()}
              </div>
            </motion.div>
          </div>
        )}
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
                    <CustomSelect value={editingTraining.training_type} onChange={(v) => setEditingTraining({...editingTraining, training_type: v})}
                      options={Object.values(TrainingType).map(t => ({ value: t, label: t.replace('_', ' ') }))} />
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
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Save Changes
                </button>
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
                  {currentUserId && selectedPlan.trainer_id === currentUserId && (
                    <>
                      <button onClick={() => handleStartEditPlan(selectedPlan)} className="p-2.5 hover:bg-brand-500/10 rounded-full transition-colors group" title="Edit"><Edit3 className="w-4 h-4 text-slate-400 group-hover:text-brand-500" /></button>
                      <button onClick={() => handleDeletePlan(selectedPlan._id)} className="p-2.5 hover:bg-red-50 dark:hover:bg-red-900/10 rounded-full transition-colors group" title="Delete"><Trash2 className="w-4 h-4 text-slate-400 group-hover:text-red-500" /></button>
                    </>
                  )}
                  <button onClick={() => setSelectedPlan(null)} className="p-2.5 hover:bg-black/5 dark:hover:bg-white/10 rounded-full transition-colors"><X className="w-5 h-5 text-slate-400" /></button>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {selectedPlan.description && <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">{selectedPlan.description}</p>}
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2"><Calendar className="w-3 h-3 text-brand-500" /> Weekly Breakdown</label>
                {(() => {
                  // Build schedule: use saved schedule or fall back to round-robin
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
                              const t = trainings.find(tr => tr._id === tid);
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
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1 flex items-center gap-2"><Hash className="w-4 h-4 text-brand-500" /> Plan Name</label>
                    <input type="text" value={editingPlan.name} onChange={e => setEditingPlan({...editingPlan, name: e.target.value})}
                      className="w-full p-4 liquid-input rounded-2xl outline-none font-medium" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1 flex items-center gap-2"><Type className="w-4 h-4 text-brand-500" /> Description</label>
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
                            <button onClick={() => setPickingForPlanDay(`edit-${day}`)} className="flex items-center gap-1.5 text-brand-600 dark:text-brand-400 font-bold text-xs bg-brand-500/10 px-3 py-1.5 rounded-lg hover:bg-brand-500/20 transition-all active:scale-95"><Plus className="w-3.5 h-3.5" /> Add</button>
                          </div>
                          {dayTrainings.length > 0 ? (
                            <div className="space-y-2 mt-2">
                              {dayTrainings.map((tid, idx) => {
                                const t = trainings.find(tr => tr._id === tid);
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
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Save Changes
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* AI MODAL */}
      <AnimatePresence>
        {isAiModalOpen && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setIsAiModalOpen(false)} className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" />
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
              className="glass-panel bg-white/95 dark:bg-slate-900/95 p-10 rounded-[2.5rem] w-full max-w-lg relative shadow-2xl z-10 border border-white/40">
              <button onClick={() => setIsAiModalOpen(false)} className="absolute top-6 right-6 p-2.5 hover:bg-black/5 dark:hover:bg-white/10 rounded-full transition-colors"><X className="w-5 h-5 text-slate-400" /></button>
              <div className="mb-8 text-center md:text-left">
                <div className="w-16 h-16 mx-auto md:mx-0 bg-gradient-to-br from-brand-400 to-brand-600 rounded-2xl flex items-center justify-center mb-5 shadow-lg shadow-brand-500/30"><Sparkles className="w-8 h-8 text-white" /></div>
                <h3 className="text-2xl font-bold text-slate-800 dark:text-white drop-shadow-sm">AI Coach Engine</h3>
                <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">Describe your objective and let our AI architect your routine.</p>
              </div>
              <div className="space-y-4 mb-10">
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1 flex items-center gap-2"><Activity className="w-4 h-4 text-brand-500" /> Current Objective</label>
                <textarea value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="e.g. 45 min HIIT focusing on agility and core stability..."
                  className="w-full h-36 p-5 liquid-input rounded-3xl outline-none resize-none font-medium text-sm leading-relaxed" />
              </div>
              <div className="flex flex-col sm:flex-row justify-end gap-3 pt-6 border-t border-slate-100 dark:border-white/5">
                <button onClick={() => setIsAiModalOpen(false)} className="px-6 py-3 text-slate-500 dark:text-slate-400 font-bold hover:text-slate-800 dark:hover:text-white transition-colors">Cancel</button>
                <button onClick={handleGenerateAi} disabled={isLoading}
                  className="liquid-btn liquid-btn-primary px-10 py-3 rounded-2xl font-bold flex items-center justify-center gap-2 shadow-lg shadow-brand-500/20 disabled:grayscale">
                  {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}
                  {isLoading ? 'Architecting...' : 'Generate Roadmap'}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
