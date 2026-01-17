/**
 * CareNest API Service
 * Centralized API client for all backend endpoints
 */

const BASE_URL = 'http://localhost:8000';

/**
 * Generic fetch wrapper with error handling
 */
async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body);
  }

  const response = await fetch(url, config);
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'API request failed');
  }
  
  return response.json();
}

// =============================================================================
// Nutrition API
// =============================================================================

export const NutritionAPI = {
  // Full Pipeline - AI analyzes and saves
  analyzeAndSave: (userId, { name, desc, amnt }) =>
    request(`/nutrition/analyze/${userId}`, {
      method: 'POST',
      body: { name, desc, amnt },
    }),

  analyzeOnly: ({ name, desc, amnt }) =>
    request('/nutrition/analyze-only', {
      method: 'POST',
      body: { name, desc, amnt },
    }),

  // Meal CRUD
  createMeal: (userId, mealData) =>
    request(`/nutrition/meals/${userId}`, {
      method: 'POST',
      body: mealData,
    }),

  getMeal: (userId, mealId) =>
    request(`/nutrition/meals/${userId}/${mealId}`),

  getAllMeals: (userId, { limit = 50, orderBy = 'created_at', descending = true } = {}) =>
    request(`/nutrition/meals/${userId}?limit=${limit}&order_by=${orderBy}&descending=${descending}`),

  getMealsByDateRange: (userId, startDate, endDate) =>
    request(`/nutrition/meals/${userId}/range?start_date=${startDate}&end_date=${endDate}`),

  updateMeal: (userId, mealId, updates) =>
    request(`/nutrition/meals/${userId}/${mealId}`, {
      method: 'PATCH',
      body: updates,
    }),

  deleteMeal: (userId, mealId) =>
    request(`/nutrition/meals/${userId}/${mealId}`, { method: 'DELETE' }),

  deleteAllMeals: (userId) =>
    request(`/nutrition/meals/${userId}`, { method: 'DELETE' }),

  // Summaries
  getDailySummary: (userId, date) =>
    request(`/nutrition/summary/${userId}/daily?date=${date}`),

  getMealCount: (userId) =>
    request(`/nutrition/stats/${userId}/count`),

  // Barcode
  scanBarcode: (barcode) =>
    request(`/nutrition/barcode/scan/${barcode}`),

  getBarcodeReport: (barcode) =>
    request(`/nutrition/barcode/report/${barcode}`),
};

// =============================================================================
// Water Log API
// =============================================================================

export const WaterAPI = {
  logWater: (userId, { amount_ml, note }) =>
    request(`/nutrition/water/${userId}`, {
      method: 'POST',
      body: { amount_ml, note },
    }),

  getWaterLog: (userId, logId) =>
    request(`/nutrition/water/${userId}/${logId}`),

  getAllWaterLogs: (userId, { limit = 50, orderBy = 'created_at', descending = true } = {}) =>
    request(`/nutrition/water/${userId}?limit=${limit}&order_by=${orderBy}&descending=${descending}`),

  getWaterLogsByDateRange: (userId, startDate, endDate) =>
    request(`/nutrition/water/${userId}/range?start_date=${startDate}&end_date=${endDate}`),

  updateWaterLog: (userId, logId, updates) =>
    request(`/nutrition/water/${userId}/${logId}`, {
      method: 'PATCH',
      body: updates,
    }),

  deleteWaterLog: (userId, logId) =>
    request(`/nutrition/water/${userId}/${logId}`, { method: 'DELETE' }),

  deleteAllWaterLogs: (userId) =>
    request(`/nutrition/water/${userId}`, { method: 'DELETE' }),

  getDailySummary: (userId, date, goalMl = 2500) =>
    request(`/nutrition/water/summary/${userId}/daily?date=${date}&goal_ml=${goalMl}`),

  getWaterLogCount: (userId) =>
    request(`/nutrition/water/stats/${userId}/count`),
};

// =============================================================================
// Symptoms API
// =============================================================================

