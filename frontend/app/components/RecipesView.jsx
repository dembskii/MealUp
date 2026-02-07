'use client';

import { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { ENDPOINTS } from '../config/network';
import RecipeCreator from './Recipe/RecipeCreator';
import { Search, Clock, Flame, ChefHat, Plus, X, Loader2, Filter, Heart, ArrowRight, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const api = axios.create({
  baseURL: ENDPOINTS.RECIPES,
  withCredentials: true,
});

export default function Recipes() {
  const [recipes, setRecipes] = useState([]);
  const [ingredientMap, setIngredientMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreator, setShowCreator] = useState(false);
  const [selectedRecipe, setSelectedRecipe] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({ time: 'All' });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [recipesRes, ingredientsRes] = await Promise.all([
        api.get('/'),
        api.get('/ingredients?limit=500'),
      ]);
      setRecipes(recipesRes.data);
      const map = {};
      ingredientsRes.data.forEach(ing => {
        map[ing.id || ing._id] = ing;
      });
      setIngredientMap(map);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const toGrams = (quantity, capacity) => {
    switch (capacity) {
      case 'kg': return quantity * 1000;
      case 'ml': return quantity;
      case 'l': return quantity * 1000;
      case 'oz': return quantity * 28.35;
      case 'lb': return quantity * 453.6;
      case 'tsp': return quantity * 5;
      case 'tbsp': return quantity * 15;
      case 'cup': return quantity * 240;
      case 'pcs': return quantity * 100;
      default: return quantity;
    }
  };

  const calculateMacros = (recipe) => {
    let calories = 0, protein = 0, carbs = 0, fat = 0, totalWeight = 0;
    if (recipe.ingredients) {
      recipe.ingredients.forEach(item => {
        const ing = ingredientMap[item.ingredient_id];
        const weightG = toGrams(item.quantity || 0, item.capacity);
        totalWeight += weightG;
        if (ing?.macro_per_hundred) {
          const factor = weightG / 100;
          calories += (ing.macro_per_hundred.calories || 0) * factor;
          protein += (ing.macro_per_hundred.proteins || 0) * factor;
          carbs += (ing.macro_per_hundred.carbs || 0) * factor;
          fat += (ing.macro_per_hundred.fats || 0) * factor;
        }
      });
    }
    if (totalWeight > 0) {
      const norm = 100 / totalWeight;
      return { calories: Math.round(calories * norm), protein: Math.round(protein * norm), carbs: Math.round(carbs * norm), fat: Math.round(fat * norm) };
    }
    return { calories: 0, protein: 0, carbs: 0, fat: 0 };
  };

  const formatTime = (seconds) => {
    if (!seconds) return '? min';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes} min`;
  };

  const getIngredientName = (ingredientId) => {
    return ingredientMap[ingredientId]?.name || 'Unknown';
  };

  const handleLike = async (e, recipeId) => {
    e.stopPropagation();
    try {
      const { data } = await api.post(`/${recipeId}/like`);
      setRecipes(prev => prev.map(r => (r._id === recipeId ? data : r)));
      if (selectedRecipe?._id === recipeId) setSelectedRecipe(data);
    } catch (err) {
      console.error('Error liking recipe:', err);
    }
  };

  const handleUnlike = async (e, recipeId) => {
    e.stopPropagation();
    try {
      const { data } = await api.post(`/${recipeId}/unlike`);
      setRecipes(prev => prev.map(r => (r._id === recipeId ? data : r)));
      if (selectedRecipe?._id === recipeId) setSelectedRecipe(data);
    } catch (err) {
      console.error('Error unliking recipe:', err);
    }
  };

  const handleDelete = async (e, recipeId) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this recipe?')) return;
    try {
      await api.delete(`/${recipeId}`);
      setRecipes(prev => prev.filter(r => r._id !== recipeId));
      if (selectedRecipe?._id === recipeId) setSelectedRecipe(null);
    } catch (err) {
      console.error('Error deleting recipe:', err);
      alert(err.response?.data?.detail || 'Failed to delete recipe.');
    }
  };

  const handleRecipeCreated = (newRecipe) => {
    setRecipes(prev => [newRecipe, ...prev]);
  };

  const getFilteredRecipes = () => {
    return recipes.filter(recipe => {
      const matchesSearch = recipe.name?.toLowerCase().includes(searchQuery.toLowerCase());
      if (!matchesSearch) return false;
      if (filters.time !== 'All') {
        const limitSeconds = parseInt(filters.time) * 60;
        if (!recipe.time_to_prepare || recipe.time_to_prepare > limitSeconds) return false;
      }
      return true;
    });
  };

  const filteredRecipes = getFilteredRecipes();

  if (loading) {
    return (
      <div className="flex justify-center items-center py-24">
        <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
        <span className="ml-3 text-slate-500 dark:text-slate-400">Loading recipes...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-24">
        <p className="text-red-500 mb-4">Error: {typeof error === 'string' ? error : error.message}</p>
        <button onClick={fetchData} className="px-5 py-2.5 liquid-btn liquid-btn-primary rounded-2xl font-semibold">Retry</button>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="p-6 md:p-10">
      <div className="flex flex-col gap-6 mb-10">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h2 className="text-3xl font-bold text-slate-800 dark:text-white drop-shadow-sm">Nutritious Recipes</h2>
            <p className="text-slate-500 dark:text-slate-400 mt-1">Discover meals that fit your goals.</p>
          </div>
          <div className="flex gap-3 w-full md:w-auto">
            <button onClick={() => setShowCreator(true)}
              className="liquid-btn liquid-btn-primary px-5 py-3 rounded-2xl flex items-center gap-2 font-semibold shadow-lg shadow-brand-200 dark:shadow-none whitespace-nowrap ml-auto md:ml-0">
              <Plus className="w-4 h-4" /><span className="hidden sm:inline">Add Recipe</span>
            </button>
          </div>
        </div>

        <div className="flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
            <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Search recipes by name..."
              className="w-full pl-10 pr-4 py-3.5 liquid-input rounded-2xl text-slate-800 dark:text-white placeholder-slate-400 outline-none" />
          </div>
          <div className="flex gap-2">
            <button onClick={() => setShowFilters(!showFilters)}
              className={`px-4 py-3 rounded-2xl flex items-center gap-2 font-semibold transition-all liquid-btn ${showFilters ? 'bg-slate-800 text-white shadow-lg' : 'liquid-btn-secondary'}`}>
              <Filter className="w-4 h-4" /><span>Filters</span>
              {filters.time !== 'All' && (<span className="w-2 h-2 rounded-full bg-brand-500"></span>)}
            </button>
          </div>
        </div>

        <AnimatePresence>
          {showFilters && (
            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
              <div className="glass-panel rounded-2xl p-4 grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Max Prep Time</label>
                  <select value={filters.time} onChange={(e) => setFilters({...filters, time: e.target.value})}
                    className="w-full p-2.5 rounded-xl border border-slate-200 dark:border-white/10 bg-white/50 dark:bg-white/5 text-slate-700 dark:text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20">
                    <option value="All">Any Time</option>
                    <option value="15">Under 15 min</option>
                    <option value="30">Under 30 min</option>
                    <option value="60">Under 60 min</option>
                    <option value="120">Under 2 hours</option>
                  </select>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Recipe Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
        <AnimatePresence>
          {filteredRecipes.length > 0 ? (
            filteredRecipes.map((recipe) => {
              const macros = calculateMacros(recipe);
              const imageUrl = recipe.images?.[0] || `https://picsum.photos/seed/${recipe._id}/400/300`;
              return (
                <motion.div key={recipe._id} onClick={() => setSelectedRecipe(recipe)}
                  initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.9 }} whileHover={{ y: -5 }}
                  className="glass-panel rounded-3xl overflow-hidden cursor-pointer flex flex-col h-full relative group">
                  <div className="relative h-56 overflow-hidden">
                    <img src={imageUrl} alt={recipe.name} className="w-full h-full object-cover"
                      onError={(e) => { e.target.src = 'https://picsum.photos/400/300?grayscale'; }} />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-60"></div>
                    <div className="absolute top-4 right-4 flex gap-2">
                      <button onClick={(e) => handleLike(e, recipe._id)}
                        className="p-2.5 bg-white/20 backdrop-blur-md rounded-full shadow-lg border border-white/30 hover:bg-white/40 transition-colors flex items-center gap-1">
                        <Heart className="w-4 h-4 text-white" />
                        {recipe.total_likes > 0 && <span className="text-white text-xs font-bold">{recipe.total_likes}</span>}
                      </button>
                    </div>
                    <div className="absolute bottom-4 left-4 flex gap-2">
                      <span className="px-3 py-1 bg-white/20 backdrop-blur-md text-white text-xs font-bold rounded-full border border-white/20 shadow-sm">
                        {recipe.ingredients?.length || 0} ingredients
                      </span>
                    </div>
                  </div>
                  <div className="p-6 flex-1 flex flex-col">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-xl font-bold text-slate-800 dark:text-white leading-tight drop-shadow-sm">{recipe.name}</h3>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400 mb-6">
                      <div className="flex items-center gap-1"><Clock className="w-4 h-4 text-brand-500" /><span>{formatTime(recipe.time_to_prepare)}</span></div>
                      <div className="flex items-center gap-1"><Flame className="w-4 h-4 text-orange-500" /><span>{macros.calories} kcal/100g</span></div>
                    </div>
                    <div className="mt-auto grid grid-cols-3 gap-2 py-4 border-t border-slate-100 dark:border-white/10 bg-white/30 dark:bg-black/20 -mx-6 px-6 -mb-6 backdrop-blur-sm">
                      <div className="text-center"><p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Protein/100g</p><p className="font-bold text-slate-700 dark:text-slate-200">{macros.protein}g</p></div>
                      <div className="text-center border-l border-slate-200 dark:border-white/10"><p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Carbs/100g</p><p className="font-bold text-slate-700 dark:text-slate-200">{macros.carbs}g</p></div>
                      <div className="text-center border-l border-slate-200 dark:border-white/10"><p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Fat/100g</p><p className="font-bold text-slate-700 dark:text-slate-200">{macros.fat}g</p></div>
                    </div>
                  </div>
                </motion.div>
              );
            })
          ) : (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="col-span-full text-center py-20 opacity-60">
              <Search className="w-12 h-12 mx-auto mb-4 text-slate-300 dark:text-slate-600" />
              <p className="text-lg font-medium text-slate-500 dark:text-slate-400">No recipes found matching your filters.</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Recipe Detail Modal */}
      <AnimatePresence>
        {selectedRecipe && (() => {
          const macros = calculateMacros(selectedRecipe);
          const imageUrl = selectedRecipe.images?.[0] || `https://picsum.photos/seed/${selectedRecipe._id}/800/500`;
          return (
            <div className="fixed inset-0 z-[70] flex items-center justify-center p-4">
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setSelectedRecipe(null)}
                className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" />
              <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
                className="w-full max-w-4xl glass-panel bg-white/95 dark:bg-slate-900/95 backdrop-blur-3xl rounded-[2.5rem] relative z-10 flex flex-col max-h-[90vh] shadow-2xl overflow-hidden border border-white/50 dark:border-white/10">
                <div className="relative h-72 md:h-80 w-full shrink-0">
                  <img src={imageUrl} alt={selectedRecipe.name} className="w-full h-full object-cover"
                    onError={(e) => { e.target.src = 'https://picsum.photos/800/500?grayscale'; }} />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
                  <div className="absolute top-6 right-6 flex gap-2">
                    <button onClick={() => setSelectedRecipe(null)} className="p-2 bg-black/20 hover:bg-black/40 text-white rounded-full transition-colors backdrop-blur-md border border-white/10">
                      <X className="w-6 h-6" />
                    </button>
                  </div>
                  <div className="absolute bottom-0 left-0 w-full p-8 text-white">
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="flex flex-wrap gap-2 mb-3">
                      <span className="px-3 py-1 bg-white/20 backdrop-blur-md text-xs font-bold rounded-full border border-white/20">
                        {selectedRecipe.ingredients?.length || 0} ingredients
                      </span>
                      <span className="px-3 py-1 bg-white/20 backdrop-blur-md text-xs font-bold rounded-full border border-white/20">
                        {selectedRecipe.prepare_instruction?.length || 0} steps
                      </span>
                    </motion.div>
                    <h2 className="text-3xl md:text-4xl font-bold leading-tight drop-shadow-lg mb-2">{selectedRecipe.name}</h2>
                    <div className="flex items-center gap-3 text-white/70 text-sm">
                      <span>By {selectedRecipe.author_id}</span>
                      {selectedRecipe._created_at && <span>• {new Date(selectedRecipe._created_at).toLocaleDateString()}</span>}
                    </div>
                  </div>
                </div>
                <div className="flex-1 overflow-y-auto">
                  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="p-8 space-y-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="flex gap-4 p-4 bg-slate-50 dark:bg-white/5 rounded-2xl border border-slate-100 dark:border-white/5 items-center justify-around">
                        <div className="text-center"><p className="text-xs text-slate-400 font-bold uppercase mb-1">Cal/100g</p>
                          <div className="flex items-center gap-1.5 justify-center"><div className="p-1.5 bg-orange-100 dark:bg-orange-900/30 rounded-full text-orange-500"><Flame className="w-4 h-4" /></div><span className="text-lg font-bold text-slate-800 dark:text-white">{macros.calories}</span></div>
                        </div>
                        <div className="w-px h-10 bg-slate-200 dark:bg-white/10" />
                        <div className="text-center"><p className="text-xs text-slate-400 font-bold uppercase mb-1">Time</p>
                          <div className="flex items-center gap-1.5 justify-center"><div className="p-1.5 bg-brand-100 dark:bg-brand-900/30 rounded-full text-brand-500"><Clock className="w-4 h-4" /></div><span className="text-lg font-bold text-slate-800 dark:text-white">{formatTime(selectedRecipe.time_to_prepare)}</span></div>
                        </div>
                        <div className="w-px h-10 bg-slate-200 dark:bg-white/10" />
                        <div className="text-center"><p className="text-xs text-slate-400 font-bold uppercase mb-1">Likes</p>
                          <div className="flex items-center gap-1.5 justify-center">
                            <button onClick={(e) => handleLike(e, selectedRecipe._id)} className="p-1.5 bg-rose-100 dark:bg-rose-900/30 rounded-full text-rose-500 hover:bg-rose-200 transition-colors"><Heart className="w-4 h-4" /></button>
                            <span className="text-lg font-bold text-slate-800 dark:text-white">{selectedRecipe.total_likes || 0}</span>
                          </div>
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-2">
                        <div className="p-3 bg-green-50 dark:bg-green-900/10 rounded-2xl border border-green-100 dark:border-green-500/10 text-center"><p className="text-[10px] text-green-600 dark:text-green-400 font-bold uppercase mb-1">Protein/100g</p><p className="text-xl font-bold text-slate-800 dark:text-white">{macros.protein}g</p></div>
                        <div className="p-3 bg-blue-50 dark:bg-blue-900/10 rounded-2xl border border-blue-100 dark:border-blue-500/10 text-center"><p className="text-[10px] text-blue-600 dark:text-blue-400 font-bold uppercase mb-1">Carbs/100g</p><p className="text-xl font-bold text-slate-800 dark:text-white">{macros.carbs}g</p></div>
                        <div className="p-3 bg-purple-50 dark:bg-purple-900/10 rounded-2xl border border-purple-100 dark:border-purple-500/10 text-center"><p className="text-[10px] text-purple-600 dark:text-purple-400 font-bold uppercase mb-1">Fat/100g</p><p className="text-xl font-bold text-slate-800 dark:text-white">{macros.fat}g</p></div>
                      </div>
                    </div>
                    <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
                      <div className="lg:col-span-2">
                        <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2"><ChefHat className="w-5 h-5 text-brand-500" /> Ingredients</h3>
                        <ul className="space-y-3">
                          {selectedRecipe.ingredients?.map((item, i) => (
                            <li key={i} className="flex items-start gap-3 p-3 bg-white/50 dark:bg-white/5 rounded-xl border border-slate-100 dark:border-white/5">
                              <div className="mt-0.5 p-0.5 bg-brand-500 rounded-full"><CheckCircle2 className="w-3 h-3 text-white" /></div>
                              <span className="text-sm text-slate-700 dark:text-slate-300 font-medium leading-relaxed">
                                {getIngredientName(item.ingredient_id)} — {item.quantity} {item.capacity}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="lg:col-span-3">
                        <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2"><ArrowRight className="w-5 h-5 text-brand-500" /> Instructions</h3>
                        <div className="space-y-6">
                          {selectedRecipe.prepare_instruction?.map((step, i) => (
                            <div key={i} className="flex gap-4 group">
                              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 font-bold flex items-center justify-center text-sm border border-slate-200 dark:border-white/10 group-hover:bg-brand-500 group-hover:text-white transition-colors duration-300">{i + 1}</div>
                              <p className="flex-1 text-slate-600 dark:text-slate-300 leading-relaxed pt-1 border-b border-slate-100 dark:border-white/5 pb-6 last:border-0 last:pb-0">{step}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                </div>
              </motion.div>
            </div>
          );
        })()}
      </AnimatePresence>

      {/* Recipe Creator Modal */}
      {showCreator && (
        <RecipeCreator
          onClose={() => setShowCreator(false)}
          onRecipeCreated={handleRecipeCreated}
        />
      )}
    </motion.div>
  );
}
