#!/bin/bash

# Climate Tech Funding Tracker 启动脚本

echo "🚀 启动 Climate Tech Funding Tracker..."

# 进入项目目录
cd "/Users/fuhuaruan/ClaudeCode/Funding Tracker_2.0"

# 激活虚拟环境
source venv/bin/activate

# 检查虚拟环境是否激活
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ 虚拟环境已激活: $(basename $VIRTUAL_ENV)"
else
    echo "❌ 虚拟环境激活失败"
    exit 1
fi

# 检查依赖
echo "📋 检查依赖..."
python -c "import streamlit; print('✅ Streamlit可用')" || {
    echo "❌ Streamlit不可用，请安装依赖"
    exit 1
}

# 检查配置
python -c "
from config import OPENAI_API_KEY
if OPENAI_API_KEY and OPENAI_API_KEY.startswith('sk-'):
    print('✅ OpenAI API配置正确')
else:
    print('⚠️  OpenAI API未配置，AI功能将被禁用')
"

echo ""
echo "🌐 启动Web应用..."
echo "📍 访问地址: http://localhost:8501"
echo "🛑 按 Ctrl+C 停止应用"
echo ""

# 启动应用
streamlit run app.py --server.port 8501