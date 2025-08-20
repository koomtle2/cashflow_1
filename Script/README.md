# 재무데이터 처리 시스템

PRD v2.0 기반으로 구현된 재무 데이터 처리 시스템입니다. CLAUDE.md 규칙을 완전히 준수하며, 데이터 완결성을 최우선으로 하는 3단계 검증 체계를 적용했습니다.

## 📋 시스템 개요

### 핵심 원칙
- **데이터 완결성 최우선**: 확실하지 않은 데이터는 절대 입력하지 않음
- **99.9% 정확도 목표**: 추정값보다 빈 값을 선택
- **교차 오염 0건 필수**: 계정간 데이터 혼재 완전 차단
- **UTF-8 인코딩 보장**: 모든 텍스트 파일 UTF-8 처리

### 시스템 구조
```
3단계 검증 체계:
Phase 1: Python 기본검증 → Phase 2: MCP 패턴분석 → Phase 3: Python 최종검증
```

## 🗂️ 파일 구조

```
Script/
├── main_processor.py          # 메인 통합 프로세서
├── validation_framework.py    # 데이터 검증 프레임워크
├── marking_system.py          # 노란색 마킹 시스템
├── mcp_interface.py          # MCP 연동 인터페이스
├── batch_processor.py        # 배치 처리 로직
├── logging_system.py         # UTF-8 로깅 시스템
├── test_suite.py             # 단위 테스트 스위트
├── run_system_test.py        # 통합 테스트 실행기
└── README.md                 # 본 파일
```

## 🚀 사용 방법

### 기본 사용법 (CLI)
```bash
python main_processor.py <입력파일경로> [출력파일경로] [설정파일경로]
```

### 예시
```bash
# 기본 처리
python main_processor.py "C:\원장파일.xlsx"

# 출력 경로 지정
python main_processor.py "C:\원장파일.xlsx" "C:\처리결과.xlsx"

# 설정 파일과 함께 실행
python main_processor.py "C:\원장파일.xlsx" "C:\결과.xlsx" "config.json"
```

### Python 코드에서 사용
```python
from main_processor import MainProcessor

# 프로세서 초기화
processor = MainProcessor()

# 파일 처리
result = processor.process_ledger_file("입력파일.xlsx", "출력파일.xlsx")

print(f"처리 완료: {result['processing_successful']}")
print(f"품질 점수: {result['quality_assessment']['overall_score']}점")
```

## 🧪 테스트 실행

### 단위 테스트
```bash
python test_suite.py
```

### 통합 테스트
```bash
python run_system_test.py
```

## ⚙️ 설정

### 설정 파일 형식 (JSON)
```json
{
  "processing": {
    "enable_mcp_analysis": true,
    "enable_batch_processing": true,
    "max_retry_attempts": 3,
    "timeout_seconds": 1800
  },
  "validation": {
    "strict_mode": true,
    "mark_uncertain_data": true,
    "cross_contamination_check": true
  },
  "output": {
    "create_summary_sheet": true,
    "generate_reports": true,
    "backup_original": true
  }
}
```

## 📊 처리 과정

### Phase 1: Python 기본 검증
- 데이터 구조 검증
- 필수 필드 존재 확인
- 계정 코드 추출 및 분류
- 전기이월 데이터 검증
- 기본적인 데이터 타입 검증

### Phase 2: MCP 패턴 분석
- 복잡한 패턴 인식
- VAT 포함/제외 판단
- 계정별 배치 처리 최적화
- 불확실한 경우 "UNCERTAIN" 반환

### Phase 3: Python 최종 검증
- 교차 오염 검사 (0건 필수)
- 데이터 무결성 확인
- 최종 품질 보증
- 처리 결과 통합

## 🟡 노란색 마킹 시스템

### 마킹 대상
- 확실하지 않은 데이터
- 형식 오류가 있는 셀
- 계정 분류 실패
- MCP 분석에서 UNCERTAIN 판정
- 교차 오염 의심 데이터

