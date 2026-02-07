'use client';

import { useState } from 'react';
import { generateRecipe } from '../services/geminiService';
import { Search, Clock, Flame, ChefHat, Plus, Sparkles, X, Loader2, Filter, Heart, ArrowRight, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Recipes() {
  const [recipes, setRecipes] = useState([
    {
      id: '1', title: 'Quinoa & Avocado Power Bowl',
      description: 'A vibrant, nutrient-packed bowl perfect for a midday energy boost. Loaded with fiber, healthy fats, and plant-based protein.',
      calories: 450, protein: 18, carbs: 52, fat: 22,
      imageUrl: 'https://picsum.photos/400/300?random=1',
      tags: ['Vegan', 'Lunch', 'Gluten-Free'], prepTime: '20 min',
      ingredients: ['1 cup Quinoa, cooked', '1 ripe Avocado, sliced', '1/2 cup Cherry Tomatoes, halved', '1/2 cup Chickpeas, rinsed', '1 tbsp Olive Oil', 'Lemon Juice', 'Salt & Pepper'],
      instructions: ['Cook quinoa according to package instructions and let cool.', 'In a bowl, arrange the quinoa, chickpeas, and cherry tomatoes.', 'Top with sliced avocado.', 'Drizzle with olive oil and lemon juice.', 'Season with salt and pepper to taste and serve immediately.'],
      isFavorite: false
    },
    {
      id: '2', title: 'Grilled Lemon Herb Salmon',
      description: 'Fresh salmon fillets marinated in zesty lemon and herbs, grilled to perfection. A keto-friendly dinner option.',
      calories: 380, protein: 35, carbs: 5, fat: 24,
      imageUrl: 'https://picsum.photos/400/300?random=2',
      tags: ['Keto', 'Dinner', 'High Protein'], prepTime: '25 min',
      ingredients: ['2 Salmon Fillets', '1 Lemon, sliced', '2 tbsp Fresh Dill', '1 bunch Asparagus', '1 tbsp Butter', 'Garlic Powder'],
      instructions: ['Preheat grill to medium-high heat.', 'Season salmon with garlic powder, salt, and fresh dill.', 'Place lemon slices on the grill and lay salmon on top.', 'Grill for 6-8 minutes per side until flaky.', 'Sauté asparagus in butter until tender.', 'Serve salmon hot with grilled lemon slices and asparagus.'],
      isFavorite: true
    },
    {
      id: '3', title: 'Berry Blast Protein Smoothie',
      description: 'A quick and delicious post-workout recovery drink. Sweet, refreshing, and packed with protein.',
      calories: 220, protein: 24, carbs: 20, fat: 6,
      imageUrl: 'https://picsum.photos/400/300?random=3',
      tags: ['Breakfast', 'Snack', 'Quick'], prepTime: '5 min',
      ingredients: ['1 scoop Whey Protein (Vanilla)', '1 cup Mixed Frozen Berries', '1 cup Almond Milk', '1/2 Banana', 'Ice cubes'],
      instructions: ['Add almond milk and protein powder to blender.', 'Add frozen berries and banana.', 'Blend on high speed until smooth.', 'Add ice cubes if a thicker consistency is desired and blend again.', 'Pour into a glass and enjoy!'],
      isFavorite: false
    },
    {
      id: '4', title: 'Bulking Beef Pasta',
      description: 'High calorie, high carb meal designed for muscle gain. Hearty, cheesy, and satisfying.',
      calories: 850, protein: 45, carbs: 90, fat: 35,
      imageUrl: 'https://picsum.photos/400/300?random=4',
      tags: ['Dinner', 'Mass', 'High Carb'], prepTime: '40 min',
      ingredients: ['200g Lean Ground Beef', '150g Pasta (Dry weight)', '1 cup Tomato Sauce', '1/2 cup Shredded Mozzarella', '1/2 Onion, diced', 'Italian Seasoning'],
      instructions: ['Boil pasta in salted water until al dente.', 'In a skillet, brown the ground beef with diced onion.', 'Drain excess fat and add tomato sauce and seasoning.', 'Simmer sauce for 5 minutes.', 'Mix cooked pasta into the sauce.', 'Top with mozzarella cheese and cover until melted.'],
      isFavorite: false
    }
  ]);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedRecipe, setSelectedRecipe] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [aiParams, setAiParams] = useState({ mealType: 'Lunch', dietType: 'Any', goal: 'Balanced', prepTime: '30 min', notes: '' });
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const [filters, setFilters] = useState({ diet: 'All', time: 'All', meal: 'All', goal: 'All' });

  const toggleFavorite = (id) => {
    setRecipes(prev => prev.map(recipe => recipe.id === id ? { ...recipe, isFavorite: !recipe.isFavorite } : recipe));
  };

  const handleGenerate = async () => {
    setIsLoading(true);
    const prompt = `Create a detailed recipe. Meal Type: ${aiParams.mealType} Diet: ${aiParams.dietType} Goal: ${aiParams.goal} Time: ${aiParams.prepTime} Notes: ${aiParams.notes}`;
    const newRecipe = await generateRecipe(prompt);
    if (newRecipe) {
      setRecipes([newRecipe, ...recipes]);
      setIsModalOpen(false);
      setAiParams(prev => ({ ...prev, notes: '' }));
    }
    setIsLoading(false);
  };

  const getFilteredRecipes = () => {
    return recipes.filter(recipe => {
      if (showFavoritesOnly && !recipe.isFavorite) return false;
      const matchesSearch = recipe.title.toLowerCase().includes(searchQuery.toLowerCase()) || recipe.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()));
      if (!matchesSearch) return false;
      if (filters.diet !== 'All' && !recipe.tags.some(tag => tag.toLowerCase() === filters.diet.toLowerCase())) return false;
      if (filters.time !== 'All') {
        const prepMinutes = parseInt(recipe.prepTime);
        const limit = parseInt(filters.time.replace(/[^\d]/g, ''));
        if (isNaN(prepMinutes) || prepMinutes > limit) return false;
      }
      if (filters.meal !== 'All' && !recipe.tags.some(tag => tag.toLowerCase() === filters.meal.toLowerCase())) return false;
      if (filters.goal !== 'All') {
        if (filters.goal === 'Reduction' && recipe.calories >= 400) return false;
        if (filters.goal === 'Recomposition' && (recipe.calories < 400 || recipe.calories > 600)) return false;
        if (filters.goal === 'Mass' && recipe.calories <= 600) return false;
      }
      return true;
    });
  };

  const filteredRecipes = getFilteredRecipes();

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="p-6 md:p-10">
      <div className="flex flex-col gap-6 mb-10">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h2 className="text-3xl font-bold text-slate-800 dark:text-white drop-shadow-sm">Nutritious Recipes</h2>
            <p className="text-slate-500 dark:text-slate-400 mt-1">Discover meals that fit your goals.</p>
          </div>
          <div className="flex gap-3 w-full md:w-auto">
            <button onClick={() => setIsModalOpen(true)}
              className="liquid-btn liquid-btn-primary px-5 py-3 rounded-2xl flex items-center gap-2 font-semibold shadow-lg shadow-brand-200 dark:shadow-none whitespace-nowrap ml-auto md:ml-0">
              <Sparkles className="w-4 h-4" /><span className="hidden sm:inline">AI Chef</span>
            </button>
          </div>
        </div>

        <div className="flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
            <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Search recipes..."
              className="w-full pl-10 pr-4 py-3.5 liquid-input rounded-2xl text-slate-800 dark:text-white placeholder-slate-400 outline-none" />
          </div>
          <div className="flex gap-2">
            <button onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}
              className={`px-4 py-3 rounded-2xl flex items-center gap-2 font-semibold transition-all liquid-btn ${showFavoritesOnly ? 'bg-rose-50 dark:bg-rose-900/30 text-rose-500 border border-rose-200 dark:border-rose-700' : 'liquid-btn-secondary'}`}>
              <Heart className={`w-4 h-4 ${showFavoritesOnly ? 'fill-current' : ''}`} /><span className="hidden sm:inline">Favorites</span>
            </button>
            <button onClick={() => setShowFilters(!showFilters)}
              className={`px-4 py-3 rounded-2xl flex items-center gap-2 font-semibold transition-all liquid-btn ${showFilters ? 'bg-slate-800 text-white shadow-lg' : 'liquid-btn-secondary'}`}>
              <Filter className="w-4 h-4" /><span>Filters</span>
              {Object.values(filters).some(v => v !== 'All') && (<span className="w-2 h-2 rounded-full bg-brand-500"></span>)}
            </button>
          </div>
        </div>

        <AnimatePresence>
          {showFilters && (
            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
              <div className="glass-panel rounded-2xl p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-2">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Diet Type</label>
                  <select value={filters.diet} onChange={(e) => setFilters({...filters, diet: e.target.value})}
                    className="w-full p-2.5 rounded-xl border border-slate-200 dark:border-white/10 bg-white/50 dark:bg-white/5 text-slate-700 dark:text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20">
                    <option value="All">All Diets</option><option value="Vegan">Vegan</option><option value="Vegetarian">Vegetarian</option>
                    <option value="Keto">Keto</option><option value="Gluten-Free">Gluten-Free</option><option value="High Protein">High Protein</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Prep Time</label>
                  <select value={filters.time} onChange={(e) => setFilters({...filters, time: e.target.value})}
                    className="w-full p-2.5 rounded-xl border border-slate-200 dark:border-white/10 bg-white/50 dark:bg-white/5 text-slate-700 dark:text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20">
                    <option value="All">Any Time</option><option value="< 15 min">Under 15 min</option>
                    <option value="< 30 min">Under 30 min</option><option value="< 60 min">Under 60 min</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Meal Type</label>
                  <select value={filters.meal} onChange={(e) => setFilters({...filters, meal: e.target.value})}
                    className="w-full p-2.5 rounded-xl border border-slate-200 dark:border-white/10 bg-white/50 dark:bg-white/5 text-slate-700 dark:text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20">
                    <option value="All">All Meals</option><option value="Breakfast">Breakfast</option>
                    <option value="Lunch">Lunch</option><option value="Dinner">Dinner</option><option value="Snack">Snack</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Goal (Calories)</label>
                  <select value={filters.goal} onChange={(e) => setFilters({...filters, goal: e.target.value})}
                    className="w-full p-2.5 rounded-xl border border-slate-200 dark:border-white/10 bg-white/50 dark:bg-white/5 text-slate-700 dark:text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20">
                    <option value="All">All Goals</option><option value="Reduction">Reduction (&lt; 400 kcal)</option>
                    <option value="Recomposition">Recomp (400-600 kcal)</option><option value="Mass">Mass (&gt; 600 kcal)</option>
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
            filteredRecipes.map((recipe) => (
              <motion.div key={recipe.id} layoutId={`recipe-card-${recipe.id}`} onClick={() => setSelectedRecipe(recipe)}
                initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.9 }} whileHover={{ y: -5 }}
                className="glass-panel rounded-3xl overflow-hidden cursor-pointer flex flex-col h-full relative group">
                <div className="relative h-56 overflow-hidden">
                  <motion.img layoutId={`recipe-image-${recipe.id}`} src={recipe.imageUrl} alt={recipe.title} className="w-full h-full object-cover" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-60"></div>
                  <div className="absolute top-4 right-4 flex gap-2">
                    <button onClick={(e) => { e.stopPropagation(); toggleFavorite(recipe.id); }}
                      className="p-2.5 bg-white/20 backdrop-blur-md rounded-full shadow-lg border border-white/30 hover:bg-white/40 transition-colors">
                      <Heart className={`w-4 h-4 transition-colors ${recipe.isFavorite ? 'fill-rose-500 text-rose-500' : 'text-white'}`} />
                    </button>
                  </div>
                  <div className="absolute bottom-4 left-4 flex gap-2">
                    {recipe.tags.slice(0, 2).map(tag => (
                      <span key={tag} className="px-3 py-1 bg-white/20 backdrop-blur-md text-white text-xs font-bold rounded-full border border-white/20 shadow-sm">{tag}</span>
                    ))}
                  </div>
                </div>
                <div className="p-6 flex-1 flex flex-col">
                  <div className="flex justify-between items-start mb-2">
                    <motion.h3 layoutId={`recipe-title-${recipe.id}`} className="text-xl font-bold text-slate-800 dark:text-white leading-tight drop-shadow-sm">{recipe.title}</motion.h3>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400 mb-6">
                    <div className="flex items-center gap-1"><Clock className="w-4 h-4 text-brand-500" /><span>{recipe.prepTime}</span></div>
                    <div className="flex items-center gap-1"><Flame className="w-4 h-4 text-orange-500" /><span>{recipe.calories} kcal</span></div>
                  </div>
                  <div className="mt-auto grid grid-cols-3 gap-2 py-4 border-t border-slate-100 dark:border-white/10 bg-white/30 dark:bg-black/20 -mx-6 px-6 -mb-6 backdrop-blur-sm">
                    <div className="text-center"><p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Protein</p><p className="font-bold text-slate-700 dark:text-slate-200">{recipe.protein}g</p></div>
                    <div className="text-center border-l border-slate-200 dark:border-white/10"><p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Carbs</p><p className="font-bold text-slate-700 dark:text-slate-200">{recipe.carbs}g</p></div>
                    <div className="text-center border-l border-slate-200 dark:border-white/10"><p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Fat</p><p className="font-bold text-slate-700 dark:text-slate-200">{recipe.fat}g</p></div>
                  </div>
                </div>
              </motion.div>
            ))
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
        {selectedRecipe && (
          <div className="fixed inset-0 z-[70] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setSelectedRecipe(null)}
              className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" />
            <motion.div layoutId={`recipe-card-${selectedRecipe.id}`} transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="w-full max-w-4xl glass-panel bg-white/95 dark:bg-slate-900/95 backdrop-blur-3xl rounded-[2.5rem] relative z-10 flex flex-col max-h-[90vh] shadow-2xl overflow-hidden border border-white/50 dark:border-white/10">
              <div className="relative h-72 md:h-80 w-full shrink-0">
                <motion.img layoutId={`recipe-image-${selectedRecipe.id}`} src={selectedRecipe.imageUrl} alt={selectedRecipe.title} className="w-full h-full object-cover" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
                <button onClick={() => setSelectedRecipe(null)} className="absolute top-6 right-6 p-2 bg-black/20 hover:bg-black/40 text-white rounded-full transition-colors backdrop-blur-md border border-white/10">
                  <X className="w-6 h-6" />
                </button>
                <div className="absolute bottom-0 left-0 w-full p-8 text-white">
                  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="flex flex-wrap gap-2 mb-3">
                    {selectedRecipe.tags.map(tag => (<span key={tag} className="px-3 py-1 bg-white/20 backdrop-blur-md text-xs font-bold rounded-full border border-white/20">{tag}</span>))}
                  </motion.div>
                  <motion.h2 layoutId={`recipe-title-${selectedRecipe.id}`} className="text-3xl md:text-4xl font-bold leading-tight drop-shadow-lg mb-2">{selectedRecipe.title}</motion.h2>
                  {selectedRecipe.description && <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-white/80 text-sm md:text-base max-w-2xl line-clamp-2">{selectedRecipe.description}</motion.p>}
                </div>
              </div>
              <div className="flex-1 overflow-y-auto">
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="p-8 space-y-8">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="flex gap-4 p-4 bg-slate-50 dark:bg-white/5 rounded-2xl border border-slate-100 dark:border-white/5 items-center justify-around">
                      <div className="text-center"><p className="text-xs text-slate-400 font-bold uppercase mb-1">Calories</p>
                        <div className="flex items-center gap-1.5 justify-center"><div className="p-1.5 bg-orange-100 dark:bg-orange-900/30 rounded-full text-orange-500"><Flame className="w-4 h-4" /></div><span className="text-lg font-bold text-slate-800 dark:text-white">{selectedRecipe.calories}</span></div>
                      </div>
                      <div className="w-px h-10 bg-slate-200 dark:bg-white/10" />
                      <div className="text-center"><p className="text-xs text-slate-400 font-bold uppercase mb-1">Time</p>
                        <div className="flex items-center gap-1.5 justify-center"><div className="p-1.5 bg-brand-100 dark:bg-brand-900/30 rounded-full text-brand-500"><Clock className="w-4 h-4" /></div><span className="text-lg font-bold text-slate-800 dark:text-white">{selectedRecipe.prepTime}</span></div>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      <div className="p-3 bg-green-50 dark:bg-green-900/10 rounded-2xl border border-green-100 dark:border-green-500/10 text-center"><p className="text-[10px] text-green-600 dark:text-green-400 font-bold uppercase mb-1">Protein</p><p className="text-xl font-bold text-slate-800 dark:text-white">{selectedRecipe.protein}g</p></div>
                      <div className="p-3 bg-blue-50 dark:bg-blue-900/10 rounded-2xl border border-blue-100 dark:border-blue-500/10 text-center"><p className="text-[10px] text-blue-600 dark:text-blue-400 font-bold uppercase mb-1">Carbs</p><p className="text-xl font-bold text-slate-800 dark:text-white">{selectedRecipe.carbs}g</p></div>
                      <div className="p-3 bg-purple-50 dark:bg-purple-900/10 rounded-2xl border border-purple-100 dark:border-purple-500/10 text-center"><p className="text-[10px] text-purple-600 dark:text-purple-400 font-bold uppercase mb-1">Fat</p><p className="text-xl font-bold text-slate-800 dark:text-white">{selectedRecipe.fat}g</p></div>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
                    <div className="lg:col-span-2">
                      <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2"><ChefHat className="w-5 h-5 text-brand-500" /> Ingredients</h3>
                      <ul className="space-y-3">
                        {selectedRecipe.ingredients?.map((ing, i) => (
                          <li key={i} className="flex items-start gap-3 p-3 bg-white/50 dark:bg-white/5 rounded-xl border border-slate-100 dark:border-white/5">
                            <div className="mt-0.5 p-0.5 bg-brand-500 rounded-full"><CheckCircle2 className="w-3 h-3 text-white" /></div>
                            <span className="text-sm text-slate-700 dark:text-slate-300 font-medium leading-relaxed">{ing}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div className="lg:col-span-3">
                      <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2"><ArrowRight className="w-5 h-5 text-brand-500" /> Instructions</h3>
                      <div className="space-y-6">
                        {selectedRecipe.instructions?.map((step, i) => (
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
        )}
      </AnimatePresence>

      {/* AI Chef Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setIsModalOpen(false)} className="absolute inset-0 bg-slate-900/40 backdrop-blur-md" />
            <motion.div initial={{ opacity: 0, scale: 0.9, y: 30 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.9, y: 30 }}
              className="glass-panel bg-white/90 dark:bg-slate-900/90 backdrop-blur-3xl rounded-[2rem] p-8 w-full max-w-lg relative shadow-2xl z-10 max-h-[90vh] overflow-y-auto border border-white/50 dark:border-white/10">
              <button onClick={() => setIsModalOpen(false)} className="absolute top-6 right-6 p-2 hover:bg-black/5 dark:hover:bg-white/10 rounded-full transition-colors"><X className="w-5 h-5 text-slate-400" /></button>
              <div className="mb-6">
                <div className="w-14 h-14 bg-gradient-to-br from-brand-400 to-brand-600 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-brand-500/30 border-t border-white/30"><ChefHat className="w-7 h-7 text-white" /></div>
                <h3 className="text-2xl font-bold text-slate-800 dark:text-white">AI Chef Generator</h3>
                <p className="text-slate-500 dark:text-slate-400">Customize your parameters and let AI create the perfect recipe.</p>
              </div>
              <div className="space-y-5 mb-8">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5"><label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Meal Type</label>
                    <select value={aiParams.mealType} onChange={(e) => setAiParams({...aiParams, mealType: e.target.value})} className="w-full p-3.5 liquid-input rounded-xl text-slate-800 dark:text-white outline-none"><option>Breakfast</option><option>Lunch</option><option>Dinner</option><option>Snack</option><option>Dessert</option></select></div>
                  <div className="space-y-1.5"><label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Prep Time</label>
                    <select value={aiParams.prepTime} onChange={(e) => setAiParams({...aiParams, prepTime: e.target.value})} className="w-full p-3.5 liquid-input rounded-xl text-slate-800 dark:text-white outline-none"><option>15 min</option><option>30 min</option><option>45 min</option><option>1 hour</option><option>Slow Cook</option></select></div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5"><label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Diet Type</label>
                    <select value={aiParams.dietType} onChange={(e) => setAiParams({...aiParams, dietType: e.target.value})} className="w-full p-3.5 liquid-input rounded-xl text-slate-800 dark:text-white outline-none"><option>Any</option><option>Vegan</option><option>Vegetarian</option><option>Keto</option><option>Paleo</option><option>Gluten-Free</option><option>High Protein</option></select></div>
                  <div className="space-y-1.5"><label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Goal</label>
                    <select value={aiParams.goal} onChange={(e) => setAiParams({...aiParams, goal: e.target.value})} className="w-full p-3.5 liquid-input rounded-xl text-slate-800 dark:text-white outline-none"><option>Balanced</option><option>Low Calorie</option><option>High Protein</option><option>Bulking</option><option>Low Carb</option></select></div>
                </div>
                <div className="space-y-1.5"><label className="text-xs font-bold text-slate-500 uppercase tracking-wide ml-1">Specific Ingredients / Notes</label>
                  <textarea value={aiParams.notes} onChange={(e) => setAiParams({...aiParams, notes: e.target.value})} placeholder="e.g., I have chicken breast and broccoli, make it spicy."
                    className="w-full h-24 p-3.5 liquid-input rounded-xl text-slate-800 dark:text-white outline-none resize-none" /></div>
              </div>
              <div className="flex justify-end gap-3">
                <button onClick={() => setIsModalOpen(false)} className="px-5 py-2.5 text-slate-600 dark:text-slate-300 font-semibold hover:bg-black/5 dark:hover:bg-white/10 rounded-xl transition-colors">Cancel</button>
                <button onClick={handleGenerate} disabled={isLoading}
                  className="liquid-btn liquid-btn-primary px-6 py-2.5 rounded-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                  {isLoading ? 'Creating...' : 'Generate Recipe'}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
