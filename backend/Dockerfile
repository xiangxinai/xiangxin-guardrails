FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY . .

# 创建数据和日志目录
RUN mkdir -p /app/data /app/logs

# 暴露端口 - 支持所有服务
EXPOSE 5000 5001 5002

# 默认启动命令（会被docker-compose覆盖）
CMD ["python", "main.py"]