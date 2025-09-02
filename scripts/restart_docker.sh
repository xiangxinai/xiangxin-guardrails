#!/bin/bash

echo "🔄 重启象信护栏Docker服务"
echo "=============================="

# 停止并删除现有容器
echo "1. 停止现有服务..."
docker-compose down

# 清理旧的镜像（可选）
echo "2. 清理旧镜像..."
docker image rm xiangxin-guardrails-backend xiangxin-guardrails-frontend 2>/dev/null || true

# 重新构建并启动服务
echo "3. 重新构建并启动服务..."
docker-compose up --build -d

echo "4. 等待服务启动..."
sleep 10

echo "5. 检查服务状态..."
docker-compose ps

echo
echo "6. 检查服务健康状态..."
echo "数据库："
curl -f http://localhost:54321 2>/dev/null && echo "✅ 数据库端口可访问" || echo "❌ 数据库端口不可访问"

sleep 5

echo "管理服务："
curl -f http://localhost:5000/health 2>/dev/null && echo "✅ 管理服务正常" || echo "❌ 管理服务异常"

echo "检测服务："
curl -f http://localhost:5001/health 2>/dev/null && echo "✅ 检测服务正常" || echo "❌ 检测服务异常"

echo "代理服务："
curl -f http://localhost:5002/health 2>/dev/null && echo "✅ 代理服务正常" || echo "❌ 代理服务异常"

echo "前端服务："
curl -f http://localhost:3000 2>/dev/null && echo "✅ 前端服务正常" || echo "❌ 前端服务异常"

echo
echo "7. 显示最新日志..."
echo "--- 管理服务日志 (最近5行) ---"
docker logs --tail 5 xiangxin-guardrails-admin

echo
echo "--- 检测服务日志 (最近5行) ---"
docker logs --tail 5 xiangxin-guardrails-detection

echo
echo "--- 代理服务日志 (最近5行) ---"
docker logs --tail 5 xiangxin-guardrails-proxy

echo
echo "🎉 重启完成!"
echo "管理平台: http://localhost:3000/platform/"
echo "管理API: http://localhost:5000/api/v1/"
echo "检测API: http://localhost:5001/v1/guardrails"
echo "代理API: http://localhost:5002/v1/"
echo
echo "如果服务异常，请运行: ./debug_services.sh"