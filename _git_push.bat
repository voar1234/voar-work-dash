@echo off
chcp 65001 > nul
cd /d "%~dp0"

REM ────────────────────────────────────────────────
REM  외부 호스팅 자동 push
REM  - 변경된 파일이 있을 때만 commit + push
REM  - 매 10분마다 _갱신.bat 에서 호출됨
REM ────────────────────────────────────────────────

REM index.html 을 항상 최신 내업무_대시보드.html 로 갱신
copy /Y "내업무_대시보드.html" "index.html" > nul 2>&1

git add -A > nul 2>&1
git diff --cached --quiet
if errorlevel 1 (
    REM 변경 있음 — commit + push
    git commit -m "auto: %DATE% %TIME%" >> "%~dp0_git_log.txt" 2>&1
    git push origin main >> "%~dp0_git_log.txt" 2>&1
    echo [%DATE% %TIME%] push 완료 >> "%~dp0_git_log.txt"
) else (
    echo [%DATE% %TIME%] 변경 없음 skip >> "%~dp0_git_log.txt"
)
exit /b 0
