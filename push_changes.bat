@echo off
set "msg="
set /p msg="Enter commit message: "
if "%msg%"=="" set msg=Automatic update of files

git add .
git commit -m "%msg%"
git push origin main

echo Done!
pause
