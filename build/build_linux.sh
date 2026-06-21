#!/usr/bin/env bash
# Linux 빌드 스크립트 → memo-app 바이너리 + install_memo_app.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> [1/3] 의존성 설치 (uv sync)..."
uv sync --group dev

echo "==> [2/3] PyInstaller 빌드..."
uv run pyinstaller \
    --onefile \
    --name "memo-app" \
    --hidden-import "pynput.keyboard._xorg" \
    --hidden-import "pynput.mouse._xorg" \
    --hidden-import "pynput.keyboard._udev" \
    --hidden-import "pynput.mouse._udev" \
    src/memo_app/main.py

echo "==> [3/3] 인스톨러 스크립트 생성..."
INSTALLER="dist/install_memo_app.sh"

cat > "$INSTALLER" << 'INSTALL_EOF'
#!/usr/bin/env bash
# MemoApp 설치 스크립트
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BINARY="$SCRIPT_DIR/memo-app"

if [ ! -f "$BINARY" ]; then
    echo "오류: memo-app 바이너리를 이 스크립트와 같은 폴더에 넣어주세요."
    exit 1
fi

BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"
mkdir -p "$BIN_DIR" "$APP_DIR"

cp "$BINARY" "$BIN_DIR/memo-app"
chmod +x "$BIN_DIR/memo-app"

cat > "$APP_DIR/memo-app.desktop" << DESKTOP_EOF
[Desktop Entry]
Type=Application
Name=MemoApp
Comment=Ctrl + 좌측 상단 코너로 열리는 오버레이 할 일 목록
Exec=$BIN_DIR/memo-app
Icon=accessories-text-editor
Terminal=false
Categories=Utility;
StartupNotify=false
DESKTOP_EOF

update-desktop-database "$APP_DIR" 2>/dev/null || true

echo "✅ 설치 완료!"
echo "   실행 파일 : $BIN_DIR/memo-app"
echo "   바탕화면 : $APP_DIR/memo-app.desktop"
echo ""

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "⚠️  PATH에 ~/.local/bin이 없습니다. 다음을 ~/.bashrc 또는 ~/.zshrc에 추가하세요:"
    echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

echo "참고: X11 환경에서 pynput 전역 키보드 후킹에는"
echo "      추가 권한이 필요하지 않습니다."
echo "      Wayland 환경에서는 제한이 있을 수 있습니다."
INSTALL_EOF

chmod +x "$INSTALLER"

echo ""
echo "✅ 완료!"
echo "   바이너리    : dist/memo-app"
echo "   인스톨러   : dist/install_memo_app.sh"
echo ""
echo "배포 시 dist/memo-app 과 dist/install_memo_app.sh 를 함께 제공하세요."
echo "설치: bash dist/install_memo_app.sh"
