"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import RecipeListElement from "./RecipeListElement";
import { ENDPOINTS } from "../../config/network";

const API_URL = ENDPOINTS.RECIPES;

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

export default function RecipeList({ onAddRecipe }) {
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchRecipes = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get("/");
      setRecipes(data);
    } catch (err) {
      console.error("Error fetching recipes:", err);
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecipes();
  }, []);

  const handleLike = async (recipeId) => {
    try {
      const { data } = await api.post(`/${recipeId}/like`);
      setRecipes((prev) =>
        prev.map((r) => (r._id === recipeId ? data : r))
      );
    } catch (err) {
      console.error("Error liking recipe:", err);
    }
  };

  const handleUnlike = async (recipeId) => {
    try {
      const { data } = await api.post(`/${recipeId}/unlike`);
      setRecipes((prev) =>
        prev.map((r) => (r._id === recipeId ? data : r))
      );
    } catch (err) {
      console.error("Error unliking recipe:", err);
    }
  };

  const handleDelete = async (recipeId) => {
    if (!confirm("Are you sure you want to delete this recipe?")) {
      return;
    }
    try {
      await api.delete(`/${recipeId}`);
      setRecipes((prev) => prev.filter((r) => r._id !== recipeId));
    } catch (err) {
      console.error("Error deleting recipe:", err);
      alert(err.response?.data?.detail || "Failed to delete recipe. You may not have permission.");
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600 dark:text-gray-400">Loading recipes...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500 mb-4">Error: {typeof error === 'string' ? error : error.message}</p>
        <button
          onClick={fetchRecipes}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100">
          Recipes ({recipes.length})
        </h2>
        <button
          onClick={onAddRecipe}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
        >
          <span>➕</span> Add Recipe
        </button>
      </div>

      {recipes.length === 0 ? (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          <p className="text-lg mb-4">No recipes yet.</p>
          <button
            onClick={onAddRecipe}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Create your first recipe
          </button>
        </div>
      ) : (
        <div>
          {recipes.map((recipe) => (
            <RecipeListElement
              key={recipe._id}
              recipe={recipe}
              onLike={handleLike}
              onUnlike={handleUnlike}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}
