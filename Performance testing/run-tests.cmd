@echo off
setlocal EnableExtensions EnableDelayedExpansion
pushd "%~dp0" || exit /b 2
set "MODE=%~1"
set "SCRIPT="
if /i "%MODE%"=="smoke"   set "SCRIPT=smoke.js"
if /i "%MODE%"=="average" set "SCRIPT=average_load.js"
if /i "%MODE%"=="stress"  set "SCRIPT=stress.js"
if /i "%MODE%"=="soak"    set "SCRIPT=soak.js"
if /i "%MODE%"=="spike"   set "SCRIPT=spike.js"
if not defined SCRIPT (
  echo Usage: .\run-tests.cmd smoke^|average^|stress^|soak^|spike
  popd
  exit /b 2
)
where k6 >nul 2>&1
if errorlevel 1 (
  echo ERROR: k6 is not installed or not in PATH.
  popd
  exit /b 2
)
if not exist "common.js" (
  echo ERROR: common.js is missing.
  popd
  exit /b 2
)
if /i "%MODE%"=="stress" (
  echo Extended Stress: 1, 2, 3, 5, 7, 10 VUs; 50s each with 10s gaps.
  echo K6 may stop early at the first breached stage. 10 VUs is a CAP, not a guarantee.
  echo Only run this on the shared course server with approval for up to 10 VUs.
  set /p "ACK=Type YES to confirm permission and run: "
  if /i not "!ACK!"=="YES" (popd & exit /b 1)
) else if /i not "%MODE%"=="smoke" (
  echo The course server is shared. Coordinate the time with the group/instructor.
  set /p "ACK=Type YES to run %MODE%: "
  if /i not "!ACK!"=="YES" (popd & exit /b 1)
)
for /f %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "STAMP=%%T"
set "OUT=%~dp0results\%MODE%_!STAMP!"
mkdir "!OUT!" >nul 2>&1
if errorlevel 1 (popd & exit /b 2)
powershell -NoProfile -Command "(Get-Date).ToString('o')" > "!OUT!\run_time_local.txt"
powershell -NoProfile -Command "(Get-Date).ToUniversalTime().ToString('o')" > "!OUT!\run_time_utc.txt"
(
  echo Test: %MODE%
  echo Script: %SCRIPT%
  echo Target: http://157.85.102.236/shop
  echo Shared-server permission coordinated by operator before run
  echo p95 limit: 1000ms; HTTP error limit: 2 percent
) > "!OUT!\metadata.txt"
echo Running %MODE%. Output: !OUT!
powershell -NoProfile -Command "& k6 run --summary-export '!OUT!\summary.json' '.\%SCRIPT%' 2>&1 | Tee-Object -FilePath '!OUT!\console.txt'; exit $LASTEXITCODE"
set "CODE=!ERRORLEVEL!"
echo k6 exit code: !CODE! >> "!OUT!\metadata.txt"
if /i "%MODE%"=="stress" if exist "!OUT!\summary.json" (
  where py >nul 2>&1
  if not errorlevel 1 (
    py ".\analyze_stress.py" "!OUT!\summary.json"
  ) else (
    where python >nul 2>&1
    if not errorlevel 1 python ".\analyze_stress.py" "!OUT!\summary.json"
  )
)
echo Done. Check !OUT!\summary.json and console.txt
popd
exit /b !CODE!
