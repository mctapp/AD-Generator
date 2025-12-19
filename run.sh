#!/bin/bash
# run.sh - 개발 모드로 앱 실행

cd "$(dirname "$0")"

# 가상환경 활성화
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 앱 실행
python3 src/main.py
