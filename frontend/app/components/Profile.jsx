'use client';

import { useState } from 'react';
import { User, MapPin, Calendar, Heart, Clock, Flame, Award, Settings } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { PostCard } from './Community';

export default function Profile() {
  const [activeTab, setActiveTab] = useState('posts');

  const userInfo = {
    name: 'Sarah Jenkins',
    handle: '@sarahj_fitness',
    avatar: 'https://i.pravatar.cc/150?u=a042581f4e29026704d',
    bio: 'Certified Personal Trainer & Nutritionist | Lover of HIIT & Plant-based meals 🌱 | Helping you reach your goals! 💪',
    location: 'San Francisco, CA',
    joined: 'January 2023',
    stats: { followers: 1240, following: 350, posts: 42 },
    badge: 'Trainer'
  };

  const userPosts = [
    {
      id: '1',
      user: { name: 'Sarah Jenkins', avatar: userInfo.avatar, badge: userInfo.badge },
      content: 'Just finished my first 10k run! The new training plan from AI Trainer really helped me pace myself. Feeling amazing! 🏃‍♀️💨',
      image: 'https://picsum.photos/600/300?random=10',
      likes: 124, commentsCount: 18, views: 520, tags: ['running', 'training'],
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2)
    },
    {
      id: 'p2',
      user: { name: 'Sarah Jenkins', avatar: userInfo.avatar, badge: userInfo.badge },
      content: 'Sunday prep done right. Who else is ready for the week? 🥦🍗',
      likes: 56, commentsCount: 4, views: 310, tags: ['mealprep'],
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 48)
    }
  ];

  const likedPosts = [
    {
      id: '3',
      user: { name: 'Elena Rodriguez', avatar: 'https://i.pravatar.cc/150?u=a042581f4e29026703d', badge: 'Pro' },
      content: 'Hit a new PR on deadlifts today! 100kg! Hard work pays off.',
      likes: 243, commentsCount: 45, views: 1240, tags: ['gym', 'pr'],
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24)
    }
  ];

  const myRecipes = [
    {
      id: 'r1', title: 'Super Green Quinoa Salad',
      description: 'A light, nutritious salad perfect for summer days.',
      calories: 450, protein: 22, carbs: 45, fat: 18,
      imageUrl: 'https://picsum.photos/400/300?random=11',
      tags: ['Vegetarian', 'Gluten-Free', 'High Protein'],
      prepTime: '15 min',
      ingredients: ['1 cup Quinoa', '2 cups Spinach', '1/2 Avocado'],
      instructions: ['Cook quinoa', 'Chop veggies', 'Mix everything'],
      isFavorite: false
    }
  ];

  const favoriteRecipes = [
    {
      id: '2', title: 'Grilled Lemon Herb Salmon',
      calories: 380, protein: 35, carbs: 5, fat: 24,
      imageUrl: 'https://picsum.photos/400/300?random=2',
      tags: ['Keto', 'Dinner', 'High Protein'], prepTime: '25 min', isFavorite: true
    },
    {
      id: '4', title: 'Bulking Beef Pasta',
      calories: 850, protein: 45, carbs: 90, fat: 35,
      imageUrl: 'https://picsum.photos/400/300?random=4',
      tags: ['Dinner', 'Mass'], prepTime: '40 min', isFavorite: true
    }
  ];

  function RecipeGridItem({ recipe }) {
    return (
      <div className="glass-panel rounded-3xl overflow-hidden hover:shadow-xl hover:scale-[1.02] transition-all duration-300 group cursor-pointer flex flex-col h-full">
        <div className="relative h-40 overflow-hidden">
          <img src={recipe.imageUrl} alt={recipe.title} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" />
          <div className="absolute inset-0 bg-black/10 group-hover:bg-transparent transition-colors"></div>
          <div className="absolute top-3 right-3">
            <div className="p-1.5 bg-white/30 backdrop-blur-md rounded-full shadow-sm border border-white/20">
              <Heart className={`w-3.5 h-3.5 ${recipe.isFavorite ? 'fill-rose-500 text-rose-500' : 'text-white'}`} />
            </div>
          </div>
          <div className="absolute bottom-3 left-3 flex gap-1">
            {recipe.tags.slice(0, 2).map(tag => (
              <span key={tag} className="px-2 py-0.5 bg-black/40 backdrop-blur-md text-white text-[10px] font-medium rounded-full border border-white/20">{tag}</span>
            ))}
          </div>
        </div>
        <div className="p-4 flex-1">
          <h4 className="font-bold text-slate-800 dark:text-white text-sm mb-3 line-clamp-1">{recipe.title}</h4>
          <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
            <div className="flex items-center gap-1"><Clock className="w-3 h-3 text-brand-500" /><span>{recipe.prepTime}</span></div>
            <div className="flex items-center gap-1"><Flame className="w-3 h-3 text-orange-500" /><span>{recipe.calories} kcal</span></div>
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
              <img src={userInfo.avatar} alt="Profile" className="w-full h-full object-cover" />
            </div>
            {userInfo.badge && (
              <div className="absolute bottom-1 right-1 bg-brand-500 text-white text-xs px-2 py-0.5 rounded-full font-bold border-2 border-white dark:border-slate-800 flex items-center gap-1 shadow-md">
                <Award className="w-3 h-3" />{userInfo.badge}
              </div>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-slate-800 dark:text-white drop-shadow-sm">{userInfo.name}</h1>
            <p className="text-slate-500 dark:text-slate-400 font-medium text-sm mb-3">{userInfo.handle}</p>
            <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed max-w-xl mb-4">{userInfo.bio}</p>
            <div className="flex flex-wrap gap-4 text-xs text-slate-500 dark:text-slate-400">
              <div className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" />{userInfo.location}</div>
              <div className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" />Joined {userInfo.joined}</div>
            </div>
          </div>
          <div className="flex gap-6 md:gap-8 bg-white/40 dark:bg-black/20 p-4 rounded-2xl border border-white/20 dark:border-white/5 min-w-[200px] justify-between backdrop-blur-sm">
            <div className="text-center">
              <p className="font-bold text-slate-800 dark:text-white text-lg">{userInfo.stats.posts}</p>
              <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">Posts</p>
            </div>
            <div className="text-center border-l border-white/20 pl-6 md:pl-8">
              <p className="font-bold text-slate-800 dark:text-white text-lg">{userInfo.stats.followers}</p>
              <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">Followers</p>
            </div>
            <div className="text-center border-l border-white/20 pl-6 md:pl-8">
              <p className="font-bold text-slate-800 dark:text-white text-lg">{userInfo.stats.following}</p>
              <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">Following</p>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex gap-6 border-b border-white/20 dark:border-white/10 mb-6 overflow-x-auto pb-1 scrollbar-hide">
        {[
          { id: 'posts', label: 'My Posts' },
          { id: 'liked', label: 'Liked Posts' },
          { id: 'my_recipes', label: 'My Recipes' },
          { id: 'favorites', label: 'Favorites' }
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
          {activeTab === 'posts' && (
            <div className="space-y-6">
              {userPosts.map(post => <PostCard key={post.id} post={post} onLike={() => {}} onContentClick={() => {}} />)}
              {userPosts.length === 0 && <p className="text-center text-slate-400 py-10">No posts yet.</p>}
            </div>
          )}
          {activeTab === 'liked' && (
            <div className="space-y-6">
              {likedPosts.map(post => <PostCard key={post.id} post={post} onLike={() => {}} onContentClick={() => {}} />)}
              {likedPosts.length === 0 && <p className="text-center text-slate-400 py-10">You haven&apos;t liked any posts yet.</p>}
            </div>
          )}
          {activeTab === 'my_recipes' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {myRecipes.map(recipe => <RecipeGridItem key={recipe.id} recipe={recipe} />)}
              {myRecipes.length === 0 && <p className="col-span-full text-center text-slate-400 py-10">You haven&apos;t created any recipes yet.</p>}
            </div>
          )}
          {activeTab === 'favorites' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {favoriteRecipes.map(recipe => <RecipeGridItem key={recipe.id} recipe={recipe} />)}
              {favoriteRecipes.length === 0 && <p className="col-span-full text-center text-slate-400 py-10">No favorite recipes yet.</p>}
            </div>
          )}
        </motion.div>
      </AnimatePresence>
    </motion.div>
  );
}
