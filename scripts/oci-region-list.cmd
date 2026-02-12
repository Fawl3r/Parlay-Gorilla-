@echo off
set "PYTHON=C:\Users\Fawl3\AppData\Local\Programs\Python\Python311\python.exe"
set "OCIDIR=C:\Users\Fawl3\AppData\Local\Programs\Python\Python311\Scripts"
set "OCI=%OCIDIR%\oci.exe"

if not exist "%OCI%" (
  echo Installing OCI CLI...
  "%PYTHON%" -m pip install oci-cli -q
)

if exist "%OCI%" goto run
echo OCI CLI not found.
pause
exit /b 1

:run
"%OCI%" iam region list --output table
