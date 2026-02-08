import { ENDPOINTS } from '../config/network';

const BASE = ENDPOINTS.WORKOUTS;

const defaultOpts = {
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
};

async function request(url, opts = {}) {
  const res = await fetch(url, { ...defaultOpts, ...opts });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Workout API ${res.status}: ${text}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

// ======================== EXERCISES ========================

export async function getExercises({ skip = 0, limit = 200, search, body_part, advancement, category } = {}) {
  const params = new URLSearchParams();
  params.set('skip', skip);
  params.set('limit', limit);
  if (search) params.set('search', search);
  if (body_part) params.set('body_part', body_part);
  if (advancement) params.set('advancement', advancement);
  if (category) params.set('category', category);
  return request(`${BASE}/exercises?${params}`);
}

export async function getExercise(exerciseId) {
  return request(`${BASE}/exercises/${exerciseId}`);
}

export async function createExercise(data) {
  return request(`${BASE}/exercises`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateExercise(exerciseId, data) {
  return request(`${BASE}/exercises/${exerciseId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteExercise(exerciseId) {
  return request(`${BASE}/exercises/${exerciseId}`, { method: 'DELETE' });
}

export async function searchExercises(q, { body_part, advancement, category, skip = 0, limit = 20 } = {}) {
  const params = new URLSearchParams();
  params.set('q', q);
  if (body_part) params.set('body_part', body_part);
  if (advancement) params.set('advancement', advancement);
  if (category) params.set('category', category);
  params.set('skip', skip);
  params.set('limit', limit);
  return request(`${BASE}/exercises/search?${params}`);
}

// ======================== TRAININGS ========================

export async function getTrainings({ skip = 0, limit = 100, training_type, search } = {}) {
  const params = new URLSearchParams();
  params.set('skip', skip);
  params.set('limit', limit);
  if (training_type) params.set('training_type', training_type);
  if (search) params.set('search', search);
  return request(`${BASE}/trainings?${params}`);
}

export async function getTraining(trainingId) {
  return request(`${BASE}/trainings/${trainingId}`);
}

export async function getTrainingWithExercises(trainingId) {
  return request(`${BASE}/trainings/${trainingId}/with-exercises`);
}

export async function createTraining(data) {
  return request(`${BASE}/trainings`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateTraining(trainingId, data) {
  return request(`${BASE}/trainings/${trainingId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteTraining(trainingId) {
  return request(`${BASE}/trainings/${trainingId}`, { method: 'DELETE' });
}

// ======================== WORKOUT PLANS ========================

export async function getWorkoutPlans({ skip = 0, limit = 100, search, is_public, trainer_id } = {}) {
  const params = new URLSearchParams();
  params.set('skip', skip);
  params.set('limit', limit);
  if (search) params.set('search', search);
  if (is_public != null) params.set('is_public', is_public);
  if (trainer_id) params.set('trainer_id', trainer_id);
  return request(`${BASE}/plans?${params}`);
}

export async function getMyWorkoutPlans({ skip = 0, limit = 100 } = {}) {
  const params = new URLSearchParams();
  params.set('skip', skip);
  params.set('limit', limit);
  return request(`${BASE}/plans/my-plans?${params}`);
}

export async function getAssignedWorkoutPlans({ skip = 0, limit = 100 } = {}) {
  const params = new URLSearchParams();
  params.set('skip', skip);
  params.set('limit', limit);
  return request(`${BASE}/plans/assigned-to-me?${params}`);
}

export async function getWorkoutPlan(planId) {
  return request(`${BASE}/plans/${planId}`);
}

export async function getWorkoutPlanDetailed(planId) {
  return request(`${BASE}/plans/${planId}/detailed`);
}

export async function createWorkoutPlan(data) {
  return request(`${BASE}/plans`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateWorkoutPlan(planId, data) {
  return request(`${BASE}/plans/${planId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteWorkoutPlan(planId) {
  return request(`${BASE}/plans/${planId}`, { method: 'DELETE' });
}

export async function addClientToPlan(planId, clientId) {
  return request(`${BASE}/plans/${planId}/clients/${clientId}`, { method: 'POST' });
}

export async function removeClientFromPlan(planId, clientId) {
  return request(`${BASE}/plans/${planId}/clients/${clientId}`, { method: 'DELETE' });
}

export async function addTrainingToPlan(planId, trainingId) {
  return request(`${BASE}/plans/${planId}/trainings/${trainingId}`, { method: 'POST' });
}

export async function removeTrainingFromPlan(planId, trainingId) {
  return request(`${BASE}/plans/${planId}/trainings/${trainingId}`, { method: 'DELETE' });
}

export async function likeWorkoutPlan(planId) {
  return request(`${BASE}/plans/${planId}/like`, { method: 'POST' });
}

export async function unlikeWorkoutPlan(planId) {
  return request(`${BASE}/plans/${planId}/unlike`, { method: 'POST' });
}
