"use client";

import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { ENDPOINTS } from "../../config/network";
import { X, Plus, Minus, Trash2, Clock, ChefHat, Image, Loader2, Save, Search, ChevronDown } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const API_URL = ENDPOINTS.RECIPES;

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

const CAPACITY_UNITS = [
  { value: "g", label: "g" },
  { value: "kg", label: "kg" },
  { value: "ml", label: "ml" },
  { value: "l", label: "l" },
  { value: "tsp", label: "tsp" },
  { value: "tbsp", label: "tbsp" },
  { value: "cup", label: "cup" },
  { value: "oz", label: "oz" },
  { value: "lb", label: "lb" },
  { value: "pcs", label: "pcs" },
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
  const dropdownRefs = useRef({});

  useEffect(() => {
    const fetchIngredients = async () => {
      try {
        const { data } = await api.get("/ingredients?limit=500");
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

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      const openKeys = Object.keys(dropdownOpen).filter(k => dropdownOpen[k]);
      if (openKeys.length === 0) return;
      for (const key of openKeys) {
        if (dropdownRefs.current[key] && !dropdownRefs.current[key].contains(e.target)) {
          setDropdownOpen(prev => ({ ...prev, [key]: false }));
        }
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [dropdownOpen]);

  const getIngredientId = (ingredient) => ingredient.id || ingredient._id;

  const getFilteredIngredients = (index) => {
    const searchTerm = searchTerms[index]?.toLowerCase() || "";
    if (!searchTerm) return availableIngredients;
    return availableIngredients.filter((ing) =>
      ing.name.toLowerCase().includes(searchTerm)
    );
  };

  const handleAddIngredient = () => {
    setIngredients([...ingredients, { ingredient_id: "", capacity: "g", quantity: 100 }]);
  };

  const handleRemoveIngredient = (index) => {
    if (ingredients.length > 1) {
      setIngredients(ingredients.filter((_, i) => i !== index));
      const ns = { ...searchTerms }; delete ns[index];
      const nd = { ...dropdownOpen }; delete nd[index];
      setSearchTerms(ns);
      setDropdownOpen(nd);
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

  const handleAddImage = () => {
    if (imageUrl.trim()) {
      setFormData({ ...formData, images: [...formData.images, imageUrl.trim()] });
      setImageUrl("");
    }
  };

  const handleRemoveImage = (index) => {
    setFormData({ ...formData, images: formData.images.filter((_, i) => i !== index) });
  };

  const handleAddStep = () => {
    setFormData({ ...formData, prepare_instruction: [...formData.prepare_instruction, ""] });
  };

  const handleRemoveStep = (index) => {
    if (formData.prepare_instruction.length > 1) {
      setFormData({ ...formData, prepare_instruction: formData.prepare_instruction.filter((_, i) => i !== index) });
    }
  };

  const handleStepChange = (index, value) => {
    const updated = [...formData.prepare_instruction];
    updated[index] = value;
    setFormData({ ...formData, prepare_instruction: updated });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    if (!formData.name.trim()) { setError("Please provide a recipe name."); setLoading(false); return; }
    if (formData.prepare_instruction.some((s) => !s.trim())) { setError("All instruction steps must be filled."); setLoading(false); return; }
    if (ingredients.some((ing) => !ing.ingredient_id)) { setError("All ingredients must be selected."); setLoading(false); return; }

    const payload = {
      name: formData.name.trim(),
      ingredients: ingredients.map((ing) => ({ ingredient_id: ing.ingredient_id, capacity: ing.capacity, quantity: ing.quantity })),
      prepare_instruction: formData.prepare_instruction.map((s) => s.trim()),
      time_to_prepare: formData.time_to_prepare * 60,
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

  const getSelectedName = (index) => {
    const id = ingredients[index]?.ingredient_id;
    if (!id) return null;
    const found = availableIngredients.find(i => getIngredientId(i) === id);
    return found?.name || null;
  };

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center p-4">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose}
        className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" />
      <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="w-full max-w-3xl glass-panel bg-white/95 dark:bg-slate-900/95 backdrop-blur-3xl rounded-[2.5rem] relative z-10 flex flex-col max-h-[90vh] shadow-2xl overflow-hidden border border-white/50 dark:border-white/10">

        {/* Header */}
        <div className="p-8 border-b border-slate-200 dark:border-white/10 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-slate-800 dark:text-white flex items-center gap-3">
            <ChefHat className="w-6 h-6 text-brand-500" /> Create New Recipe
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-slate-100 dark:hover:bg-white/10 rounded-full transition-colors">
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="flex flex-col flex-1 overflow-hidden">
          <div className="flex-1 overflow-y-auto p-8 space-y-6">
            <AnimatePresence>
              {error && (
                <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
                  className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-2xl border border-red-200 dark:border-red-500/20 text-sm font-medium">
                  {error}
                </motion.div>
              )}
            </AnimatePresence>

            {ingredientsLoading && (
              <div className="flex items-center gap-3 p-4 bg-brand-50 dark:bg-brand-900/20 rounded-2xl border border-brand-200 dark:border-brand-500/20">
                <Loader2 className="w-4 h-4 animate-spin text-brand-500" />
                <span className="text-sm text-brand-600 dark:text-brand-400 font-medium">Loading ingredients...</span>
              </div>
            )}

            {/* Recipe Name */}
            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 block">Recipe Name</label>
              <input type="text" value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Tomato Pasta"
                className="w-full p-3 liquid-input rounded-2xl text-slate-800 dark:text-white outline-none font-medium placeholder-slate-400"
                required />
            </div>

            {/* Prep Time */}
            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-2">
                <Clock className="w-3 h-3" /> Prep Time (minutes)
              </label>
              <div className="flex items-center gap-2">
                <button type="button" onClick={() => setFormData(prev => ({ ...prev, time_to_prepare: Math.max(1, prev.time_to_prepare - 5) }))}
                  className="w-10 h-10 flex items-center justify-center rounded-xl liquid-input text-slate-500 hover:text-brand-500 hover:bg-brand-500/10 transition-colors shrink-0"><Minus className="w-4 h-4" /></button>
                <input type="text" inputMode="numeric" value={formData.time_to_prepare}
                  onChange={(e) => setFormData({ ...formData, time_to_prepare: parseInt(e.target.value) || 1 })}
                  className="flex-1 p-3 liquid-input rounded-2xl text-slate-800 dark:text-white outline-none font-medium text-center"
                  required />
                <button type="button" onClick={() => setFormData(prev => ({ ...prev, time_to_prepare: prev.time_to_prepare + 5 }))}
                  className="w-10 h-10 flex items-center justify-center rounded-xl liquid-input text-slate-500 hover:text-brand-500 hover:bg-brand-500/10 transition-colors shrink-0"><Plus className="w-4 h-4" /></button>
              </div>
            </div>

            {/* Ingredients */}
            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3 block">
                Ingredients ({ingredients.length})
              </label>
              <div className="space-y-3">
                {ingredients.map((ing, index) => {
                  const selectedName = getSelectedName(index);
                  const filteredIngredients = getFilteredIngredients(index);
                  const isOpen = dropdownOpen[index] || false;

                  return (
                    <div key={index} className="p-4 bg-white/40 dark:bg-white/5 rounded-2xl border border-white/50 dark:border-white/10 space-y-3">
                      {/* Ingredient Selector */}
                      <div className="relative" ref={(el) => (dropdownRefs.current[index] = el)}>
                        <button type="button"
                          onClick={() => setDropdownOpen({ ...dropdownOpen, [index]: !isOpen })}
                          className="w-full flex items-center justify-between p-3 liquid-input rounded-xl text-left">
                          <span className={`text-sm font-medium ${selectedName ? 'text-slate-800 dark:text-white' : 'text-slate-400'}`}>
                            {selectedName || 'Select ingredient...'}
                          </span>
                          <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
                        </button>

                        <AnimatePresence>
                          {isOpen && (
                            <motion.div initial={{ opacity: 0, y: -5 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -5 }}
                              className="absolute top-full left-0 right-0 mt-1 z-20 glass-panel bg-white/95 dark:bg-slate-900/95 rounded-xl overflow-hidden shadow-xl border border-white/50 dark:border-white/10">
                              <div className="p-2 border-b border-slate-100 dark:border-white/10">
                                <div className="relative">
                                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
                                  <input type="text" placeholder="Search ingredients..."
                                    value={searchTerms[index] || ""}
                                    onChange={(e) => setSearchTerms({ ...searchTerms, [index]: e.target.value })}
                                    className="w-full pl-9 pr-3 py-2 text-sm liquid-input rounded-lg outline-none"
                                    autoFocus />
                                </div>
                              </div>
                              <div className="max-h-40 overflow-y-auto">
                                {filteredIngredients.length > 0 ? (
                                  filteredIngredients.map((ingredient) => (
                                    <button type="button" key={getIngredientId(ingredient)}
                                      onClick={() => handleSelectIngredient(index, ingredient)}
                                      className="w-full px-4 py-2.5 text-left hover:bg-brand-50 dark:hover:bg-brand-900/20 text-sm text-slate-700 dark:text-slate-300 font-medium transition-colors flex justify-between items-center">
                                      <span>{ingredient.name}</span>
                                      {ingredient.macro_per_hundred && (
                                        <span className="text-[10px] text-slate-400 font-bold">
                                          {Math.round(ingredient.macro_per_hundred.calories)} kcal
                                        </span>
                                      )}
                                    </button>
                                  ))
                                ) : (
                                  <div className="px-4 py-3 text-sm text-slate-400 text-center">No ingredients found</div>
                                )}
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>

                      {/* Quantity & Unit & Remove */}
                      <div className="flex items-center gap-2">
                        <button type="button" onClick={() => handleIngredientChange(index, "quantity", Math.max(0.1, (ing.quantity || 0.1) - 1))}
                          className="w-8 h-8 flex items-center justify-center rounded-lg liquid-input text-slate-400 hover:text-brand-500 hover:bg-brand-500/10 transition-colors shrink-0"><Minus className="w-3 h-3" /></button>
                        <input type="text" inputMode="decimal" placeholder="Qty" value={ing.quantity}
                          onChange={(e) => handleIngredientChange(index, "quantity", parseFloat(e.target.value) || 0)}
                          className="w-16 p-2.5 text-sm liquid-input rounded-xl text-center font-medium"
                          required />
                        <button type="button" onClick={() => handleIngredientChange(index, "quantity", (ing.quantity || 0) + 1)}
                          className="w-8 h-8 flex items-center justify-center rounded-lg liquid-input text-slate-400 hover:text-brand-500 hover:bg-brand-500/10 transition-colors shrink-0"><Plus className="w-3 h-3" /></button>
                        <div className="relative">
                          <select value={ing.capacity}
                            onChange={(e) => handleIngredientChange(index, "capacity", e.target.value)}
                            className="p-2.5 text-sm liquid-input rounded-xl text-slate-800 dark:text-white font-medium outline-none appearance-none cursor-pointer pr-7">
                            {CAPACITY_UNITS.map((u) => <option key={u.value} value={u.value}>{u.label}</option>)}
                          </select>
                          <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-400 pointer-events-none" />
                        </div>
                        {ingredients.length > 1 && (
                          <button type="button" onClick={() => handleRemoveIngredient(index)}
                            className="p-2 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-full text-red-500 transition-colors">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}

                <button type="button" onClick={handleAddIngredient} disabled={ingredientsLoading}
                  className="w-full p-3 rounded-xl border-2 border-dashed border-slate-200 dark:border-white/10 text-slate-400 hover:border-brand-500 hover:text-brand-500 transition-colors text-sm font-bold flex items-center justify-center gap-2 disabled:opacity-50">
                  <Plus className="w-4 h-4" /> Add Ingredient
                </button>
              </div>
            </div>

            {/* Instructions */}
            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3 block">
                Instructions ({formData.prepare_instruction.length} steps)
              </label>
              <div className="space-y-3">
                {formData.prepare_instruction.map((step, index) => (
                  <div key={index} className="flex items-start gap-2">
                    <span className="flex-shrink-0 w-7 h-7 rounded-full bg-brand-500 text-white text-xs font-bold flex items-center justify-center mt-2">
                      {index + 1}
                    </span>
                    <textarea value={step}
                      onChange={(e) => handleStepChange(index, e.target.value)}
                      placeholder={`Step ${index + 1}...`}
                      className="flex-1 p-3 liquid-input rounded-xl text-sm text-slate-800 dark:text-white outline-none resize-none"
                      rows={2} required />
                    {formData.prepare_instruction.length > 1 && (
                      <button type="button" onClick={() => handleRemoveStep(index)}
                        className="p-1.5 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-full text-red-500 transition-colors mt-2">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))}
                <button type="button" onClick={handleAddStep}
                  className="w-full p-3 rounded-xl border-2 border-dashed border-slate-200 dark:border-white/10 text-slate-400 hover:border-brand-500 hover:text-brand-500 transition-colors text-sm font-bold flex items-center justify-center gap-2">
                  <Plus className="w-4 h-4" /> Add Step
                </button>
              </div>
            </div>

            {/* Images */}
            <div>
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-2">
                <Image className="w-3 h-3" /> Recipe Images
              </label>
              <div className="flex gap-2 mb-3">
                <input type="url" placeholder="Image URL" value={imageUrl}
                  onChange={(e) => setImageUrl(e.target.value)}
                  className="flex-1 p-3 liquid-input rounded-2xl text-sm text-slate-800 dark:text-white outline-none placeholder-slate-400" />
                <button type="button" onClick={handleAddImage}
                  className="liquid-btn liquid-btn-secondary px-5 py-3 rounded-2xl text-sm font-bold">
                  Add
                </button>
              </div>
              {formData.images.length > 0 && (
                <div className="grid grid-cols-3 gap-3">
                  {formData.images.map((img, idx) => (
                    <div key={idx} className="relative group rounded-xl overflow-hidden border border-white/20 dark:border-white/10">
                      <img src={img} alt={`Recipe ${idx}`} className="w-full h-24 object-cover"
                        onError={(e) => { e.target.src = "https://via.placeholder.com/150?text=Invalid+URL"; }} />
                      <button type="button" onClick={() => handleRemoveImage(idx)}
                        className="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity text-white">
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="p-6 border-t border-slate-200 dark:border-white/10 flex justify-end gap-3">
            <button type="button" onClick={onClose}
              className="px-6 py-2.5 rounded-2xl font-bold text-slate-500 hover:bg-slate-100 dark:hover:bg-white/10 transition-colors">
              Cancel
            </button>
            <button type="submit" disabled={loading || ingredientsLoading}
              className="liquid-btn liquid-btn-primary px-10 py-2.5 rounded-2xl font-bold flex items-center gap-2 shadow-lg shadow-brand-500/20 disabled:opacity-50 disabled:grayscale transition-all">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              {loading ? "Creating..." : "Create Recipe"}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}
