"""
재무데이터 처리 시스템 - MCP 연동 인터페이스
PRD 기반 MCP와 Python 간 효율적 역할 분담
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from logging_system import UTF8LoggingSystem

@dataclass
class MCPRequest:
    """MCP 요청 데이터 구조"""
    request_type: str
    account_data: Dict
    context: Dict
    batch_size: int
    priority: str = "NORMAL"

@dataclass
class MCPResponse:
    """MCP 응답 데이터 구조"""
    success: bool
    analysis_result: Dict
    confidence_level: str
    uncertain_items: List
    token_usage: Dict
    processing_time: float
    error_message: Optional[str] = None

class MCPInterface:
    """
    MCP 연동 인터페이스
    토큰 효율성보다 정확도를 최우선으로 하는 설계
    """
    
    def __init__(self, logging_system: UTF8LoggingSystem):
        self.logger = logging_system
        self.mcp_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'uncertain_responses': 0,
            'total_tokens_used': 0,
            'average_response_time': 0
        }
        
        # PRD 기반 최적 배치 크기 설정
        self.optimal_batch_sizes = {
            'BS': {'default': 3, 'max': 6},  # BS 계정: 3개월 단위, 최대 6개월
            'PL': {'default': 1, 'max': 3},  # PL 계정: 1개월 단위, 최대 3개월
            'VAT': {'default': 3, 'max': 6}  # VAT 계정: 3개월 단위
        }
        
        # MCP 프롬프트 템플릿
        self.prompt_templates = {
            'account_pattern_analysis': self._get_account_pattern_template(),
            'vat_judgment': self._get_vat_judgment_template(),
            'carry_forward_verification': self._get_carry_forward_template(),
            'anomaly_detection': self._get_anomaly_detection_template()
        }
        
        self.logger.log_mcp_interaction(
            'INFO', 'INITIALIZATION', 
            '시스템초기화', '정확도우선설계완료',
            {'batch_sizes': self.optimal_batch_sizes}
        )
    
    def analyze_account_patterns(self, account_data: Dict, account_type: str) -> MCPResponse:
        """
        계정 패턴 분석 (MCP 전용 작업)
        정확도 최우선, 불확실하면 UNCERTAIN 반환
        """
        start_time = time.time()
        
        try:
            # 배치 크기 결정
            batch_size = self._determine_optimal_batch_size(account_data, account_type)
            
            # 배치 단위로 데이터 분할
            batched_data = self._create_data_batches(account_data, batch_size)
            
            # MCP 요청 준비
            mcp_request = MCPRequest(
                request_type='account_pattern_analysis',
                account_data=batched_data,
                context={
                    'account_type': account_type,
                    'batch_size': batch_size,
                    'analysis_goal': '정확도_최우선_패턴_분석'
                },
                batch_size=batch_size,
                priority='HIGH'
            )
            
            # MCP 호출 (시뮬레이션 - 실제로는 MCP API 호출)
            response = self._call_mcp_api(mcp_request)
            
            processing_time = time.time() - start_time
            
            # 통계 업데이트
            self._update_mcp_stats(response, processing_time)
            
            # 로깅
            self.logger.log_mcp_interaction(
                'INFO', 'PATTERN_ANALYSIS',
                f'계정패턴분석_{account_type}_배치{batch_size}',
                f'성공_{response.success}_확신도_{response.confidence_level}',
                response.token_usage
            )
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            error_response = MCPResponse(
                success=False,
                analysis_result={},
                confidence_level='UNCERTAIN',
                uncertain_items=[],
                token_usage={'error': True},
                processing_time=processing_time,
                error_message=str(e)
            )
            
            self.logger.log_mcp_interaction(
                'ERROR', 'PATTERN_ANALYSIS_ERROR',
                f'계정패턴분석오류_{account_type}',
                str(e),
                {'error': True}
            )
            
            return error_response
    
    def verify_vat_status(self, transaction_data: List[Dict]) -> MCPResponse:
        """
        VAT 포함/제외 판단 (MCP 전용 작업)
        복잡한 판단 로직 필요한 경우
        """
        start_time = time.time()
        
        try:
            # VAT 판단을 위한 특별한 배치 처리
            vat_batches = self._create_vat_analysis_batches(transaction_data)
            
            all_results = []
            total_uncertain = 0
            
            for batch in vat_batches:
                mcp_request = MCPRequest(
                    request_type='vat_judgment',
                    account_data=batch,
                    context={
                        'judgment_criteria': ['거래성격', '거래처유형', '금액패턴'],
                        'certainty_threshold': 'HIGH'  # 높은 확신도 요구
                    },
                    batch_size=len(batch),
                    priority='HIGH'
                )
                
                batch_response = self._call_mcp_api(mcp_request)
                all_results.append(batch_response.analysis_result)
                
                if batch_response.confidence_level == 'UNCERTAIN':
                    total_uncertain += len(batch_response.uncertain_items)
            
            # 전체 결과 통합
            consolidated_response = MCPResponse(
                success=True,
                analysis_result={'vat_analysis': all_results},
                confidence_level='HIGH' if total_uncertain == 0 else 'UNCERTAIN',
                uncertain_items=[],  # VAT 판단 불확실 항목들
                token_usage={'vat_tokens': len(vat_batches) * 500},  # 예상 토큰 사용량
                processing_time=time.time() - start_time
            )
            
            self.logger.log_mcp_interaction(
                'INFO', 'VAT_VERIFICATION',
                f'VAT판단_배치{len(vat_batches)}개',
                f'불확실항목_{total_uncertain}건',
                consolidated_response.token_usage
            )
            
            return consolidated_response
            
        except Exception as e:
            error_response = MCPResponse(
                success=False,
                analysis_result={},
                confidence_level='UNCERTAIN',
                uncertain_items=[],
                token_usage={'error': True},
                processing_time=time.time() - start_time,
                error_message=str(e)
            )
            
            return error_response
    
    def detect_data_anomalies(self, processed_data: Dict, original_data: Dict) -> MCPResponse:
        """
        데이터 이상 패턴 감지 (MCP의 패턴 인식 능력 활용)
        교차 오염 및 이상치 감지
        """
        start_time = time.time()
        
        try:
            # 이상 패턴 감지를 위한 데이터 준비
            anomaly_data = {
                'processed_data_summary': self._summarize_data_for_anomaly_check(processed_data),
                'original_data_summary': self._summarize_data_for_anomaly_check(original_data),
                'comparison_points': self._create_comparison_points(processed_data, original_data)
            }
            
            mcp_request = MCPRequest(
                request_type='anomaly_detection',
                account_data=anomaly_data,
                context={
                    'detection_types': ['교차오염', '부호반전', '이상금액', '패턴불일치'],
                    'sensitivity': 'HIGH',  # 높은 민감도로 설정
                    'false_positive_tolerance': 'LOW'  # 거짓 양성 허용도 낮음
                },
                batch_size=1,  # 전체 데이터를 한 번에 분석
                priority='CRITICAL'
            )
            
            response = self._call_mcp_api(mcp_request)
            
            # 이상 패턴이 발견된 경우 즉시 알림
            if response.success and response.analysis_result.get('anomalies_detected', 0) > 0:
                self.logger.log_mcp_interaction(
                    'WARNING', 'ANOMALIES_DETECTED',
                    f'이상패턴감지_{response.analysis_result.get("anomalies_detected", 0)}건',
                    '즉시확인필요',
                    response.token_usage
                )
            
            return response
            
        except Exception as e:
            error_response = MCPResponse(
                success=False,
                analysis_result={'error': str(e)},
                confidence_level='UNCERTAIN',
                uncertain_items=[],
                token_usage={'error': True},
                processing_time=time.time() - start_time,
                error_message=str(e)
            )
            
            return error_response
    
    def _determine_optimal_batch_size(self, account_data: Dict, account_type: str) -> int:
        """최적 배치 크기 결정 (PRD 기준)"""
        data_volume = len(account_data)
        config = self.optimal_batch_sizes.get(account_type, {'default': 1, 'max': 3})
        
        if data_volume <= 50:  # 소량 데이터
            return min(config['max'], data_volume)
        elif data_volume <= 200:  # 중간 데이터
            return config['default']
        else:  # 대량 데이터
            return 1  # 정확도를 위해 작은 배치 사용
    
    def _create_data_batches(self, account_data: Dict, batch_size: int) -> List[Dict]:
        """데이터 배치 생성"""
        batches = []
        data_items = list(account_data.items())
        
        for i in range(0, len(data_items), batch_size):
            batch = dict(data_items[i:i + batch_size])
            batches.append(batch)
        
        return batches
    
    def _create_vat_analysis_batches(self, transaction_data: List[Dict]) -> List[List[Dict]]:
        """VAT 분석용 특별 배치 생성"""
        # 거래 유형별로 그룹화
        grouped_transactions = {
            'large_amounts': [],  # 대형 거래 (VAT 포함 가능성 높음)
            'small_amounts': [],  # 소액 거래
            'service_transactions': [],  # 서비스 거래 (법무, 번역 등 비과세 가능)
            'regular_transactions': []  # 일반 거래
        }
        
        for transaction in transaction_data:
            amount = transaction.get('amount', 0)
            description = transaction.get('description', '').lower()
            
            if amount > 1000000:  # 100만원 초과
                grouped_transactions['large_amounts'].append(transaction)
            elif amount < 100000:  # 10만원 미만
                grouped_transactions['small_amounts'].append(transaction)
            elif any(keyword in description for keyword in ['법무', '번역', '컨설팅', '용역']):
                grouped_transactions['service_transactions'].append(transaction)
            else:
                grouped_transactions['regular_transactions'].append(transaction)
        
        # 각 그룹을 배치로 변환
        batches = []
        for group_name, transactions in grouped_transactions.items():
            if transactions:
                batches.append(transactions)
        
        return batches
    
    def _summarize_data_for_anomaly_check(self, data: Dict) -> Dict:
        """이상 감지용 데이터 요약"""
        summary = {
            'total_accounts': len(data),
            'account_types': {},
            'value_ranges': {},
            'zero_value_accounts': 0,
            'negative_value_accounts': 0
        }
        
        for account_code, account_data in data.items():
            if isinstance(account_data, dict):
                for year, year_data in account_data.items():
                    if isinstance(year_data, dict):
                        for month, value in year_data.items():
                            if value == 0:
                                summary['zero_value_accounts'] += 1
                            elif value < 0:
                                summary['negative_value_accounts'] += 1
        
        return summary
    
    def _create_comparison_points(self, processed_data: Dict, original_data: Dict) -> List[Dict]:
        """비교 포인트 생성"""
        comparison_points = []
        
        for account_code in processed_data.keys():
            if account_code in original_data:
                comparison_points.append({
                    'account_code': account_code,
                    'processed_exists': True,
                    'original_exists': True,
                    'match_status': 'TO_VERIFY'
                })
            else:
                comparison_points.append({
                    'account_code': account_code,
                    'processed_exists': True,
                    'original_exists': False,
                    'match_status': 'CONTAMINATION_SUSPECT'
                })
        
        return comparison_points
    
    def _call_mcp_api(self, request: MCPRequest) -> MCPResponse:
        """
        MCP API 호출 (시뮬레이션)
        실제 구현시에는 실제 MCP API 호출로 대체
        """
        # 시뮬레이션: 실제로는 MCP API를 호출
        time.sleep(0.1)  # API 호출 시간 시뮬레이션
        
        # 요청 타입에 따른 응답 시뮬레이션
        if request.request_type == 'account_pattern_analysis':
            return self._simulate_pattern_analysis_response(request)
        elif request.request_type == 'vat_judgment':
            return self._simulate_vat_judgment_response(request)
        elif request.request_type == 'anomaly_detection':
            return self._simulate_anomaly_detection_response(request)
        else:
            return MCPResponse(
                success=False,
                analysis_result={},
                confidence_level='UNCERTAIN',
                uncertain_items=[],
                token_usage={},
                processing_time=0.1,
                error_message='Unknown request type'
            )
    
    def _simulate_pattern_analysis_response(self, request: MCPRequest) -> MCPResponse:
        """패턴 분석 응답 시뮬레이션"""
        # 실제로는 MCP의 응답을 받아서 처리
        return MCPResponse(
            success=True,
            analysis_result={
                'pattern_identified': True,
                'account_classification': 'VERIFIED',
                'vat_status': 'REQUIRES_MANUAL_CHECK',  # 수동 확인 필요
                'anomalies': []
            },
            confidence_level='MEDIUM',
            uncertain_items=['VAT_STATUS'],
            token_usage={'tokens_used': request.batch_size * 200},
            processing_time=0.5
        )
    
    def _simulate_vat_judgment_response(self, request: MCPRequest) -> MCPResponse:
        """VAT 판단 응답 시뮬레이션"""
        return MCPResponse(
            success=True,
            analysis_result={
                'vat_included_transactions': [],
                'vat_excluded_transactions': [],
                'uncertain_transactions': []  # 불확실한 거래들
            },
            confidence_level='UNCERTAIN',  # 정확도 우선이므로 보수적 판단
            uncertain_items=['COMPLEX_TRANSACTIONS'],
            token_usage={'tokens_used': len(request.account_data) * 150},
            processing_time=0.3
        )
    
    def _simulate_anomaly_detection_response(self, request: MCPRequest) -> MCPResponse:
        """이상 감지 응답 시뮬레이션"""
        return MCPResponse(
            success=True,
            analysis_result={
                'anomalies_detected': 0,
                'contamination_risk': 'LOW',
                'data_integrity': 'GOOD'
            },
            confidence_level='HIGH',
            uncertain_items=[],
            token_usage={'tokens_used': 800},  # 전체 데이터 분석
            processing_time=1.2
        )
    
    def _update_mcp_stats(self, response: MCPResponse, processing_time: float):
        """MCP 통계 업데이트"""
        self.mcp_stats['total_requests'] += 1
        
        if response.success:
            self.mcp_stats['successful_requests'] += 1
        else:
            self.mcp_stats['failed_requests'] += 1
        
        if response.confidence_level == 'UNCERTAIN':
            self.mcp_stats['uncertain_responses'] += 1
        
        if 'tokens_used' in response.token_usage:
            self.mcp_stats['total_tokens_used'] += response.token_usage['tokens_used']
        
        # 평균 응답 시간 계산
        total_time = self.mcp_stats['average_response_time'] * (self.mcp_stats['total_requests'] - 1)
        self.mcp_stats['average_response_time'] = (total_time + processing_time) / self.mcp_stats['total_requests']
    
    def _get_account_pattern_template(self) -> str:
        """계정 패턴 분석 프롬프트 템플릿"""
        return """