export const SymptomsAPI = {
  reportSymptom: (userId, { symptom_name, severity, description, context }) =>
    request(`/symptoms/${userId}`, {
      method: 'POST',
      body: { symptom_name, severity, description, context },
    }),

  getSymptom: (userId, stoneId) =>
    request(`/symptoms/${userId}/${stoneId}`),

  getRecentSymptoms: (userId, { days = 7, limit = 50 } = {}) =>
    request(`/symptoms/${userId}?days=${days}&limit=${limit}`),

  getSymptomsByDateRange: (userId, startDate, endDate, symptomName = null) => {
    let url = `/symptoms/${userId}/range?start_date=${startDate}&end_date=${endDate}`;
    if (symptomName) url += `&symptom_name=${symptomName}`;
    return request(url);
  },

  updateSymptom: (userId, stoneId, updates) =>
    request(`/symptoms/${userId}/${stoneId}`, {
      method: 'PATCH',
      body: updates,
    }),

  deleteSymptom: (userId, stoneId) =>
    request(`/symptoms/${userId}/${stoneId}`, { method: 'DELETE' }),

  // Analysis
  getAllFrequencies: (userId, days = 30) =>
    request(`/symptoms/${userId}/analysis/all?days=${days}`),

  getSymptomAnalysis: (userId, symptomName, days = 30) =>
    request(`/symptoms/${userId}/analysis/${symptomName}?days=${days}`),
};

// =============================================================================
// Insights API
// =============================================================================

export const InsightsAPI = {
  generateInsights: (userId, {
    trimester,
    age,
    height_cm,
    weight_kg,
    activity_factor = 1.4,
    forecast_days = 7,
    context_days = 30,
    force_regenerate = false,
  }) =>
    request(`/insights/${userId}`, {
      method: 'POST',
      body: {
        trimester,
        age,
        height_cm,
        weight_kg,
        activity_factor,
        forecast_days,
        context_days,
        force_regenerate,
      },
    }),

  getLatestInsights: (userId) =>
    request(`/insights/${userId}/latest`),

  getInsightsHistory: (userId, limit = 10) =>
    request(`/insights/${userId}/history?limit=${limit}`),

  deleteAllInsights: (userId) =>
    request(`/insights/${userId}`, { method: 'DELETE' }),
};

// =============================================================================
// Chat API
// =============================================================================

export const ChatAPI = {
  sendMessage: (userId, { message, provider = 'groq', model = null, include_sources = true, max_history = 10 }) =>
    request(`/chat/message?user_id=${userId}`, {
      method: 'POST',
      body: { message, provider, model, include_sources, max_history },
    }),

  streamMessage: (userId, { message, provider = 'groq', model = null }) => {
    // Returns EventSource for SSE streaming
    const url = `${BASE_URL}/chat/stream?user_id=${userId}`;
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, provider, model }),
    });
  },

  getHistory: (userId, limit = 20) =>
    request(`/chat/history/${userId}?limit=${limit}`),

  clearHistory: (userId) =>
    request(`/chat/history/${userId}`, { method: 'DELETE' }),

  getProviders: () =>
    request('/chat/providers'),
};

// =============================================================================
// Memory API
// =============================================================================

