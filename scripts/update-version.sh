#!/bin/bash

# 版本更新脚本 - 基于环境变量和 VERSION 文件
# 使用方式：
#   方式1：./scripts/update-version.sh 1.3.0
#   方式2：手动编辑 VERSION 文件后运行 ./scripts/update-version.sh

set -e

# 项目根目录
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION_FILE="$ROOT_DIR/VERSION"

# 获取版本号
if [ $# -eq 1 ]; then
    # 从命令行参数获取版本号
    VERSION="$1"
    # 移除 v 前缀（如果存在）
    VERSION=${VERSION#v}
    echo "使用命令行参数版本: $VERSION"
    
    # 更新 VERSION 文件
    echo "$VERSION" > "$VERSION_FILE"
    echo "✓ 已更新 VERSION 文件"
elif [ -f "$VERSION_FILE" ]; then
    # 从 VERSION 文件读取
    VERSION=$(cat "$VERSION_FILE" | tr -d '\n\r')
    echo "从 VERSION 文件读取版本: $VERSION"
else
    echo "❌ 错误: 请提供版本号参数或创建 VERSION 文件"
    echo "使用方式："
    echo "  ./scripts/update-version.sh 1.3.0"
    echo "  或者先创建/编辑 VERSION 文件，然后运行 ./scripts/update-version.sh"
    exit 1
fi

echo "正在更新版本号到: $VERSION"

# 1. 更新前端 package.json 中的版本号
PACKAGE_JSON="$ROOT_DIR/frontend/package.json"
if [ -f "$PACKAGE_JSON" ]; then
    echo "更新前端 package.json 版本..."
    sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$VERSION\"/" "$PACKAGE_JSON"
    echo "✓ 已更新 frontend/package.json"
else
    echo "⚠ 警告: 未找到 frontend/package.json"
fi

# 2. 后端配置现在通过 VERSION 文件动态读取，无需修改
echo "✓ 后端版本将自动从 VERSION 文件读取"

# 3. 前端版本现在通过 API 动态获取，无需修改硬编码
echo "✓ 前端版本将通过 API 自动获取"

echo ""
echo "🎉 版本更新完成！"
echo "当前版本: $VERSION"
echo ""
echo "更新的文件："
echo "  - VERSION (主版本文件)"
echo "  - frontend/package.json"
echo ""
echo "版本号读取方式："
echo "  - 后端: VERSION 文件 → 环境变量 APP_VERSION → 默认值"
echo "  - 前端: 通过 API 从后端获取"
echo ""
echo "建议操作："
echo "1. 检查 VERSION 文件内容是否正确: cat VERSION"
echo "2. 重新构建和部署应用"
echo "3. 可选：设置环境变量 export APP_VERSION=$VERSION"
echo "4. 提交版本更新到 git："
echo "   git add ."
echo "   git commit -m \"chore: update version to $VERSION\""
echo ""
echo "与 Git Tag 同步（可选）："
echo "   git tag v$VERSION"
echo "   git push origin v$VERSION"