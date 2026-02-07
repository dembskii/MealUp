'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Heart, MessageCircle, Share2, MoreHorizontal,
  Search, Flame, Clock, X,
  Eye, TrendingUp, Send, Plus, Hash, Loader2,
  Pencil, Trash2, AlertTriangle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import * as forumAPI from '../services/forumService';
import { batchGetDisplayNames } from '../services/userService';

// ======================== UTILITIES ========================

const formatNumber = (num) => {
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
  return num.toString();
};

const timeAgo = (dateStr) => {
  const date = typeof dateStr === 'string' ? new Date(dateStr) : dateStr;
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return 'Just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months}mo ago`;
  return `${Math.floor(months / 12)}y ago`;
};

// Map API PostResponse to internal shape
const mapPost = (p) => ({
  id: p._id,
  author_id: p.author_id,
  title: p.title,
  content: p.content,
  tags: p.tags || [],
  images: p.images || [],
  likes: p.total_likes ?? 0,
  views: p.views_count ?? 0,
  commentCount: 0,
  timestamp: p._created_at,
  updatedAt: p._updated_at,
});

// Collect all comment IDs from a tree
function collectCommentIds(tree) {
  const ids = [];
  function walk(nodes) {
    for (const node of nodes) {
      const data = node.comment || node;
      ids.push(data._id || data.id);
      if (node.replies?.length) walk(node.replies);
    }
  }
  walk(tree);
  return ids;
}

// Count all comments in a tree recursively
function countTreeComments(tree) {
  let count = 0;
  function walk(nodes) {
    for (const node of nodes) {
      count++;
      if (node.replies?.length) walk(node.replies);
    }
  }
  walk(tree);
  return count;
}

// ======================== HOOKS ========================

function useInfiniteScroll(callback, hasMore, loading) {
  const sentinelRef = useRef(null);

  useEffect(() => {
    if (!hasMore || loading) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) callback();
      },
      { rootMargin: '400px' }
    );
    const el = sentinelRef.current;
    if (el) observer.observe(el);
    return () => { if (el) observer.unobserve(el); };
  }, [callback, hasMore, loading]);

  return sentinelRef;
}

// Simple virtualization hook
function useVirtualList(items, estimatedHeight = 320, overscan = 3) {
  const containerRef = useRef(null);
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: 20 });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const onScroll = () => {
      const scrollTop = window.scrollY - (container.offsetTop || 0);
      const viewportHeight = window.innerHeight;

      const startIdx = Math.max(0, Math.floor(scrollTop / estimatedHeight) - overscan);
      const endIdx = Math.min(
        items.length,
        Math.ceil((scrollTop + viewportHeight) / estimatedHeight) + overscan
      );
      setVisibleRange({ start: startIdx, end: endIdx });
    };

    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onScroll);
    };
  }, [items.length, estimatedHeight, overscan]);

  const totalHeight = items.length * estimatedHeight;
  const offsetY = visibleRange.start * estimatedHeight;
  const visibleItems = items.slice(visibleRange.start, visibleRange.end);

  return { containerRef, totalHeight, offsetY, visibleItems, visibleRange };
}

// ======================== DELETE CONFIRMATION POPUP ========================

function ConfirmDeleteModal({ title, message, onConfirm, onCancel }) {
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-md" onClick={onCancel}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-sm bg-white dark:bg-slate-900 rounded-2xl shadow-2xl overflow-hidden border border-white/20"
      >
        <div className="p-6 text-center">
          <div className="w-14 h-14 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-7 h-7 text-red-500" />
          </div>
          <h3 className="font-bold text-lg text-slate-800 dark:text-white mb-2">{title}</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">{message}</p>
        </div>
        <div className="flex border-t border-slate-200 dark:border-white/10">
          <button onClick={onCancel}
            className="flex-1 py-3 text-sm font-bold text-slate-500 hover:bg-slate-50 dark:hover:bg-white/5 transition-colors">
            Cancel
          </button>
          <button onClick={onConfirm}
            className="flex-1 py-3 text-sm font-bold text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors border-l border-slate-200 dark:border-white/10">
            Delete
          </button>
        </div>
      </motion.div>
    </div>
  );
}

// ======================== COMMENT NODE ========================