[재무 데이터 계정 패턴 분석 요청]

입력 데이터:
{account_data_batch}

분석 기준:
1. 계정 분류 검증
   - BS/PL 계정 구분 정확성
   - 계정 코드와 거래 내용 일치성
   
2. VAT 포함/제외 판단
   - 거래 패턴 기반 추론
   - 금액 규모별 VAT 처리 방식
   - 거래처 유형 고려
   
3. 이상 패턴 감지
   - 부호 반전 오류
   - 금액 이상치
   - 계정 성격과 맞지 않는 거래

출력 형식 (JSON):
{
  "account_analysis": {
    "account_code": "계정코드",
    "classification": "BS|PL|VERIFIED|UNCERTAIN",
    "vat_status": "포함|제외|UNCERTAIN",
    "confidence": "HIGH|MEDIUM|LOW|UNCERTAIN",
    "anomalies": ["발견된_이상_패턴들"],
    "recommendations": ["권고_사항들"]
  }
}

중요 원칙:
- 확실하지 않으면 반드시 "UNCERTAIN" 반환
- 추정이나 가정 절대 금지
- 데이터 완결성 최우선
- 의심스러운 경우 수동 확인 권고
"""
    
    def _get_vat_judgment_template(self) -> str:
        """VAT 판단 프롬프트 템플릿"""
        return """
