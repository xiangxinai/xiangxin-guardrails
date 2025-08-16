import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  // 优先使用构建期传入的环境变量，其次读取 .env 中的变量，最后回退到/platform/
  const base = process.env.VITE_BASE || env.VITE_BASE || '/platform/'

  return {
    plugins: [react()],
    base,
    server: {
      host: '0.0.0.0', // 允许从任何IP访问
      port: 3000,
      proxy: {
        // API代理到后端服务
        '/api': {
          target: 'http://localhost:5001',
          changeOrigin: true,
          secure: false
        },
        // 护栏检测代理到后端服务
        '/v1': {
          target: 'http://localhost:5000',
          changeOrigin: true,
          secure: false
        }
      }
    }
  }
})