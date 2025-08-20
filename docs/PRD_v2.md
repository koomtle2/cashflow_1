# 재무데이터 처리 시스템 PRD v2

## 1. 핵심 원칙 (CLAUDE.md 기반)

### 1.1 데이터 완결성 최우선 원칙
- **절대 원칙**: 데이터 완결성이 모든 다른 고려사항보다 우선
- **추정값 금지**: 확실하지 않은 데이터는 절대 입력하지 않음
- **빈 값 허용**: 틀린 데이터보다 빈 데이터가 훨씬 안전
- **의심시 표시**: 불확실한 데이터는 노란색(#FFFF00) 마킹

### 1.2 노란색 마킹 시스템
- **대상**: 데이터 누락, 형식 오류, 분류 실패, 검증 불가능한 모든 상황
- **방법**: openpyxl을 사용하여 해당 셀을 노란색(#FFFF00)으로 마킹
- **값 처리**: 문제 있는 셀에는 값을 입력하지 않거나 원본 그대로 유지
- **로깅**: ./log/YYYY-MM-DD_HHMMSS.log 파일에 상세 기록

### 1.3 교차 오염 방지 시스템
- **정의**: 한 계정의 데이터가 다른 계정에 잘못 반영되는 현상 완전 차단
- **처리**: 계정별 완전 격리 처리
- **감지**: 실시간 오염 패턴 감지 시스템
- **대응**: 오염 감지시 즉시 중단 및 백업 복원

## 2. 시스템 아키텍처

### 2.1 3단계 검증 체계

#### 1단계: Python 기본 검증
- 데이터 구조 및 형식 검증
- 필수 필드 존재 확인
- 숫자형 데이터 타입 검증
- 날짜 형식 검증

#### 2단계: MCP 패턴 분석
- 복잡한 패턴 인식
- VAT 포함/제외 판단
- 계정 분류 검증
- 이상 케이스 분석

#### 3단계: Python 최종 검증
- 교차 오염 검사
- 데이터 무결성 확인
- 원장 vs 처리결과 1:1 대조
- 최종 품질 보증

### 2.2 Python-MCP 역할 분담

#### Python 담당 작업 (정형화된 처리)
- 숫자 계산 및 집계
- 데이터 타입 검증
- 파일 읽기/쓰기
- 로그 파일 생성 (UTF-8 필수)
- 노란색 마킹 적용
- 교차 오염 감지

#### MCP 담당 작업 (복잡한 판단)
- 계정 패턴 인식
- VAT 포함/제외 판단
- 전기이월 여부 판단
- 특이 케이스 분석
- 불규칙한 데이터 해석

### 2.3 데이터 흐름도

```
[원장 Excel] 
    ↓
[Python 1차 검증] → [이상 데이터 노란색 마킹]
    ↓
[MCP 패턴 분석] → [불확실시 "UNCERTAIN" 반환]
    ↓
[Python 2차 검증] → [교차 오염 검사]
    ↓
[최종 결과 파일] + [UTF-8 로그 파일]
```

## 3. 구현 상세

### 3.1 Python 스크립트 명세

#### validation_framework.py
```python
import logging
import os
from datetime import datetime
from openpyxl.styles import PatternFill

class DataValidator:
    def __init__(self):
        self.yellow_marks = []
        self.log_file = self._create_utf8_log()
        self.yellow_fill = PatternFill(
            start_color="FFFF00", 
            end_color="FFFF00", 
            fill_type="solid"
        )
    
    def _create_utf8_log(self):
        log_filename = f"./log/{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.log"
        os.makedirs("./log", exist_ok=True)
        logging.basicConfig(
            filename=log_filename,
            level=logging.INFO,
            format='[%(asctime)s] [%(levelname)s] %(message)s',
            filemode='w',
            encoding='utf-8'
        )
        return log_filename
    
    def validate_data_structure(self, sheet):
        """1단계: 데이터 구조 검증"""
        required_columns = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        for col in required_columns:
            if not sheet[f'{col}1'].value:
                self._mark_yellow_and_log(
                    sheet[f'{col}1'], 
                    "구조오류", 
                    f"필수컬럼_{col}_누락"
                )
                return False
        return True
    
    def validate_data_certainty(self, cell, account_code, data_type):
        """2단계: 데이터 확실성 검증"""
        value = cell.value
        
        # 전기이월 확인
        if data_type == "전기이월":
            if not self._is_certain_carry_forward(cell):
                self._mark_yellow_and_log(
                    cell, 
                    account_code, 
                    "전기이월_불확실", 
                    "B5가_전기이월이_아님"
                )
                return None
        
        # 숫자 데이터 검증
        if data_type == "금액":
            if not isinstance(value, (int, float)) and value is not None:
                self._mark_yellow_and_log(
                    cell, 
                    account_code, 
                    "형식오류", 
                    f"숫자아님_{value}"
                )
                return None
        
        return value
    
    def detect_cross_contamination(self, processed_data, original_data):
        """3단계: 교차 오염 검사"""
        contamination_alerts = []
        
        for account_code in processed_data.keys():
            for year, year_data in processed_data[account_code].items():
                for month, processed_value in year_data.items():
                    original_value = original_data.get(year, {}).get(account_code, {}).get(month, 0)
                    
                    if processed_value != 0 and original_value == 0:
                        contamination_alerts.append({
                            'account': account_code,
                            'year': year,
                            'month': month,
                            'suspicion': 'v3에_외부데이터_유입_의심'
                        })
                        logging.error(f"[교차오염위험] [계정_{account_code}] [년_{year}] [월_{month}] [처리중단]")
        
        if contamination_alerts:
            logging.error(f"[교차오염감지] [총_{len(contamination_alerts)}건] [즉시중단필요]")
            return contamination_alerts
        
        return []
    
    def _mark_yellow_and_log(self, cell, account_code, issue, detail):
        """노란색 마킹 + 로깅 동시 처리"""
        cell.fill = self.yellow_fill
        cell.value = None  # 추정값 입력 금지
        self.yellow_marks.append({
            'cell': cell.coordinate,
            'account': account_code,
            'issue': issue,
            'detail': detail
        })
        logging.warning(f"[{account_code}] [{issue}] [{detail}] [셀_{cell.coordinate}_노란색마킹,값비움]")
    
    def _is_certain_carry_forward(self, sheet):
        """전기이월 확실성 검증"""
        b5_value = sheet['B5'].value
        return b5_value == "전기이월"
```

#### marking_system.py
```python
from openpyxl.styles import PatternFill

class YellowMarkingSystem:
    def __init__(self):
        self.yellow_fill = PatternFill(
            start_color="FFFF00", 
            end_color="FFFF00", 
            fill_type="solid"
        )
        self.marked_cells = []
    
    def mark_uncertain_cell(self, workbook, cell, reason):
        """불확실한 데이터 노란색 마킹"""
        cell.fill = self.yellow_fill
        original_value = cell.value
        cell.value = None  # 추정값 절대 금지
        
        self.marked_cells.append({
            'sheet': workbook.active.title,
            'cell': cell.coordinate,
            'original_value': original_value,
            'reason': reason,
            'action': '값_비움_노란색_마킹'
        })
        
        return {
            'marked': True,
            'original_value': original_value,
            'reason': reason
        }
    
    def get_marking_summary(self):
        """마킹 결과 요약"""
        return {
            'total_marked': len(self.marked_cells),
            'details': self.marked_cells
        }
```

### 3.2 MCP 프롬프트 설계

#### 계정 패턴 분석 프롬프트
```
[재무 데이터 패턴 분석 요청]

입력 데이터:
{account_data_batch}

분석 기준:
1. VAT 포함/제외 판단
   - 거래 패턴 기반 판단
   - 금액 규모별 추론
   - 계정 성격 고려
2. 계정 분류 확인
   - BS/PL 계정 구분
   - 계정 코드 검증
3. 이상 패턴 감지
   - 부호 반전 오류
   - 중복 데이터 의심
   - 금액 이상치

출력 형식 (JSON):
{
  "account_analysis": {
    "account_code": "계정코드",
    "vat_status": "포함|제외|UNCERTAIN",
    "account_type": "BS|PL|UNCERTAIN",
    "anomalies": ["이상패턴1", "이상패턴2"],
    "confidence": "HIGH|MEDIUM|LOW|UNCERTAIN"
  }
}

중요 규칙:
- 확실하지 않으면 반드시 "UNCERTAIN" 반환
- 추정이나 가정 절대 금지
- 의심스러운 데이터는 명시적 표시
```

#### VAT 판단 전용 프롬프트
```
[VAT 포함/제외 판단 요청]

거래 데이터:
- 거래처: {counterpart}
- 금액: {amount}
- 거래 내용: {description}
- 계정: {account_code}

판단 기준:
1. 거래 성격 (면세, 과세, 영세율)
2. 거래처 유형 (개인, 법인, 정부기관)
3. 금액 패턴 (VAT 계산 가능 여부)

출력:
{
  "vat_judgment": "포함|제외|UNCERTAIN",
  "reasoning": "판단 근거",
  "confidence": "HIGH|MEDIUM|LOW"
}

확실하지 않으면 반드시 "UNCERTAIN" 반환
```

### 3.3 통합 처리 시스템

#### main_processor.py
```python
import json
from validation_framework import DataValidator
from marking_system import YellowMarkingSystem

class IntegratedProcessor:
    def __init__(self):
        self.validator = DataValidator()
        self.marker = YellowMarkingSystem()
        self.mcp_results = []
    
    def process_ledger_data(self, workbook_path):
        """통합 처리 메인 함수"""
        
        # 1단계: Python 기본 검증
        validation_result = self.validator.validate_data_structure(workbook)
        if not validation_result:
            logging.error("[1단계실패] [구조검증실패] [처리중단]")
            return False
        
        # 2단계: MCP 패턴 분석 (배치 처리)
        batch_data = self._prepare_batch_data(workbook)
        mcp_result = self._call_mcp_analysis(batch_data)
        
        # MCP 결과 처리
        uncertain_items = []
        for result in mcp_result:
            if "UNCERTAIN" in str(result):
                uncertain_items.append(result)
                self._handle_uncertain_data(result)
        
        # 3단계: 최종 검증
        contamination_check = self.validator.detect_cross_contamination(
            processed_data, original_data
        )
        
        if contamination_check:
            logging.error("[교차오염감지] [처리완전중단] [백업복원필요]")
            return False
        
        # 결과 보고
        self._generate_final_report()
        
        return True
    
    def _handle_uncertain_data(self, uncertain_result):
        """불확실한 데이터 처리"""
        account = uncertain_result.get('account_code')
        cell_ref = uncertain_result.get('cell_reference')
        
        # 노란색 마킹
        self.marker.mark_uncertain_cell(
            workbook, 
            cell_ref, 
            f"MCP분석불확실_{account}"
        )
        
        # 로깅
        logging.warning(f"[MCP불확실] [계정_{account}] [셀_{cell_ref}] [노란색마킹적용]")
    
    def _generate_final_report(self):
        """최종 처리 보고서 생성"""
        report = {
            'processing_date': datetime.now().isoformat(),
            'total_accounts_processed': len(self.processed_accounts),
            'yellow_marked_cells': self.marker.get_marking_summary(),
            'mcp_uncertain_items': len([r for r in self.mcp_results if "UNCERTAIN" in str(r)]),
            'cross_contamination_detected': False,
            'accuracy_achieved': self._calculate_accuracy(),
            'log_file_path': self.validator.log_file
        }
        
        # UTF-8 인코딩으로 보고서 저장
        with open(f"./log/final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
                  'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
```

## 4. 품질 보증 체계

### 4.1 검증 체크리스트

#### 처리 전 검증
- [ ] 원본 파일 백업 완료
- [ ] 필수 컬럼 존재 확인
- [ ] 계정 시트 구조 검증
- [ ] 로그 폴더 생성 확인

#### 처리 중 검증
- [ ] 모든 불확실 데이터 노란색 마킹
- [ ] UTF-8 로그 파일 실시간 기록
- [ ] 교차 오염 실시간 감지
- [ ] MCP "UNCERTAIN" 응답 적절 처리

#### 처리 후 검증
- [ ] 노란색 마킹 개수와 로그 엔트리 1:1 대응
- [ ] 원장 vs 처리결과 100% 일치 (노란색 제외)
- [ ] 교차 오염 0건 확인
- [ ] 최종 보고서 UTF-8 생성 확인

### 4.2 오류 처리 매트릭스

| 오류 유형 | 감지 단계 | 처리 방법 | 복구 방안 |
|----------|----------|-----------|-----------|
| 구조 오류 | Python 1차 | 즉시 중단 | 수동 수정 후 재실행 |
| 데이터 불확실 | Python/MCP | 노란색 마킹 | 사용자 확인 |
| 교차 오염 | Python 3차 | 즉시 중단 | 백업 복원 |
| MCP 오류 | MCP 호출 | 재시도 3회 | Python 단독 처리 |
| 인코딩 오류 | 파일 저장 | UTF-8 재시도 | 수동 인코딩 수정 |

### 4.3 성공 지표

#### 필수 달성 지표 (99.9% 목표)
- **데이터 정확도**: 99.9% (불확실 데이터 제외)
- **교차 오염**: 0건 (절대 허용 불가)
- **노란색 마킹 정확도**: 100% (모든 불확실 데이터 표시)
- **로그 완전성**: 100% (모든 처리 과정 기록)
- **UTF-8 인코딩**: 100% (모든 텍스트 파일)

#### 추가 개선 지표
- **처리 시간**: 기존 대비 50% 단축
- **사용자 만족도**: 95% 이상
- **재처리 빈도**: 5% 이하

## 5. 구현 로드맵

### Phase 1: Python 기초 시스템 (1주차)
- [ ] validation_framework.py 완성
- [ ] marking_system.py 완성 
- [ ] UTF-8 로깅 시스템 구축
- [ ] 기본 테스트 케이스 작성

### Phase 2: MCP 연동 시스템 (2주차)
- [ ] MCP 프롬프트 최적화
- [ ] 배치 처리 로직 구현
- [ ] 불확실 데이터 처리 시스템
- [ ] 통합 처리 시스템 구축

### Phase 3: 품질 보증 시스템 (3주차)
- [ ] 실제 원장 데이터로 전체 테스트
- [ ] 교차 오염 감지 테스트
- [ ] 99.9% 정확도 달성 검증
- [ ] 최종 시스템 검수 및 배포

## 6. 리스크 관리 방안

### 6.1 기술적 리스크
- **MCP API 장애**: Python 단독 처리 모드 구축
- **대용량 파일**: 메모리 효율적 처리 로직
- **인코딩 문제**: UTF-8 강제 적용 시스템

### 6.2 데이터 리스크  
- **원본 손상**: 자동 백업 시스템
- **교차 오염**: 실시간 감지 및 즉시 중단
- **데이터 유실**: 다단계 백업 체계

### 6.3 품질 리스크
- **정확도 미달**: 추가 검증 단계 구축
- **사용자 오해**: 상세 문서화 및 교육
- **유지보수**: 코드 주석 및 문서화

---

**작성일**: 2025-08-19  
**버전**: v2.0  
**기반 규칙**: C:\K04_cashflow_1\CLAUDE.md  
**목표 정확도**: 99.9%  
**핵심 원칙**: 데이터 완결성 최우선