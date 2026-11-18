import axios from 'axios'
import { ElMessage } from 'element-plus'

// 统一的 axios 实例：baseURL 为 /api（开发走 Vite 代理，生产走 Nginx 反代）
const request = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// 请求拦截：自动带上登录 token
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：token 失效时跳回登录页
request.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('role')
      if (window.location.pathname !== '/login') {
        ElMessage.error('登录已过期，请重新登录')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default request
