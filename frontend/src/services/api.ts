import axios from "axios"

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
})

// Attach token automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token")
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auth
export const authApi = {
  register: (data: any) => api.post("/auth/register", data),
  login: (data: any) => api.post("/auth/login/json", data),
  me: () => api.get("/auth/me"),
}

// Tickets
export const ticketsApi = {
  list: (params?: any) => api.get("/tickets", { params }),
  get: (id: string) => api.get(`/tickets/${id}`),
  create: (data: any) => api.post("/tickets", data),
}

// Documents
export const documentsApi = {
  list: () => api.get("/documents"),
  upload: (formData: FormData) =>
    api.post("/documents/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  delete: (id: string) => api.delete(`/documents/${id}`),
}

// AI
export const aiApi = {
  processTicket: (ticketId: string) => api.post(`/ai/process-ticket/${ticketId}`),
}

// Approvals
export const approvalsApi = {
  action: (ticketId: string, responseId: string, data: any) =>
    api.post(`/approvals/${ticketId}/response/${responseId}`, data),
}

// Analytics
export const analyticsApi = {
  overview: () => api.get("/analytics/overview"),
}

export default api
