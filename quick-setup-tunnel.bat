@echo off
echo.
echo ========================================
echo Quick Tunnel Setup
echo ========================================
echo.
echo Enter your BACKEND tunnel URL from the "Backend Tunnel" window.
echo (It looks like: https://xxxx-xxxx-xxxx.trycloudflare.com)
echo.
set /p URL="Backend URL: "

if "%URL%"=="" (
    echo No URL entered. Exiting.
    pause
    exit /b 1
)

echo.
echo Updating frontend/.env.local...

REM Update .env.local
powershell -Command "$content = Get-Content 'frontend\.env.local' -ErrorAction SilentlyContinue; $content = $content | Where-Object { $_ -notmatch '^PG_BACKEND_URL=' -and $_ -notmatch '^NEXT_PUBLIC_API_URL=' -and $_ -notmatch '^# Backend API URL' }; while ($content.Count -gt 0 -and [string]::IsNullOrWhiteSpace($content[-1])) { $content = $content[0..($content.Count-2)] }; if ($content.Count -gt 0) { $content += '' }; $content += '# Backend API URL (Tunnel)'; $content += 'PG_BACKEND_URL=%URL%'; $content += 'NEXT_PUBLIC_API_URL=%URL%'; $content | Set-Content 'frontend\.env.local' -Encoding UTF8"

echo.
echo Done! Backend URL set to: %URL%
echo.
echo IMPORTANT: Restart the frontend server for changes to take effect.
echo.
pause



