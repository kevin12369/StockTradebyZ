/**
 * Axios API 客户端配置
 */

import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosError, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

// API 响应类型
interface ApiErrorResponse {
  code: number
  message: string
  data?: unknown
}

// API 基础配置
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

// 创建 Axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 14400000, // 14400秒（4小时）超时，个人本地项目不需要严格限制
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加 token 等认证信息
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // 统一处理响应数据
    const { data } = response

    // 如果响应包含 code 字段，根据 code 判断
    if (data && typeof data === 'object' && 'code' in data) {
      if (data.code === 200) {
        return data.data
      } else {
        // 业务错误
        const errorMessage = (data as ApiErrorResponse).message || '请求失败'
        ElMessage.error(errorMessage)
        return Promise.reject(new Error(errorMessage))
      }
    }

    return response.data
  },
  (error: AxiosError) => {
    // 统一错误处理
    let message = '请求失败'

    if (error.response) {
      // 服务器返回错误状态码
      const { status, data } = error.response as AxiosResponse<ApiErrorResponse>

      switch (status) {
        case 400:
          message = data?.message || '请求参数错误'
          break
        case 404:
          message = '请求的资源不存在'
          break
        case 500:
          message = '服务器内部错误'
          break
        default:
          message = data?.message || `请求失败 (${status})`
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      message = '网络连接失败，请检查网络'
    } else {
      // 其他错误
      message = error.message || '请求失败'
    }

    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// 封装常用请求方法
export const request = {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return apiClient.get(url, config)
  },

  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return apiClient.post(url, data, config)
  },

  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return apiClient.put(url, data, config)
  },

  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return apiClient.delete(url, config)
  },
}

export default apiClient
