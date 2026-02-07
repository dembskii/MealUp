'use client';

import { useState, useEffect, useMemo } from 'react';
import { TrainingType, DayOfWeek, SetUnit } from '../data/types';
import { MOCK_EXERCISES_DB } from '../data/mockData';
import {
  Heart, MessageCircle, Share2, MoreHorizontal, Award,
  Search, Filter, Flame, Clock, ChefHat, X,
  ChevronDown, ChevronUp, Eye, TrendingUp, Send, Dumbbell, Link, Plus, Calendar, Check, Hash
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// --- MOCK DATA GENERATION ---

const generateMockComments = (count, depth = 0) => {
  if (depth > 2) return [];
  return Array.from({ length: count }).map((_, i) => ({
    id: `c-${depth}-${i}-${Math.random()}`,
    user: {
      name: ['Alice', 'Bob', 'Charlie', 'Dana'][Math.floor(Math.random() * 4)],
      avatar: `https://i.pravatar.cc/150?u=${Math.random()}`,
      badge: Math.random() > 0.8 ? 'Pro' : undefined
    },
    content: [
      'This looks amazing! 🔥',
      'Can I substitute the chicken?',
      'Tried this yesterday, solid workout.',
      'Thanks for sharing!'
    ][Math.floor(Math.random() * 4)],
    timestamp: new Date(Date.now() - Math.random() * 10000000),
    likes: Math.floor(Math.random() * 20),
    replies: Math.random() > 0.7 ? generateMockComments(1, depth + 1) : []
  }));
};

const AVAILABLE_RECIPES = [
  { type: 'recipe', id: 'r1', title: 'Super Green Quinoa Salad', subtitle: '450 kcal • 15 min', image: 'https://picsum.photos/100/100?random=11' },
  { type: 'recipe', id: 'r2', title: 'Grilled Lemon Herb Salmon', subtitle: '380 kcal • 25 min', image: 'https://picsum.photos/100/100?random=2' },
  { type: 'recipe', id: 'r3', title: 'Berry Blast Smoothie', subtitle: '220 kcal • 5 min', image: 'https://picsum.photos/100/100?random=3' },
  { type: 'recipe', id: 'r4', title: 'Avocado Toast & Eggs', subtitle: '320 kcal • 10 min', image: 'https://picsum.photos/100/100?random=4' },
  { type: 'recipe', id: 'r5', title: 'Protein Pancakes', subtitle: '400 kcal • 20 min', image: 'https://picsum.photos/100/100?random=5' },
];

const AVAILABLE_WORKOUTS = [
  { type: 'workout', id: 'w1', title: '10k Runner Prep', subtitle: 'Advanced • 60 min', image: 'https://picsum.photos/100/100?random=99' },
  { type: 'workout', id: 'w2', title: 'Full Body HIIT', subtitle: 'Intermediate • 45 min', image: 'https://picsum.photos/100/100?random=98' },
  { type: 'workout', id: 'w3', title: 'Morning Yoga', subtitle: 'Beginner • 20 min', image: 'https://picsum.photos/100/100?random=97' },
  { type: 'workout', id: 'w4', title: 'Upper Body Power', subtitle: 'Advanced • 50 min', image: 'https://picsum.photos/100/100?random=96' },
  { type: 'workout', id: 'w5', title: 'Core Crusher', subtitle: 'Intermediate • 15 min', image: 'https://picsum.photos/100/100?random=95' },
];

const SUGGESTED_TAGS = ['fitness', 'nutrition', 'recipe', 'workout', 'motivation', 'healthy', 'beginner', 'gains', 'weightloss', 'cardio'];

const mockPopulatedTraining = (id, name, type) => ({
  _id: id,
  name: name,
  day: DayOfWeek.MONDAY,
  training_type: type,
  est_time: 3600,
  exercises: [
    {
      exercise_id: 'ex_burpee',
      rest_between_sets: 60,
      sets: [{ volume: 10, units: SetUnit.REPS }],
      _exerciseDetails: MOCK_EXERCISES_DB['ex_burpee']
    },
    {
      exercise_id: 'ex_pushup',
      rest_between_sets: 60,
      sets: [{ volume: 15, units: SetUnit.REPS }],
      _exerciseDetails: MOCK_EXERCISES_DB['ex_pushup']
    }
  ]
});

const INITIAL_POSTS = [
  {
    id: '1',
    user: { name: 'Sarah Jenkins', avatar: 'https://i.pravatar.cc/150?u=a042581f4e29026704d', badge: 'Trainer' },
    content: 'Just finished my first 10k run! The new training plan from AI Trainer really helped me pace myself. Feeling amazing! 🏃‍♀️💨',
    image: 'https://picsum.photos/600/300?random=10',
    likes: 124,
    commentsCount: 18,
    views: 1250,
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2),
    tags: ['running', 'milestone', 'cardio'],
    comments: generateMockComments(3),
    linkedContent: {
      type: 'workout', id: 'w1', title: '10k Runner Prep',
      subtitle: 'Advanced • 60 min', image: 'https://picsum.photos/100/100?random=99',
      payload: mockPopulatedTraining('w1', '10k Runner Prep', TrainingType.CARDIO)
    }
  },
  {
    id: '2',
    user: { name: 'Mike Ross', avatar: 'https://i.pravatar.cc/150?u=a042581f4e29026024d' },
    content: 'Meal prep Sunday! Try this high protein salad I just made. It keeps me full for hours. 🥗',
    likes: 89, commentsCount: 12, views: 890,
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 5),
    tags: ['mealprep', 'healthy', 'recipe'],
    comments: generateMockComments(2),
    linkedContent: {
      type: 'recipe', id: 'r1', title: 'Super Green Quinoa Salad',
      subtitle: '450 kcal • 15 min', image: 'https://picsum.photos/100/100?random=11',
      payload: {
        id: 'r1', title: 'Super Green Quinoa Salad',
        description: 'A refreshing and nutrient-dense salad perfect for post-workout recovery. Packed with plant-based protein and healthy fats from avocado and seeds.',
        calories: 450, protein: 18, carbs: 45, fat: 22, prepTime: '15 min',
        tags: ['Vegetarian', 'Gluten-Free', 'High Protein', 'Lunch'],
        ingredients: ['1 cup cooked Quinoa', '2 cups fresh Spinach', '1/2 Avocado, sliced', '1/4 cup Cherry Tomatoes', '2 tbsp Olive Oil & Lemon dressing', '1 tbsp Pumpkin Seeds'],
        instructions: ['Rinse quinoa and cook according to package instructions.', 'While quinoa cools, chop the vegetables.', 'In a large bowl, toss spinach, cooled quinoa, and tomatoes.', 'Top with sliced avocado and drizzle with dressing.', 'Sprinkle pumpkin seeds on top for crunch.', 'Season with salt and pepper to taste.'],
        imageUrl: 'https://picsum.photos/600/400?random=11'
      }
    }
  },
  {
    id: '3',
    user: { name: 'Elena Rodriguez', avatar: 'https://i.pravatar.cc/150?u=a042581f4e29026703d', badge: 'Pro' },
    content: 'Hit a new PR on deadlifts today! 100kg! Hard work pays off.',
    likes: 243, commentsCount: 45, views: 3400,
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24),
    tags: ['gym', 'pr', 'strength'],
    comments: generateMockComments(5)
  },
  {
    id: '4',
    user: { name: 'Tom Hardy', avatar: 'https://i.pravatar.cc/150?u=tom', badge: 'Chef' },
    content: 'Does anyone have a good substitute for whey protein in baking? I want to make these brownies but keep them dairy free.',
    likes: 15, commentsCount: 8, views: 120,
    timestamp: new Date(Date.now() - 1000 * 60 * 30),
    tags: ['question', 'baking', 'nutrition'],
    comments: generateMockComments(1)
  }
];

