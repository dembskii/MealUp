import { BodyPart, Advancement, ExerciseCategory } from './types';

// --- MOCK DATABASE FOR EXERCISES ---
export const MOCK_EXERCISES_DB = {
  'ex_burpee': { _id: 'ex_burpee', name: 'Burpees', body_part: BodyPart.FULL_BODY, advancement: Advancement.INTERMEDIATE, category: ExerciseCategory.HIIT },
  'ex_pushup': { _id: 'ex_pushup', name: 'Pushups', body_part: BodyPart.CHEST, advancement: Advancement.BEGINNER, category: ExerciseCategory.CALISTHENICS },
  'ex_squat_jump': { _id: 'ex_squat_jump', name: 'Jump Squats', body_part: BodyPart.QUADRICEPS, advancement: Advancement.INTERMEDIATE, category: ExerciseCategory.PLYOMETRIC },
  'ex_bench': { _id: 'ex_bench', name: 'Barbell Bench Press', body_part: BodyPart.CHEST, advancement: Advancement.INTERMEDIATE, category: ExerciseCategory.STRENGTH },
  'ex_pullup': { _id: 'ex_pullup', name: 'Pull Ups', body_part: BodyPart.BACK, advancement: Advancement.ADVANCED, category: ExerciseCategory.CALISTHENICS },
  'ex_ohp': { _id: 'ex_ohp', name: 'Overhead Press', body_part: BodyPart.SHOULDERS, advancement: Advancement.INTERMEDIATE, category: ExerciseCategory.STRENGTH },
  'ex_squat': { _id: 'ex_squat', name: 'Barbell Squat', body_part: BodyPart.QUADRICEPS, advancement: Advancement.INTERMEDIATE, category: ExerciseCategory.STRENGTH },
  'ex_dl': { _id: 'ex_dl', name: 'Deadlift', body_part: BodyPart.HAMSTRINGS, advancement: Advancement.ADVANCED, category: ExerciseCategory.POWERLIFTING },
  'ex_plank': { _id: 'ex_plank', name: 'Plank', body_part: BodyPart.ABS, advancement: Advancement.BEGINNER, category: ExerciseCategory.STRENGTH },
  'ex_lunge': { _id: 'ex_lunge', name: 'Walking Lunges', body_part: BodyPart.GLUTES, advancement: Advancement.BEGINNER, category: ExerciseCategory.STRENGTH },
};
