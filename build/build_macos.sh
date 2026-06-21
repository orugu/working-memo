#!/usr/bin/env bash
# macOS 빌드 스크립트 → MemoApp.app + MemoApp.dmg
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> [1/3] 의존성 설치 (uv sync)..."
uv sync --group dev

echo "==> [2/3] PyInstaller 빌드..."
uv run pyinstaller \
    --onefile \
    --windowed \
    --name "MemoApp" \
    --hidden-import "pynput.keyboard._darwin" \
    --hidden-import "pynput.mouse._darwin" \
    --hidden-import "pkg_resources.py2_warn" \
    --collect-all "PySide6" \
    src/memo_app/main.py

echo "==> [3/3] .dmg 생성..."
if command -v hdiutil &>/dev/null; then
    rm -f dist/MemoApp.dmg
    hdiutil create \
        -volname "MemoApp" \
        -srcfolder "dist/MemoApp.app" \
        -ov \
        -format UDZO \
        "dist/MemoApp.dmg"
    echo ""
    echo "✅ 완료!"
    echo "   앱 번들 : dist/MemoApp.app"
    echo "   DMG     : dist/MemoApp.dmg"
else
    echo "⚠️  hdiutil 없음 — .dmg 생성 건너뜀"
    echo "✅ 완료!"
    echo "   앱 번들 : dist/MemoApp.app"
fi

echo ""
echo "▶ 처음 실행 시 macOS 보안 설정:"
echo "  시스템 환경설정 → 개인 정보 보호 및 보안 → 손쉬운 사용"
echo "  에서 MemoApp 에 권한을 부여해야 합니다 (키보드/마우스 감시)."
