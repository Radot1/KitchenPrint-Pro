@echo off
REM Batch file to start the Sushaki Kitchen Order System Flask app and open the browser.

REM Set the title of this command prompt window
title Sushaki System Launcher

echo Starting Sushaki Kitchen Order System...
echo.

REM Change directory to the location of this batch file.
REM This ensures that app.py is found and can correctly locate sushaki.html and the /data folder.
cd /d "%~dp0"

echo Current working directory: %cd%
echo.

REM Check if app.py exists in the current directory
IF NOT EXIST "app.py" (
    echo ERROR: app.py not found in the current directory:
    echo %cd%
    echo Please ensure this batch file is in the same directory as app.py.
    pause
    exit /b 1
)

REM Start the Python Flask server in a new command prompt window.
REM The new window will remain open (cmd /k) so you can see server logs and errors.
echo Starting Flask server (app.py)...
start "Sushaki Server" cmd /k "python app.py"

REM Give the server a moment to start up.
echo Waiting for the server to initialize (5 seconds)...
timeout /t 5 /nobreak > nul

REM Open the sushaki.html page in the default web browser.
REM The Flask app serves sushaki.html at the root (/).
echo Opening the application in your browser at http://localhost:5000/
start http://localhost:5000/

echo.
echo The Sushaki Kitchen Order System server should be running in a separate window
echo titled "Sushaki Server".
echo The application should now be open in your web browser.
echo.
echo You can close this launcher window. To stop the server, close the "Sushaki Server" window.

REM Optional: pause before this window closes, or just let it exit.
REM pause
exit /b 0
