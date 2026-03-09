import { ENDPOINTS } from '../config/network';

const BASE = ENDPOINTS.FORUM;

const defaultOpts = {
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
};

async function request(url, opts = {}) {
  const res = await fetch(url, { ...defaultOpts, ...opts });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Forum API ${res.status}: ${text}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

// ======================== POSTS ========================

export async function getPosts({ skip = 0, limit = 20 } = {}) {
  const params = new URLSearchParams({ skip, limit });
  return request(`${BASE}/posts?${params}`);
}

export async function getTrendingPosts({ skip = 0, limit = 20, min_coefficient = 0 } = {}) {
  const params = new URLSearchParams({ skip, limit, min_coefficient });
  return request(`${BASE}/posts/trending?${params}`);
}

export async function getPostById(postId) {
  return request(`${BASE}/posts/${postId}`);
}

export async function createPost(data) {
  return request(`${BASE}/posts`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updatePost(postId, data) {
  return request(`${BASE}/posts/${postId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deletePost(postId) {
  return request(`${BASE}/posts/${postId}`, { method: 'DELETE' });
}

// ======================== LIKES ========================

export async function likePost(postId) {
  return request(`${BASE}/posts/${postId}/like`, { method: 'POST' });
}

export async function unlikePost(postId) {
  return request(`${BASE}/posts/${postId}/like`, { method: 'DELETE' });
}

export async function getPostLikes(postId) {
  return request(`${BASE}/posts/${postId}/likes`);
}

export async function getPostLikeStatus(postId) {
  return request(`${BASE}/posts/${postId}/like/status`);
}

export async function checkPostsLiked(postIds) {
  return request(`${BASE}/posts/likes/check`, {
    method: 'POST',
    body: JSON.stringify({ post_ids: postIds }),
  });
}

// ======================== VIEWS ========================

export async function trackPostView(postId, engagementSeconds) {
  const params = new URLSearchParams();
  if (engagementSeconds != null) params.set('engagement_seconds', engagementSeconds);
  return request(`${BASE}/posts/${postId}/view?${params}`, { method: 'POST' });
}

// ======================== COMMENTS ========================

export async function getComments(postId, { skip = 0, limit = 50 } = {}) {
  const params = new URLSearchParams({ skip, limit });
  return request(`${BASE}/posts/${postId}/comments?${params}`);
}

export async function getCommentsTree(postId, { max_depth = 3 } = {}) {
  const params = new URLSearchParams({ max_depth });
  return request(`${BASE}/posts/${postId}/comments/tree?${params}`);
}

export async function createComment(postId, data) {
  return request(`${BASE}/posts/${postId}/comments`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getComment(commentId) {
  return request(`${BASE}/comments/${commentId}`);
}

export async function updateComment(commentId, data) {
  return request(`${BASE}/comments/${commentId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteComment(commentId) {
  return request(`${BASE}/comments/${commentId}`, { method: 'DELETE' });
}

export async function getCommentReplies(commentId, { skip = 0, limit = 50 } = {}) {
  const params = new URLSearchParams({ skip, limit });
  return request(`${BASE}/comments/${commentId}/replies?${params}`);
}

export async function likeComment(commentId) {
  return request(`${BASE}/comments/${commentId}/like`, { method: 'POST' });
}

export async function unlikeComment(commentId) {
  return request(`${BASE}/comments/${commentId}/like`, { method: 'DELETE' });
}

export async function getCommentLikeStatus(commentId) {
  return request(`${BASE}/comments/${commentId}/like/status`);
}

export async function checkCommentsLiked(commentIds) {
  return request(`${BASE}/comments/likes/check`, {
    method: 'POST',
    body: JSON.stringify({ comment_ids: commentIds }),
  });
}

// ======================== COMMENT COUNT ========================

export async function getCommentsCount(postId) {
  return request(`${BASE}/posts/${postId}/comments/count`);
}

// ======================== SEARCH ========================

export async function searchForum(q, { category = 'all', tags, author_id, sort_by = 'relevance', skip = 0, limit = 20 } = {}) {
  const params = new URLSearchParams({ q, category, sort_by, skip, limit });
  if (tags && tags.length > 0) {
    tags.forEach(t => params.append('tags', t));
  }
  if (author_id) params.set('author_id', author_id);
  return request(`${BASE}/search?${params}`);
}

export async function getSearchSuggestions(q, { limit = 10 } = {}) {
  const params = new URLSearchParams({ q, limit });
  return request(`${BASE}/search/suggestions?${params}`);
}

export async function getPopularTags({ q, limit = 20 } = {}) {
  const params = new URLSearchParams({ limit });
  if (q) params.set('q', q);
  return request(`${BASE}/search/tags?${params}`);
}

export async function searchByTag(tag, { sort_by = 'newest', skip = 0, limit = 20 } = {}) {
  const params = new URLSearchParams({ sort_by, skip, limit });
  return request(`${BASE}/search/by-tag/${encodeURIComponent(tag)}?${params}`);
}
