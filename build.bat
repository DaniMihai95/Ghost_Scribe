@echo off
echo.
echo  ======================================================
echo            GHOST SCRIBE - Build Script            
echo  ======================================================
echo.

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
) else (
    echo [WARN] No .venv found, using system Python
)

REM Install dependencies
echo.
echo [1/5] Installing dependencies...
pip install openvino-genai keyboard pyperclip pystray pillow pyinstaller -q

REM Create icon from image.png
echo [2/5] Creating icon from image.png...
if exist "image.png" (
    python convert_icon.py
) else (
    echo [WARN] image.png not found, using existing icon
)

REM Kill any running GhostScribe process
echo [3/5] Cleaning old build files...
taskkill /F /IM GhostScribe.exe >nul 2>&1
timeout /t 2 /nobreak >nul
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

REM Build with PyInstaller
echo [4/5] Building executable...
pyinstaller --clean --noconfirm GhostScribe.spec

REM Copy required files
echo [5/5] Copying additional files...

REM Copy model folder
if not exist "dist\GhostScribe\tinyllama-model" mkdir "dist\GhostScribe\tinyllama-model"
xcopy /E /Y /Q "tinyllama-model\*.*" "dist\GhostScribe\tinyllama-model\" > nul

REM Copy image for tray icon
if exist "image.png" copy /Y "image.png" "dist\GhostScribe\" > nul

REM Copy icon file
if exist "ghost_scribe.ico" copy /Y "ghost_scribe.ico" "dist\GhostScribe\" > nul

echo.
echo  ======================================================
echo               BUILD COMPLETE!                     
echo  ======================================================
echo   Output: dist\GhostScribe\GhostScribe.exe        
echo.
echo   Features:                                       
echo   - Runs in background (no console window)        
echo   - System tray icon                              
echo   - Hotkey: Ctrl+Space                            
echo  ======================================================
echo.
echo To distribute: Zip the entire 'dist\GhostScribe' folder
echo.
pause
