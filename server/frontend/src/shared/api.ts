type HttpError = Error & { status?: number }

function logoutAndGoLogin() {
  try {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  } catch {}
  if (location.pathname !== '/login') location.assign('/login')
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const token = localStorage.getItem('access_token')
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(url, { ...init, headers: { ...headers, ...(init?.headers as any) } })
  if (!res.ok) {
    const err: HttpError = new Error(`HTTP ${res.status}`)
    err.status = res.status
    if (res.status === 401) logoutAndGoLogin()
    throw err
  }
  const text = await res.text()
  return (text ? JSON.parse(text) : null) as T
}

export const api = {
  get: <T>(url: string) => request<T>(url),
  post: <T>(url: string, body?: any) => request<T>(url, { method: 'POST', body: JSON.stringify(body ?? {}) }),
  put:  <T>(url: string, body?: any) => request<T>(url, { method: 'PUT',  body: JSON.stringify(body ?? {}) }),
  del:  <T>(url: string) => request<T>(url, { method: 'DELETE' }),
}