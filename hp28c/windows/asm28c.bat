@echo off
REM ---------------------------------------------------
REM asm28.bat — assemble with entry-point substitution
REM Usage: asm28.bat source.a
REM Assumes entries28c.a and replace_entries.py live in the same directory
REM ---------------------------------------------------

REM 1. Check that a source file was provided
if "%~1"=="" (
  echo Usage: %~nx0 source.a
  exit /b 1
)

set "source=%~1"
set "base=%~n1"
set "entries=entries28c.a"

REM 2. Verify that source.a exists
if not exist "%source%" (
  echo Error: File "%source%" not found.
  exit /b 1
)

REM 3. Verify that entries28c.a exists
if not exist "%entries%" (
  echo Error: Entries file "%entries%" not found.
  exit /b 1
)

REM 4. Create temporary filenames based on the source’s basename
set "tempA=%base%.tmp.a"
set "tempO=%base%.tmp.o"
set "finalO=%base%.o"

REM 5. Preprocess source → tempA (replace =NAME with #HEX)
python rpl28a.py "%source%" "%entries%" "%tempA%"
if errorlevel 1 (
  echo.
  echo *** Preprocessing failed.
  exit /b 1
)

REM 6. Assemble tempA → tempA.o (SASM’s default output)
sasm -h "%tempA%"
if errorlevel 1 (
  echo.
  echo *** SASM reported errors.
  exit /b 1
)

REM 7. Rename the generated .o to tempO (if SASM produced tempA.o)
if exist "%tempA:.a=.o%" (
  move /Y "%tempA:.a=.o%" "%tempO%" >nul
) else (
  echo Error: Expected "%tempA:.a=.o%" not found.
  exit /b 1
)

REM 8. Insert a space every 5 chars into finalO
powershell -NoProfile -Command ^
  "(Get-Content '%tempO%' -Raw) -replace '.{5}','$& ' | Set-Content '%finalO%'"
if errorlevel 1 (
  echo.
  echo *** Failed to post-process %tempO%.
  exit /b 1
)

REM 9. Display the tempO
echo.
echo --- Contents of %temp0% ---
type "%tempO%
echo.

REM 9. Display the spaced finalO
echo.
echo --- Contents of %finalO% ---
type "%finalO%"

echo.
echo *** Done. Output in "%finalO%".
exit /b 0
