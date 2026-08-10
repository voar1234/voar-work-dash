@echo off
chcp 65001 > nul
cd /d "%~dp0"

REM ------------------------------------------------
REM  Voar work dash - GitHub Pages auto push
REM  - CRLF encoding (fixed 2026-08-10)
REM  - _??.bat ?? ??
REM ------------------------------------------------

copy /Y "???_????.html" "index.html" > nul 2>&1

git add -A > nul 2>&1
git diff --cached --quiet
if errorlevel 1 (
    git commit -m "auto: %DATE% %TIME%" >> "%~dp0_git_log.txt" 2>&1
    git push origin main >> "%~dp0_git_log.txt" 2>&1
    echo [%DATE% %TIME%] push done >> "%~dp0_git_log.txt"
) else (
    echo [%DATE% %TIME%] no changes skip >> "%~dp0_git_log.txt"
)
exit /b 0