function CommentNode({ comment, onReply, onDeleteComment, onEditComment, currentUserId, likedCommentIds, depth = 0 }) {
  const [isReplying, setIsReplying] = useState(false);
  const [replyText, setReplyText] = useState('');
  const data = comment.comment || comment;
  const replies = comment.replies || [];

  const commentId = data._id || data.id;
  const [liked, setLiked] = useState(likedCommentIds.has(commentId));
  const [likeCount, setLikeCount] = useState(data.total_likes ?? 0);
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(data.content);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const isOwner = currentUserId && (data.user_id === currentUserId || data.author_id === currentUserId);

  const handleLike = async () => {
    try {
      if (liked) {
        await forumAPI.unlikeComment(commentId);
        setLikeCount((c) => c - 1);
      } else {
        await forumAPI.likeComment(commentId);
        setLikeCount((c) => c + 1);
      }
      setLiked(!liked);
    } catch {
      /* ignore */
    }
  };

  const handleReply = async () => {
    if (!replyText.trim()) return;
    await onReply(commentId, replyText);
    setReplyText('');
    setIsReplying(false);
  };

  const handleEdit = async () => {
    if (!editText.trim() || editText === data.content) {
      setIsEditing(false);
      return;
    }
    try {
      await onEditComment(commentId, editText);
      setIsEditing(false);
    } catch (e) {
      console.error('Failed to edit comment:', e);
    }
  };

  const handleDelete = async () => {
    try {
      await onDeleteComment(commentId);
    } catch (e) {
      console.error('Failed to delete comment:', e);
    }
    setConfirmDelete(false);
  };

  return (
    <div className={`flex gap-3 ${depth > 0 ? 'mt-3' : 'mt-4'}`}>
      <div className="w-8 h-8 rounded-full bg-brand-500/20 flex items-center justify-center text-brand-500 font-bold text-xs shrink-0">
        {(data.user_id || data.author_id || '?').slice(-2).toUpperCase()}
      </div>
      <div className="flex-1 min-w-0">
        <div className="bg-white/40 dark:bg-white/5 rounded-2xl px-4 py-2 inline-block min-w-[200px] relative group">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-bold text-sm text-slate-800 dark:text-white truncate">
              {(data.user_id || data.author_id)?.slice(0, 12) || 'User'}
            </span>
            <span className="text-xs text-slate-400">{timeAgo(data._created_at || data.created_at)}</span>
            {isOwner && (
              <div className="ml-auto flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => {
                    setIsEditing(true);
                    setEditText(data.content);
                  }}
                  className="p-1 hover:bg-white/20 rounded transition-colors"
                  title="Edit"
                >
                  <Pencil className="w-3 h-3 text-slate-400 hover:text-brand-500" />
                </button>
                <button
                  onClick={() => setConfirmDelete(true)}
                  className="p-1 hover:bg-white/20 rounded transition-colors"
                  title="Delete"
                >
                  <Trash2 className="w-3 h-3 text-slate-400 hover:text-red-500" />
                </button>
              </div>
            )}
          </div>
          {isEditing ? (
            <div className="flex gap-2 mt-1">
              <input
                type="text"
                autoFocus
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleEdit();
                  if (e.key === 'Escape') setIsEditing(false);
                }}
                className="flex-1 bg-white/50 dark:bg-white/10 border border-slate-200 dark:border-white/10 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
              <button onClick={handleEdit} className="text-xs font-bold text-brand-500 hover:text-brand-600">
                Save
              </button>
              <button onClick={() => setIsEditing(false)} className="text-xs font-bold text-slate-400 hover:text-slate-600">
                Cancel
              </button>
            </div>
          ) : (
            <p className="text-sm text-slate-700 dark:text-slate-300 break-words">{data.content}</p>
          )}
        </div>
        <div className="flex items-center gap-4 mt-1 ml-2 text-xs font-semibold text-slate-500">
          <button onClick={handleLike} className={`hover:text-rose-500 flex items-center gap-1 ${liked ? 'text-rose-500' : ''}`}>
            <Heart className={`w-3 h-3 ${liked ? 'fill-current' : ''}`} />
            {likeCount}
          </button>
          {depth < 2 && (
            <button onClick={() => setIsReplying(!isReplying)} className="hover:text-brand-500">
              Reply
            </button>
          )}
        </div>
        {isReplying && (
          <div className="mt-2 flex gap-2">
            <input
              type="text"
              autoFocus
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleReply()}
              placeholder="Write a reply..."
              className="flex-1 bg-white/50 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
            <button onClick={handleReply} className="p-1.5 bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors">
              <Send className="w-4 h-4" />
            </button>
          </div>
        )}
        {replies.length > 0 && (
          <div className="pl-4 border-l-2 border-slate-200/50 dark:border-white/5 mt-2">
            {replies.map((reply) => (
              <CommentNode
                key={reply.comment?._id || reply._id}
                comment={reply}
                onReply={onReply}
                onDeleteComment={onDeleteComment}
                onEditComment={onEditComment}
                currentUserId={currentUserId}
                likedCommentIds={likedCommentIds}
                depth={depth + 1}
              />
            ))}
          </div>
        )}
      </div>

      <AnimatePresence>
        {confirmDelete && (
          <ConfirmDeleteModal
            title="Delete Comment"
            message="Are you sure you want to delete this comment? This action cannot be undone."
            onConfirm={handleDelete}
            onCancel={() => setConfirmDelete(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

// ======================== COMMENT MODAL (Facebook-style) ========================

function CommentModal({ post, onClose, currentUserId, onCommentCountChange }) {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newComment, setNewComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [likedCommentIds, setLikedCommentIds] = useState(new Set());

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    forumAPI
      .getCommentsTree(post.id)
      .then(async (data) => {
        if (cancelled) return;
        setComments(data);
        // Check liked status for all comments
        const allIds = collectCommentIds(data);
        if (allIds.length > 0) {
          try {
            const result = await forumAPI.checkCommentsLiked(allIds);
            if (!cancelled) {
              setLikedCommentIds(new Set(result.liked_comment_ids || []));
            }
          } catch {
            /* ignore */
          }
        }
        // Update comment count
        if (onCommentCountChange) {
          onCommentCountChange(post.id, countTreeComments(data));
        }
      })
      .catch(() => {
        if (!cancelled) setComments([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [post.id]);

  const handleAddComment = async () => {
    if (!newComment.trim() || submitting) return;
    setSubmitting(true);
    try {
      const created = await forumAPI.createComment(post.id, { content: newComment });
      setComments((prev) => {
        const updated = [{ comment: created, replies: [] }, ...prev];
        if (onCommentCountChange) onCommentCountChange(post.id, countTreeComments(updated));
        return updated;
      });
      setNewComment('');
    } catch (e) {
      console.error('Failed to create comment:', e);
    } finally {
      setSubmitting(false);
    }
  };

  const handleReply = async (parentCommentId, text) => {
    try {
      const created = await forumAPI.createComment(post.id, {
        content: text,
        parent_comment_id: parentCommentId,
      });
      const addReply = (nodes) =>
        nodes.map((node) => {
          const nodeId = node.comment?._id || node._id;
          if (nodeId === parentCommentId) {
            return { ...node, replies: [...(node.replies || []), { comment: created, replies: [] }] };
          }
          return { ...node, replies: addReply(node.replies || []) };
        });
      setComments((prev) => {
        const updated = addReply(prev);
        if (onCommentCountChange) onCommentCountChange(post.id, countTreeComments(updated));
        return updated;
      });
    } catch (e) {
      console.error('Failed to reply:', e);
    }
  };

  const handleDeleteComment = async (commentId) => {
    try {
      await forumAPI.deleteComment(commentId);
      const removeFromTree = (nodes) =>
        nodes.filter((node) => {
          const nodeId = node.comment?._id || node._id;
          if (nodeId === commentId) return false;
          node.replies = removeFromTree(node.replies || []);
          return true;
        });
      setComments((prev) => {
        const updated = removeFromTree(prev);
        if (onCommentCountChange) onCommentCountChange(post.id, countTreeComments(updated));
        return updated;
      });
    } catch (e) {
      console.error('Failed to delete comment:', e);
    }
  };

  const handleEditComment = async (commentId, newContent) => {
    const updated = await forumAPI.updateComment(commentId, { content: newContent });
    const updateInTree = (nodes) =>
      nodes.map((node) => {
        const nodeId = node.comment?._id || node._id;
        if (nodeId === commentId) {
          const updatedComment = node.comment
            ? { ...node.comment, content: updated.content || newContent }
            : { ...node, content: updated.content || newContent };
          return { ...node, comment: updatedComment };
        }
        return { ...node, replies: updateInTree(node.replies || []) };
      });
    setComments(updateInTree(comments));
  };

  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = '';
    };
  }, []);

  const totalComments = countTreeComments(comments);

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-md" onClick={onClose}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-2xl bg-white dark:bg-slate-900 rounded-[2rem] shadow-2xl overflow-hidden max-h-[90vh] flex flex-col border border-white/20"
      >
        {/* Post context header */}
        <div className="p-5 border-b border-slate-200/50 dark:border-white/10 bg-white/50 dark:bg-white/5 backdrop-blur-sm">
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-10 h-10 rounded-full bg-brand-500/20 flex items-center justify-center text-brand-500 font-bold text-sm shrink-0">
                {(post.author_id || '?').slice(-2).toUpperCase()}
              </div>
              <div className="min-w-0">
                <h3 className="font-bold text-slate-800 dark:text-white truncate">{post.title || 'Post'}</h3>
                <span className="text-xs text-slate-400">{timeAgo(post.timestamp)}</span>
              </div>
            </div>
            <button onClick={onClose} className="p-2 hover:bg-black/5 dark:hover:bg-white/10 rounded-full transition-colors">
              <X className="w-5 h-5 text-slate-400" />
            </button>
          </div>
          <p className="mt-3 text-sm text-slate-600 dark:text-slate-300 line-clamp-3">{post.content}</p>
          {post.tags?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {post.tags.map((tag) => (
                <span key={tag} className="text-[10px] uppercase font-bold text-slate-500 bg-slate-100 dark:bg-white/10 px-2 py-0.5 rounded-md">
                  #{tag}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Comments count */}
        <div className="px-5 pt-3 pb-1 text-xs font-bold text-slate-400 border-b border-slate-100 dark:border-white/5">
          {loading ? 'Loading...' : `${totalComments} comment${totalComments !== 1 ? 's' : ''}`}
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 min-h-[200px]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-brand-500" />
              <span className="ml-2 text-sm text-slate-400">Loading comments...</span>
            </div>
          ) : comments.length === 0 ? (
            <div className="text-center py-12">
              <MessageCircle className="w-10 h-10 mx-auto mb-3 text-slate-300 dark:text-slate-600" />
              <p className="text-sm text-slate-400">No comments yet. Be the first!</p>
            </div>
          ) : (
            <div className="space-y-1">
              {comments.map((c) => (
                <CommentNode
                  key={c.comment?._id || c._id}
                  comment={c}
                  onReply={handleReply}
                  onDeleteComment={handleDeleteComment}
                  onEditComment={handleEditComment}
                  currentUserId={currentUserId}
                  likedCommentIds={likedCommentIds}
                />
              ))}
            </div>
          )}
        </div>

        {/* New comment input */}
        <div className="p-4 border-t border-slate-200/50 dark:border-white/10 bg-slate-50/50 dark:bg-black/20">
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-brand-500 flex items-center justify-center text-white font-bold text-xs shrink-0">
              {currentUserId ? currentUserId.slice(-2).toUpperCase() : 'Y'}
            </div>
            <div className="flex-1 relative">
              <input
                type="text"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAddComment()}
                placeholder="Write a comment..."
                disabled={submitting}
                className="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-white/10 rounded-2xl pl-4 pr-12 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 shadow-sm disabled:opacity-50"
              />
              <button
                onClick={handleAddComment}
                disabled={submitting || !newComment.trim()}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 bg-brand-500 text-white rounded-xl hover:scale-105 transition-transform disabled:opacity-50"
              >
                {submitting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />}
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

// ======================== POST CARD ========================

function PostCard({ post, onCommentClick, currentUserId, isLiked, onLikeChange, onEdit, onDelete, viewedPostIdsRef, authorName }) {
  const [localLiked, setLocalLiked] = useState(isLiked);
  const [likeCount, setLikeCount] = useState(post.likes);
  const cardRef = useRef(null);
  const [showMenu, setShowMenu] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const menuRef = useRef(null);

  const isOwner = currentUserId && post.author_id === currentUserId;

  // Sync isLiked prop to local state when it changes (after API check)
  useEffect(() => {
    setLocalLiked(isLiked);
  }, [isLiked]);

  // Track view when post enters viewport (using parent-level Set to survive virtualization)
  useEffect(() => {
    const el = cardRef.current;
    if (!el || !viewedPostIdsRef?.current) return;
    if (viewedPostIdsRef.current.has(post.id)) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !viewedPostIdsRef.current.has(post.id)) {
          viewedPostIdsRef.current.add(post.id);
          forumAPI.trackPostView(post.id).catch(() => {});
        }
      },
      { threshold: 0.5 }
    );
    observer.observe(el);
    return () => observer.unobserve(el);
  }, [post.id]);

  // Close menu on outside click
  useEffect(() => {
    if (!showMenu) return;
    const handler = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setShowMenu(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showMenu]);

  const handleLike = async () => {
    try {
      if (localLiked) {
        await forumAPI.unlikePost(post.id);
        setLikeCount((c) => c - 1);
      } else {
        await forumAPI.likePost(post.id);
        setLikeCount((c) => c + 1);
      }
      const newState = !localLiked;
      setLocalLiked(newState);
      if (onLikeChange) onLikeChange(post.id, newState);
    } catch (e) {
      console.error('Like failed:', e);
    }
  };

  const handleDelete = async () => {
    setConfirmDelete(false);
    setShowMenu(false);
    if (onDelete) onDelete(post.id);
  };

  return (
    <div ref={cardRef} className="glass-panel rounded-3xl p-6 transition-all duration-300 hover:shadow-xl mb-6">
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-brand-500/20 flex items-center justify-center text-brand-500 font-bold border-2 border-white/80 shadow-md">
            {(authorName || post.author_id || '?').slice(0, 2).toUpperCase()}
          </div>
          <div>
            <span className="font-semibold text-slate-800 dark:text-white drop-shadow-sm">
              {authorName || post.author_id?.slice(0, 12) || 'User'}
            </span>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span>{timeAgo(post.timestamp)}</span>
              <span>&bull;</span>
              <span className="flex items-center gap-0.5">
                <Eye className="w-3 h-3" /> {formatNumber(post.views)}
              </span>
            </div>
          </div>
        </div>
        {isOwner && (
          <div className="relative" ref={menuRef}>
            <button onClick={() => setShowMenu(!showMenu)} className="text-slate-300 hover:text-slate-500 transition-colors p-1">
              <MoreHorizontal className="w-5 h-5" />
            </button>
            {showMenu && (
              <div className="absolute right-0 top-8 bg-white dark:bg-slate-800 border border-slate-200 dark:border-white/10 rounded-xl shadow-xl z-50 min-w-[140px] overflow-hidden">
                <button
                  onClick={() => {
                    setShowMenu(false);
                    onEdit(post);
                  }}
                  className="w-full text-left px-4 py-2.5 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-white/5 flex items-center gap-2"
                >
                  <Pencil className="w-4 h-4" /> Edit
                </button>
                <button
                  onClick={() => {
                    setShowMenu(false);
                    setConfirmDelete(true);
                  }}
                  className="w-full text-left px-4 py-2.5 text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2"
                >
                  <Trash2 className="w-4 h-4" /> Delete
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Title */}
      {post.title && (
        <h3 className="font-bold text-lg text-slate-800 dark:text-white mb-2">{post.title}</h3>
      )}

      {/* Content */}
      <p className="text-slate-600 dark:text-slate-300 mb-4 leading-relaxed whitespace-pre-line">{post.content}</p>

      {/* Tags */}
      {post.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {post.tags.map((tag) => (
            <span
              key={tag}
              className="text-[10px] uppercase font-bold text-slate-500 bg-slate-100 dark:bg-white/10 px-2 py-1 rounded-md border border-slate-200 dark:border-white/5"
            >
              #{tag}
            </span>
          ))}
        </div>
      )}

      {/* Images */}
      {post.images?.length > 0 && (
        <div className="rounded-2xl overflow-hidden mb-4 border border-white/20 shadow-md">
          <img src={post.images[0]} alt="Post" className="w-full h-auto object-cover max-h-[400px]" />
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-6 pt-4 mt-4 border-t border-slate-200/50 dark:border-white/10">
        <button
          onClick={handleLike}
          className={`flex items-center gap-2 transition-colors group ${localLiked ? 'text-rose-500' : 'text-slate-400 hover:text-rose-500'}`}
        >
          <div
            className={`p-2 rounded-full transition-colors ${localLiked ? 'bg-rose-50 dark:bg-rose-900/20' : 'group-hover:bg-rose-50 dark:group-hover:bg-rose-900/20'}`}
          >
            <Heart className={`w-5 h-5 ${localLiked ? 'fill-current' : ''}`} />
          </div>
          <span className="font-medium text-sm">{likeCount}</span>
        </button>

        <button onClick={() => onCommentClick(post)} className="flex items-center gap-2 text-slate-400 hover:text-blue-500 transition-colors group">
          <div className="p-2 rounded-full group-hover:bg-blue-50 dark:group-hover:bg-blue-900/20 transition-colors">
            <MessageCircle className="w-5 h-5" />
          </div>
          <span className="font-medium text-sm">{post.commentCount > 0 ? `${post.commentCount} ` : ''}Comments</span>
        </button>

        <button className="flex items-center gap-2 text-slate-400 hover:text-green-500 transition-colors ml-auto group">
          <div className="p-2 rounded-full group-hover:bg-green-50 dark:group-hover:bg-green-900/20 transition-colors">
            <Share2 className="w-5 h-5" />
          </div>
        </button>
      </div>

      <AnimatePresence>
        {confirmDelete && (
          <ConfirmDeleteModal
            title="Delete Post"
            message="Are you sure you want to delete this post? All comments will also be removed. This action cannot be undone."
            onConfirm={handleDelete}
            onCancel={() => setConfirmDelete(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

// ======================== SHARED POST FORM MODAL (Create / Edit) ========================

const SUGGESTED_TAGS = ['fitness', 'nutrition', 'recipe', 'workout', 'motivation', 'healthy', 'beginner', 'gains', 'weightloss', 'cardio'];

function PostFormModal({ onClose, onSubmit, editPost }) {
  const isEdit = !!editPost;
  const [title, setTitle] = useState(editPost?.title || '');
  const [content, setContent] = useState(editPost?.content || '');
  const [tags, setTags] = useState(editPost?.tags || []);
  const [tagInput, setTagInput] = useState('');
  const [showTagSuggestions, setShowTagSuggestions] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const filteredTags = SUGGESTED_TAGS.filter((t) => !tags.includes(t) && t.toLowerCase().includes(tagInput.toLowerCase()));

  const addTag = (tag) => {
    const clean = tag.replace('#', '').toLowerCase();
    if (clean && !tags.includes(clean)) setTags([...tags, clean]);
    setTagInput('');
    setShowTagSuggestions(false);
  };

  const handleSubmit = async () => {
    if (!title.trim() || !content.trim() || submitting) return;
    setSubmitting(true);
    try {
      const payload = {
        title: title.trim(),
        content: content.trim(),
        tags: tags.length > 0 ? tags : undefined,
      };
      if (isEdit && editPost.images?.length > 0) {
        payload.images = editPost.images;
      }
      await onSubmit(payload);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-md" onClick={onClose}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-lg bg-white dark:bg-slate-900 rounded-3xl shadow-2xl overflow-hidden border border-white/20 flex flex-col max-h-[90vh]"
      >
        <div className="p-4 border-b border-slate-100 dark:border-white/5 flex justify-between items-center bg-white/50 dark:bg-white/5 backdrop-blur-sm">
          <h3 className="font-bold text-lg text-slate-800 dark:text-white pl-2">{isEdit ? 'Edit Post' : 'Create Post'}</h3>
          <button onClick={onClose} className="p-2 hover:bg-black/5 dark:hover:bg-white/10 rounded-full transition-colors">
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        <div className="p-6 space-y-4 overflow-y-auto flex-1">
          {/* Title */}
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Post title..."
            className="w-full bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl px-4 py-3 text-slate-800 dark:text-white placeholder-slate-400 outline-none focus:ring-2 focus:ring-brand-500/20 text-base font-medium"
          />

          {/* Content */}
          <textarea
            autoFocus
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Share your progress, ask a question, or motivate others..."
            className="w-full h-32 bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl px-4 py-3 text-slate-800 dark:text-white placeholder-slate-400 outline-none resize-none text-base focus:ring-2 focus:ring-brand-500/20"
          />

          {/* Tags */}
          <div className="space-y-2">
            <div className="flex flex-wrap gap-2 mb-2">
              {tags.map((tag) => (
                <span
                  key={tag}
                  className="px-2.5 py-1 rounded-lg bg-brand-50 dark:bg-brand-900/20 text-brand-600 dark:text-brand-400 text-xs font-bold border border-brand-200 dark:border-brand-700/50 flex items-center gap-1"
                >
                  #{tag}
                  <button onClick={() => setTags(tags.filter((t) => t !== tag))} className="hover:text-red-500 transition-colors">
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
            <div className="relative">
              <div className="flex items-center gap-2 px-3 py-2 bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl">
                <Hash className="w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={tagInput}
                  onChange={(e) => {
                    setTagInput(e.target.value);
                    setShowTagSuggestions(true);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && tagInput.trim()) {
                      e.preventDefault();
                      addTag(tagInput.trim());
                    }
                  }}
                  placeholder="Add tags..."
                  className="flex-1 bg-transparent text-sm text-slate-800 dark:text-white outline-none placeholder-slate-400"
                />
              </div>
              {showTagSuggestions && tagInput && filteredTags.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-white/10 rounded-xl shadow-lg z-50 max-h-40 overflow-y-auto">
                  {filteredTags.map((tag) => (
                    <button
                      key={tag}
                      onClick={() => addTag(tag)}
                      className="w-full text-left px-4 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-white/5 flex items-center gap-2"
                    >
                      <Hash className="w-3 h-3 text-brand-500" />
                      {tag}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="p-4 bg-slate-50 dark:bg-black/20 flex justify-end gap-3 border-t border-slate-100 dark:border-white/5">
          <button onClick={onClose} className="px-5 py-2 text-slate-500 dark:text-slate-400 font-bold hover:text-slate-700 dark:hover:text-white transition-colors">
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!title.trim() || !content.trim() || submitting}
            className="liquid-btn liquid-btn-primary px-6 py-2 rounded-xl font-bold disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            {isEdit ? 'Save' : 'Post'}
          </button>
        </div>
      </motion.div>
    </div>
  );
}

// ======================== MAIN COMPONENT ========================

const PAGE_SIZE = 15;

export default function Community() {
  const [posts, setPosts] = useState([]);
  const [sortMode, setSortMode] = useState('trending');
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [filterType, setFilterType] = useState('All');
  const [isCreating, setIsCreating] = useState(false);
  const [editingPost, setEditingPost] = useState(null);
  const [commentPost, setCommentPost] = useState(null);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState(null);
  const [currentUserId, setCurrentUserId] = useState(null);
  const [likedPostIds, setLikedPostIds] = useState(new Set());
  const skipRef = useRef(0);
  const fetchIdRef = useRef(0);
  const viewedPostIdsRef = useRef(new Set());
  const [authorNames, setAuthorNames] = useState({});

  // Fetch current user on mount
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('http://localhost:8000/api/v1/auth/me', { credentials: 'include' });
        if (res.ok) {
          const auth = await res.json();
          setCurrentUserId(auth.internal_uid || null);
        }
      } catch {
        /* not logged in */
      }
    })();
  }, []);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchQuery), 400);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Check like status for a batch of posts
  const checkLikeStatus = useCallback(
    async (postIds) => {
      if (!currentUserId || postIds.length === 0) return;
      try {
        const result = await forumAPI.checkPostsLiked(postIds);
        const newLiked = new Set(result.liked_post_ids || []);
        setLikedPostIds((prev) => {
          const merged = new Set(prev);
          newLiked.forEach((id) => merged.add(id));
          return merged;
        });
      } catch {
        /* ignore */
      }
    },
    [currentUserId]
  );

  // Fetch comment counts for a batch of posts
  const fetchCommentCounts = useCallback(async (postsList) => {
    const promises = postsList.map(async (post) => {
      try {
        const result = await forumAPI.getCommentsCount(post.id);
        return { id: post.id, count: result.count };
      } catch {
        return { id: post.id, count: 0 };
      }
    });
    const results = await Promise.all(promises);
    setPosts((prev) =>
      prev.map((p) => {
        const found = results.find((r) => r.id === p.id);
        return found ? { ...p, commentCount: found.count } : p;
      })
    );
  }, []);

  // Fetch author display names for posts
  const fetchAuthorNames = useCallback(async (postsList) => {
    const uids = postsList.map((p) => p.author_id).filter(Boolean);
    if (uids.length === 0) return;
    try {
      const nameMap = await batchGetDisplayNames(uids);
      setAuthorNames((prev) => {
        const next = { ...prev };
        nameMap.forEach((name, uid) => { next[uid] = name; });
        return next;
      });
    } catch {
      /* ignore */
    }
  }, []);

  // Fetch posts
  const fetchPosts = useCallback(
    async (reset = false) => {
      if (loading && !reset) return;
      setLoading(true);
      setError(null);

      const currentFetchId = ++fetchIdRef.current;
      const skip = reset ? 0 : skipRef.current;

      try {
        let data;

        if (debouncedSearch.trim()) {
          const category = filterType === 'Recipes' ? 'recipes' : filterType === 'Workouts' ? 'workouts' : 'posts';
          const result = await forumAPI.searchForum(debouncedSearch, {
            category,
            sort_by: sortMode === 'trending' ? 'trending' : 'newest',
            skip,
            limit: PAGE_SIZE,
          });
          data = (result.posts || []).map((p) => ({
            _id: p.id,
            author_id: p.author_id,
            title: p.title,
            content: p.content,
            tags: p.tags || [],
            images: p.images || [],
            total_likes: p.total_likes ?? 0,
            views_count: p.views_count ?? 0,
            _created_at: p.created_at,
            _updated_at: p.updated_at,
          }));
          setHasMore(result.has_more ?? data.length === PAGE_SIZE);
        } else if (sortMode === 'trending') {
          data = await forumAPI.getTrendingPosts({ skip, limit: PAGE_SIZE });
          setHasMore(data.length === PAGE_SIZE);
        } else {
          data = await forumAPI.getPosts({ skip, limit: PAGE_SIZE });
          setHasMore(data.length === PAGE_SIZE);
        }

        if (currentFetchId !== fetchIdRef.current) return;

        const mapped = data.map(mapPost);

        if (reset) {
          setPosts(mapped);
          skipRef.current = mapped.length;
          if (currentUserId && mapped.length > 0) {
            setLikedPostIds(new Set());
            checkLikeStatus(mapped.map((p) => p.id));
          }
          fetchCommentCounts(mapped);
          fetchAuthorNames(mapped);
        } else {
          setPosts((prev) => {
            const existingIds = new Set(prev.map((p) => p.id));
            const newPosts = mapped.filter((p) => !existingIds.has(p.id));
            return [...prev, ...newPosts];
          });
          skipRef.current = skip + mapped.length;
          const newIds = mapped.map((p) => p.id);
          if (currentUserId && newIds.length > 0) {
            checkLikeStatus(newIds);
          }
          fetchCommentCounts(mapped);
          fetchAuthorNames(mapped);
        }
      } catch (e) {
        if (currentFetchId !== fetchIdRef.current) return;
        console.error('Failed to fetch posts:', e);
        setError(e.message);
      } finally {
        if (currentFetchId === fetchIdRef.current) {
          setLoading(false);
          setInitialLoading(false);
        }
      }
    },
    [sortMode, debouncedSearch, filterType, currentUserId, checkLikeStatus, fetchCommentCounts, fetchAuthorNames]
  );

  // Reset & fetch on sort/search/filter change
  useEffect(() => {
    skipRef.current = 0;
    setPosts([]);
    setHasMore(true);
    setInitialLoading(true);
    fetchPosts(true);
  }, [sortMode, debouncedSearch, filterType]);

  // Re-check like status when currentUserId becomes available after posts loaded
  useEffect(() => {
    if (!currentUserId || posts.length === 0) return;
    // Only re-check if likedPostIds is empty (meaning initial fetch didn't check)
    if (likedPostIds.size > 0) return;
    checkLikeStatus(posts.map((p) => p.id));
  }, [currentUserId, posts.length]);

  const loadMore = useCallback(() => {
    if (!loading && hasMore) fetchPosts(false);
  }, [fetchPosts, loading, hasMore]);

  const sentinelRef = useInfiniteScroll(loadMore, hasMore, loading);
  const { containerRef, totalHeight, offsetY, visibleItems } = useVirtualList(posts, 280, 5);

  // Create post handler
  const handleCreatePost = async (postData) => {
    try {
      const created = await forumAPI.createPost(postData);
      const mapped = mapPost(created);
      setPosts((prev) => [mapped, ...prev]);
      fetchAuthorNames([mapped]);
      setIsCreating(false);
    } catch (e) {
      console.error('Failed to create post:', e);
      alert('Failed to create post: ' + e.message);
    }
  };

  // Edit post handler
  const handleEditPost = async (postData) => {
    if (!editingPost) return;
    try {
      const updated = await forumAPI.updatePost(editingPost.id, postData);
      const mapped = mapPost(updated);
      mapped.commentCount = editingPost.commentCount || 0;
      setPosts((prev) => prev.map((p) => (p.id === editingPost.id ? mapped : p)));
      setEditingPost(null);
    } catch (e) {
      console.error('Failed to update post:', e);
      alert('Failed to update post: ' + e.message);
    }
  };

  // Delete post handler
  const handleDeletePost = async (postId) => {
    try {
      await forumAPI.deletePost(postId);
      setPosts((prev) => prev.filter((p) => p.id !== postId));
    } catch (e) {
      console.error('Failed to delete post:', e);
      alert('Failed to delete post: ' + e.message);
    }
  };

  // Like change handler
  const handleLikeChange = (postId, liked) => {
    setLikedPostIds((prev) => {
      const next = new Set(prev);
      if (liked) next.add(postId);
      else next.delete(postId);
      return next;
    });
  };

  // Comment count change handler (called from CommentModal)
  const handleCommentCountChange = (postId, count) => {
    setPosts((prev) => prev.map((p) => (p.id === postId ? { ...p, commentCount: count } : p)));
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-4 md:p-8 max-w-4xl mx-auto">
      {/* Header */}
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
              <button
                onClick={() => setSortMode('trending')}
                className={`px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 transition-all ${sortMode === 'trending' ? 'bg-white dark:bg-slate-700 shadow-sm text-brand-600 dark:text-brand-400' : 'text-slate-500'}`}
              >
                <TrendingUp className="w-4 h-4" /> Trending
              </button>
              <button
                onClick={() => setSortMode('newest')}
                className={`px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2 transition-all ${sortMode === 'newest' ? 'bg-white dark:bg-slate-700 shadow-sm text-brand-600 dark:text-brand-400' : 'text-slate-500'}`}
              >
                <Clock className="w-4 h-4" /> Newest
              </button>
            </div>
            <button onClick={() => setIsCreating(true)} className="liquid-btn liquid-btn-primary px-5 py-2.5 rounded-xl font-bold flex items-center gap-2">
              <Plus className="w-5 h-5" /> <span className="hidden sm:inline">New Post</span>
            </button>
          </div>
        </div>

        {/* Search bar */}
        <div className="glass-panel p-2 rounded-2xl flex flex-col md:flex-row gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search posts, recipes, workouts, or authors..."
              className="w-full pl-10 pr-10 py-3 bg-transparent text-slate-800 dark:text-white placeholder-slate-400 outline-none"
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
          <div className="flex gap-1 border-l border-slate-200 dark:border-white/10 pl-2">
            {['All', 'Recipes', 'Workouts'].map((f) => (
              <button
                key={f}
                onClick={() => setFilterType(f)}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${filterType === f ? 'bg-slate-800 dark:bg-white text-white dark:text-slate-900 shadow-lg' : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-white/5'}`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl text-red-700 dark:text-red-300 text-sm flex items-center justify-between">
          <span>Failed to load posts. Please try again.</span>
          <button onClick={() => fetchPosts(true)} className="font-bold hover:underline ml-4">
            Retry
          </button>
        </div>
      )}

      {/* Posts feed with virtualization */}
      <div ref={containerRef}>
        {initialLoading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-brand-500 mb-4" />
            <p className="text-sm text-slate-400">Loading community feed...</p>
          </div>
        ) : posts.length === 0 ? (
          <div className="text-center py-20 opacity-50">
            <Search className="w-12 h-12 mx-auto mb-4 text-slate-300 dark:text-slate-600" />
            <p className="text-lg font-medium text-slate-500 dark:text-slate-400">No posts found</p>
            <p className="text-sm text-slate-400">Try adjusting your search or filters</p>
          </div>
        ) : (
          <div style={{ minHeight: totalHeight, position: 'relative' }}>
            <div style={{ transform: `translateY(${offsetY}px)` }}>
              {visibleItems.map((post) => (
                <PostCard
                  key={post.id}
                  post={post}
                  currentUserId={currentUserId}
                  isLiked={likedPostIds.has(post.id)}
                  onLikeChange={handleLikeChange}
                  onCommentClick={(p) => setCommentPost(p)}
                  onEdit={(p) => setEditingPost(p)}
                  onDelete={handleDeletePost}
                  viewedPostIdsRef={viewedPostIdsRef}
                  authorName={authorNames[post.author_id]}
                />
              ))}
            </div>
          </div>
        )}

        <div ref={sentinelRef} className="h-4" />

        {loading && !initialLoading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 animate-spin text-brand-500" />
            <span className="ml-2 text-sm text-slate-400">Loading more...</span>
          </div>
        )}

        {!hasMore && posts.length > 0 && (
          <div className="text-center py-8 text-sm text-slate-400">You&apos;ve reached the end of the feed</div>
        )}
      </div>

      {/* Create Post Modal */}
      <AnimatePresence>{isCreating && <PostFormModal onClose={() => setIsCreating(false)} onSubmit={handleCreatePost} />}</AnimatePresence>

      {/* Edit Post Modal (shared form) */}
      <AnimatePresence>
        {editingPost && <PostFormModal onClose={() => setEditingPost(null)} onSubmit={handleEditPost} editPost={editingPost} />}
      </AnimatePresence>

      {/* Comment Modal */}
      <AnimatePresence>
        {commentPost && (
          <CommentModal post={commentPost} onClose={() => setCommentPost(null)} currentUserId={currentUserId} onCommentCountChange={handleCommentCountChange} />
        )}
      </AnimatePresence>
    </motion.div>
  );
}
