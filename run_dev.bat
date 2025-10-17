@echo off
REM run_dev.bat — start Node API in new window, wait until healthy, then start Flutter app

:: Config
set NODE_CMD=node
set NODE_SCRIPT=%~dp0app.js
set API_URL=http://127.0.0.1:5057/api/test
set FLUTTER_DIR=%~dp0flutter_app
set TIMEOUT_SECONDS=30

:StartNode
echo Starting Node API in new window...
start "CAP API" cmd /k "cd /d "%~dp0" && %NODE_CMD% "%NODE_SCRIPT%""
echo Waiting for API to become healthy (up to %TIMEOUT_SECONDS% seconds)...
set /a elapsed=0
:PollLoop
  rem use PowerShell Invoke-WebRequest for a simple health check
  powershell -Command "try { $r = Invoke-WebRequest -Uri '%API_URL%' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { Write-Output 'OK'; exit 0 } else { exit 1 } } catch { exit 1 }"
  if %ERRORLEVEL%==0 (
    echo API is healthy.
    goto RunFlutter
  )
  if %elapsed% GEQ %TIMEOUT_SECONDS% (
    echo Timed out waiting for API after %TIMEOUT_SECONDS% seconds.
    echo You can start the Flutter app manually once the API is running.
    goto End
  )
  timeout /t 1 >nul
  set /a elapsed+=1
  goto PollLoop

:RunFlutter
echo Running flutter pub get and launching desktop app...
if not exist "%FLUTTER_DIR%" (
  echo Flutter project folder not found: %FLUTTER_DIR%
  goto End
)
pushd "%FLUTTER_DIR%"
echo Running: flutter pub get
flutter pub get
echo Launching: flutter run -d windows
flutter run -d windows
popd
:End
echo Done. Press any key to exit.
pause > nul
exit /b 0