export const MemoryAPI = {
  // SRS
  queryKnowledgeBase: (userId, { query, top_k_stores = 2, top_k_chunks = 5, include_context = true }) =>
    request(`/memory/query?user_id=${userId}`, {
      method: 'POST',
      body: { query, top_k_stores, top_k_chunks, include_context },
    }),

  listStores: () =>
    request('/memory/stores'),

  getLoadedStores: () =>
    request('/memory/stores/loaded'),

  explainRouting: (query) =>
    request(`/memory/route?query=${encodeURIComponent(query)}`),

  // Symptoms (via memory)
  logSymptom: (userId, { symptom_name, severity, description, notes }) =>
    request(`/memory/symptoms?user_id=${userId}`, {
      method: 'POST',
      body: { symptom_name, severity, description, notes },
    }),

  getSymptoms: (userId, days = 7) =>
    request(`/memory/symptoms/${userId}?days=${days}`),

  getSymptomTimeline: (userId, days = 30) =>
    request(`/memory/symptoms/${userId}/timeline?days=${days}`),

  getSymptomPatterns: (userId, days = 60) =>
    request(`/memory/symptoms/${userId}/patterns?days=${days}`),

  getSymptomFrequencies: (userId, days = 30) =>
    request(`/memory/symptoms/${userId}/frequencies?days=${days}`),

  deleteSymptom: (userId, stoneId) =>
    request(`/memory/symptoms/${userId}/${stoneId}`, { method: 'DELETE' }),

  // Doctor Summary
  getDoctorSummary: (userId, { days = 30, format = 'json' } = {}) =>
    request(`/memory/doctor-summary/${userId}?days=${days}&format=${format}`),

  // Context Pyramid
  getContextPyramid: (userId, { query = null, max_tokens = 2000, layers = null }) =>
    request(`/memory/context/${userId}`, {
      method: 'POST',
      body: { query, max_tokens, layers },
    }),

  getContextString: (userId, query = '', maxTokens = 2000) =>
    request(`/memory/context/${userId}/string?query=${encodeURIComponent(query)}&max_tokens=${maxTokens}`),

  getContextLayer: (userId, layerId) =>
    request(`/memory/context/${userId}/layer/${layerId}`),
};

// =============================================================================
// Parser API
// =============================================================================

export const ParserAPI = {
  extractEntities: ({ text, confidence_threshold = 0.7, entity_types = null }) =>
    request('/parser/extract-entities', {
      method: 'POST',
      body: { text, confidence_threshold, entity_types },
    }),

  generateInsights: ({ text, entities = null }) =>
    request('/parser/insights', {
      method: 'POST',
      body: { text, entities },
    }),

  analyzeReport: (text) =>
    request('/parser/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `text=${encodeURIComponent(text)}`,
    }),

  // PDF uploads require FormData
  extractPdfText: async (file, method = 'pdfplumber') => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${BASE_URL}/parser/pdf/extract-text?method=${method}`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) throw new Error('Failed to extract PDF text');
    return response.json();
  },

  extractPdfTables: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${BASE_URL}/parser/pdf/extract-tables`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) throw new Error('Failed to extract PDF tables');
    return response.json();
  },

  extractPdfAll: async (file, textMethod = 'pdfplumber') => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${BASE_URL}/parser/pdf/extract-all?text_method=${textMethod}`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) throw new Error('Failed to extract PDF content');
    return response.json();
  },
};

// =============================================================================
// User API
// =============================================================================

export const UserAPI = {
  initOnboarding: ({ user, maternal, consent, baby = null }) =>
    request('/user/onboarding/init', {
      method: 'POST',
      body: { user, maternal, consent, baby },
    }),

  getOnboardingStatus: (userId) =>
    request(`/user/onboarding/status/${userId}`),

  updateOnboardingStep: (userId, step, value) =>
    request(`/user/onboarding/step/${userId}?step=${step}&value=${value}`, {
      method: 'PATCH',
    }),

  completeOnboarding: (userId) =>
    request(`/user/onboarding/complete/${userId}`, { method: 'POST' }),
};

// =============================================================================
// Hospital Finder API
// =============================================================================

export const HospitalAPI = {
  findNearbyHospitals: ({ lat, lng, radius = 5000, limit = 5 }) =>
    request('/nearby-hospitals', {
      method: 'POST',
      body: { lat, lng, radius, limit },
    }),
};

// =============================================================================
// Default Export - All APIs
// =============================================================================

export default {
  Nutrition: NutritionAPI,
  Water: WaterAPI,
  Symptoms: SymptomsAPI,
  Insights: InsightsAPI,
  Chat: ChatAPI,
  Memory: MemoryAPI,
  Parser: ParserAPI,
  User: UserAPI,
  Hospital: HospitalAPI,
  setBaseUrl: (url) => {
    // Allow runtime configuration
    Object.defineProperty(globalThis, 'CARENEST_API_URL', { value: url, writable: true });
  },
};
