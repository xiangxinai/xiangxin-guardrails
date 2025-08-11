FROM node:18-alpine AS builder

WORKDIR /app

# 复制package文件
COPY frontend/package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY frontend/ .

# 构建参数：允许设置 Vite base 前缀
ARG VITE_BASE=/platform/
ENV VITE_BASE=${VITE_BASE}

# 构建项目（将 VITE_BASE 注入）
RUN VITE_BASE=${VITE_BASE} npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建产物到platform目录
COPY --from=builder /app/dist /usr/share/nginx/html/platform

# 复制landing页面
COPY landing /usr/share/nginx/html/landing

# 复制nginx配置
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]