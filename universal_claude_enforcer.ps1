# Universal CLAUDE.md Rules Enforcer
# 모든 워크스페이스에서 CLAUDE.md 파일을 자동 감지하고 규칙 표시

function Show-ClaudeRules {
    param(
        [string]$ProjectPath = (Get-Location).Path
    )
    
    # CLAUDE.md 파일 검색 (현재 디렉토리부터 상위로)
    $currentPath = $ProjectPath
    $claudeFile = $null
    $searchDepth = 0
    $maxDepth = 5  # 최대 5단계 상위까지 검색
    
    while ($searchDepth -lt $maxDepth -and $currentPath -ne $null) {
        $claudePath = Join-Path $currentPath "CLAUDE.md"
        if (Test-Path $claudePath) {
            $claudeFile = $claudePath
            break
        }
        
        # 상위 디렉토리로 이동
        $parentPath = Split-Path $currentPath -Parent
        if ($parentPath -eq $currentPath) {
            break  # 루트 디렉토리 도달
        }
        $currentPath = $parentPath
        $searchDepth++
    }
    
    if ($claudeFile) {
        # CLAUDE.md 파일 발견 시 규칙 표시
        Clear-Host
        Write-Host ""
        Write-Host "========================================================================================" -ForegroundColor Yellow
        Write-Host "                     🚨 CLAUDE.MD 규칙 발견! 자동 적용 중 🚨" -ForegroundColor Red
        Write-Host "========================================================================================" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "📁 프로젝트 경로: $($currentPath)" -ForegroundColor Cyan
        Write-Host "📄 규칙 파일: $($claudeFile)" -ForegroundColor Cyan
        Write-Host ""
        
        # CLAUDE.md에서 규칙 9번 추출 및 표시
        try {
            $content = Get-Content $claudeFile -Encoding UTF8
            $inRule9 = $false
            $rule9Content = @()
            
            foreach ($line in $content) {
                if ($line -match "### 9\. Python 스크립트 활용 규칙") {
                    $inRule9 = $true
                    continue
                }
                if ($inRule9 -and $line -match "### \d+\.") {
                    break
                }
                if ($inRule9 -and $line.Trim() -ne "") {
                    $rule9Content += $line
                }
            }
            
            if ($rule9Content.Count -gt 0) {
                Write-Host "🚨 핵심 규칙 (자동 추출):" -ForegroundColor Red
                foreach ($line in $rule9Content[0..10]) {  # 처음 10줄만 표시
                    if ($line -match "\*\*.*\*\*") {
                        Write-Host "   $line" -ForegroundColor Yellow
                    } else {
                        Write-Host "   $line" -ForegroundColor White
                    }
                }
                if ($rule9Content.Count -gt 10) {
                    Write-Host "   ... (더 많은 규칙 있음)" -ForegroundColor Gray
                }
            }
        }
        catch {
            Write-Host "⚠️ CLAUDE.md 파일 읽기 오류: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "✅ Claude에게 반드시 명시할 명령어:" -ForegroundColor Green
        Write-Host "   '기존 Script 폴더 스크립트만 사용해'" -ForegroundColor Cyan
        Write-Host "   '새 파일 생성하지 마'" -ForegroundColor Cyan
        Write-Host "   '먼저 기존 것 확인해'" -ForegroundColor Cyan
        Write-Host ""
        
        # 기존 스크립트 폴더 확인
        $scriptFolder = Join-Path $currentPath "Script"
        if (Test-Path $scriptFolder) {
            $scriptFiles = Get-ChildItem $scriptFolder -Filter "*.py" | Select-Object -First 5
            if ($scriptFiles.Count -gt 0) {
                Write-Host "📁 기존 스크립트 발견:" -ForegroundColor Magenta
                foreach ($file in $scriptFiles) {
                    Write-Host "   - $($file.Name)" -ForegroundColor Gray
                }
                if ((Get-ChildItem $scriptFolder -Filter "*.py").Count -gt 5) {
                    Write-Host "   - ... (총 $((Get-ChildItem $scriptFolder -Filter '*.py').Count)개 파일)" -ForegroundColor Gray
                }
            }
        }
        
        Write-Host ""
        Write-Host "========================================================================================" -ForegroundColor Yellow
        Write-Host "          위 규칙을 위반하면 즉시 중단하고 기존 스크립트 사용 요구" -ForegroundColor Red
        Write-Host "========================================================================================" -ForegroundColor Yellow
        Write-Host ""
        
        # 환경 변수 설정 (세션 동안 유지)
        $env:CLAUDE_RULES_ACTIVE = "TRUE"
        $env:CLAUDE_PROJECT_PATH = $currentPath
        
    } else {
        # CLAUDE.md 파일이 없는 경우
        Write-Host ""
        Write-Host "📝 CLAUDE.md 파일을 찾을 수 없습니다." -ForegroundColor Gray
        Write-Host "   범용 Claude 작업 모드로 진행합니다." -ForegroundColor Gray
        Write-Host ""
        
        $env:CLAUDE_RULES_ACTIVE = "FALSE"
    }
}

# 터미널 시작시 자동 실행
Show-ClaudeRules

# 디렉토리 변경시 자동 재검사를 위한 함수 오버라이드
function Set-Location {
    param([string]$Path)
    
    # 기본 Set-Location 실행
    Microsoft.PowerShell.Management\Set-Location $Path
    
    # CLAUDE.md 규칙 재검사
    if ($env:CLAUDE_RULES_ACTIVE -eq "TRUE") {
        Show-ClaudeRules
    }
}

# cd 별칭도 오버라이드
Set-Alias cd Set-Location -Force