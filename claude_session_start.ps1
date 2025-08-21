# Claude Code 세션 시작시 자동 실행되는 PowerShell 스크립트
# 터미널 시작시 CLAUDE.md 규칙 자동 알림

Clear-Host
Write-Host ""
Write-Host "========================================================================================" -ForegroundColor Yellow
Write-Host "                        🚨 CLAUDE.MD 규칙 준수 필수 알림 🚨" -ForegroundColor Red
Write-Host "========================================================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "⚠️  규칙 9번: Python 스크립트 활용 규칙" -ForegroundColor Yellow
Write-Host "   - 기존 Script 폴더의 스크립트만 사용" -ForegroundColor White
Write-Host "   - 새로운 .py 파일 생성 절대 금지" -ForegroundColor Red
Write-Host "   - 임시 분석용 파일 생성 금지" -ForegroundColor Red
Write-Host "   - 사용자 명시적 승인 없는 새 파일 생성 완전 차단" -ForegroundColor Red
Write-Host ""
Write-Host "✅ Claude에게 요청시 반드시 명시:" -ForegroundColor Green
Write-Host "   '기존 Script 폴더 스크립트만 사용해'" -ForegroundColor Cyan
Write-Host "   '새 파일 생성하지 마'" -ForegroundColor Cyan
Write-Host "   '먼저 기존 것 확인해'" -ForegroundColor Cyan
Write-Host ""
Write-Host "📁 기존 스크립트 위치:" -ForegroundColor Magenta
Write-Host "   C:\K04_cashflow_1\Script\" -ForegroundColor White
Write-Host "   - main_processor.py (메인 처리)" -ForegroundColor Gray
Write-Host "   - validation_framework.py (데이터 검증)" -ForegroundColor Gray
Write-Host "   - logging_system.py (로깅)" -ForegroundColor Gray
Write-Host "   - marking_system.py (마킹)" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================================================================" -ForegroundColor Yellow
Write-Host "          위 규칙을 위반하면 즉시 중단하고 기존 스크립트 사용 요구" -ForegroundColor Red
Write-Host "========================================================================================" -ForegroundColor Yellow
Write-Host ""