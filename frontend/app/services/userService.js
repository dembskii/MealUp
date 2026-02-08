import { ENDPOINTS } from '../config/network';

// In-memory cache for user display names
const userCache = new Map();

/**
 * Fetch user info by UUID from user-service.
 * Returns { username, first_name, last_name } or null.
 */
export async function getUserById(uid) {
  if (!uid) return null;
  try {
    const res = await fetch(`${ENDPOINTS.USERS}/users/${uid}`, {
      credentials: 'include',
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/**
 * Get a display name for a user.
 * Uses in-memory cache to avoid repeated API calls.
 * Returns the cached/fetched display name or a short fallback.
 */
export async function getUserDisplayName(uid) {
  if (!uid) return 'User';
  if (userCache.has(uid)) return userCache.get(uid);

  const user = await getUserById(uid);
  let displayName;
  if (user) {
    if (user.first_name && user.last_name) {
      displayName = `${user.first_name} ${user.last_name}`;
    } else if (user.username) {
      displayName = user.username;
    } else {
      displayName = uid.slice(0, 8);
    }
  } else {
    displayName = uid.slice(0, 8);
  }

  userCache.set(uid, displayName);
  return displayName;
}

/**
 * Batch-fetch display names for multiple user IDs.
 * Returns a Map<uid, displayName>.
 */
export async function batchGetDisplayNames(uids) {
  const unique = [...new Set(uids)];
  const results = new Map();
  const toFetch = [];

  for (const uid of unique) {
    if (userCache.has(uid)) {
      results.set(uid, userCache.get(uid));
    } else {
      toFetch.push(uid);
    }
  }

  if (toFetch.length > 0) {
    const promises = toFetch.map((uid) => getUserDisplayName(uid));
    const names = await Promise.all(promises);
    toFetch.forEach((uid, i) => {
      results.set(uid, names[i]);
    });
  }

  return results;
}

export default { getUserById, getUserDisplayName, batchGetDisplayNames };

// ======================== LIKED WORKOUTS ========================

const defaultOpts = {
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
};

/**
 * Like a workout for a user.
 * POST /user/users/{uid}/liked-workouts
 */
export async function likeWorkout(uid, workoutId) {
  const res = await fetch(`${ENDPOINTS.USERS}/users/${uid}/liked-workouts`, {
    ...defaultOpts,
    method: 'POST',
    body: JSON.stringify({ workout_id: workoutId }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Like workout failed ${res.status}: ${text}`);
  }
  return res.json();
}

/**
 * Unlike a workout for a user.
 * DELETE /user/users/{uid}/liked-workouts/{workout_id}
 */
export async function unlikeWorkout(uid, workoutId) {
  const res = await fetch(`${ENDPOINTS.USERS}/users/${uid}/liked-workouts/${workoutId}`, {
    ...defaultOpts,
    method: 'DELETE',
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Unlike workout failed ${res.status}: ${text}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

/**
 * Get all liked workouts for a user (paginated).
 * GET /user/users/{uid}/liked-workouts
 * Returns { total, items: [{ id, user_id, workout_id, created_at }] }
 */
export async function getLikedWorkouts(uid, { skip = 0, limit = 100 } = {}) {
  const params = new URLSearchParams();
  params.set('skip', skip);
  params.set('limit', limit);
  const res = await fetch(`${ENDPOINTS.USERS}/users/${uid}/liked-workouts?${params}`, {
    credentials: 'include',
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Get liked workouts failed ${res.status}: ${text}`);
  }
  return res.json();
}

/**
 * Bulk check like status for multiple workouts.
 * POST /user/users/{uid}/liked-workouts/check-bulk
 * Returns { results: { [workout_id]: boolean } }
 */
export async function checkWorkoutsLikedBulk(uid, workoutIds) {
  const res = await fetch(`${ENDPOINTS.USERS}/users/${uid}/liked-workouts/check-bulk`, {
    ...defaultOpts,
    method: 'POST',
    body: JSON.stringify({ workout_ids: workoutIds }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Bulk like check failed ${res.status}: ${text}`);
  }
  return res.json();
}
