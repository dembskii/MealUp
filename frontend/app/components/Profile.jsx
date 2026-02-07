'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { ENDPOINTS } from '../config/network';
import { User, MapPin, Calendar, Heart, Clock, Flame, Award, Settings, Loader2, ChefHat, ArrowRight, CheckCircle2, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const authApi = axios.create({ baseURL: ENDPOINTS.AUTH, withCredentials: true });
const userApi = axios.create({ baseURL: ENDPOINTS.USERS, withCredentials: true });
const recipeApi = axios.create({ baseURL: ENDPOINTS.RECIPES, withCredentials: true });

export default function Profile() {
  const [activeTab, setActiveTab] = useState('my_recipes');

  const [authUser, setAuthUser] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [myRecipes, setMyRecipes] = useState([]);
  const [ingredientMap, setIngredientMap] = useState({});
  const [selectedRecipe, setSelectedRecipe] = useState(null);

  const [loading, setLoading] = useState(true);
  const [recipesLoading, setRecipesLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchProfileData();
  }, []);

  const fetchProfileData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Get current auth user
      const { data: auth } = await authApi.get('/me');
      setAuthUser(auth);

      // 2. Get full user profile from user-service
      let profile = null;
      if (auth.internal_uid) {
        try {
          const { data } = await userApi.get(`/users/${auth.internal_uid}`);
          profile = data;
        } catch (err) {
          console.warn('Could not fetch user profile by uid:', err);
        }
      }
      if (!profile && auth.user_id) {
        try {
          const { data } = await userApi.get(`/users/auth0/${auth.user_id}`);
          profile = data;
        } catch (err) {
          console.warn('Could not fetch user profile by auth0_sub:', err);
        }
      }
      setUserProfile(profile);

      // 3. Fetch recipes and ingredients in parallel
      const authorId = auth.internal_uid || profile?.uid;
      const [recipesRes, ingredientsRes] = await Promise.all([
        authorId ? recipeApi.get('/', { params: { author_id: authorId, limit: 100 } }) : Promise.resolve({ data: [] }),
        recipeApi.get('/ingredients?limit=500'),
      ]);
      setMyRecipes(recipesRes.data);

      const map = {};
      ingredientsRes.data.forEach(ing => {
        map[ing.id || ing._id] = ing;
      });
      setIngredientMap(map);
    } catch (err) {
      console.error('Error fetching profile data:', err);
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
      setRecipesLoading(false);
    }
  };

  const calculateMacros = (recipe) => {
    let calories = 0, protein = 0, carbs = 0, fat = 0;
    if (recipe.ingredients) {
      recipe.ingredients.forEach(item => {
        const ing = ingredientMap[item.ingredient_id];
        if (ing?.macro_per_hundred) {
          const factor = (item.quantity || 0) / 100;
          calories += (ing.macro_per_hundred.calories || 0) * factor;
          protein += (ing.macro_per_hundred.proteins || 0) * factor;
          carbs += (ing.macro_per_hundred.carbs || 0) * factor;
          fat += (ing.macro_per_hundred.fats || 0) * factor;
        }
      });
    }
    return {
      calories: Math.round(calories),
      protein: Math.round(protein),
      carbs: Math.round(carbs),
      fat: Math.round(fat),
    };
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

  const handleLike = async (recipeId) => {
    try {
      const { data } = await recipeApi.post(`/${recipeId}/like`);
      setMyRecipes(prev => prev.map(r => (r._id === recipeId ? data : r)));
      if (selectedRecipe?._id === recipeId) setSelectedRecipe(data);
    } catch (err) {
      console.error('Error liking recipe:', err);
    }
  };

  const handleDelete = async (recipeId) => {
    if (!confirm('Are you sure you want to delete this recipe?')) return;
    try {
      await recipeApi.delete(`/${recipeId}`);
      setMyRecipes(prev => prev.filter(r => r._id !== recipeId));
      if (selectedRecipe?._id === recipeId) setSelectedRecipe(null);
    } catch (err) {
      console.error('Error deleting recipe:', err);
      alert(err.response?.data?.detail || 'Failed to delete recipe.');
    }
  };

  // Derive display info from real data
  const displayName = userProfile
    ? `${userProfile.first_name || ''} ${userProfile.last_name || ''}`.trim() || userProfile.username
    : authUser?.name || 'User';
  const displayUsername = userProfile?.username ? `@${userProfile.username}` : authUser?.email || '';
  const displayAvatar = authUser?.picture || '';
  const displayRole = userProfile?.role || authUser?.role || 'user';
  const displayEmail = userProfile?.email || authUser?.email || '';
  const joinedDate = userProfile?.created_at
    ? new Date(userProfile.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    : '';

  if (loading) {
    return (
      <div className="flex justify-center items-center py-24">
        <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
        <span className="ml-3 text-slate-500 dark:text-slate-400">Loading profile...</span>
      </div>
    );
  }

  if (error && !authUser) {
    return (
      <div className="text-center py-24">
        <p className="text-red-500 mb-4">You need to be logged in to view your profile.</p>
        <button onClick={fetchProfileData} className="px-5 py-2.5 liquid-btn liquid-btn-primary rounded-2xl font-semibold">Retry</button>
      </div>
    );
  }

  function RecipeGridItem({ recipe }) {
    const macros = calculateMacros(recipe);
    const imageUrl = recipe.images?.[0] || `https://picsum.photos/seed/${recipe._id}/400/300`;
    return (
      <div
        onClick={() => setSelectedRecipe(recipe)}
        className="glass-panel rounded-3xl overflow-hidden hover:shadow-xl hover:scale-[1.02] transition-all duration-300 group cursor-pointer flex flex-col h-full"
      >
        <div className="relative h-40 overflow-hidden">
          <img src={imageUrl} alt={recipe.name} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            onError={(e) => { e.target.src = 'https://picsum.photos/400/300?grayscale'; }} />
          <div className="absolute inset-0 bg-black/10 group-hover:bg-transparent transition-colors"></div>
          <div className="absolute top-3 right-3">
            <button
              onClick={(e) => { e.stopPropagation(); handleLike(recipe._id); }}
              className="p-1.5 bg-white/30 backdrop-blur-md rounded-full shadow-sm border border-white/20 hover:bg-white/50 transition-colors"
            >
              <Heart className="w-3.5 h-3.5 text-white" />
            </button>
          </div>
          <div className="absolute bottom-3 left-3 flex gap-1">
            <span className="px-2 py-0.5 bg-black/40 backdrop-blur-md text-white text-[10px] font-medium rounded-full border border-white/20">
              {recipe.ingredients?.length || 0} ing.
            </span>
            {recipe.total_likes > 0 && (
              <span className="px-2 py-0.5 bg-black/40 backdrop-blur-md text-white text-[10px] font-medium rounded-full border border-white/20">
                {recipe.total_likes} likes
              </span>
            )}
          </div>
        </div>
        <div className="p-4 flex-1">
          <h4 className="font-bold text-slate-800 dark:text-white text-sm mb-3 line-clamp-1">{recipe.name}</h4>
          <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
            <div className="flex items-center gap-1"><Clock className="w-3 h-3 text-brand-500" /><span>{formatTime(recipe.time_to_prepare)}</span></div>
            <div className="flex items-center gap-1"><Flame className="w-3 h-3 text-orange-500" /><span>{macros.calories} kcal</span></div>
          </div>
          <div className="mt-2 grid grid-cols-3 gap-1 text-[10px] text-slate-400">
            <span>P: {macros.protein}g</span>
            <span>C: {macros.carbs}g</span>
            <span>F: {macros.fat}g</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-4xl mx-auto p-4 md:p-8">
      {/* Profile Header */}
      <div className="glass-panel rounded-3xl p-6 md:p-8 mb-8 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-r from-brand-400/20 to-brand-600/20 blur-3xl"></div>
        <div className="relative flex flex-col md:flex-row gap-6 items-start md:items-end">
          <div className="relative -mt-4 md:mt-0">
            <div className="w-28 h-28 rounded-full border-4 border-white dark:border-slate-800 shadow-xl overflow-hidden bg-slate-100 dark:bg-slate-700">
              {displayAvatar ? (
                <img src={displayAvatar} alt="Profile" className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-3xl font-bold text-slate-400">
                  {displayName.charAt(0).toUpperCase()}
                </div>
              )}
            </div>
            {displayRole !== 'user' && (
              <div className="absolute bottom-1 right-1 bg-brand-500 text-white text-xs px-2 py-0.5 rounded-full font-bold border-2 border-white dark:border-slate-800 flex items-center gap-1 shadow-md">
                <Award className="w-3 h-3" />{displayRole}
              </div>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-slate-800 dark:text-white drop-shadow-sm">{displayName}</h1>
            <p className="text-slate-500 dark:text-slate-400 font-medium text-sm mb-1">{displayUsername}</p>
            {displayEmail && displayEmail !== displayUsername?.replace('@', '') && (
              <p className="text-slate-400 dark:text-slate-500 text-xs mb-3">{displayEmail}</p>
            )}
            {userProfile && (
              <div className="flex flex-wrap gap-4 text-xs text-slate-500 dark:text-slate-400">
                {userProfile.sex && (
                  <div className="flex items-center gap-1"><User className="w-3.5 h-3.5" />{userProfile.sex}</div>
                )}
                {userProfile.age && (
                  <div className="flex items-center gap-1"><User className="w-3.5 h-3.5" />{userProfile.age} years</div>
                )}
                {userProfile.body_params?.weight && (
                  <div className="flex items-center gap-1">
                    {userProfile.body_params.weight} {userProfile.body_params.weight_unit || 'kg'}
                  </div>
                )}
                {userProfile.body_params?.height && (
                  <div className="flex items-center gap-1">
                    {userProfile.body_params.height} {userProfile.body_params.height_unit || 'cm'}
                  </div>
                )}
                {joinedDate && (
                  <div className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" />Joined {joinedDate}</div>
                )}
              </div>
            )}
          </div>
          <div className="flex gap-6 md:gap-8 bg-white/40 dark:bg-black/20 p-4 rounded-2xl border border-white/20 dark:border-white/5 min-w-[140px] justify-between backdrop-blur-sm">
            <div className="text-center">
              <p className="font-bold text-slate-800 dark:text-white text-lg">{myRecipes.length}</p>
              <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">Recipes</p>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex gap-6 border-b border-white/20 dark:border-white/10 mb-6 overflow-x-auto pb-1 scrollbar-hide">
        {[
          { id: 'my_recipes', label: `My Recipes (${myRecipes.length})` },
        ].map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`pb-3 text-sm font-bold relative whitespace-nowrap transition-colors ${activeTab === tab.id ? 'text-brand-600 dark:text-brand-400' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'}`}>
            {tab.label}
            {activeTab === tab.id && (
              <motion.div layoutId="activeTab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-brand-500 rounded-full shadow-[0_0_8px_rgba(27,211,132,0.8)]" />
            )}
          </button>
        ))}
      </div>

      {/* Content Area */}
      <AnimatePresence mode="wait">
        <motion.div key={activeTab} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }}>
          {activeTab === 'my_recipes' && (
            <div>
              {myRecipes.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                  {myRecipes.map(recipe => <RecipeGridItem key={recipe._id} recipe={recipe} />)}
                </div>
              ) : (
                <p className="text-center text-slate-400 py-10">You haven&apos;t created any recipes yet.</p>
              )}
            </div>
          )}
        </motion.div>
      </AnimatePresence>

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
                    <button onClick={() => handleDelete(selectedRecipe._id)} className="p-2 bg-red-500/70 hover:bg-red-500 text-white rounded-full transition-colors backdrop-blur-md border border-white/10" title="Delete recipe">
                      <X className="w-5 h-5" />
                    </button>
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
                    {selectedRecipe._created_at && (
                      <p className="text-white/70 text-sm">Created {new Date(selectedRecipe._created_at).toLocaleDateString()}</p>
                    )}
                  </div>
                </div>
                <div className="flex-1 overflow-y-auto">
                  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="p-8 space-y-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="flex gap-4 p-4 bg-slate-50 dark:bg-white/5 rounded-2xl border border-slate-100 dark:border-white/5 items-center justify-around">
                        <div className="text-center"><p className="text-xs text-slate-400 font-bold uppercase mb-1">Calories</p>
                          <div className="flex items-center gap-1.5 justify-center"><div className="p-1.5 bg-orange-100 dark:bg-orange-900/30 rounded-full text-orange-500"><Flame className="w-4 h-4" /></div><span className="text-lg font-bold text-slate-800 dark:text-white">{macros.calories}</span></div>
                        </div>
                        <div className="w-px h-10 bg-slate-200 dark:bg-white/10" />
                        <div className="text-center"><p className="text-xs text-slate-400 font-bold uppercase mb-1">Time</p>
                          <div className="flex items-center gap-1.5 justify-center"><div className="p-1.5 bg-brand-100 dark:bg-brand-900/30 rounded-full text-brand-500"><Clock className="w-4 h-4" /></div><span className="text-lg font-bold text-slate-800 dark:text-white">{formatTime(selectedRecipe.time_to_prepare)}</span></div>
                        </div>
                        <div className="w-px h-10 bg-slate-200 dark:bg-white/10" />
                        <div className="text-center"><p className="text-xs text-slate-400 font-bold uppercase mb-1">Likes</p>
                          <div className="flex items-center gap-1.5 justify-center">
                            <button onClick={() => handleLike(selectedRecipe._id)} className="p-1.5 bg-rose-100 dark:bg-rose-900/30 rounded-full text-rose-500 hover:bg-rose-200 transition-colors"><Heart className="w-4 h-4" /></button>
                            <span className="text-lg font-bold text-slate-800 dark:text-white">{selectedRecipe.total_likes || 0}</span>
                          </div>
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-2">
                        <div className="p-3 bg-green-50 dark:bg-green-900/10 rounded-2xl border border-green-100 dark:border-green-500/10 text-center"><p className="text-[10px] text-green-600 dark:text-green-400 font-bold uppercase mb-1">Protein</p><p className="text-xl font-bold text-slate-800 dark:text-white">{macros.protein}g</p></div>
                        <div className="p-3 bg-blue-50 dark:bg-blue-900/10 rounded-2xl border border-blue-100 dark:border-blue-500/10 text-center"><p className="text-[10px] text-blue-600 dark:text-blue-400 font-bold uppercase mb-1">Carbs</p><p className="text-xl font-bold text-slate-800 dark:text-white">{macros.carbs}g</p></div>
                        <div className="p-3 bg-purple-50 dark:bg-purple-900/10 rounded-2xl border border-purple-100 dark:border-purple-500/10 text-center"><p className="text-[10px] text-purple-600 dark:text-purple-400 font-bold uppercase mb-1">Fat</p><p className="text-xl font-bold text-slate-800 dark:text-white">{macros.fat}g</p></div>
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
    </motion.div>
  );
}