[VAT 포함/제외 정밀 판단 요청]

거래 데이터:
{transaction_data}

판단 기준:
1. 거래 성격 분석
   - 면세 거래: 법무, 번역, 의료 등
   - 과세 거래: 일반 상품, 서비스
   - 영세율: 수출 등
   
2. 거래처 유형
   - 개인/법인 구분
   - 정부기관 여부
   - 외국인/외국법인 여부
   
3. 금액 패턴 분석
   - VAT 역산 가능 여부
   - 단수 처리 패턴
   - 금액 규모별 처리 방식

출력 형식 (JSON):
{
  "vat_analysis": {
    "transaction_id": "거래ID",
    "vat_judgment": "포함|제외|UNCERTAIN",
    "confidence": "HIGH|MEDIUM|LOW",
    "reasoning": "판단_근거",
    "manual_check_required": true/false
  }
}

절대 원칙:
- 불확실한 경우 반드시 "UNCERTAIN" + manual_check_required: true
- 추정 판단 절대 금지
- 복잡한 케이스는 수동 검토 요청
"""
    
    def _get_carry_forward_template(self) -> str:
        """전기이월 검증 템플릿"""
        return """
[전기이월 데이터 검증 요청]

검증 데이터:
- B5 셀 값: {b5_value}
- G5 셀 값: {g5_value}
- 계정 코드: {account_code}
- 계정 유형: {account_type}

