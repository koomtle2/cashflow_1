# Windows Terminal 자동 실행 설정 가이드

## 현재 상황
Windows Terminal이 설치되지 않았거나 설정 파일을 찾을 수 없습니다.

## 해결 방법

### 1. Windows Terminal 설치 (권장)
```bash
# Microsoft Store에서 "Windows Terminal" 검색 후 설치
# 또는 winget 사용:
winget install Microsoft.WindowsTerminal
```

### 2. 설치 후 설정 적용
1. Windows Terminal 실행
2. 설정 열기 (Ctrl + ,)
3. "JSON 파일 열기" 클릭
4. `windows_terminal_setup.json` 내용을 복사하여 붙여넣기
5. 저장

### 3. 대안: 기본 CMD 자동화
Windows Terminal이 없다면 다음 방법 사용:

#### 방법 A: 바탕화면 바로가기
1. 바탕화면 우클릭 → 새로 만들기 → 바로 가기
2. 대상: `cmd.exe /k "cd C:\K04_cashflow_1 && claude_rules_reminder.bat"`
3. 이름: "Claude 프로젝트"

#### 방법 B: 시작 메뉴 바로가기
1. `Win + R` → `shell:startup` 입력
2. 바로가기 파일을 해당 폴더에 복사
3. Windows 시작시 자동 실행

## 자동 실행 테스트
설정 완료 후:
1. 새 터미널 창 열기
2. 자동으로 규칙 표시 확인
3. 프로젝트 폴더로 이동 확인

## 단축키
- `Ctrl + Shift + C`: Claude 프로젝트 새 탭 열기

## 파일 위치
- 설정 템플릿: `C:\K04_cashflow_1\windows_terminal_setup.json`
- 규칙 알림: `C:\K04_cashflow_1\claude_rules_reminder.bat`