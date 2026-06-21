#!/usr/bin/env bash
# GitHub Release 생성 스크립트 (macOS/Linux)
# 필요: gh CLI (https://cli.github.com) 인증 완료 상태
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> 버전 확인 중..."
VERSION=$(uv run python -c "import tomllib; d=tomllib.loads(open('pyproject.toml','rb').read().decode()); print(d['project']['version'])")
TAG="v${VERSION}"
echo "    버전: ${TAG}"

EXE="WorkingMemo-v${VERSION}-macos.tar.gz"

if [ ! -f "${EXE}" ]; then
    echo "[ERROR] ${EXE} 가 없습니다. 먼저 bash build/build_macos.sh 를 실행하세요."
    exit 1
fi

echo "==> gh 인증 확인..."
gh auth status

echo "==> git 태그 생성 및 푸시..."
git tag -a "${TAG}" -m "Release ${TAG}"
git push origin "${TAG}"

echo "==> GitHub Release 생성 및 업로드..."
gh release create "${TAG}" "${EXE}" \
    --title "WorkingMemo ${TAG}" \
    --notes "## WorkingMemo ${TAG}

### 변경 사항
- (릴리스 노트를 여기에 작성하세요)

### 설치
- **macOS**: WorkingMemo-v${VERSION}-macos.tar.gz 압축 해제 후 WorkingMemo.app 실행"

echo ""
echo "✅ GitHub Release ${TAG} 생성 완료!"
echo "   https://github.com/orugu/working-memo/releases/tag/${TAG}"