### 마킹 규칙
1. 셀을 노란색(#FFFF00)으로 마킹
2. 셀 값을 비움 (추정값 입력 금지)
3. 원본 값은 로그에 기록
4. 상세 코멘트 추가

## 📈 품질 메트릭

### 점수 계산 (100점 만점)
- 기본 점수: 100점
- 마킹된 셀: 셀당 -2점 (최대 -30점)
- UNCERTAIN 항목: 항목당 -5점 (최대 -25점)
- 교차 오염 감지: -40점

### 등급 기준
- A등급: 90점 이상
- B등급: 80-89점
- C등급: 70-79점
- D등급: 70점 미만

## 🔍 로그 시스템

### 로그 파일 종류
- `main_YYYYMMDD_HHMMSS.log`: 메인 처리 로그
- `validation_YYYYMMDD_HHMMSS.log`: 검증 상세 로그
- `marking_YYYYMMDD_HHMMSS.log`: 마킹 상세 로그
- `contamination_YYYYMMDD_HHMMSS.log`: 교차 오염 로그
- `mcp_YYYYMMDD_HHMMSS.log`: MCP 상호작용 로그

### 로그 형식
```
[TIMESTAMP] [LEVEL] [ACCOUNT] [EVENT] [DETAIL] [DATA]
```

### UTF-8 인코딩 보장
- 모든 로그 파일 UTF-8 인코딩
- 한국어 텍스트 완벽 지원
- 인코딩 검증 기능 내장

## 🚨 오류 처리

### 교차 오염 감지시
1. 즉시 처리 중단
2. 백업 파일로 복원
3. 상세 로그 기록
4. 사용자에게 명시적 알림

### 데이터 불확실시
1. 해당 셀 노란색 마킹
2. 셀 값 비우기 (추정 금지)
3. 로그에 상세 기록
4. 수동 검토 권고

### MCP 오류시
1. 3회까지 재시도
2. 재시도 실패시 Python 단독 처리
3. 불확실한 결과는 모두 마킹

## 📋 요구사항

### Python 패키지
```
openpyxl>=3.1.0
```

### 시스템 요구사항
- Python 3.8 이상
- Windows 10/11 (현재 환경 기준)
- 메모리: 4GB 이상 권장
- 디스크: 처리 파일 크기의 3배 이상 여유공간

## 🎯 성능 지표

### 목표 성능
- 정확도: 99.9% (최우선)
- 처리 속도: 기존 대비 50% 단축
- 교차 오염: 0건 (절대 허용 불가)
- 마킹 정확도: 100%

### 실제 성능 (예상)
- 중형 파일(10MB): 약 5-10분
- 대형 파일(50MB): 약 30-60분
- 처리량: 0.1-0.5 MB/초

## 🔧 문제 해결

### 일반적인 문제들

#### 1. 한글 깨짐 현상
```bash
# Windows CMD에서
chcp 65001
python main_processor.py 파일.xlsx
```

#### 2. 메모리 부족 오류
- 배치 크기 조정: config.json에서 batch_size 감소
- 불필요한 프로그램 종료

#### 3. MCP 연결 오류
- 네트워크 연결 확인
- 재시도 대기 시간 증가
- Python 단독 모드로 처리

### 로그 확인 방법
```bash
# 최근 로그 파일 확인
ls -la log/*.log

# 특정 오류 검색
grep -i "error" log/main_*.log
```

## 🤝 기여 방법

### 개발 환경 설정
1. 리포지토리 클론
2. 가상환경 생성
3. 의존성 설치
4. 테스트 실행

### 코딩 규칙
- CLAUDE.md 규칙 완전 준수
- UTF-8 인코딩 보장
- 상세한 로깅 필수
- 모든 불확실한 데이터 마킹

## 📄 라이센스

이 프로젝트는 내부 사용을 위해 개발되었습니다.

## 📞 지원

기술 지원이 필요한 경우:
1. 로그 파일 확인 (`./log/` 폴더)
2. 테스트 실행 결과 검토
3. 설정 파일 검증
4. 입력 데이터 형식 확인

---
**생성일**: 2025-08-19  
**버전**: v2.0  
**기반 문서**: C:\K04_cashflow_1\docs\PRD_v2.md  
**핵심 원칙**: 데이터 완결성 최우선, 99.9% 정확도 목표