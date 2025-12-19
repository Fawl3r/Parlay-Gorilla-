@echo off
echo ========================================
echo Fixing Next.js 16.1 Dependencies
echo ========================================
echo.
echo This will:
echo   1. Remove node_modules
echo   2. Remove .next cache
echo   3. Clear npm cache
echo   4. Reinstall all dependencies
echo.
pause

cd /d "%~dp0"

echo [1/4] Removing node_modules...
if exist node_modules (
    rmdir /s /q node_modules
    echo   Done.
) else (
    echo   node_modules not found, skipping.
)

echo.
echo [2/4] Removing .next cache...
if exist .next (
    rmdir /s /q .next
    echo   Done.
) else (
    echo   .next not found, skipping.
)

echo.
echo [3/4] Clearing npm cache...
call npm cache clean --force
echo   Done.

echo.
echo [4/4] Installing dependencies...
call npm install
if errorlevel 1 (
    echo.
    echo ERROR: npm install failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Dependencies Fixed!
echo ========================================
echo.
echo Next steps:
echo   1. Run: npm run dev
echo   2. Or use: ..\restart-all.bat
echo.
pause

