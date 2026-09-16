const TOKEN_KEY = 'token'
const MEMBER_KEY = 'me'

export function authHeaders() {
  const token = localStorage.getItem(TOKEN_KEY)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export function apiFetch(path, options = {}) {
  return fetch(path, {
    ...options,
    headers: { ...authHeaders(), ...(options.headers || {}) },
    credentials: 'include',
  })
}

export function isLogged() {
  return Boolean(localStorage.getItem(TOKEN_KEY))
}

export function setSession(token, member) {
  if (token && member) {
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(MEMBER_KEY, JSON.stringify(member))
    return
  }
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(MEMBER_KEY)
}

export function setMe(member) {
  if (member) localStorage.setItem(MEMBER_KEY, JSON.stringify(member))
  else setSession(null, null)
}

export function getMe() {
  try {
    return JSON.parse(localStorage.getItem(MEMBER_KEY) || 'null')
  } catch {
    return null
  }
}

export async function logout() {
  try {
    await apiFetch('/api/logout', { method: 'POST' })
  } finally {
    // La déconnexion locale doit fonctionner même si l'API est indisponible.
    setSession(null, null)
  }
}
