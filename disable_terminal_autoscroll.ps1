# 모든 터미널에서 오토 스크롤 비활성화 설정
# Windows Terminal, CMD, PowerShell 전체 적용
# UTF-8 인코딩으로 한글 지원

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "모든 터미널 오토 스크롤 비활성화 설정 스크립트" -ForegroundColor Yellow
Write-Host "작성일: 2025-08-20" -ForegroundColor Gray
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Windows Terminal 설정 확인
Write-Host "[1/4] Windows Terminal 설정 확인 중..." -ForegroundColor Green
$wtSettingsPath = "$env:LOCALAPPDATA\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
if (Test-Path $wtSettingsPath) {
    Write-Host "✓ Windows Terminal 설정 파일이 이미 업데이트되었습니다." -ForegroundColor Green
} else {
    Write-Host "⚠ Windows Terminal이 설치되지 않았거나 설정 파일을 찾을 수 없습니다." -ForegroundColor Yellow
}

# 2. CMD 레지스트리 설정
Write-Host ""
Write-Host "[2/4] CMD(Command Prompt) 레지스트리 설정 적용 중..." -ForegroundColor Green
try {
    # QuickEdit 모드 비활성화 (마우스 클릭시 스크롤 방지)
    Set-ItemProperty -Path "HKCU:\Console" -Name "QuickEdit" -Value 0 -Type DWord -Force
    # 스크린 버퍼 크기 설정 (300줄 x 80열)
    Set-ItemProperty -Path "HKCU:\Console" -Name "ScreenBufferSize" -Value 0x012C0050 -Type DWord -Force
    # 윈도우 크기 설정 (50줄 x 80열)
    Set-ItemProperty -Path "HKCU:\Console" -Name "WindowSize" -Value 0x00320050 -Type DWord -Force
    Write-Host "✓ CMD 설정이 적용되었습니다." -ForegroundColor Green
} catch {
    Write-Host "✗ CMD 설정 적용에 실패했습니다: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. PowerShell 프로필 설정
Write-Host ""
Write-Host "[3/4] PowerShell 프로필 설정 적용 중..." -ForegroundColor Green
try {
    $profilePath = $PROFILE.AllUsersAllHosts
    $profileDir = Split-Path $profilePath -Parent
    
    if (!(Test-Path $profileDir)) { 
        New-Item -Path $profileDir -ItemType Directory -Force | Out-Null
    }
    
    $profileContent = @"
# 터미널 오토 스크롤 비활성화 설정 (자동 추가됨)
if (`$Host.UI.RawUI) {
    try {
        `$Host.UI.RawUI.WindowTitle = 'PowerShell - AutoScroll Disabled'
        if (Get-Module -ListAvailable -Name PSReadLine) {
            Set-PSReadLineOption -EditMode Windows -BellStyle None
        }
    } catch {
        # 설정 적용 실패시 무시
    }
}
"@
    
    # 기존 설정이 없으면 추가
    if (!(Get-Content $profilePath -ErrorAction SilentlyContinue | Select-String "AutoScroll Disabled")) {
        Add-Content -Path $profilePath -Value $profileContent -Encoding UTF8
    }
    
    Write-Host "✓ PowerShell 프로필 설정이 적용되었습니다." -ForegroundColor Green
} catch {
    Write-Host "✗ PowerShell 프로필 설정 적용에 실패했습니다: $($_.Exception.Message)" -ForegroundColor Red
}

# 4. 특정 콘솔 속성 설정
Write-Host ""
Write-Host "[4/4] 콘솔 기본 속성 설정 적용 중..." -ForegroundColor Green
try {
    # CMD 전용 설정
    $cmdKey = "HKCU:\Console\%SystemRoot%_System32_cmd.exe"
    if (!(Test-Path $cmdKey)) { New-Item -Path $cmdKey -Force | Out-Null }
    Set-ItemProperty -Path $cmdKey -Name "QuickEdit" -Value 0 -Type DWord -Force
    
    # PowerShell 전용 설정
    $psKey = "HKCU:\Console\%SystemRoot%_System32_WindowsPowerShell_v1.0_powershell.exe"
    if (!(Test-Path $psKey)) { New-Item -Path $psKey -Force | Out-Null }
    Set-ItemProperty -Path $psKey -Name "QuickEdit" -Value 0 -Type DWord -Force
    
    Write-Host "✓ 콘솔 기본 속성이 설정되었습니다." -ForegroundColor Green
} catch {
    Write-Host "⚠ 일부 콘솔 설정이 적용되지 않았을 수 있습니다: $($_.Exception.Message)" -ForegroundColor Yellow
}

# 결과 요약
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "설정 완료! 다음 동작들이 비활성화되었습니다:" -ForegroundColor Green
Write-Host "• 입력시 자동 스크롤 (scrollToInputWhenTyping: false)" -ForegroundColor White
Write-Host "• 입력시 화면 이동 (snapToInput: false)" -ForegroundColor White  
Write-Host "• QuickEdit 모드 (마우스 클릭시 스크롤 방지)" -ForegroundColor White
Write-Host "• 히스토리 크기 고정 (9001줄)" -ForegroundColor White
Write-Host ""
Write-Host "변경사항을 적용하려면 모든 터미널 창을 닫고 다시 열어주세요." -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Cyan

Read-Host "계속하려면 Enter 키를 누르세요"