// --- UTILITIES ---

const calculateTrendingScore = (post) => {
  const hoursSincePost = (Date.now() - post.timestamp.getTime()) / (1000 * 60 * 60);
  const gravity = 1.8;
  const engagementScore = (post.likes * 2) + (post.commentsCount * 3) + (post.views * 0.1);
  return engagementScore / Math.pow(hoursSincePost + 2, gravity);
};

const formatNumber = (num) => {
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
  return num.toString();
};

const timeAgo = (date) => {
  const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);
  let interval = seconds / 31536000;
  if (interval > 1) return Math.floor(interval) + "y ago";
  interval = seconds / 2592000;
  if (interval > 1) return Math.floor(interval) + "mo ago";
  interval = seconds / 86400;
  if (interval > 1) return Math.floor(interval) + "d ago";
  interval = seconds / 3600;
  if (interval > 1) return Math.floor(interval) + "h ago";
  interval = seconds / 60;
  if (interval > 1) return Math.floor(interval) + "m ago";
  return "Just now";
};

// --- SUB-COMPONENTS ---

function CommentNode({ comment, onReply }) {
  const [isReplying, setIsReplying] = useState(false);
  const [replyText, setReplyText] = useState('');

  return (
    <div className="flex gap-3 mt-4">
      <img src={comment.user.avatar} alt={comment.user.name} className="w-8 h-8 rounded-full object-cover border border-white/50" />
      <div className="flex-1">
        <div className="bg-white/40 dark:bg-white/5 rounded-2xl px-4 py-2 inline-block min-w-[200px]">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-bold text-sm text-slate-800 dark:text-white">{comment.user.name}</span>
            {comment.user.badge && (
              <span className="text-[10px] bg-brand-500/20 text-brand-600 dark:text-brand-400 px-1.5 rounded font-bold border border-brand-500/30">{comment.user.badge}</span>
            )}
            <span className="text-xs text-slate-400">{timeAgo(comment.timestamp)}</span>
          </div>
          <p className="text-sm text-slate-700 dark:text-slate-300">{comment.content}</p>
        </div>
        <div className="flex items-center gap-4 mt-1 ml-2 text-xs font-semibold text-slate-500">
          <button className="hover:text-brand-500">Like ({comment.likes})</button>
          <button onClick={() => setIsReplying(!isReplying)} className="hover:text-brand-500">Reply</button>
        </div>
        {isReplying && (
          <div className="mt-2 flex gap-2 animate-in fade-in slide-in-from-top-1">
            <input type="text" autoFocus value={replyText} onChange={(e) => setReplyText(e.target.value)}
              placeholder={`Reply to ${comment.user.name}...`}
              className="flex-1 bg-white/50 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500" />
            <button onClick={() => { onReply(comment.id, replyText); setIsReplying(false); setReplyText(''); }}
              className="p-1.5 bg-brand-500 text-white rounded-lg"><Send className="w-4 h-4" /></button>
          </div>
        )}
        {comment.replies.length > 0 && (
          <div className="pl-4 border-l-2 border-slate-200/50 dark:border-white/5 mt-2">
            {comment.replies.map(reply => (
              <CommentNode key={reply.id} comment={reply} onReply={onReply} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function LinkedContentCard({ content, onClick }) {
  return (
    <div onClick={onClick}
      className={`mt-3 flex items-center gap-4 p-3 rounded-2xl bg-gradient-to-br from-white/60 to-white/30 dark:from-slate-800/60 dark:to-slate-900/30 border border-white/50 dark:border-white/10 group shadow-sm ${onClick ? 'cursor-pointer hover:scale-[1.01] transition-transform' : ''}`}>
      <div className="relative w-16 h-16 shrink-0">
        <img src={content.image || `https://picsum.photos/100?random=${content.id}`} alt={content.title} className="w-full h-full object-cover rounded-xl shadow-md" />
        <div className="absolute -top-2 -left-2 p-1.5 bg-white dark:bg-slate-800 rounded-lg shadow-sm text-brand-500">
          {content.type === 'recipe' ? <ChefHat className="w-3 h-3" /> : <Dumbbell className="w-3 h-3" />}
        </div>
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-bold text-brand-600 dark:text-brand-400 uppercase tracking-wider mb-0.5">{content.type}</p>
        <h4 className="font-bold text-slate-800 dark:text-white truncate group-hover:text-brand-500 transition-colors">{content.title}</h4>
        <p className="text-xs text-slate-500 dark:text-slate-400">{content.subtitle}</p>
      </div>
      {onClick && (
        <div className="mr-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <ChevronDown className="-rotate-90 w-5 h-5 text-slate-400" />
        </div>
      )}
    </div>
  );
}

export function PostCard({ post, onLike, onContentClick }) {
  const [showComments, setShowComments] = useState(false);
  const [isLiked, setIsLiked] = useState(false);
  const [comments, setComments] = useState(post.comments || []);
  const [newComment, setNewComment] = useState('');

  const handleAddComment = () => {
    if (!newComment.trim()) return;
    const comment = {
      id: Math.random().toString(),
      user: { name: 'You', avatar: 'https://i.pravatar.cc/150?u=me' },
      content: newComment,
      timestamp: new Date(),
      likes: 0,
      replies: []
    };
    setComments([comment, ...comments]);
    setNewComment('');
  };

  const handleReply = (parentId, text) => {
    const addReply = (nodes) => {
      return nodes.map(node => {
        if (node.id === parentId) {
          return {
            ...node,
            replies: [...node.replies, {
              id: Math.random().toString(),
              user: { name: 'You', avatar: 'https://i.pravatar.cc/150?u=me' },
              content: text, timestamp: new Date(), likes: 0, replies: []
            }]
          };
        }
        return { ...node, replies: addReply(node.replies) };
      });
    };
    setComments(addReply(comments));
  };

  return (
    <motion.div layout initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
      className="glass-panel rounded-3xl p-6 transition-all duration-300 hover:shadow-xl">
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-3">
          <div className="relative">
            <img src={post.user.avatar} alt={post.user.name} className="w-12 h-12 rounded-full object-cover border-2 border-white/80 shadow-md" />
            {post.user.badge && (
              <div className="absolute -bottom-1 -right-1 bg-brand-500 text-white text-[10px] px-1.5 py-0.5 rounded-md font-bold border border-white flex items-center gap-0.5 shadow-sm">
                <Award className="w-2 h-2" />{post.user.badge}
              </div>
            )}
          </div>
          <div>
            <h3 className="font-bold text-slate-800 dark:text-white drop-shadow-sm">{post.user.name}</h3>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span>{timeAgo(post.timestamp)}</span><span>•</span>
              <span className="flex items-center gap-0.5"><Eye className="w-3 h-3" /> {formatNumber(post.views)}</span>
            </div>
          </div>
        </div>
        <button className="text-slate-300 hover:text-slate-500 transition-colors"><MoreHorizontal className="w-5 h-5" /></button>
      </div>

      <p className="text-slate-600 dark:text-slate-300 mb-4 leading-relaxed whitespace-pre-line">
        {post.content.split(' ').map((word, i) =>
          word.startsWith('#') ? <span key={i} className="text-brand-500 font-medium cursor-pointer hover:underline">{word} </span> : word + ' '
        )}
      </p>

      {post.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {post.tags.map(tag => (
            <span key={tag} className="text-[10px] uppercase font-bold text-slate-500 bg-slate-100 dark:bg-white/10 px-2 py-1 rounded-md border border-slate-200 dark:border-white/5">
              #{tag}
            </span>
          ))}
        </div>
      )}

      {post.image && !post.linkedContent && (
        <div className="rounded-2xl overflow-hidden mb-4 border border-white/20 shadow-md">
          <img src={post.image} alt="Post content" className="w-full h-auto object-cover" />
        </div>
      )}

      {post.linkedContent && (
        <LinkedContentCard content={post.linkedContent} onClick={() => onContentClick && onContentClick(post.linkedContent)} />
      )}

      <div className="flex items-center gap-6 pt-4 mt-4 border-t border-slate-200/50 dark:border-white/10">
        <button onClick={() => { onLike(post.id); setIsLiked(!isLiked); }}
          className={`flex items-center gap-2 transition-colors group ${isLiked ? 'text-rose-500' : 'text-slate-400 hover:text-rose-500'}`}>
          <div className={`p-2 rounded-full transition-colors ${isLiked ? 'bg-rose-50 dark:bg-rose-900/20' : 'group-hover:bg-rose-50 dark:group-hover:bg-rose-900/20'}`}>
            <Heart className={`w-5 h-5 ${isLiked ? 'fill-current' : ''}`} />
          </div>
          <span className="font-medium text-sm">{post.likes + (isLiked ? 1 : 0)}</span>
        </button>
        <button onClick={() => setShowComments(!showComments)}
          className={`flex items-center gap-2 text-slate-400 hover:text-blue-500 transition-colors group ${showComments ? 'text-blue-500' : ''}`}>
          <div className="p-2 rounded-full group-hover:bg-blue-50 dark:group-hover:bg-blue-900/20 transition-colors"><MessageCircle className="w-5 h-5" /></div>
          <span className="font-medium text-sm">{comments.length}</span>
        </button>
        <button className="flex items-center gap-2 text-slate-400 hover:text-green-500 transition-colors ml-auto group">
          <div className="p-2 rounded-full group-hover:bg-green-50 dark:group-hover:bg-green-900/20 transition-colors"><Share2 className="w-5 h-5" /></div>
        </button>
      </div>

      <AnimatePresence>
        {showComments && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
            <div className="mt-4 pt-4 border-t border-slate-200/50 dark:border-white/5 bg-slate-50/50 dark:bg-black/20 -mx-6 px-6 -mb-6 pb-6 rounded-b-3xl">
              <div className="flex gap-3 mb-6">
                <img src="https://i.pravatar.cc/150?u=me" className="w-8 h-8 rounded-full border border-white/50" />
                <div className="flex-1 relative">
                  <input type="text" value={newComment} onChange={(e) => setNewComment(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleAddComment()}
                    placeholder="Add a comment..." className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-white/10 rounded-2xl pl-4 pr-10 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 shadow-sm" />
                  <button onClick={handleAddComment} className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 bg-brand-500 text-white rounded-xl hover:scale-105 transition-transform"><Send className="w-3 h-3" /></button>
                </div>
              </div>
              <div className="space-y-1">
                {comments.map(c => <CommentNode key={c.id} comment={c} onReply={handleReply} />)}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function ContentDetailModal({ content, onClose }) {
  const isRecipe = content.type === 'recipe';
  const payload = content.payload;
  const description = payload?.description || "No description available.";
  const tags = isRecipe ? (payload?.tags || []) : [payload?.training_type].filter(Boolean);
  const imageUrl = payload?.imageUrl || content.image;

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-md">
      <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
        className="w-full max-w-2xl bg-white dark:bg-slate-900 rounded-[2rem] shadow-2xl overflow-hidden max-h-[90vh] flex flex-col border border-white/20">
        <div className="relative h-64 shrink-0">
          <img src={imageUrl} alt={content.title} className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent" />
          <button onClick={onClose} className="absolute top-4 right-4 p-2 bg-black/20 backdrop-blur-md hover:bg-black/40 text-white rounded-full transition-colors"><X className="w-5 h-5" /></button>
          <div className="absolute bottom-6 left-6 right-6">
            <div className="flex items-center gap-2 mb-2">
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${isRecipe ? 'bg-brand-500 text-white' : 'bg-blue-500 text-white'}`}>{content.type}</span>
              {tags.map(tag => <span key={tag} className="px-2.5 py-0.5 rounded-full bg-white/20 backdrop-blur-md text-xs font-medium text-white border border-white/20">{tag}</span>)}
            </div>
            <h2 className="text-3xl font-bold text-white drop-shadow-md leading-tight">{content.title}</h2>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-8">
          {isRecipe && payload && (
            <div className="grid grid-cols-4 gap-4 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-2xl border border-slate-100 dark:border-white/5">
              <div className="text-center">
                <p className="text-xs text-slate-400 font-bold uppercase mb-1">Calories</p>
                <p className="text-lg font-bold text-slate-800 dark:text-white flex justify-center items-center gap-1"><Flame className="w-4 h-4 text-orange-500" /> {payload.calories}</p>
              </div>
              <div className="text-center border-l border-slate-200 dark:border-white/10">
                <p className="text-xs text-slate-400 font-bold uppercase mb-1">Prep Time</p>
                <p className="text-lg font-bold text-slate-800 dark:text-white flex justify-center items-center gap-1"><Clock className="w-4 h-4 text-brand-500" /> {payload.prepTime}</p>
              </div>
              <div className="text-center border-l border-slate-200 dark:border-white/10">
                <p className="text-xs text-slate-400 font-bold uppercase mb-1">Protein</p>
                <p className="text-lg font-bold text-slate-800 dark:text-white">{payload.protein}g</p>
              </div>
              <div className="text-center border-l border-slate-200 dark:border-white/10">
                <p className="text-xs text-slate-400 font-bold uppercase mb-1">Carbs</p>
                <p className="text-lg font-bold text-slate-800 dark:text-white">{payload.carbs}g</p>
              </div>
            </div>
          )}
          {!isRecipe && payload && (
            <div className="flex gap-4 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-2xl border border-slate-100 dark:border-white/5">
              <div className="flex-1 text-center">
                <p className="text-xs text-slate-400 font-bold uppercase mb-1">Duration</p>
                <p className="text-lg font-bold text-slate-800 dark:text-white flex justify-center items-center gap-1"><Clock className="w-4 h-4 text-blue-500" /> {Math.floor(payload.est_time / 60)} min</p>
              </div>
              <div className="w-px bg-slate-200 dark:bg-white/10" />
              <div className="flex-1 text-center">
                <p className="text-xs text-slate-400 font-bold uppercase mb-1">Type</p>
                <p className="text-lg font-bold text-slate-800 dark:text-white capitalize">{payload.training_type}</p>
              </div>
            </div>
          )}
          <div>
            <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-2">About this {content.type}</h3>
            <p className="text-slate-600 dark:text-slate-300 leading-relaxed">{description}</p>
          </div>
          {isRecipe && payload?.ingredients && (
            <div>
              <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-3">Ingredients</h3>
              <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {payload.ingredients.map((ing, i) => (
                  <li key={i} className="flex items-center gap-3 p-3 bg-white dark:bg-white/5 border border-slate-100 dark:border-white/5 rounded-xl shadow-sm">
                    <div className="w-2 h-2 rounded-full bg-brand-400 shrink-0" /><span className="text-sm font-medium text-slate-700 dark:text-slate-200">{ing}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {isRecipe && payload?.instructions && (
            <div>
              <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-3">Preparation Steps</h3>
              <div className="space-y-4">
                {payload.instructions.map((step, i) => (
                  <div key={i} className="flex gap-4">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-bold flex items-center justify-center text-sm border border-slate-200 dark:border-white/10">{i + 1}</div>
                    <p className="flex-1 text-slate-600 dark:text-slate-300 leading-relaxed pt-1">{step}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          {!isRecipe && payload?.exercises && (
            <div>
              <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-3">Exercises</h3>
              <div className="space-y-3">
                {payload.exercises.map((ex, i) => (
                  <div key={i} className="flex justify-between items-center p-4 bg-white dark:bg-white/5 rounded-xl border border-slate-100 dark:border-white/5">
                    <div>
                      <span className="font-bold text-slate-700 dark:text-slate-200">{ex._exerciseDetails?.name || 'Unknown'}</span>
                      <div className="text-xs text-slate-400 mt-1">{ex._exerciseDetails?.body_part}</div>
                    </div>
                    <div className="flex gap-4 text-sm text-slate-500">
                      <span>{ex.sets.length} sets</span>
                      {ex.sets[0] && <span>{ex.sets[0].volume} {ex.sets[0].units}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}

function CreatePost({ onClose, onSubmit }) {
  const [content, setContent] = useState('');
  const [attachment, setAttachment] = useState(undefined);
  const [activeTab, setActiveTab] = useState(null);
  const [tags, setTags] = useState([]);
  const [tagInput, setTagInput] = useState('');
  const [showTagSuggestions, setShowTagSuggestions] = useState(false);
  const [attachmentSearchQuery, setAttachmentSearchQuery] = useState('');

  useEffect(() => { if (!activeTab) setAttachmentSearchQuery(''); }, [activeTab]);

  const filteredTags = SUGGESTED_TAGS.filter(t => !tags.includes(t) && t.toLowerCase().includes(tagInput.toLowerCase()));

  const addTag = (tag) => {
    const cleanTag = tag.replace('#', '');
    if (!tags.includes(cleanTag)) setTags([...tags, cleanTag]);
    setTagInput(''); setShowTagSuggestions(false);
  };
  const removeTag = (tag) => setTags(tags.filter(t => t !== tag));
  const handleSelectAttachment = (item) => { setAttachment(item); setActiveTab(null); };

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-md">
      <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
        className="w-full max-w-lg bg-white dark:bg-slate-900 rounded-3xl shadow-2xl overflow-hidden border border-white/20 flex flex-col max-h-[90vh]">
        <div className="p-4 border-b border-slate-100 dark:border-white/5 flex justify-between items-center bg-white/50 dark:bg-white/5 backdrop-blur-sm">
          <h3 className="font-bold text-lg text-slate-800 dark:text-white pl-2">Create Post</h3>
          <button onClick={onClose} className="p-2 hover:bg-black/5 dark:hover:bg-white/10 rounded-full transition-colors"><X className="w-5 h-5 text-slate-400" /></button>
        </div>
        <div className="p-6 space-y-4 overflow-y-auto flex-1">
          <div className="flex gap-4">
            <img src="https://i.pravatar.cc/150?u=me" alt="You" className="w-10 h-10 rounded-full border border-white/50 shrink-0" />
            <div className="flex-1">
              <textarea autoFocus value={content} onChange={(e) => setContent(e.target.value)}
                placeholder="Share your progress, ask a question, or motivate others..."
                className="w-full h-24 bg-transparent text-slate-800 dark:text-white placeholder-slate-400 outline-none resize-none text-base" />
            </div>
          </div>
          {/* Tag input */}
          <div className="space-y-2">
            <div className="flex flex-wrap gap-2 mb-2">
              {tags.map(tag => (
                <span key={tag} className="px-2.5 py-1 rounded-lg bg-brand-50 dark:bg-brand-900/20 text-brand-600 dark:text-brand-400 text-xs font-bold border border-brand-200 dark:border-brand-700/50 flex items-center gap-1">
                  #{tag}<button onClick={() => removeTag(tag)} className="hover:text-red-500 transition-colors"><X className="w-3 h-3" /></button>
                </span>
              ))}
            </div>
            <div className="relative">
              <div className="flex items-center gap-2 px-3 py-2 bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl">
                <Hash className="w-4 h-4 text-slate-400" />
                <input type="text" value={tagInput} onChange={(e) => { setTagInput(e.target.value); setShowTagSuggestions(true); }}
                  onKeyDown={(e) => { if (e.key === 'Enter' && tagInput.trim()) { e.preventDefault(); addTag(tagInput.trim()); } }}
                  placeholder="Add tags..." className="flex-1 bg-transparent text-sm text-slate-800 dark:text-white outline-none placeholder-slate-400" />
              </div>
              {showTagSuggestions && (tagInput || filteredTags.length > 0) && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-white/10 rounded-xl shadow-lg z-50 max-h-40 overflow-y-auto">
                  {filteredTags.map(tag => (
                    <button key={tag} onClick={() => addTag(tag)} className="w-full text-left px-4 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-white/5 flex items-center gap-2">
                      <Hash className="w-3 h-3 text-brand-500" />{tag}
                    </button>
                  ))}
                  {tagInput && !filteredTags.includes(tagInput.toLowerCase()) && (
                    <button onClick={() => addTag(tagInput)} className="w-full text-left px-4 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-white/5 flex items-center gap-2 font-medium">
                      <Plus className="w-3 h-3 text-slate-400" />Create &quot;{tagInput}&quot;
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
          {attachment && (
            <div className="relative">
              <LinkedContentCard content={attachment} />
              <button onClick={() => setAttachment(undefined)} className="absolute -top-1 -right-1 p-1.5 bg-rose-500 text-white rounded-full shadow-md hover:scale-110 transition-transform"><X className="w-3 h-3" /></button>
            </div>
          )}
          <AnimatePresence>
            {activeTab === 'recipe' && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                <div className="sticky top-0 z-10 bg-white dark:bg-slate-900 pb-2">
                  <p className="text-xs font-bold text-slate-500 uppercase mb-2">Select a Recipe</p>
                  <div className="relative mb-2">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input type="text" placeholder="Search recipes..." value={attachmentSearchQuery} onChange={(e) => setAttachmentSearchQuery(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-sm outline-none focus:ring-2 focus:ring-brand-500/20" />
                  </div>
                </div>
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {AVAILABLE_RECIPES.filter(r => r.title.toLowerCase().includes(attachmentSearchQuery.toLowerCase())).map(recipe => (
                    <div key={recipe.id} onClick={() => handleSelectAttachment(recipe)} className="flex items-center gap-3 p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-white/5 cursor-pointer transition-colors">
                      <img src={recipe.image} className="w-10 h-10 rounded-lg object-cover" /><div className="flex-1"><p className="text-sm font-bold text-slate-800 dark:text-white">{recipe.title}</p><p className="text-xs text-slate-500">{recipe.subtitle}</p></div><Plus className="w-4 h-4 text-brand-500" />
                    </div>
                  ))}
                  {AVAILABLE_RECIPES.filter(r => r.title.toLowerCase().includes(attachmentSearchQuery.toLowerCase())).length === 0 && <p className="text-xs text-slate-400 text-center py-2">No recipes found.</p>}
                </div>
              </motion.div>
            )}
            {activeTab === 'workout' && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                <div className="sticky top-0 z-10 bg-white dark:bg-slate-900 pb-2">
                  <p className="text-xs font-bold text-slate-500 uppercase mb-2">Select a Workout</p>
                  <div className="relative mb-2">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input type="text" placeholder="Search workouts..." value={attachmentSearchQuery} onChange={(e) => setAttachmentSearchQuery(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl text-sm outline-none focus:ring-2 focus:ring-brand-500/20" />
                  </div>
                </div>
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {AVAILABLE_WORKOUTS.filter(w => w.title.toLowerCase().includes(attachmentSearchQuery.toLowerCase())).map(workout => (
                    <div key={workout.id} onClick={() => handleSelectAttachment(workout)} className="flex items-center gap-3 p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-white/5 cursor-pointer transition-colors">
                      <img src={workout.image} className="w-10 h-10 rounded-lg object-cover" /><div className="flex-1"><p className="text-sm font-bold text-slate-800 dark:text-white">{workout.title}</p><p className="text-xs text-slate-500">{workout.subtitle}</p></div><Plus className="w-4 h-4 text-brand-500" />
                    </div>
                  ))}
                  {AVAILABLE_WORKOUTS.filter(w => w.title.toLowerCase().includes(attachmentSearchQuery.toLowerCase())).length === 0 && <p className="text-xs text-slate-400 text-center py-2">No workouts found.</p>}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          {!attachment && (
            <div className="flex gap-2 border-t border-slate-100 dark:border-white/5 pt-4">
              <button onClick={() => setActiveTab(activeTab === 'recipe' ? null : 'recipe')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${activeTab === 'recipe' ? 'bg-brand-500 text-white shadow-lg shadow-brand-500/30' : 'bg-slate-100 dark:bg-white/5 text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-white/10'}`}>
                <ChefHat className="w-4 h-4" /> Add Recipe
              </button>
              <button onClick={() => setActiveTab(activeTab === 'workout' ? null : 'workout')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${activeTab === 'workout' ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/30' : 'bg-slate-100 dark:bg-white/5 text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-white/10'}`}>
                <Dumbbell className="w-4 h-4" /> Add Workout
              </button>
            </div>
          )}
        </div>
        <div className="p-4 bg-slate-50 dark:bg-black/20 flex justify-end gap-3 border-t border-slate-100 dark:border-white/5">
          <button onClick={onClose} className="px-5 py-2 text-slate-500 dark:text-slate-400 font-bold hover:text-slate-700 dark:hover:text-white transition-colors">Cancel</button>
          <button onClick={() => onSubmit(content, attachment, tags)} disabled={!content.trim()}
            className="liquid-btn liquid-btn-primary px-6 py-2 rounded-xl font-bold disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"><Send className="w-4 h-4" /> Post</button>
        </div>
      </motion.div>
    </div>
  );
}

// --- MAIN COMPONENT ---

export default function Community() {
  const [posts, setPosts] = useState(INITIAL_POSTS);
  const [sortMode, setSortMode] = useState('trending');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('All');
  const [isCreating, setIsCreating] = useState(false);
  const [page, setPage] = useState(1);
  const [selectedContent, setSelectedContent] = useState(null);

  const sortedPosts = useMemo(() => {
    let sorted = [...posts];
    if (sortMode === 'newest') {
      sorted.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
    } else {
      sorted.sort((a, b) => calculateTrendingScore(b) - calculateTrendingScore(a));
    }
    return sorted;
  }, [posts, sortMode]);

  const filteredPosts = useMemo(() => {
    return sortedPosts.filter(post => {
      const query = searchQuery.toLowerCase();
      const matchesText =
        post.content.toLowerCase().includes(query) ||
        post.user.name.toLowerCase().includes(query) ||
        post.tags.some(t => t.toLowerCase().includes(query)) ||
        post.linkedContent?.title.toLowerCase().includes(query);
      if (!matchesText) return false;
      if (filterType === 'Recipes') return post.linkedContent?.type === 'recipe';
      if (filterType === 'Workouts') return post.linkedContent?.type === 'workout';
      return true;
    });
  }, [sortedPosts, searchQuery, filterType]);

  const visiblePosts = filteredPosts.slice(0, page * 5);
  const hasMore = visiblePosts.length < filteredPosts.length;

  const handleCreatePost = (content, attachment, tags = []) => {
    const newPost = {
      id: Math.random().toString(),
      user: { name: 'You', avatar: 'https://i.pravatar.cc/150?u=me', badge: 'New' },
      content, likes: 0, commentsCount: 0, views: 1,
      timestamp: new Date(), tags: tags, linkedContent: attachment
    };
    setPosts([newPost, ...posts]);
    setIsCreating(false);
  };

  const handleLike = (id) => {
    setPosts(prev => prev.map(p => p.id === id ? { ...p, likes: p.likes + 1 } : p));
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-4 md:p-8 max-w-4xl mx-auto">
      <div className="flex flex-col gap-6 mb-8">
        <div className="flex flex-col md:flex-row justify-between md:items-center gap-4">
          <div>
            <h2 className="text-3xl font-bold text-slate-800 dark:text-white drop-shadow-sm flex items-center gap-2">
              Community Feed
              {sortMode === 'trending' && <Flame className="w-6 h-6 text-orange-500 animate-pulse" />}
            </h2>
            <p className="text-slate-500 dark:text-slate-400 mt-1">Connect, share, and grow together.</p>
          </div>
          <div className="flex gap-3 items-center self-end md:self-auto">
            <div className="flex bg-slate-200/50 dark:bg-white/5 p-1 rounded-xl border border-white/10">
              <button onClick={() => setSortMode('trending')}
                className={`px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 transition-all ${sortMode === 'trending' ? 'bg-white dark:bg-slate-700 shadow-sm text-brand-600 dark:text-brand-400' : 'text-slate-500'}`}>
                <TrendingUp className="w-4 h-4" /> Trending
              </button>
              <button onClick={() => setSortMode('newest')}
                className={`px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 transition-all ${sortMode === 'newest' ? 'bg-white dark:bg-slate-700 shadow-sm text-brand-600 dark:text-brand-400' : 'text-slate-500'}`}>
                <Clock className="w-4 h-4" /> Newest
              </button>
            </div>
            <button onClick={() => setIsCreating(true)}
              className="liquid-btn liquid-btn-primary px-5 py-2.5 rounded-xl font-bold flex items-center gap-2">
              <Plus className="w-5 h-5" /> <span className="hidden sm:inline">New Post</span>
            </button>
          </div>
        </div>

        <div className="glass-panel p-2 rounded-2xl flex flex-col md:flex-row gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
            <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search posts, recipes, workouts, or authors..."
              className="w-full pl-10 pr-10 py-3 bg-transparent text-slate-800 dark:text-white placeholder-slate-400 outline-none" />
            {searchQuery && (
              <button onClick={() => setSearchQuery('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"><X className="w-4 h-4" /></button>
            )}
          </div>
          <div className="flex gap-1 border-l border-slate-200 dark:border-white/10 pl-2">
            {['All', 'Recipes', 'Workouts'].map(f => (
              <button key={f} onClick={() => setFilterType(f)}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${filterType === f ? 'bg-slate-800 dark:bg-white text-white dark:text-slate-900 shadow-lg' : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-white/5'}`}>
                {f}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="space-y-6">
        <AnimatePresence mode="popLayout">
          {visiblePosts.length > 0 ? (
            <div key="posts-list">
              {visiblePosts.map((post) => (
                <PostCard key={post.id} post={post} onLike={handleLike} onContentClick={(content) => setSelectedContent(content)} />
              ))}
              {hasMore && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-center pt-4">
                  <button onClick={() => setPage(p => p + 1)}
                    className="px-6 py-3 rounded-xl bg-white/40 dark:bg-white/5 border border-white/20 hover:bg-white/60 text-slate-600 dark:text-slate-300 font-bold transition-all">Load More Posts</button>
                </motion.div>
              )}
            </div>
          ) : (
            <div className="text-center py-20 opacity-50">
              <Search className="w-12 h-12 mx-auto mb-4 text-slate-300 dark:text-slate-600" />
              <p className="text-lg font-medium text-slate-500 dark:text-slate-400">No posts found</p>
              <p className="text-sm text-slate-400">Try adjusting your search or filters</p>
            </div>
          )}
        </AnimatePresence>
      </div>

      {isCreating && <CreatePost onClose={() => setIsCreating(false)} onSubmit={handleCreatePost} />}

      <AnimatePresence>
        {selectedContent && <ContentDetailModal content={selectedContent} onClose={() => setSelectedContent(null)} />}
      </AnimatePresence>
    </motion.div>
  );
}
