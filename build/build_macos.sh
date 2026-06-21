#!/usr/bin/env bash
# macOS 빌드 스크립트 → WorkingMemo.app + WorkingMemo.dmg + WorkingMemo-vX.Y.Z-macos.tar.gz
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> [0/4] 환경 확인..."
uv sync

# pyproject.toml 에서 버전 읽기
VERSION=$(uv run python -c "import tomllib; d=tomllib.loads(open('pyproject.toml','rb').read().decode()); print(d['project']['version'])")
echo "    버전: v${VERSION}"

TAR_NAME="WorkingMemo-v${VERSION}-macos.tar.gz"
DMG_NAME="WorkingMemo-v${VERSION}-macos.dmg"

echo "==> [1/4] 이전 빌드 정리..."
rm -rf dist/WorkingMemo.app dist/WorkingMemo "${TAR_NAME}" "${DMG_NAME}" build/pyi-work 2>/dev/null || true

echo "==> [2/4] PyInstaller 빌드..."
uv run pyinstaller --clean --workpath build/pyi-work WorkingMemo-macos.spec

echo "==> [3/4] auto-update용 tar.gz 생성 (WorkingMemo.app 번들)..."
(cd dist && tar -czf "../${TAR_NAME}" "WorkingMemo.app")
echo "    생성: ${TAR_NAME}"

echo "==> [4/4] .dmg 생성 (배포용)..."
if command -v hdiutil &>/dev/null; then
    hdiutil create \
        -volname "WorkingMemo" \
        -srcfolder "dist/WorkingMemo.app" \
        -ov -format UDZO \
        "dist/${DMG_NAME}"
    echo "    생성: dist/${DMG_NAME}"
else
    echo "    hdiutil 없음 — .dmg 생성 건너뜀"
fi

echo ""
echo "✅ 완료!"
echo "   앱 번들    : dist/WorkingMemo.app"
echo "   DMG (배포) : dist/${DMG_NAME}"
echo "   tar.gz     : ${TAR_NAME}  ← GitHub Release 에 업로드할 파일"
echo ""
echo "▶ 릴리스 업로드: bash build/release.sh"
echo ""
echo "▶ 처음 실행 시 macOS 보안 설정:"
echo "  시스템 설정 → 개인 정보 보호 및 보안 → 손쉬운 사용"
echo "  에서 WorkingMemo 에 권한을 부여해야 합니다."
