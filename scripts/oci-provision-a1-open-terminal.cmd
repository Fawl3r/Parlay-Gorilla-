@echo off
rem Opens a NEW visible terminal window so you can watch the script run.
set "SCRIPTDIR=%~dp0"
for %%I in ("%~dp0..") do set "ROOTDIR=%%~fI"
start "OCI A1 Provision" cmd /k "cd /d ""%ROOTDIR%"" && ""%SCRIPTDIR%oci-provision-a1.cmd"""
