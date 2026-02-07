'use client';

import { useState, useMemo } from 'react';
import {
  TrainingType, SetUnit, DayOfWeek, BodyPart, Advancement
} from '../data/types';
import { MOCK_EXERCISES_DB } from '../data/mockData';
import { generateWorkout } from '../services/geminiService';
import {
  Dumbbell, Clock, Activity, Plus, Sparkles, X,
  Loader2, Search, Filter, ChevronDown,
  Save, Trash2, Calendar, LayoutGrid, Layers, Info, Hash, Type
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const populateTraining = (training) => {
  return {
    ...training,
    exercises: training.exercises.map(ex => ({
      ...ex,
      _exerciseDetails: MOCK_EXERCISES_DB[ex.exercise_id] || {
        _id: ex.exercise_id, name: 'Unknown Exercise',
        body_part: BodyPart.FULL_BODY, advancement: Advancement.BEGINNER,
        category: 'custom'
      }
    }))
  };
};

const INITIAL_TRAININGS = [
  populateTraining({
    _id: '1', name: 'Full Body HIIT Blast', est_time: 2700,
    day: DayOfWeek.MONDAY, training_type: TrainingType.HIIT,
    exercises: [
      { exercise_id: 'ex_burpee', sets: Array(4).fill({ volume: 15, units: SetUnit.REPS }), rest_between_sets: 45 },
      { exercise_id: 'ex_pushup', sets: Array(4).fill({ volume: 20, units: SetUnit.REPS }), rest_between_sets: 45 },
      { exercise_id: 'ex_squat_jump', sets: Array(4).fill({ volume: 20, units: SetUnit.REPS }), rest_between_sets: 45 }
    ]
  }),
  populateTraining({
    _id: '2', name: 'Upper Body Power', est_time: 3600,
    day: DayOfWeek.WEDNESDAY, training_type: TrainingType.STRENGTH,
    exercises: [
      { exercise_id: 'ex_bench', sets: Array(5).fill({ volume: 5, units: SetUnit.REPS }), rest_between_sets: 120 },
      { exercise_id: 'ex_pullup', sets: Array(4).fill({ volume: 10, units: SetUnit.REPS }), rest_between_sets: 90 },
      { exercise_id: 'ex_ohp', sets: Array(4).fill({ volume: 8, units: SetUnit.REPS }), rest_between_sets: 90 }
    ]
  })
];

const INITIAL_PLANS = [
  {
    _id: 'p1', name: 'Summer Shred 2024', trainer_id: 'self', clients: [],
    schedule: {
      [DayOfWeek.MONDAY]: ['1'], [DayOfWeek.TUESDAY]: [], [DayOfWeek.WEDNESDAY]: ['2'],
      [DayOfWeek.THURSDAY]: [], [DayOfWeek.FRIDAY]: ['1'], [DayOfWeek.SATURDAY]: [], [DayOfWeek.SUNDAY]: [],
    },
    trainings: ['1', '2'],
    description: 'A 4-week high intensity program to get lean. Focuses on HIIT and compound movements.',
    is_public: false, total_likes: 0
  }
];

export default function Workouts() {
  const [activeTab, setActiveTab] = useState('plans');
  const [trainings, setTrainings] = useState(INITIAL_TRAININGS);
  const [plans, setPlans] = useState(INITIAL_PLANS);
  const [isAiModalOpen, setIsAiModalOpen] = useState(false);
  const [isWorkoutCreatorOpen, setIsWorkoutCreatorOpen] = useState(false);
  const [isPlanCreatorOpen, setIsPlanCreatorOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [workoutSearchQuery, setWorkoutSearchQuery] = useState('');
  const [planSearchQuery, setPlanSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPlanFilters, setShowPlanFilters] = useState(false);
  const [filterBodyPart, setFilterBodyPart] = useState('ALL');
  const [filterAdvancement, setFilterAdvancement] = useState('ALL');
  const [filterMaxTime, setFilterMaxTime] = useState(120);
  const [planFilterFrequency, setPlanFilterFrequency] = useState('ALL');
  const [planFilterDuration, setPlanFilterDuration] = useState(300);
  const [newTraining, setNewTraining] = useState({
    name: '', description: '', day: DayOfWeek.MONDAY,
    training_type: TrainingType.CUSTOM, est_time: 3600, exercises: []
  });
  const [newPlan, setNewPlan] = useState({
    name: '', description: '',
    schedule: { [DayOfWeek.MONDAY]: [], [DayOfWeek.TUESDAY]: [], [DayOfWeek.WEDNESDAY]: [], [DayOfWeek.THURSDAY]: [], [DayOfWeek.FRIDAY]: [], [DayOfWeek.SATURDAY]: [], [DayOfWeek.SUNDAY]: [] }
  });
  const [pickingForPlanDay, setPickingForPlanDay] = useState(null);
  const [showExercisePicker, setShowExercisePicker] = useState(false);
  const [pickerSearch, setPickerSearch] = useState('');
  const [pickerBodyPart, setPickerBodyPart] = useState('ALL');

  const handleGenerateAi = async () => {
    if (!prompt.trim()) return;
    setIsLoading(true);
    const generated = await generateWorkout(prompt);
    if (generated) {
      setTrainings([populateTraining(generated), ...trainings]);
      setIsAiModalOpen(false);
      setPrompt('');
      setActiveTab('workouts');
    }
    setIsLoading(false);
  };

  const handleAddExerciseToTraining = (exerciseId) => {
    const newEx = {
      exercise_id: exerciseId,
      sets: [{ volume: 10, units: SetUnit.REPS }, { volume: 10, units: SetUnit.REPS }, { volume: 10, units: SetUnit.REPS }],
      rest_between_sets: 60, notes: ''
    };
    setNewTraining(prev => ({ ...prev, exercises: [...(prev.exercises || []), newEx] }));
    setShowExercisePicker(false);
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

  const handleSaveTraining = () => {
    if (!newTraining.name || !newTraining.exercises?.length) return;
    const finalTraining = {
      _id: crypto.randomUUID(), name: newTraining.name, exercises: newTraining.exercises,
      est_time: newTraining.est_time || 3600, day: newTraining.day || DayOfWeek.MONDAY,
      training_type: newTraining.training_type || TrainingType.CUSTOM, description: newTraining.description
    };
    setTrainings([populateTraining(finalTraining), ...trainings]);
    setIsWorkoutCreatorOpen(false);
    setNewTraining({ name: '', description: '', day: DayOfWeek.MONDAY, training_type: TrainingType.CUSTOM, est_time: 3600, exercises: [] });
  };

  const handleAddToPlanSchedule = (trainingId) => {
    if (pickingForPlanDay !== null) {
      setNewPlan(prev => ({
        ...prev,
        schedule: { ...prev.schedule, [pickingForPlanDay]: [...prev.schedule[pickingForPlanDay], trainingId] }
      }));
      setPickingForPlanDay(null);
    }
  };

  const handleRemoveFromPlanSchedule = (day, index) => {
    setNewPlan(prev => {
      const newDaySchedule = [...prev.schedule[day]];
      newDaySchedule.splice(index, 1);
      return { ...prev, schedule: { ...prev.schedule, [day]: newDaySchedule } };
    });
  };

  const handleSavePlan = () => {
    const totalWorkouts = Object.values(newPlan.schedule).flat().length;
    if (!newPlan.name || totalWorkouts === 0) return;
    const uniqueTrainings = Array.from(new Set(Object.values(newPlan.schedule).flat()));
    const createdPlan = {
      _id: crypto.randomUUID(), name: newPlan.name, description: newPlan.description,
      schedule: newPlan.schedule, trainings: uniqueTrainings, trainer_id: 'self',
      clients: [], is_public: false, total_likes: 0
    };
    setPlans([createdPlan, ...plans]);
    setIsPlanCreatorOpen(false);
    setNewPlan({ name: '', description: '', schedule: { [DayOfWeek.MONDAY]: [], [DayOfWeek.TUESDAY]: [], [DayOfWeek.WEDNESDAY]: [], [DayOfWeek.THURSDAY]: [], [DayOfWeek.FRIDAY]: [], [DayOfWeek.SATURDAY]: [], [DayOfWeek.SUNDAY]: [] } });
  };

  const formatDuration = (seconds) => `${Math.floor(seconds / 60)} min`;

  const getDifficultyColor = (type) => {
    switch (type) {
      case TrainingType.HIIT: return 'text-orange-600 bg-orange-100/50 border-orange-200';
      case TrainingType.STRENGTH: return 'text-red-600 bg-red-100/50 border-red-200';
      case TrainingType.CARDIO: return 'text-blue-600 bg-blue-100/50 border-blue-200';
      case TrainingType.YOGA: return 'text-green-600 bg-green-100/50 border-green-200';
      default: return 'text-slate-500 bg-slate-100/50 border-slate-100';
    }
  };

  const filteredTrainings = useMemo(() => {
    return trainings.filter(t => {
      if (workoutSearchQuery && !t.name.toLowerCase().includes(workoutSearchQuery.toLowerCase())) return false;
      if (t.est_time / 60 > filterMaxTime) return false;
      if (filterBodyPart !== 'ALL' && !t.exercises.some(ex => ex._exerciseDetails?.body_part === filterBodyPart)) return false;
      if (filterAdvancement !== 'ALL' && !t.exercises.some(ex => ex._exerciseDetails?.advancement === filterAdvancement)) return false;
      return true;
    });
  }, [trainings, workoutSearchQuery, filterMaxTime, filterBodyPart, filterAdvancement]);

  const filteredPlans = useMemo(() => {
    return plans.filter(p => {
      if (planSearchQuery && !p.name.toLowerCase().includes(planSearchQuery.toLowerCase())) return false;
      const frequency = Object.values(p.schedule).filter(day => day.length > 0).length;
      if (planFilterFrequency !== 'ALL' && frequency !== planFilterFrequency) return false;
      const totalDuration = Object.values(p.schedule).flat().reduce((acc, tid) => {
        const t = trainings.find(tr => tr._id === tid);
        return acc + (t ? t.est_time / 60 : 0);
      }, 0);
      if (totalDuration > planFilterDuration) return false;
      return true;
    });
  }, [plans, planSearchQuery, planFilterFrequency, planFilterDuration, trainings]);

  const filteredExercisesForPicker = useMemo(() => {
    return Object.values(MOCK_EXERCISES_DB).filter(ex => {
      const matchesName = ex.name.toLowerCase().includes(pickerSearch.toLowerCase());
      const matchesBody = pickerBodyPart === 'ALL' || ex.body_part === pickerBodyPart;
      return matchesName && matchesBody;
    });
  }, [pickerSearch, pickerBodyPart]);

  const dayNames = {
    [DayOfWeek.MONDAY]: "Monday", [DayOfWeek.TUESDAY]: "Tuesday", [DayOfWeek.WEDNESDAY]: "Wednesday",
    [DayOfWeek.THURSDAY]: "Thursday", [DayOfWeek.FRIDAY]: "Friday", [DayOfWeek.SATURDAY]: "Saturday",
    [DayOfWeek.SUNDAY]: "Sunday",
  };

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
                  <div className="glass-panel rounded-2xl p-6 grid grid-cols-1 md:grid-cols-2 gap-8 border-dashed">
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredPlans.map((plan) => {
              const workoutCount = Object.values(plan.schedule).filter(day => day.length > 0).length;
              const uniqueWorkoutIds = Array.from(new Set(Object.values(plan.schedule).flat()));
              return (
                <motion.div key={plan._id} layoutId={`plan-${plan._id}`} onClick={() => setSelectedPlan(plan)}
                  initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} whileHover={{ scale: 1.02 }}
                  className="glass-panel rounded-3xl p-6 relative overflow-hidden group cursor-pointer">
                  <div className="absolute top-0 left-0 w-2 h-full bg-brand-500"></div>
                  <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-2 ml-2 group-hover:text-brand-600 transition-colors">{plan.name}</h3>
                  <p className="text-sm text-slate-500 mb-4 ml-2 line-clamp-2">{plan.description || "Personal goal plan."}</p>
                  <div className="flex gap-2 mb-4 ml-2">
                    <span className="bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-full text-xs font-bold text-slate-600 dark:text-slate-300 border border-slate-200">{workoutCount} Days / Week</span>
                  </div>
                  <div className="ml-2 space-y-2">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-2">Highlights:</p>
                    {uniqueWorkoutIds.slice(0, 3).map(tid => {
                      const t = trainings.find(tr => tr._id === tid);
                      return t ? <div key={tid} className="flex items-center gap-2 text-sm text-slate-600"><Dumbbell className="w-3.5 h-3.5 text-brand-500" />{t.name}</div> : null;
                    })}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}

      {/* WORKOUTS TAB */}
      {activeTab === 'workouts' && (
        <div className="space-y-6">
          <div className="glass-panel p-2 rounded-2xl flex flex-col md:flex-row gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
              <input type="text" value={workoutSearchQuery} onChange={(e) => setWorkoutSearchQuery(e.target.value)} placeholder="Search workouts..."
                className="w-full pl-12 pr-4 py-3 bg-transparent text-slate-800 dark:text-white placeholder-slate-400 outline-none font-medium" />
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredTrainings.map((training) => (
              <motion.div key={training._id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} whileHover={{ scale: 1.02 }}
                className="glass-panel rounded-3xl p-6 relative overflow-hidden group cursor-pointer">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-lg font-bold text-slate-800 dark:text-white group-hover:text-brand-600 transition-colors">{training.name}</h3>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getDifficultyColor(training.training_type)}`}>{training.training_type}</span>
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
                </div>
              </motion.div>
            ))}
          </div>
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
                    <div className="relative">
                      <select value={newTraining.training_type} onChange={e => setNewTraining({...newTraining, training_type: e.target.value})}
                        className="w-full p-4 liquid-input rounded-2xl text-slate-800 dark:text-white outline-none appearance-none font-medium">
                        {Object.values(TrainingType).map(t => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}
                      </select>
                      <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                    </div>
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
                              <span className="font-bold text-slate-800 dark:text-white">{MOCK_EXERCISES_DB[ex.exercise_id]?.name || 'Exercise'}</span>
                              <p className="text-[9px] text-slate-400 font-bold uppercase tracking-widest mt-0.5">{MOCK_EXERCISES_DB[ex.exercise_id]?.body_part.replace('_', ' ')}</p>
                            </div>
                          </div>
                          <button onClick={() => handleRemoveExercise(exIdx)} className="p-2 text-slate-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 rounded-xl transition-all"><Trash2 className="w-4 h-4" /></button>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          {ex.sets.map((set, setIdx) => (
                            <div key={setIdx} className="flex gap-2 items-center bg-white/60 dark:bg-black/20 p-2 rounded-2xl border border-white/40 dark:border-white/5 group/set">
                              <div className="w-8 h-8 flex items-center justify-center rounded-lg bg-slate-100 dark:bg-slate-800 text-[10px] font-bold text-slate-400">{setIdx + 1}</div>
                              <input type="number" value={set.volume} onChange={e => handleUpdateSet(exIdx, setIdx, 'volume', parseInt(e.target.value))}
                                className="w-14 p-2 bg-transparent text-center text-sm font-bold text-slate-800 dark:text-white focus:outline-none" />
                              <select value={set.units} onChange={e => handleUpdateSet(exIdx, setIdx, 'units', e.target.value)}
                                className="flex-1 p-2 bg-transparent text-[10px] font-bold text-slate-500 dark:text-slate-400 outline-none cursor-pointer">
                                {Object.values(SetUnit).map(u => <option key={u} value={u}>{u}</option>)}
                              </select>
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
              className="w-full max-w-[94vw] bg-white/95 dark:bg-slate-900/95 glass-panel rounded-[2.5rem] relative z-10 flex flex-col max-h-[94vh] shadow-2xl border border-white/40 overflow-hidden">
              <div className="p-5 border-b border-slate-100 dark:border-white/5 flex justify-between items-center bg-white/50 dark:bg-white/5 backdrop-blur-sm">
                <div className="pl-3">
                  <h3 className="font-bold text-xl text-slate-800 dark:text-white drop-shadow-sm">Weekly Goal Architect</h3>
                  <p className="text-[10px] font-bold text-brand-600 dark:text-brand-400 uppercase tracking-[0.2em]">Crystalline Program Mapping</p>
                </div>
                <button onClick={() => setIsPlanCreatorOpen(false)} className="p-2.5 hover:bg-black/5 dark:hover:bg-white/10 rounded-full transition-colors group"><X className="w-5 h-5 text-slate-400 group-hover:text-slate-600 dark:group-hover:text-white transition-colors" /></button>
              </div>
              <div className="flex-1 overflow-y-auto p-8 space-y-10">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 p-8 bg-brand-500/5 dark:bg-white/5 rounded-[2rem] border-2 border-dashed border-brand-500/10 backdrop-blur-sm">
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1 flex items-center gap-2"><Hash className="w-4 h-4 text-brand-500" /> Plan Identity</label>
                    <input type="text" placeholder="e.g. Project Shred: Summer Edition" value={newPlan.name} onChange={(e) => setNewPlan({...newPlan, name: e.target.value})}
                      className="w-full p-4 liquid-input rounded-2xl outline-none font-medium" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1 flex items-center gap-2"><Type className="w-4 h-4 text-brand-500" /> Primary Vision</label>
                    <input type="text" placeholder="e.g. Focus on strength gain and fat loss" value={newPlan.description} onChange={(e) => setNewPlan({...newPlan, description: e.target.value})}
                      className="w-full p-4 liquid-input rounded-2xl outline-none font-medium" />
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7 gap-4">
                  {Object.values(DayOfWeek).filter(v => typeof v === 'number').map((day) => (
                    <div key={day} className="flex flex-col min-h-[380px] bg-white/30 dark:bg-white/5 border border-white/50 dark:border-white/5 p-5 rounded-[2rem] shadow-sm backdrop-blur-sm transition-all hover:border-brand-500/20 group/day">
                      <div className="flex items-center gap-2 mb-5 pb-3 border-b border-slate-100 dark:border-white/5">
                        <div className="p-1.5 bg-slate-50 dark:bg-slate-800 rounded-lg"><Calendar className="w-3.5 h-3.5 text-brand-500" /></div>
                        <h3 className="font-bold text-slate-800 dark:text-white text-xs">{dayNames[day]}</h3>
                      </div>
                      <div className="flex-1 flex flex-col gap-3">
                        {newPlan.schedule[day].map((tid, idx) => {
                          const training = trainings.find(t => t._id === tid);
                          return training ? (
                            <motion.div key={idx} initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                              className="bg-white/80 dark:bg-slate-800/80 rounded-2xl p-3 border border-slate-100 dark:border-white/10 relative group/card shadow-sm">
                              <h4 className="text-[10px] font-bold text-slate-700 dark:text-slate-200 leading-tight pr-6">{training.name}</h4>
                              <div className="flex items-center gap-2 mt-1.5 opacity-60"><div className="w-1.5 h-1.5 rounded-full bg-brand-500"></div><p className="text-[9px] font-bold uppercase tracking-widest">{training.training_type}</p></div>
                              <button onClick={() => handleRemoveFromPlanSchedule(day, idx)} className="absolute top-1.5 right-1.5 p-1 bg-slate-100 dark:bg-slate-700 text-slate-400 hover:text-red-500 rounded-lg opacity-0 group-hover/card:opacity-100 transition-all z-20" title="Remove workout"><X className="w-3.5 h-3.5" /></button>
                            </motion.div>
                          ) : null;
                        })}
                        <button onClick={() => setPickingForPlanDay(day)}
                          className="w-full py-5 rounded-2xl border-2 border-dashed border-slate-100 dark:border-white/5 text-slate-300 hover:border-brand-500/50 hover:bg-brand-500/5 hover:text-brand-600 transition-all flex flex-col items-center justify-center gap-1.5 mt-auto">
                          <Plus className="w-5 h-5" /><span className="text-[10px] font-bold uppercase tracking-widest">Assign</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="p-6 bg-slate-50/80 dark:bg-black/20 backdrop-blur-md flex justify-end gap-3 border-t border-slate-100 dark:border-white/5">
                <button onClick={() => setIsPlanCreatorOpen(false)} className="px-6 py-2.5 text-slate-500 dark:text-slate-400 font-bold hover:text-slate-800 dark:hover:text-white transition-colors">Cancel</button>
                <button onClick={handleSavePlan} disabled={!newPlan.name || Object.values(newPlan.schedule).flat().length === 0}
                  className="liquid-btn liquid-btn-primary px-12 py-3 rounded-2xl font-bold flex items-center gap-2 shadow-lg shadow-brand-500/20 disabled:opacity-50 disabled:grayscale transition-all">
                  <Save className="w-4 h-4" /> Finalize Plan
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ASSIGN TRAINING PICKER MODAL */}
      <AnimatePresence>
        {pickingForPlanDay !== null && (
          <div className="fixed inset-0 z-[70] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setPickingForPlanDay(null)} className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" />
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-lg bg-white/95 dark:bg-slate-900/95 glass-panel rounded-[2rem] relative z-10 flex flex-col max-h-[70vh] shadow-2xl border border-white/40 overflow-hidden">
              <div className="p-5 border-b border-slate-100 dark:border-white/5 flex justify-between items-center bg-white/50 dark:bg-white/5 backdrop-blur-sm">
                <div className="pl-2"><h3 className="font-bold text-lg text-slate-800 dark:text-white">Assign to {dayNames[pickingForPlanDay]}</h3></div>
                <button onClick={() => setPickingForPlanDay(null)} className="p-2.5 hover:bg-black/5 dark:hover:bg-white/10 rounded-full transition-colors"><X className="w-5 h-5 text-slate-400" /></button>
              </div>
              <div className="flex-1 overflow-y-auto p-5 space-y-3">
                {trainings.map(training => (
                  <div key={training._id} onClick={() => handleAddToPlanSchedule(training._id)}
                    className="p-4 rounded-2xl border border-slate-100 dark:border-white/5 hover:border-brand-500/30 hover:bg-brand-500/5 dark:hover:bg-brand-500/5 cursor-pointer flex justify-between items-center group transition-all">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-slate-50 dark:bg-slate-800 rounded-xl flex items-center justify-center text-slate-400 group-hover:text-brand-500 transition-colors"><Activity className="w-5 h-5" /></div>
                      <div>
                        <h4 className="font-bold text-sm text-slate-800 dark:text-white">{training.name}</h4>
                        <p className="text-[9px] text-slate-500 mt-1 uppercase font-bold tracking-[0.2em]">{formatDuration(training.est_time)} • {training.training_type}</p>
                      </div>
                    </div>
                    <div className="w-9 h-9 rounded-xl bg-brand-500/10 text-brand-500 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all scale-75 group-hover:scale-100"><Plus className="w-5 h-5" /></div>
                  </div>
                ))}
                {trainings.length === 0 && (
                  <div className="text-center py-16 opacity-40"><p className="text-xs font-bold uppercase tracking-widest">No custom sessions found</p><p className="text-[10px] mt-2">Create some workouts first to assign them to a plan.</p></div>
                )}
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
