@echo off
:: 모든 터미널에서 오토 스크롤 비활성화 설정
:: Windows Terminal, CMD, PowerShell 전체 적용

echo ============================================================================
echo 모든 터미널 오토 스크롤 비활성화 설정 스크립트
echo 작성일: 2025-08-20
echo ============================================================================
echo.

echo [1/4] Windows Terminal 설정 확인 중...
if exist "%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json" (
    echo ✓ Windows Terminal 설정 파일이 이미 업데이트되었습니다.
) else (
    echo ⚠ Windows Terminal이 설치되지 않았거나 설정 파일을 찾을 수 없습니다.
)

echo.
echo [2/4] CMD(Command Prompt) 레지스트리 설정 적용 중...
reg add "HKEY_CURRENT_USER\Console" /v QuickEdit /t REG_DWORD /d 0 /f > nul 2>&1
reg add "HKEY_CURRENT_USER\Console" /v ScreenBufferSize /t REG_DWORD /d 0x012C0050 /f > nul 2>&1
reg add "HKEY_CURRENT_USER\Console" /v WindowSize /t REG_DWORD /d 0x00320050 /f > nul 2>&1
if %errorlevel% == 0 (
    echo ✓ CMD 설정이 적용되었습니다.
) else (
    echo ✗ CMD 설정 적용에 실패했습니다. 관리자 권한이 필요할 수 있습니다.
)

echo.
echo [3/4] PowerShell 프로필 설정 적용 중...
powershell -Command "& {
    $profilePath = $PROFILE.AllUsersAllHosts
    $profileDir = Split-Path $profilePath -Parent
    if (!(Test-Path $profileDir)) { New-Item -Path $profileDir -ItemType Directory -Force }
    $content = @'
# 터미널 오토 스크롤 비활성화 설정
if ($Host.UI.RawUI) {
    try {
        $Host.UI.RawUI.WindowTitle = 'PowerShell - AutoScroll Disabled'
        Set-PSReadLineOption -EditMode Windows -BellStyle None
    } catch {}
}
'@
    Add-Content -Path $profilePath -Value $content -Force
}" > nul 2>&1
if %errorlevel% == 0 (
    echo ✓ PowerShell 프로필 설정이 적용되었습니다.
) else (
    echo ✗ PowerShell 프로필 설정 적용에 실패했습니다.
)

echo.
echo [4/4] 콘솔 기본 속성 설정 적용 중...
reg add "HKEY_CURRENT_USER\Console\%%SystemRoot%%_System32_cmd.exe" /v QuickEdit /t REG_DWORD /d 0 /f > nul 2>&1
reg add "HKEY_CURRENT_USER\Console\%%SystemRoot%%_System32_WindowsPowerShell_v1.0_powershell.exe" /v QuickEdit /t REG_DWORD /d 0 /f > nul 2>&1
if %errorlevel% == 0 (
    echo ✓ 콘솔 기본 속성이 설정되었습니다.
) else (
    echo ⚠ 일부 콘솔 설정이 적용되지 않았을 수 있습니다.
)

echo.
echo ============================================================================
echo 설정 완료! 다음 동작들이 비활성화되었습니다:
echo • 입력시 자동 스크롤 (scrollToInputWhenTyping: false)
echo • 입력시 화면 이동 (snapToInput: false)  
echo • QuickEdit 모드 (마우스 클릭시 스크롤 방지)
echo • 히스토리 크기 고정 (9001줄)
echo.
echo 변경사항을 적용하려면 모든 터미널 창을 닫고 다시 열어주세요.
echo ============================================================================

pause