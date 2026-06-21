@echo off
chcp 65001 >nul
:: Windows build script -> WorkingMemo.exe
cd /d "%~dp0.."

echo =^> [0/2] Checking virtual environment...
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] .venv not found. Run: uv venv --python cpython-3.12 ^&^& uv sync
    exit /b 1
)

:: Verify it's not Anaconda Python (Anaconda breaks PySide6 DLL loading)
for /f "tokens=*" %%v in ('".venv\Scripts\python.exe" -c "import sys; print(\"anaconda\" in sys.version.lower())"') do set IS_ANACONDA=%%v
if "%IS_ANACONDA%"=="True" (
    echo [ERROR] .venv is using Anaconda Python which is incompatible with PySide6.
    echo         Recreate with: uv venv --python cpython-3.12 ^&^& uv sync
    exit /b 1
)

echo =^> [1/2] Cleaning previous output...
if exist "build\pyi-work" rmdir /s /q "build\pyi-work"
if exist "dist\WorkingMemo.exe" del /f /q "dist\WorkingMemo.exe"

echo =^> [2/2] Running PyInstaller...
".venv\Scripts\python.exe" -m PyInstaller --clean --workpath "build\pyi-work" WorkingMemo.spec
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. Check the messages above.
    exit /b 1
)

echo.
echo [OK] Build complete.
echo    Executable: dist\WorkingMemo.exe
echo.
echo Note: Windows Defender SmartScreen may warn on first launch.
echo       Click "More info" then "Run anyway".
