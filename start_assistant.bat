@echo off
title AI Personal Assistant
echo Starting AI Personal Assistant...
echo This window keeps your assistant running 24/7. Please don't close it.

:start
python main.py
if errorlevel 1 goto error
goto start

:error
echo Error occurred! Restarting in 5 seconds...
timeout /t 5
goto start 