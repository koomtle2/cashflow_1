"""
재무데이터 처리 시스템 - 배치 처리 로직
정확도 최우선, 효율적인 데이터 처리 배치 시스템
"""

import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from queue import Queue, PriorityQueue
from enum import Enum
import json

from logging_system import UTF8LoggingSystem
from mcp_interface import MCPInterface, MCPRequest, MCPResponse

class BatchPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4

class BatchStatus(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    UNCERTAIN = "UNCERTAIN"

@dataclass
class BatchTask:
    """배치 작업 단위"""
    task_id: str
    account_code: str
    account_type: str
    data: Dict
    task_type: str
    priority: BatchPriority = BatchPriority.NORMAL
    created_time: datetime = field(default_factory=datetime.now)
    processing_time: Optional[float] = None
    status: BatchStatus = BatchStatus.PENDING
    result: Optional[Dict] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    def __lt__(self, other):
        """우선순위 큐를 위한 비교 함수"""
        return self.priority.value < other.priority.value

@dataclass
class BatchResult:
    """배치 처리 결과"""
    task_id: str
    success: bool
    result_data: Dict
    processing_time: float
    confidence_level: str
    uncertain_items: List
    error_message: Optional[str] = None

class BatchProcessor:
    """
    배치 처리 시스템
    정확도 우선, 데이터 완결성 보장
    """
    
    def __init__(self, logging_system: UTF8LoggingSystem, mcp_interface: MCPInterface):
        self.logger = logging_system
        self.mcp = mcp_interface
        
        # 배치 처리 큐
        self.task_queue = PriorityQueue()
        self.result_queue = Queue()
        self.failed_tasks = []
        self.uncertain_tasks = []
        
        # 배치 처리 통계
        self.batch_stats = {
            'total_batches': 0,
            'completed_batches': 0,
            'failed_batches': 0,
            'uncertain_batches': 0,
            'retry_batches': 0,
            'total_processing_time': 0,
            'average_batch_time': 0
        }
        
        # 워커 스레드 풀 (동시 처리용)
        self.worker_threads = []
        self.max_workers = 3  # 정확도 우선이므로 적은 수의 워커
        self.shutdown_flag = False
        
        # 배치 크기 최적화 설정 (PRD 기반)
        self.batch_optimization = {
            'BS': {
                'small_data': {'batch_size': 6, 'max_concurrent': 2},  # <= 50건
                'medium_data': {'batch_size': 3, 'max_concurrent': 2}, # 50-200건
                'large_data': {'batch_size': 1, 'max_concurrent': 1}   # > 200건
            },
            'PL': {
                'small_data': {'batch_size': 3, 'max_concurrent': 2},
                'medium_data': {'batch_size': 1, 'max_concurrent': 1},
                'large_data': {'batch_size': 1, 'max_concurrent': 1}
            },
            'VAT': {
                'small_data': {'batch_size': 6, 'max_concurrent': 2},
                'medium_data': {'batch_size': 3, 'max_concurrent': 2},
                'large_data': {'batch_size': 1, 'max_concurrent': 1}
            }
        }
        
        self.logger.log_validation_event(
            'INFO', 'SYSTEM', 'BATCH_PROCESSOR_INIT',
            '배치처리시스템초기화완료', {'max_workers': self.max_workers}
        )
    
    def add_batch_task(self, account_code: str, account_type: str, 
                      task_type: str, data: Dict, 
                      priority: BatchPriority = BatchPriority.NORMAL) -> str:
        """배치 작업 추가"""
        task_id = f"{account_code}_{task_type}_{datetime.now().strftime('%H%M%S%f')}"
        
        task = BatchTask(
            task_id=task_id,
            account_code=account_code,
            account_type=account_type,
            data=data,
            task_type=task_type,
            priority=priority
        )
        
        self.task_queue.put(task)
        self.batch_stats['total_batches'] += 1
        
        self.logger.log_validation_event(
            'INFO', account_code, 'BATCH_TASK_ADDED',
            f'배치작업추가_{task_type}_{priority.name}',
            {'task_id': task_id, 'data_size': len(data)}
        )
        
        return task_id
    
    def start_batch_processing(self):
        """배치 처리 시작"""
        self.logger.log_validation_event(
            'INFO', 'SYSTEM', 'BATCH_PROCESSING_START',
            f'배치처리시작_{self.max_workers}개워커'
        )
        
        # 워커 스레드 생성 및 시작
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_thread,
                name=f"BatchWorker-{i+1}",
                daemon=True
            )
            worker.start()
            self.worker_threads.append(worker)
    
    def _worker_thread(self):
        """워커 스레드 함수"""
        worker_name = threading.current_thread().name
        
        while not self.shutdown_flag:
            try:
                # 작업 가져오기 (5초 타임아웃)
                task = self.task_queue.get(timeout=5)
                
                self.logger.log_validation_event(
                    'INFO', task.account_code, 'BATCH_PROCESSING_START',
                    f'{worker_name}_작업시작_{task.task_type}',
                    {'task_id': task.task_id}
                )
                
                # 작업 처리
                result = self._process_batch_task(task)
                
                # 결과 처리
                self._handle_batch_result(task, result)
                
                self.task_queue.task_done()
                
            except Exception as e:
                if not self.shutdown_flag:  # 정상 종료가 아닌 경우만 로그
                    self.logger.log_validation_event(
                        'ERROR', 'SYSTEM', 'WORKER_ERROR',
                        f'{worker_name}_워커오류_{str(e)}'
                    )
                continue
    
    def _process_batch_task(self, task: BatchTask) -> BatchResult:
        """개별 배치 작업 처리"""
        start_time = time.time()
        task.status = BatchStatus.PROCESSING
        
        try:
            # 작업 유형별 처리
            if task.task_type == 'account_pattern_analysis':
                mcp_response = self.mcp.analyze_account_patterns(
                    task.data, task.account_type
                )
            elif task.task_type == 'vat_verification':
                mcp_response = self.mcp.verify_vat_status(task.data)
            elif task.task_type == 'anomaly_detection':
                mcp_response = self.mcp.detect_data_anomalies(
                    task.data.get('processed_data', {}),
                    task.data.get('original_data', {})
                )
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
            
            processing_time = time.time() - start_time
            
            # 결과 분석 및 상태 결정
            if mcp_response.success:
                if mcp_response.confidence_level == 'UNCERTAIN':
                    status = BatchStatus.UNCERTAIN
                    self.uncertain_tasks.append(task)
                else:
                    status = BatchStatus.COMPLETED
                    
                task.status = status
                confidence = mcp_response.confidence_level
                uncertain_items = mcp_response.uncertain_items
                
            else:
                task.status = BatchStatus.FAILED
                confidence = 'UNCERTAIN'
                uncertain_items = []
                
            result = BatchResult(
                task_id=task.task_id,
                success=mcp_response.success,
                result_data=mcp_response.analysis_result,
                processing_time=processing_time,
                confidence_level=confidence,
                uncertain_items=uncertain_items,
                error_message=mcp_response.error_message
            )
            
            self.logger.log_validation_event(
                'INFO' if mcp_response.success else 'WARNING',
                task.account_code,
                'BATCH_TASK_COMPLETED',
                f'작업완료_{task.task_type}_{status.value}_{confidence}',
                {
                    'task_id': task.task_id,
                    'processing_time': processing_time,
                    'uncertain_items': len(uncertain_items)
                }
            )
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            task.status = BatchStatus.FAILED
            
            error_result = BatchResult(
                task_id=task.task_id,
                success=False,
                result_data={},
                processing_time=processing_time,
                confidence_level='UNCERTAIN',
                uncertain_items=[],
                error_message=str(e)
            )
            
            self.logger.log_validation_event(
                'ERROR', task.account_code, 'BATCH_TASK_ERROR',
                f'작업오류_{task.task_type}_{str(e)}',
                {'task_id': task.task_id, 'processing_time': processing_time}
            )
            
            return error_result
    
    def _handle_batch_result(self, task: BatchTask, result: BatchResult):
        """배치 결과 처리"""
        task.result = result.result_data
        task.processing_time = result.processing_time
        
        # 통계 업데이트
        self._update_batch_stats(task, result)
        
        # 결과 큐에 추가
        self.result_queue.put(result)
        
        # 실패한 작업 재시도 처리
        if not result.success and task.retry_count < task.max_retries:
            self._retry_failed_task(task)
        elif not result.success:
            self.failed_tasks.append(task)
            
        # UNCERTAIN 작업 특별 처리
        if result.confidence_level == 'UNCERTAIN':
            self._handle_uncertain_task(task, result)
    
    def _retry_failed_task(self, task: BatchTask):
        """실패한 작업 재시도"""
        task.retry_count += 1
        task.status = BatchStatus.PENDING
        
        # 우선순위를 높여서 재시도
        if task.priority == BatchPriority.NORMAL:
            task.priority = BatchPriority.HIGH
        elif task.priority == BatchPriority.HIGH:
            task.priority = BatchPriority.CRITICAL
        
        self.task_queue.put(task)
        self.batch_stats['retry_batches'] += 1
        
        self.logger.log_validation_event(
            'WARNING', task.account_code, 'BATCH_TASK_RETRY',
            f'작업재시도_{task.task_type}_시도{task.retry_count}회',
            {'task_id': task.task_id}
        )
    
    def _handle_uncertain_task(self, task: BatchTask, result: BatchResult):
        """UNCERTAIN 작업 특별 처리"""
        # UNCERTAIN 작업에 대한 특별한 로깅 및 알림
        self.logger.log_validation_event(
            'WARNING', task.account_code, 'UNCERTAIN_RESULT',
            f'불확실결과_{task.task_type}_수동확인필요',
            {
                'task_id': task.task_id,
                'uncertain_items': result.uncertain_items,
                'manual_review_required': True
            }
        )
        
        # 추가 검증이 필요한 경우 별도 큐에 추가
        # (사용자 검토를 위해)
        pass
    
    def _update_batch_stats(self, task: BatchTask, result: BatchResult):
        """배치 통계 업데이트"""
        self.batch_stats['total_processing_time'] += result.processing_time
        
        if result.success:
            if result.confidence_level == 'UNCERTAIN':
                self.batch_stats['uncertain_batches'] += 1
            else:
                self.batch_stats['completed_batches'] += 1
        else:
            self.batch_stats['failed_batches'] += 1
        
        # 평균 처리 시간 계산
        completed_total = (self.batch_stats['completed_batches'] + 
                          self.batch_stats['uncertain_batches'] +
                          self.batch_stats['failed_batches'])
        
        if completed_total > 0:
            self.batch_stats['average_batch_time'] = (
                self.batch_stats['total_processing_time'] / completed_total
            )
    
    def optimize_batch_size(self, account_type: str, data_size: int) -> Dict:
        """데이터 크기에 따른 배치 크기 최적화"""
        if account_type not in self.batch_optimization:
            account_type = 'PL'  # 기본값
        
        config = self.batch_optimization[account_type]
        
        if data_size <= 50:
            optimization = config['small_data']
        elif data_size <= 200:
            optimization = config['medium_data']
        else:
            optimization = config['large_data']
        
        self.logger.log_validation_event(
            'INFO', 'SYSTEM', 'BATCH_OPTIMIZATION',
            f'배치최적화_{account_type}_데이터{data_size}건',
            optimization
        )
        
        return optimization
    
    def create_optimized_batches(self, account_code: str, account_type: str, 
                               monthly_data: Dict, task_type: str) -> List[str]:
        """최적화된 배치 생성"""
        data_size = len(monthly_data)
        optimization = self.optimize_batch_size(account_type, data_size)
        
        batch_size = optimization['batch_size']
        task_ids = []
        
        # 월별 데이터를 배치 크기에 맞게 분할
        items = list(monthly_data.items())
        
        for i in range(0, len(items), batch_size):
            batch_data = dict(items[i:i + batch_size])
            
            # 중요한 데이터일수록 높은 우선순위
            if account_type == 'VAT' or len(batch_data) > optimization['batch_size'] * 0.8:
                priority = BatchPriority.HIGH
            else:
                priority = BatchPriority.NORMAL
            
            task_id = self.add_batch_task(
                account_code, account_type, task_type, 
                batch_data, priority
            )
            task_ids.append(task_id)
        
        self.logger.log_validation_event(
            'INFO', account_code, 'OPTIMIZED_BATCHES_CREATED',
            f'최적화배치생성_{len(task_ids)}개_크기{batch_size}',
            {'task_ids': task_ids, 'total_data': data_size}
        )
        
        return task_ids
    
    def wait_for_batch_completion(self, timeout_seconds: int = 300) -> Dict:
        """배치 작업 완료 대기"""
        start_time = time.time()
        
        while (self.task_queue.qsize() > 0 and 
               (time.time() - start_time) < timeout_seconds):
            time.sleep(1)
        
        # 모든 작업 완료 확인
        self.task_queue.join()
        
        completion_time = time.time() - start_time
        
        # 완료 상태 로깅
        completion_stats = {
            'total_time': completion_time,
            'completed_batches': self.batch_stats['completed_batches'],
            'failed_batches': self.batch_stats['failed_batches'],
            'uncertain_batches': self.batch_stats['uncertain_batches'],
            'retry_batches': self.batch_stats['retry_batches'],
            'timeout_reached': completion_time >= timeout_seconds
        }
        
        self.logger.log_validation_event(
            'INFO', 'SYSTEM', 'BATCH_COMPLETION',
            f'배치완료_시간{completion_time:.1f}초',
            completion_stats
        )
        
        return completion_stats
    
    def get_all_results(self) -> List[BatchResult]:
        """모든 배치 결과 수집"""
        results = []
        
        while not self.result_queue.empty():
            results.append(self.result_queue.get())
        
        return results
    
    def get_uncertain_tasks(self) -> List[BatchTask]:
        """UNCERTAIN 상태의 작업들 반환"""
        return self.uncertain_tasks.copy()
    
    def get_failed_tasks(self) -> List[BatchTask]:
        """실패한 작업들 반환"""
        return self.failed_tasks.copy()
    
    def generate_batch_report(self) -> Dict:
        """배치 처리 보고서 생성"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'batch_statistics': self.batch_stats,
            'queue_status': {
                'pending_tasks': self.task_queue.qsize(),
                'pending_results': self.result_queue.qsize()
            },
            'task_analysis': {
                'uncertain_tasks_count': len(self.uncertain_tasks),
                'failed_tasks_count': len(self.failed_tasks),
                'success_rate': self._calculate_success_rate(),
                'uncertainty_rate': self._calculate_uncertainty_rate()
            },
            'performance_metrics': {
                'average_processing_time': self.batch_stats['average_batch_time'],
                'total_processing_time': self.batch_stats['total_processing_time'],
                'throughput_per_minute': self._calculate_throughput()
            }
        }
        
        # 보고서 파일 저장 (UTF-8 보장)
        report_file = f"./log/batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            report['report_file'] = report_file
        except Exception as e:
            self.logger.log_validation_event(
                'ERROR', 'SYSTEM', 'REPORT_GENERATION_ERROR',
                f'보고서생성오류_{str(e)}'
            )
        
        return report
    
    def _calculate_success_rate(self) -> float:
        """성공률 계산"""
        total = (self.batch_stats['completed_batches'] + 
                self.batch_stats['failed_batches'] + 
                self.batch_stats['uncertain_batches'])
        
        if total == 0:
            return 0.0
            
        return (self.batch_stats['completed_batches'] / total) * 100
    
    def _calculate_uncertainty_rate(self) -> float:
        """불확실률 계산"""
        total = (self.batch_stats['completed_batches'] + 
                self.batch_stats['failed_batches'] + 
                self.batch_stats['uncertain_batches'])
        
        if total == 0:
            return 0.0
            
        return (self.batch_stats['uncertain_batches'] / total) * 100
    
    def _calculate_throughput(self) -> float:
        """처리량 계산 (작업/분)"""
        total_time_minutes = self.batch_stats['total_processing_time'] / 60
        total_completed = (self.batch_stats['completed_batches'] + 
                          self.batch_stats['uncertain_batches'] + 
                          self.batch_stats['failed_batches'])
        
        if total_time_minutes == 0:
            return 0.0
            
        return total_completed / total_time_minutes
    
    def shutdown(self):
        """배치 처리 시스템 종료"""
        self.shutdown_flag = True
        
        self.logger.log_validation_event(
            'INFO', 'SYSTEM', 'BATCH_SYSTEM_SHUTDOWN',
            '배치처리시스템종료시작'
        )
        
        # 모든 워커 스레드 대기
        for worker in self.worker_threads:
            worker.join(timeout=10)
        
        # 최종 보고서 생성
        final_report = self.generate_batch_report()
        
        self.logger.log_validation_event(
            'INFO', 'SYSTEM', 'BATCH_SYSTEM_SHUTDOWN_COMPLETE',
            '배치처리시스템종료완료',
            {'final_stats': self.batch_stats}
        )