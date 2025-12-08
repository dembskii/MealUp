"use client";

import { useState, useEffect } from "react";
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
    name: "",
    prepare_instruction: [""],
    time_to_prepare: 30,
    images: [],
  });
  const [ingredients, setIngredients] = useState([
    { ingredient_id: "", capacity: "g", quantity: 100 },
  ]);
  const [availableIngredients, setAvailableIngredients] = useState([]);
  const [searchTerms, setSearchTerms] = useState({});
  const [dropdownOpen, setDropdownOpen] = useState({});
  const [imageUrl, setImageUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [ingredientsLoading, setIngredientsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch all ingredients on mount
  useEffect(() => {
    const fetchIngredients = async () => {
      try {
        const { data } = await api.get("/ingredients?limit=500");
        console.log("Fetched ingredients:", data);
        setAvailableIngredients(data);
      } catch (err) {
        console.error("Error fetching ingredients:", err);
        setError("Failed to load ingredients");
      } finally {
        setIngredientsLoading(false);
      }
    };

    fetchIngredients();
  }, []);

  // Get ingredient ID - handle both 'id' and '_id' from API
  const getIngredientId = (ingredient) => {
    return ingredient.id || ingredient._id;
  };

  // Filter ingredients based on search term
  const getFilteredIngredients = (index) => {
    const searchTerm = searchTerms[index]?.toLowerCase() || "";
    if (!searchTerm) return availableIngredients;

    return availableIngredients.filter((ing) =>
      ing.name.toLowerCase().includes(searchTerm)
    );
  };

  const handleAddIngredient = () => {
    setIngredients([
      ...ingredients,
      { ingredient_id: "", capacity: "g", quantity: 100 },
    ]);
  };

  const handleRemoveIngredient = (index) => {
    if (ingredients.length > 1) {
      setIngredients(ingredients.filter((_, i) => i !== index));
      const newSearchTerms = { ...searchTerms };
      const newDropdownOpen = { ...dropdownOpen };
      delete newSearchTerms[index];
      delete newDropdownOpen[index];
      setSearchTerms(newSearchTerms);
      setDropdownOpen(newDropdownOpen);
    }
  };

  const handleIngredientChange = (index, field, value) => {
    const updated = [...ingredients];
    updated[index][field] = value;
    setIngredients(updated);
  };

  const handleSelectIngredient = (index, ingredient) => {
    const updated = [...ingredients];
    updated[index].ingredient_id = getIngredientId(ingredient);
    setIngredients(updated);
    setDropdownOpen({ ...dropdownOpen, [index]: false });
    setSearchTerms({ ...searchTerms, [index]: "" });
  };

  const handleSearchChange = (index, value) => {
    setSearchTerms({ ...searchTerms, [index]: value });
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

  const handleAddStep = () => {
    setFormData({
      ...formData,
      prepare_instruction: [...formData.prepare_instruction, ""],
    });
  };

  const handleRemoveStep = (index) => {
    if (formData.prepare_instruction.length > 1) {
      setFormData({
        ...formData,
        prepare_instruction: formData.prepare_instruction.filter((_, i) => i !== index),
      });
    }
  };

  const handleStepChange = (index, value) => {
    const updated = [...formData.prepare_instruction];
    updated[index] = value;
    setFormData({
      ...formData,
      prepare_instruction: updated,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Validate
    if (!formData.name.trim()) {
      setError("Please provide a recipe name.");
      setLoading(false);
      return;
    }

    if (formData.prepare_instruction.some((step) => !step.trim())) {
      setError("All instruction steps must be filled.");
      setLoading(false);
      return;
    }

    if (ingredients.some((ing) => !ing.ingredient_id)) {
      setError("All ingredients must be selected.");
      setLoading(false);
      return;
    }

    const payload = {
      name: formData.name.trim(),
      ingredients: ingredients.map((ing) => ({
        ingredient_id: ing.ingredient_id,
        capacity: ing.capacity,
        quantity: ing.quantity,
      })),
      prepare_instruction: formData.prepare_instruction.map((step) => step.trim()),
      time_to_prepare: formData.time_to_prepare * 60, // Convert minutes to seconds
      images: formData.images.length > 0 ? formData.images : null,
    };

    try {
      console.log("Submitting payload:", payload);
      const { data } = await api.post("/", payload);
      console.log("Recipe created successfully:", data);
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

          {ingredientsLoading && (
            <div className="mb-4 p-3 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-lg">
              Loading ingredients...
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Recipe Name */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Recipe Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    name: e.target.value,
                  })
                }
                placeholder="e.g., Tomato Pasta"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200"
                required
              />
            </div>

            {/* Ingredients */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Ingredients ({ingredients.length})
              </label>
              {ingredients.map((ing, index) => {
                const selectedIngredient = availableIngredients.find(
                  (i) => getIngredientId(i) === ing.ingredient_id
                );
                const filteredIngredients = getFilteredIngredients(index);
                const isOpen = dropdownOpen[index] || false;

                return (
                  <div
                    key={index}
                    className="mb-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg"
                  >
                    {/* Ingredient Selector */}
                    <div className="relative mb-2">
                      <div
                        className="flex items-center gap-2 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 cursor-pointer hover:border-gray-400 dark:hover:border-gray-500"
                        onClick={() =>
                          setDropdownOpen({
                            ...dropdownOpen,
                            [index]: !isOpen,
                          })
                        }
                      >
                        <span className="text-sm text-gray-600 dark:text-gray-400 flex-1">
                          {selectedIngredient ? (
                            <span className="text-gray-800 dark:text-gray-200 font-medium">
                              {selectedIngredient.name}
                            </span>
                          ) : (
                            "Select ingredient..."
                          )}
                        </span>
                        <span className="text-gray-400">▼</span>
                      </div>

                      {isOpen && (
                        <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg z-10">
                          <input
                            type="text"
                            placeholder="Search ingredients..."
                            value={searchTerms[index] || ""}
                            onChange={(e) =>
                              handleSearchChange(index, e.target.value)
                            }
                            className="w-full px-3 py-2 border-b border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 text-sm"
                            autoFocus
                          />
                          <div className="max-h-40 overflow-y-auto">
                            {filteredIngredients.length > 0 ? (
                              filteredIngredients.map((ingredient) => (
                                <div
                                  key={getIngredientId(ingredient)}
                                  onClick={() =>
                                    handleSelectIngredient(index, ingredient)
                                  }
                                  className="px-3 py-2 hover:bg-blue-50 dark:hover:bg-blue-900/30 cursor-pointer text-sm text-gray-700 dark:text-gray-300 flex justify-between items-center"
                                >
                                  <span>{ingredient.name}</span>
                                  <span className="text-xs text-gray-500 dark:text-gray-400">
                                    {ingredient.units}
                                  </span>
                                </div>
                              ))
                            ) : (
                              <div className="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">
                                No ingredients found
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Quantity & Unit */}
                    <div className="flex gap-2">
                      <input
                        type="number"
                        placeholder="Quantity"
                        value={ing.quantity}
                        onChange={(e) =>
                          handleIngredientChange(
                            index,
                            "quantity",
                            e.target.value
                          )
                        }
                        className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 text-sm"
                        min="0.1"
                        step="0.1"
                        required
                      />
                      <select
                        value={ing.capacity}
                        onChange={(e) =>
                          handleIngredientChange(
                            index,
                            "capacity",
                            e.target.value
                          )
                        }
                        className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 text-sm"
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
                          className="px-3 py-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg font-semibold"
                        >
                          🗑️
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}

              <button
                type="button"
                onClick={handleAddIngredient}
                disabled={ingredientsLoading}
                className="mt-2 w-full px-4 py-2 text-blue-600 dark:text-blue-400 border border-blue-600 dark:border-blue-400 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition disabled:opacity-50"
              >
                + Add Ingredient
              </button>
            </div>

            {/* Preparation Instructions */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Preparation Instructions ({formData.prepare_instruction.length} steps)
              </label>
              {formData.prepare_instruction.map((step, index) => (
                <div key={index} className="mb-2 flex gap-2">
                  <div className="flex-shrink-0 w-8 h-10 flex items-center justify-center bg-blue-100 dark:bg-blue-900/30 rounded-lg text-sm font-semibold text-blue-600 dark:text-blue-400">
                    {index + 1}
                  </div>
                  <textarea
                    value={step}
                    onChange={(e) => handleStepChange(index, e.target.value)}
                    placeholder={`Step ${index + 1}...`}
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 h-16 resize-none text-sm"
                    required
                  />
                  {formData.prepare_instruction.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveStep(index)}
                      className="px-3 py-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg font-semibold flex-shrink-0"
                    >
                      🗑️
                    </button>
                  )}
                </div>
              ))}

              <button
                type="button"
                onClick={handleAddStep}
                className="mt-2 w-full px-4 py-2 text-blue-600 dark:text-blue-400 border border-blue-600 dark:border-blue-400 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition"
              >
                + Add Step
              </button>
            </div>

            {/* Preparation Time */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Preparation Time (minutes)
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

            {/* Images */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Recipe Images
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
                  className="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-400 dark:hover:bg-gray-500 transition"
                >
                  Add
                </button>
              </div>

              {formData.images.length > 0 && (
                <div className="grid grid-cols-3 gap-2">
                  {formData.images.map((img, idx) => (
                    <div
                      key={idx}
                      className="relative group bg-gray-200 dark:bg-gray-700 rounded-lg overflow-hidden"
                    >
                      <img
                        src={img}
                        alt={`Recipe ${idx}`}
                        className="w-full h-24 object-cover"
                        onError={(e) => {
                          e.target.src =
                            "https://via.placeholder.com/150?text=Invalid+URL";
                        }}
                      />
                      <button
                        type="button"
                        onClick={() => handleRemoveImage(idx)}
                        className="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition text-white"
                      >
                        🗑️
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Submit */}
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={loading || ingredientsLoading}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {loading ? "Creating..." : "Create Recipe"}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-400 dark:hover:bg-gray-500 transition font-medium"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
