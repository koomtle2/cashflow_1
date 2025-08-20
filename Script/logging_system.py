"""
재무데이터 처리 시스템 - UTF-8 로깅 시스템
CLAUDE.md 규칙: 모든 텍스트 파일 UTF-8 인코딩 필수
"""

import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

class UTF8LoggingSystem:
    """
    UTF-8 인코딩 보장 로깅 시스템
    모든 한국어 텍스트 처리를 위한 전용 로거
    """
    
    def __init__(self, log_base_path: str = "./log"):
        self.log_base_path = Path(log_base_path)
        self.log_base_path.mkdir(exist_ok=True)
        
        # 로그 파일 경로들
        self.main_log_file = self._create_log_file("main")
        self.validation_log_file = self._create_log_file("validation")
        self.marking_log_file = self._create_log_file("marking")
        self.contamination_log_file = self._create_log_file("contamination")
        self.mcp_log_file = self._create_log_file("mcp")
        
        # 로거 설정
        self._setup_loggers()
        
        # 세션 정보
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.session_stats = {
            'start_time': datetime.now().isoformat(),
            'total_logs': 0,
            'error_count': 0,
            'warning_count': 0,
            'info_count': 0
        }
        
        self.main_logger.info(f"[UTF8로깅시스템초기화] [세션_{self.session_id}] [UTF8인코딩보장]")
    
    def _create_log_file(self, log_type: str) -> str:
        """UTF-8 인코딩을 보장하는 로그 파일 생성"""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        log_filename = self.log_base_path / f"{log_type}_{timestamp}.log"
        
        # UTF-8 인코딩으로 빈 로그 파일 생성 (인코딩 확실히 보장)
        with open(log_filename, 'w', encoding='utf-8') as f:
            f.write(f"=== {log_type.upper()} 로그 파일 ===\n")
            f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"인코딩: UTF-8\n")
            f.write(f"세션ID: {datetime.now().strftime('%Y%m%d_%H%M%S')}\n")
            f.write("=" * 50 + "\n\n")
        
        return str(log_filename)
    
    def _setup_loggers(self):
        """각 로그 유형별 로거 설정"""
        # 기존 핸들러 제거 (중복 방지)
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # 메인 로거
        self.main_logger = self._create_logger('main', self.main_log_file)
        
        # 검증 로거
        self.validation_logger = self._create_logger('validation', self.validation_log_file)
        
        # 마킹 로거
        self.marking_logger = self._create_logger('marking', self.marking_log_file)
        
        # 교차 오염 로거
        self.contamination_logger = self._create_logger('contamination', self.contamination_log_file)
        
        # MCP 로거
        self.mcp_logger = self._create_logger('mcp', self.mcp_log_file)
    
    def _create_logger(self, name: str, log_file: str) -> logging.Logger:
        """개별 로거 생성 (UTF-8 인코딩 보장)"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        
        # 기존 핸들러 제거
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # UTF-8 파일 핸들러 추가
        handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
        handler.setLevel(logging.INFO)
        
        # 포맷터 설정
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # 상위 로거로 전파 방지 (중복 로그 방지)
        logger.propagate = False
        
        return logger
    
    def log_validation_event(self, level: str, account_code: str, event_type: str, 
                           detail: str, additional_data: Dict = None):
        """검증 이벤트 로깅"""
        message = f"[계정_{account_code}] [이벤트_{event_type}] [상세_{detail}]"
        
        if additional_data:
            message += f" [데이터_{json.dumps(additional_data, ensure_ascii=False)}]"
        
        self._log_with_stats(self.validation_logger, level, message)
    
    def log_marking_event(self, level: str, sheet_name: str, cell_coordinate: str,
                         account_code: str, issue_type: str, detail: str,
                         original_value: Any = None):
        """마킹 이벤트 로깅"""
        message = (f"[시트_{sheet_name}] [셀_{cell_coordinate}] [계정_{account_code}] "
                  f"[이슈_{issue_type}] [상세_{detail}] [원본값_{original_value}]")
        
        self._log_with_stats(self.marking_logger, level, message)
    
    def log_contamination_event(self, level: str, contamination_data: Dict):
        """교차 오염 이벤트 로깅"""
        account = contamination_data.get('account', 'UNKNOWN')
        year = contamination_data.get('year', 'UNKNOWN')
        month = contamination_data.get('month', 'UNKNOWN')
        suspicion = contamination_data.get('suspicion', 'UNKNOWN')
        processed_value = contamination_data.get('processed_value', 0)
        original_value = contamination_data.get('original_value', 0)
        
        message = (f"[교차오염감지] [계정_{account}] [년_{year}] [월_{month}] "
                  f"[의심_{suspicion}] [처리값_{processed_value}] [원장값_{original_value}]")
        
        self._log_with_stats(self.contamination_logger, level, message)
    
    def log_mcp_interaction(self, level: str, interaction_type: str, 
                          prompt_summary: str, response_summary: str,
                          token_usage: Dict = None):
        """MCP 상호작용 로깅"""
        message = f"[MCP_{interaction_type}] [요청_{prompt_summary}] [응답_{response_summary}]"
        
        if token_usage:
            message += f" [토큰_{json.dumps(token_usage, ensure_ascii=False)}]"
        
        self._log_with_stats(self.mcp_logger, level, message)
    
    def _log_with_stats(self, logger: logging.Logger, level: str, message: str):
        """통계와 함께 로깅"""
        # 통계 업데이트
        self.session_stats['total_logs'] += 1
        if level.upper() == 'ERROR':
            self.session_stats['error_count'] += 1
        elif level.upper() == 'WARNING':
            self.session_stats['warning_count'] += 1
        elif level.upper() == 'INFO':
            self.session_stats['info_count'] += 1
        
        # 로깅
        if level.upper() == 'ERROR':
            logger.error(message)
        elif level.upper() == 'WARNING':
            logger.warning(message)
        elif level.upper() == 'INFO':
            logger.info(message)
        elif level.upper() == 'DEBUG':
            logger.debug(message)
        
        # 메인 로그에도 기록
        if logger != self.main_logger:
            self.main_logger.info(f"[{logger.name.upper()}] {message}")
    
    def create_session_summary(self) -> Dict:
        """세션 요약 생성"""
        self.session_stats['end_time'] = datetime.now().isoformat()
        self.session_stats['duration_minutes'] = (
            datetime.now() - datetime.fromisoformat(self.session_stats['start_time'])
        ).total_seconds() / 60
        
        summary = {
            'session_id': self.session_id,
            'statistics': self.session_stats,
            'log_files': {
                'main_log': self.main_log_file,
                'validation_log': self.validation_log_file,
                'marking_log': self.marking_log_file,
                'contamination_log': self.contamination_log_file,
                'mcp_log': self.mcp_log_file
            }
        }
        
        # 요약 파일 생성 (UTF-8 보장)
        summary_file = self.log_base_path / f"session_summary_{self.session_id}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        self.main_logger.info(
            f"[세션요약생성] [ID_{self.session_id}] "
            f"[총로그_{self.session_stats['total_logs']}건] "
            f"[오류_{self.session_stats['error_count']}건] "
            f"[경고_{self.session_stats['warning_count']}건] "
            f"[파일_{summary_file}]"
        )
        
        return summary
    
    def export_consolidated_log(self) -> str:
        """통합 로그 파일 생성"""
        consolidated_file = self.log_base_path / f"consolidated_{self.session_id}.log"
        
        try:
            with open(consolidated_file, 'w', encoding='utf-8') as outfile:
                outfile.write("=== 통합 로그 파일 ===\n")
                outfile.write(f"세션 ID: {self.session_id}\n")
                outfile.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                outfile.write("=" * 50 + "\n\n")
                
                # 각 로그 파일 내용 통합
                log_files = [
                    ('MAIN', self.main_log_file),
                    ('VALIDATION', self.validation_log_file),
                    ('MARKING', self.marking_log_file),
                    ('CONTAMINATION', self.contamination_log_file),
                    ('MCP', self.mcp_log_file)
                ]
                
                for log_type, log_file in log_files:
                    outfile.write(f"\n{'=' * 20} {log_type} LOG {'=' * 20}\n")
                    try:
                        with open(log_file, 'r', encoding='utf-8') as infile:
                            outfile.write(infile.read())
                    except FileNotFoundError:
                        outfile.write(f"{log_type} 로그 파일을 찾을 수 없습니다.\n")
                    outfile.write(f"\n{'=' * (42 + len(log_type))}\n")
            
            self.main_logger.info(f"[통합로그생성완료] [파일_{consolidated_file}]")
            return str(consolidated_file)
            
        except Exception as e:
            self.main_logger.error(f"[통합로그생성오류] [오류_{str(e)}]")
            return ""
    
    def validate_utf8_encoding(self) -> Dict:
        """로그 파일 UTF-8 인코딩 검증"""
        validation_result = {
            'all_files_utf8': True,
            'validated_files': [],
            'encoding_issues': []
        }
        
        log_files = [
            self.main_log_file,
            self.validation_log_file,
            self.marking_log_file,
            self.contamination_log_file,
            self.mcp_log_file
        ]
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read(100)  # 첫 100자만 테스트
                    validation_result['validated_files'].append({
                        'file': log_file,
                        'encoding': 'UTF-8',
                        'status': 'OK'
                    })
            except UnicodeDecodeError as e:
                validation_result['all_files_utf8'] = False
                validation_result['encoding_issues'].append({
                    'file': log_file,
                    'error': str(e),
                    'status': 'ENCODING_ERROR'
                })
            except FileNotFoundError:
                validation_result['encoding_issues'].append({
                    'file': log_file,
                    'error': 'File not found',
                    'status': 'FILE_NOT_FOUND'
                })
        
        self.main_logger.info(
            f"[UTF8인코딩검증] "
            f"[전체파일UTF8_{validation_result['all_files_utf8']}] "
            f"[검증파일_{len(validation_result['validated_files'])}개] "
            f"[이슈_{len(validation_result['encoding_issues'])}개]"
        )
        
        return validation_result
    
    def get_log_files_info(self) -> Dict:
        """로그 파일 정보 반환"""
        return {
            'session_id': self.session_id,
            'log_files': {
                'main': self.main_log_file,
                'validation': self.validation_log_file,
                'marking': self.marking_log_file,
                'contamination': self.contamination_log_file,
                'mcp': self.mcp_log_file
            },
            'session_stats': self.session_stats
        }
    
    def close_session(self):
        """세션 종료 및 정리"""
        # 최종 통계 로깅
        self.create_session_summary()
        
        # UTF-8 인코딩 최종 검증
        encoding_check = self.validate_utf8_encoding()
        
        # 통합 로그 생성
        consolidated_log = self.export_consolidated_log()
        
        self.main_logger.info(
            f"[세션종료] [ID_{self.session_id}] "
            f"[UTF8검증_{encoding_check['all_files_utf8']}] "
            f"[통합로그_{bool(consolidated_log)}]"
        )
        
        # 로거 핸들러 정리
        for logger in [self.main_logger, self.validation_logger, self.marking_logger,
                      self.contamination_logger, self.mcp_logger]:
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)