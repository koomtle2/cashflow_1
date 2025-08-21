# 터미널 CLAUDE.md 룰 알림 설정 가이드

## 자동 실행 설정 방법

### 1. Windows Terminal 사용시
```bash
# 프로필 시작 디렉토리를 C:\K04_cashflow_1로 설정
# Windows Terminal 설정에서:
"startingDirectory": "C:\\K04_cashflow_1"

# 시작 명령어 추가:
"commandline": "cmd.exe /k claude_rules_reminder.bat"
```

### 2. PowerShell 사용시
```powershell
# PowerShell 프로필에 추가
# $PROFILE 파일 편집:
notepad $PROFILE

# 다음 내용 추가:
if (Get-Location).Path -eq "C:\K04_cashflow_1") {
    . "C:\K04_cashflow_1\claude_session_start.ps1"
}
```

### 3. CMD 사용시
```batch
# 배치 파일 직접 실행
cd C:\K04_cashflow_1
claude_rules_reminder.bat
```

## 사용법

1. **터미널 시작시 자동 실행**
2. **규칙 알림 확인**
3. **Claude 세션 시작 전 규칙 숙지**

## 핵심 명령어

Claude에게 항상 이렇게 요청하세요:
```
기존 Script 폴더 스크립트만 사용해
새 파일 생성하지 마
먼저 기존 것 확인해
```

## 파일 위치
- `claude_rules_reminder.bat` - Windows 배치 파일
- `claude_session_start.ps1` - PowerShell 스크립트
- `CLAUDE.md` - 업데이트된 규칙 파일