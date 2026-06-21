@echo off
chcp 65001 >nul
:: GitHub Release 생성 스크립트 (Windows)
:: 필요: gh CLI (https://cli.github.com) 인증 완료 상태
cd /d "%~dp0.."

echo =^> 버전 확인 중...
for /f "tokens=*" %%v in ('".venv\Scripts\python.exe" -c "import tomllib; d=tomllib.loads(open(\"pyproject.toml\",\"rb\").read().decode()); print(d[\"project\"][\"version\"])"') do set VERSION=%%v
if "%VERSION%"=="" (
    echo [ERROR] 버전을 읽지 못했습니다.
    exit /b 1
)

set TAG=v%VERSION%
set EXE=dist\WorkingMemo-v%VERSION%-windows.exe

echo    버전: %TAG%

if not exist "%EXE%" (
    echo [ERROR] %EXE% 가 없습니다. 먼저 build\build_windows.bat 를 실행하세요.
    exit /b 1
)

echo =^> gh 인증 확인...
gh auth status >nul 2>&1
if errorlevel 1 (
    echo [ERROR] gh 가 인증되지 않았습니다. 먼저 실행: gh auth login
    exit /b 1
)

echo =^> git 태그 생성 및 푸시...
git tag -a "%TAG%" -m "Release %TAG%"
git push origin "%TAG%"

echo =^> GitHub Release 생성 및 업로드...
gh release create "%TAG%" "%EXE%" ^
    --title "WorkingMemo %TAG%" ^
    --notes "## WorkingMemo %TAG%

### 변경 사항
- (릴리스 노트를 여기에 작성하세요)

### 설치
- **Windows**: WorkingMemo-v%VERSION%-windows.exe 를 다운로드하여 실행"

if errorlevel 1 (
    echo [ERROR] Release 생성 실패.
    exit /b 1
)

echo.
echo [OK] GitHub Release %TAG% 생성 완료!
echo    https://github.com/orugu/working-memo/releases/tag/%TAG%
