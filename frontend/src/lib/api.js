import { API_BASE_URL } from './config'

const handleResponse = async (response) => {
  if (response.status === 204) {
    return null
  }
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const message = data?.detail || 'Request failed'
    throw new Error(message)
  }
  return data
}

const apiFetch = (path, options = {}) => {
  return fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  }).then(handleResponse)
}

export const api = {
  listIndexes: () => apiFetch('/indexes'),
  createIndex: (payload) => apiFetch('/indexes', { method: 'POST', body: JSON.stringify(payload) }),
  updateIndex: (name, payload) => apiFetch(`/indexes/${encodeURIComponent(name)}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteIndex: (name) => apiFetch(`/indexes/${encodeURIComponent(name)}`, { method: 'DELETE' }),
  listDocuments: (name) => apiFetch(`/indexes/${encodeURIComponent(name)}/documents`),
  createDocument: (name, payload) => apiFetch(`/indexes/${encodeURIComponent(name)}/documents`, { method: 'POST', body: JSON.stringify(payload) }),
  updateDocument: (name, docId, payload) =>
    apiFetch(`/indexes/${encodeURIComponent(name)}/documents/${docId}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteDocument: (name, docId) =>
    apiFetch(`/indexes/${encodeURIComponent(name)}/documents/${docId}`, { method: 'DELETE' }),
  search: (payload) => apiFetch('/search', { method: 'POST', body: JSON.stringify(payload) }),
}
