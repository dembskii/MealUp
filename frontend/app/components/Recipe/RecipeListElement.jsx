"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { ENDPOINTS } from "../../config/network";

const api = axios.create({
  baseURL: ENDPOINTS.RECIPES,
  withCredentials: true,
});

export default function RecipeListElement({ recipe, onLike, onUnlike, onDelete }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [ingredients, setIngredients] = useState([]);
  const [loadingIngredients, setLoadingIngredients] = useState(false);
  const [ingredientError, setIngredientError] = useState(null);

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes} min`;
  };

  // Fetch ingredients when expanding
  const handleExpandToggle = async () => {
    if (!isExpanded && ingredients.length === 0 && recipe.ingredients?.length > 0) {
      setLoadingIngredients(true);
      setIngredientError(null);
      
      try {
        const { data: allIngredients } = await api.get("/ingredients?limit=500");
        
        const ingredientMap = {};
        allIngredients.forEach((ing) => {
          ingredientMap[ing.id || ing._id] = ing;
        });

        const enrichedIngredients = recipe.ingredients.map((item) => ({
          ...item,
          ingredient: ingredientMap[item.ingredient_id] || { name: "Unknown", units: "?" },
        }));

        setIngredients(enrichedIngredients);
      } catch (err) {
        console.error("Error fetching ingredients:", err);
        setIngredientError("Failed to load ingredients");
      } finally {
        setLoadingIngredients(false);
      }
    }

    setIsExpanded(!isExpanded);
  };

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 mb-4 bg-white dark:bg-gray-800 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-2">
            {recipe.name}
          </h3>
          
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm text-gray-500 dark:text-gray-400">
              ⏱️ {formatTime(recipe.time_to_prepare)}
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              • {recipe.ingredients?.length || 0} ingredients
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              • {recipe.prepare_instruction?.length || 0} steps
            </span>
          </div>

          <button
            onClick={handleExpandToggle}
            disabled={loadingIngredients}
            className="text-blue-600 dark:text-blue-400 text-sm hover:underline disabled:opacity-50"
          >
            {loadingIngredients ? "Loading..." : isExpanded ? "Hide details ▲" : "Show details ▼"}
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onLike(recipe._id)}
            className="flex items-center gap-1 px-3 py-1 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-full hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors"
          >
            ❤️ {recipe.total_likes || 0}
          </button>

          <button
            onClick={() => onDelete(recipe._id)}
            className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm"
          >
            🗑️
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
          {/* Images */}
          {recipe.images && recipe.images.length > 0 && (
            <div className="flex gap-2 mb-4 overflow-x-auto">
              {recipe.images.map((img, idx) => (
                <img
                  key={idx}
                  src={img}
                  alt={`Recipe image ${idx + 1}`}
                  className="w-24 h-24 object-cover rounded-lg"
                  onError={(e) => {
                    e.target.src = "https://via.placeholder.com/100?text=Error";
                  }}
                />
              ))}
            </div>
          )}

          {/* Ingredients */}
          <div className="mb-4">
            <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Ingredients:
            </h4>
            {ingredientError ? (
              <p className="text-sm text-red-500">{ingredientError}</p>
            ) : loadingIngredients ? (
              <p className="text-sm text-gray-500">Loading ingredients...</p>
            ) : ingredients.length > 0 ? (
              <ul className="list-disc list-inside text-sm text-gray-600 dark:text-gray-400">
                {ingredients.map((item, idx) => (
                  <li key={idx}>
                    <span className="font-medium">{item.ingredient?.name || "Unknown"}</span> —{" "}
                    {item.quantity} {item.capacity}
                    {item.ingredient?.units && (
                      <span className="text-xs text-gray-500"> (base: {item.ingredient.units})</span>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500">No ingredients</p>
            )}
          </div>

          {/* Instructions */}
          <div className="mb-4">
            <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Instructions:
            </h4>
            {recipe.prepare_instruction && recipe.prepare_instruction.length > 0 ? (
              <ol className="space-y-2">
                {recipe.prepare_instruction.map((step, idx) => (
                  <li key={idx} className="flex gap-3 text-sm text-gray-600 dark:text-gray-400">
                    <span className="flex-shrink-0 font-semibold text-blue-600 dark:text-blue-400 w-6">
                      {idx + 1}.
                    </span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="text-sm text-gray-500">No instructions</p>
            )}
          </div>

          {/* Metadata */}
          <div className="mt-4 text-xs text-gray-400">
            <span>Created: {new Date(recipe._created_at).toLocaleDateString()}</span>
            <span className="ml-4">Author: {recipe.author_id}</span>
          </div>
        </div>
      )}
    </div>
  );
}
