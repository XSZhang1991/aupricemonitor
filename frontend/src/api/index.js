import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

export const getLatest = () => api.get('/market/latest')

export const getKline = (interval, start, end) =>
  api.get('/market/kline', { params: { interval, start, end } })

export const getIndicators = (start, end) =>
  api.get('/market/indicators', { params: { start, end } })

export const fetchHistory = () => api.post('/market/fetch_history')

export const getStatus = () => api.get('/system/status')
