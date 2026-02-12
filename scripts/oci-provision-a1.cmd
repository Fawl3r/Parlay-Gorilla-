@echo off
title OCI A1 Provision - Parlay Gorilla
cd /d "%~dp0.."
set OCI_CLI_USE_PAGER=false
set "PATH=C:\Windows\System32\WindowsPowerShell\v1.0;C:\Users\Fawl3\AppData\Local\Programs\Python\Python311\Scripts;%PATH%"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0oci-provision-a1-instance.ps1"
pause
