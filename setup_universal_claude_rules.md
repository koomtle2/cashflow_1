# 범용 CLAUDE.md 룰 감지 시스템 설정 완료

## 🎯 핵심 기능
이제 **모든 워크스페이스**에서 CLAUDE.md 파일을 자동으로 감지하고 규칙을 표시합니다.

## 🔍 자동 감지 방식
1. **현재 디렉토리**에서 CLAUDE.md 검색
2. **상위 5단계**까지 재귀 검색
3. **발견시 즉시 규칙 표시**
4. **디렉토리 변경시 재검사**

## 🚀 사용 방법

### 1. 기존 프로젝트 (K04_cashflow_1)
```bash
cd C:\K04_cashflow_1
# 자동으로 CLAUDE.md 규칙 표시됨
```

### 2. 새로운 프로젝트
```bash
cd C:\MyNewProject
echo "### 9. Python 스크립트 활용 규칙..." > CLAUDE.md
# 즉시 규칙 감지 및 표시
```

### 3. 규칙 없는 프로젝트
```bash
cd C:\RegularProject
# "CLAUDE.md 파일을 찾을 수 없습니다" 메시지 표시
```

## 🛠️ 설정된 파일들

### 1. PowerShell 버전 (권장)
- 파일: `universal_claude_enforcer.ps1`
- 기능: 고급 검색, 동적 규칙 추출, 실시간 감지

### 2. Batch 버전 (백업)
- 파일: `universal_claude_enforcer.bat`
- 기능: 기본 검색, 단순 규칙 표시

### 3. Windows Terminal 설정
- 프로필명: "🌍 Universal Claude - Auto Rules Detection"
- 시작 위치: 사용자 홈 디렉토리
- 자동 감지: 모든 디렉토리에서 작동

## ✨ 주요 개선사항

### 이전 (특정 프로젝트만)
```json
"startingDirectory": "C:\\K04_cashflow_1"
"commandline": "cmd.exe /k \"cd C:\\K04_cashflow_1 && claude_rules_reminder.bat\""
```

### 현재 (범용)
```json
"startingDirectory": "%USERPROFILE%"
"commandline": "powershell.exe -NoExit -ExecutionPolicy Bypass -File \"C:\\K04_cashflow_1\\universal_claude_enforcer.ps1\""
```

## 🎮 단축키
- `Ctrl + Shift + C`: 범용 Claude 터미널 열기
- `cd [프로젝트경로]`: 이동 시 자동 규칙 재검사

## 🔧 커스터마이징

새 프로젝트에서 CLAUDE.md 생성 예시:
```markdown
### 9. Python 스크립트 활용 규칙
- **절대 금지**: 새 파일 생성
- **우선 사용**: 기존 스크립트
- **필수 확인**: Script 폴더 내용
```

## 🎯 테스트 방법
1. 새 터미널 창 열기
2. 다양한 디렉토리로 이동
3. CLAUDE.md 유무에 따른 자동 감지 확인
4. Claude 작업 시 규칙 준수 확인

이제 어떤 프로젝트에서도 CLAUDE.md 파일만 있으면 자동으로 규칙이 적용됩니다!