검증 기준:
1. B5 값이 정확히 "전기이월"인가?
2. G5 값이 유효한 숫자인가?
3. 계정 성격상 전기이월이 합리적인가?

출력 형식 (JSON):
{
  "carry_forward_verification": {
    "is_valid": true/false,
    "confidence": "HIGH|MEDIUM|LOW|UNCERTAIN",
    "issues": ["발견된_문제들"],
    "verified_amount": 숫자_또는_null
  }
}

검증 원칙:
- B5가 "전기이월"이 아니면 즉시 UNCERTAIN
- 금액이 숫자가 아니면 즉시 UNCERTAIN
- 의심스러운 경우 수동 확인 요청
"""
    
    def _get_anomaly_detection_template(self) -> str:
        """이상 감지 템플릿"""
        return """
[데이터 이상 패턴 감지 요청]

분석 데이터:
{anomaly_data}

감지 대상:
1. 교차 오염
   - 계정간 데이터 혼재
   - 원장과 처리 결과 불일치
   
2. 부호 반전
   - 의도치 않은 음수/양수 전환
   - 차변/대변 처리 오류
   
3. 이상 금액
   - 비정상적 큰 금액
   - 패턴에 맞지 않는 금액
   
4. 데이터 무결성
   - 누락된 데이터
   - 중복된 데이터

출력 형식 (JSON):
{
  "anomaly_detection": {
    "anomalies_found": 숫자,
    "contamination_alerts": [],
    "integrity_issues": [],
    "critical_issues": [],
    "confidence": "HIGH|MEDIUM|LOW"
  }
}

감지 원칙:
- 의심스러운 패턴은 모두 보고
- 거짓 양성보다 거짓 음성이 더 위험
- 임계적 이슈는 즉시 처리 중단 권고
"""
    
    def get_mcp_statistics(self) -> Dict:
        """MCP 사용 통계 반환"""
        return {
            'session_stats': self.mcp_stats,
            'efficiency_metrics': {
                'success_rate': (self.mcp_stats['successful_requests'] / 
                               max(self.mcp_stats['total_requests'], 1)) * 100,
                'uncertainty_rate': (self.mcp_stats['uncertain_responses'] / 
                                   max(self.mcp_stats['total_requests'], 1)) * 100,
                'average_tokens_per_request': (self.mcp_stats['total_tokens_used'] / 
                                             max(self.mcp_stats['total_requests'], 1))
            },
            'optimal_batch_sizes': self.optimal_batch_sizes
        }