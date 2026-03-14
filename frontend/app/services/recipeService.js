import { ENDPOINTS } from '../config/network';

const BASE = ENDPOINTS.RECIPES;

const defaultOpts = {
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
};

async function request(url, opts = {}) {
  const res = await fetch(url, { ...defaultOpts, ...opts });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Recipe API ${res.status}: ${text}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

// ======================== RECIPES ========================

export async function getRecipes({ skip = 0, limit = 100 } = {}) {
  const params = new URLSearchParams({ skip, limit });
  return request(`${BASE}/?${params}`);
}

export async function getRecipeById(recipeId) {
  return request(`${BASE}/${recipeId}`);
}

export async function getIngredients({ skip = 0, limit = 500 } = {}) {
  const params = new URLSearchParams({ skip, limit });
  return request(`${BASE}/ingredients?${params}`);
}

export default { getRecipes, getRecipeById, getIngredients };
