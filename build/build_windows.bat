@echo off
chcp 65001 >nul
:: Windows build script → WorkingMemo-v{version}-windows.exe
cd /d "%~dp0.."

echo =^> [0/3] 환경 확인 중...
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] .venv 없음. 먼저 실행: uv venv --python cpython-3.12 ^&^& uv sync
    exit /b 1
)

:: Anaconda Python 검사 (PySide6 DLL 호환 불가)
for /f "tokens=*" %%v in ('".venv\Scripts\python.exe" -c "import sys; print(\"anaconda\" in sys.version.lower())"') do set IS_ANACONDA=%%v
if "%IS_ANACONDA%"=="True" (
    echo [ERROR] .venv 가 Anaconda Python 을 사용 중입니다 ^(PySide6 와 DLL 충돌^).
    echo         재생성: uv venv --python cpython-3.12 ^&^& uv sync
    exit /b 1
)

:: pyproject.toml 에서 버전 읽기
for /f "tokens=*" %%v in ('".venv\Scripts\python.exe" -c "import tomllib; d=tomllib.load(open(\"pyproject.toml\",\"rb\")); print(d[\"project\"][\"version\"])"') do set VERSION=%%v
if "%VERSION%"=="" (
    echo [ERROR] pyproject.toml 에서 버전을 읽지 못했습니다.
    exit /b 1
)
echo    버전: v%VERSION%

set EXE_NAME=WorkingMemo-v%VERSION%-windows.exe

echo =^> [1/3] 이전 빌드 정리...
if exist "build\pyi-work" rmdir /s /q "build\pyi-work"
if exist "dist\%EXE_NAME%" del /f /q "dist\%EXE_NAME%"
if exist "dist\WorkingMemo.exe" del /f /q "dist\WorkingMemo.exe"

echo =^> [2/3] PyInstaller 빌드...
".venv\Scripts\python.exe" -m PyInstaller --clean --workpath "build\pyi-work" WorkingMemo.spec
if errorlevel 1 (
    echo [ERROR] 빌드 실패.
    exit /b 1
)

:: 버전 포함된 이름으로 복사
copy /y "dist\WorkingMemo.exe" "dist\%EXE_NAME%" >nul
echo    생성: dist\%EXE_NAME%

echo =^> [3/3] 완료!
echo.
echo    실행 파일: dist\%EXE_NAME%
echo    릴리스 업로드: build\release.bat
echo.
echo Note: Windows Defender SmartScreen 경고 시 "추가 정보" → "실행" 클릭.
