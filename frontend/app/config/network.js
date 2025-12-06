// Base configuration
const GATEWAY_HOST = "localhost";
const GATEWAY_PORT = 8000;
const API_VERSION = "v1";
const API_PREFIX = "api";

// Constructed URLs
export const GATEWAY_URL = `http://${GATEWAY_HOST}:${GATEWAY_PORT}`;
export const API_ENDPOINT_URL = `${GATEWAY_URL}/${API_PREFIX}/${API_VERSION}`;

// Service endpoints
export const ENDPOINTS = {
  AUTH: `${API_ENDPOINT_URL}/auth`,
  USERS: `${API_ENDPOINT_URL}/users`,
  RECIPES: `${API_ENDPOINT_URL}/recipes`,
};

export default {
  GATEWAY_URL,
  API_ENDPOINT_URL,
  ENDPOINTS,
};
