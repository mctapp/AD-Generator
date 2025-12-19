#!/bin/bash
# build.sh - macOS 앱 빌드

cd "$(dirname "$0")"

echo "🍅 TOMATO AD Voice Generator 빌드 시작..."
echo ""

# 가상환경 활성화
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 이전 빌드 삭제
rm -rf dist build/*.app

# PyInstaller 빌드
echo "📦 PyInstaller로 빌드 중..."
pyinstaller build/TomatoAD.spec --noconfirm

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 빌드 성공!"
    echo ""
    echo "📁 앱 위치: dist/TOMATO AD Voice Generator.app"
    echo ""
    echo "실행 방법:"
    echo "  open 'dist/TOMATO AD Voice Generator.app'"
    echo ""
    echo "Applications 폴더로 복사:"
    echo "  cp -r 'dist/TOMATO AD Voice Generator.app' /Applications/"
else
    echo ""
    echo "❌ 빌드 실패"
    exit 1
fi
