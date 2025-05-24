@echo off
REM ---------------------------------------------------
REM asm28.bat — assemble a Saturn source, insert spaces,
REM              and display the .o file content
REM Usage: asm28 filename.a
REM ---------------------------------------------------

REM 1. Check arguments
if "%~1"=="" (
  echo Usage: %~nx0 filename.a
  exit /b 1
)

set "infile=%~1"
set "base=%~n1"
set "objfile=%base%.o"

REM 2. Assemble with SASM in host mode
sasm -h "%infile%"
if errorlevel 1 (
  echo.
  echo *** SASM reported errors.
  exit /b %errorlevel%
)

REM 3. Insert a space after every 5 characters in the .o file
powershell -NoProfile -Command ^
  "(Get-Content '%objfile%' -Raw) -replace '.{5}','$& ' | Set-Content '%objfile%'"
if errorlevel 1 (
  echo.
  echo *** Failed to post-process %objfile%.
  exit /b %errorlevel%
)

REM 4. Display the content of the spaced .o file
echo.
echo --- Contents of %objfile% ---
echo.
type "%objfile%"

echo.
echo *** Done. Assembled, spaced, and displayed: %objfile%
