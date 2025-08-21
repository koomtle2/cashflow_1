@echo off
:: Universal CLAUDE.md Rules Enforcer (Batch Version)
:: 모든 워크스페이스에서 CLAUDE.md 파일 자동 감지

setlocal enabledelayedexpansion

:: 현재 디렉토리부터 상위로 CLAUDE.md 검색
set "currentPath=%cd%"
set "claudeFile="
set "searchDepth=0"
set "maxDepth=5"

:searchLoop
if !searchDepth! geq !maxDepth! goto :notFound
if exist "!currentPath!\CLAUDE.md" (
    set "claudeFile=!currentPath!\CLAUDE.md"
    goto :found
)

:: 상위 디렉토리로 이동
for %%i in ("!currentPath!") do set "parentPath=%%~dpi"
set "parentPath=!parentPath:~0,-1!"
if "!parentPath!"=="!currentPath!" goto :notFound
set "currentPath=!parentPath!"
set /a searchDepth+=1
goto :searchLoop

:found
echo.
echo ========================================================================================
echo                      🚨 CLAUDE.MD 규칙 발견! 자동 적용 중 🚨
echo ========================================================================================
echo.
echo 📁 프로젝트 경로: !currentPath!
echo 📄 규칙 파일: !claudeFile!
echo.
echo 🚨 핵심 규칙:
echo    - 기존 Script 폴더의 스크립트만 사용
echo    - 새로운 .py 파일 생성 절대 금지
echo    - 임시 분석용 파일 생성 금지
echo    - 사용자 명시적 승인 없는 새 파일 생성 완전 차단
echo.
echo ✅ Claude에게 반드시 명시할 명령어:
echo    "기존 Script 폴더 스크립트만 사용해"
echo    "새 파일 생성하지 마"
echo    "먼저 기존 것 확인해"
echo.

:: 기존 스크립트 폴더 확인
if exist "!currentPath!\Script" (
    echo 📁 기존 스크립트 폴더 발견: !currentPath!\Script
    dir /b "!currentPath!\Script\*.py" 2>nul | findstr /r ".*" >nul
    if !errorlevel! equ 0 (
        echo    기존 Python 스크립트:
        for /f %%f in ('dir /b "!currentPath!\Script\*.py" 2^>nul') do echo       - %%f
    )
    echo.
)

echo ========================================================================================
echo           위 규칙을 위반하면 즉시 중단하고 기존 스크립트 사용 요구
echo ========================================================================================
echo.

:: 환경 변수 설정
set CLAUDE_RULES_ACTIVE=TRUE
set CLAUDE_PROJECT_PATH=!currentPath!
goto :end

:notFound
echo.
echo 📝 CLAUDE.md 파일을 찾을 수 없습니다.
echo    범용 Claude 작업 모드로 진행합니다.
echo.
set CLAUDE_RULES_ACTIVE=FALSE

:end
endlocal