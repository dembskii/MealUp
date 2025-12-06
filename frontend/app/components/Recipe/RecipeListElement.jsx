"use client";

import { useState } from "react";

export default function RecipeListElement({ recipe, onLike, onUnlike, onDelete }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes} min`;
  };

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 mb-4 bg-white dark:bg-gray-800 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm text-gray-500 dark:text-gray-400">
              ⏱️ {formatTime(recipe.time_to_prepare)}
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              • {recipe.ingredients?.length || 0} ingredients
            </span>
          </div>
          
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-blue-600 dark:text-blue-400 text-sm hover:underline"
          >
            {isExpanded ? "Hide details ▲" : "Show details ▼"}
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
                />
              ))}
            </div>
          )}

          {/* Ingredients */}
          <div className="mb-4">
            <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Ingredients:
            </h4>
            <ul className="list-disc list-inside text-sm text-gray-600 dark:text-gray-400">
              {recipe.ingredients?.map((item, idx) => (
                <li key={idx}>
                  {item.ingredient?.name || "Unknown"} - {item.quantity} {item.capacity}
                </li>
              ))}
            </ul>
          </div>

          {/* Instructions */}
          <div>
            <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Instructions:
            </h4>
            <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-line">
              {recipe.prepare_instruction}
            </p>
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
