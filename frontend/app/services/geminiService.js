// Stub service — returns mock data instead of calling Gemini API

import { DayOfWeek } from '../data/types';

export const generateRecipe = async (_prompt) => {
  // Simulate network delay
  await new Promise((r) => setTimeout(r, 1500));

  return {
    id: crypto.randomUUID(),
    title: 'AI-Generated Power Bowl',
    description: 'A balanced meal crafted by our AI chef, packed with nutrients and flavour.',
    calories: 520,
    protein: 30,
    carbs: 55,
    fat: 18,
    prepTime: '25 min',
    tags: ['AI', 'Balanced', 'Lunch'],
    ingredients: [
      '150g Brown Rice',
      '120g Grilled Chicken',
      '1/2 Avocado',
      '1 cup Mixed Greens',
      '2 tbsp Tahini Dressing',
    ],
    instructions: [
      'Cook brown rice according to package instructions.',
      'Grill chicken breast seasoned with salt, pepper & paprika.',
      'Slice avocado and arrange greens in a bowl.',
      'Top with rice, sliced chicken and avocado.',
      'Drizzle with tahini dressing and serve.',
    ],
    imageUrl: `https://picsum.photos/400/300?random=${Math.floor(Math.random() * 1000)}`,
  };
};

export const generateWorkout = async (_goal) => {
  await new Promise((r) => setTimeout(r, 1500));

  return {
    _id: crypto.randomUUID(),
    name: 'AI Full-Body Blast',
    description: 'An AI-generated session targeting all major muscle groups.',
    est_time: 2700,
    day: DayOfWeek.MONDAY,
    training_type: 'hiit',
    exercises: [
      {
        exercise_id: 'ex_burpee',
        sets: [
          { volume: 12, units: 'reps' },
          { volume: 12, units: 'reps' },
          { volume: 12, units: 'reps' },
        ],
        rest_between_sets: 45,
      },
      {
        exercise_id: 'ex_squat',
        sets: [
          { volume: 10, units: 'reps' },
          { volume: 10, units: 'reps' },
          { volume: 10, units: 'reps' },
        ],
        rest_between_sets: 60,
      },
      {
        exercise_id: 'ex_pushup',
        sets: [
          { volume: 15, units: 'reps' },
          { volume: 15, units: 'reps' },
          { volume: 15, units: 'reps' },
        ],
        rest_between_sets: 45,
      },
    ],
  };
};
