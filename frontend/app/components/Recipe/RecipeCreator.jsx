"use client";

import { useState } from "react";
import axios from "axios";
import { ENDPOINTS } from "../../config/network";

const API_URL = ENDPOINTS.RECIPES;

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

const CAPACITY_UNITS = [
  { value: "g", label: "grams (g)" },
  { value: "kg", label: "kilograms (kg)" },
  { value: "ml", label: "milliliters (ml)" },
  { value: "l", label: "liters (l)" },
  { value: "tsp", label: "teaspoon (tsp)" },
  { value: "tbsp", label: "tablespoon (tbsp)" },
  { value: "cup", label: "cup" },
  { value: "oz", label: "ounce (oz)" },
  { value: "lb", label: "pound (lb)" },
  { value: "pcs", label: "pieces (pcs)" },
];

export default function RecipeCreator({ onClose, onRecipeCreated }) {
  const [formData, setFormData] = useState({
    prepare_instruction: "",
    time_to_prepare: 30,
    images: [],
  });
  const [ingredients, setIngredients] = useState([
    { ingredient: { name: "", units: "g" }, capacity: "g", quantity: 100 },
  ]);
  const [imageUrl, setImageUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAddIngredient = () => {
    setIngredients([
      ...ingredients,
      { ingredient: { name: "", units: "g" }, capacity: "g", quantity: 100 },
    ]);
  };

  const handleRemoveIngredient = (index) => {
    if (ingredients.length > 1) {
      setIngredients(ingredients.filter((_, i) => i !== index));
    }
  };

  const handleIngredientChange = (index, field, value) => {
    const updated = [...ingredients];
    if (field === "name" || field === "units") {
      updated[index].ingredient[field] = value;
    } else if (field === "capacity") {
      updated[index].capacity = value;
    } else if (field === "quantity") {
      updated[index].quantity = parseFloat(value) || 0;
    }
    setIngredients(updated);
  };

  const handleAddImage = () => {
    if (imageUrl.trim()) {
      setFormData({
        ...formData,
        images: [...formData.images, imageUrl.trim()],
      });
      setImageUrl("");
    }
  };

  const handleRemoveImage = (index) => {
    setFormData({
      ...formData,
      images: formData.images.filter((_, i) => i !== index),
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Validate
    if (!formData.prepare_instruction.trim()) {
      setError("Please provide preparation instructions.");
      setLoading(false);
      return;
    }

    if (ingredients.some((ing) => !ing.ingredient.name.trim())) {
      setError("All ingredients must have a name.");
      setLoading(false);
      return;
    }

    const payload = {
      ingredients: ingredients.map((ing) => ({
        ingredient: {
          name: ing.ingredient.name,
          units: ing.ingredient.units,
        },
        capacity: ing.capacity,
        quantity: ing.quantity,
      })),
      prepare_instruction: formData.prepare_instruction,
      time_to_prepare: formData.time_to_prepare * 60, // Convert minutes to seconds
      images: formData.images.length > 0 ? formData.images : null,
    };

    try {
      const { data } = await api.post("/", payload);
      onRecipeCreated(data);
      onClose();
    } catch (err) {
      console.error("Error creating recipe:", err);
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100">
              Create New Recipe
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 text-2xl"
            >
              ×
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-lg">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Ingredients */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Ingredients
              </label>
              {ingredients.map((ing, index) => (
                <div key={index} className="flex gap-2 mb-2 items-center">
                  <input
                    type="text"
                    placeholder="Ingredient name"
                    value={ing.ingredient.name}
                    onChange={(e) =>
                      handleIngredientChange(index, "name", e.target.value)
                    }
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200"
                    required
                  />
                  <input
                    type="number"
                    placeholder="Qty"
                    value={ing.quantity}
                    onChange={(e) =>
                      handleIngredientChange(index, "quantity", e.target.value)
                    }
                    className="w-20 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200"
                    min="0.1"
                    step="0.1"
                    required
                  />
                  <select
                    value={ing.capacity}
                    onChange={(e) =>
                      handleIngredientChange(index, "capacity", e.target.value)
                    }
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200"
                  >
                    {CAPACITY_UNITS.map((unit) => (
                      <option key={unit.value} value={unit.value}>
                        {unit.label}
                      </option>
                    ))}
                  </select>
                  {ingredients.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveIngredient(index)}
                      className="px-3 py-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
                    >
                      🗑️
                    </button>
                  )}
                </div>
              ))}
              <button
                type="button"
                onClick={handleAddIngredient}
                className="mt-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
              >
                + Add ingredient
              </button>
            </div>

            {/* Time to prepare */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Time to prepare (minutes)
              </label>
              <input
                type="number"
                value={formData.time_to_prepare}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    time_to_prepare: parseInt(e.target.value) || 0,
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200"
                min="1"
                required
              />
            </div>

            {/* Instructions */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Preparation Instructions
              </label>
              <textarea
                value={formData.prepare_instruction}
                onChange={(e) =>
                  setFormData({ ...formData, prepare_instruction: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 h-32"
                placeholder="1. First step...&#10;2. Second step...&#10;3. Third step..."
                required
              />
            </div>

            {/* Images */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Images (optional)
              </label>
              <div className="flex gap-2 mb-2">
                <input
                  type="url"
                  placeholder="Image URL"
                  value={imageUrl}
                  onChange={(e) => setImageUrl(e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200"
                />
                <button
                  type="button"
                  onClick={handleAddImage}
                  className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
                >
                  Add
                </button>
              </div>
              {formData.images.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {formData.images.map((img, index) => (
                    <div key={index} className="relative group">
                      <img
                        src={img}
                        alt={`Preview ${index + 1}`}
                        className="w-16 h-16 object-cover rounded-lg"
                      />
                      <button
                        type="button"
                        onClick={() => handleRemoveImage(index)}
                        className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-5 h-5 text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-3 justify-end">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Creating..." : "Create Recipe"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
