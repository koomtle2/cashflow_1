"""
재무데이터 처리 시스템 - 실제 데이터 기반 통합 테스트
실제 원장 파일을 사용한 종단간 테스트
"""

import sys
import os
import json
import traceback
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

# 메인 시스템 임포트
try:
    from main_processor import MainProcessor
    from logging_system import UTF8LoggingSystem
except ImportError as e:
    print(f"모듈 임포트 오류: {e}")
    print("현재 작업 디렉토리:", os.getcwd())
    print("스크립트 디렉토리:", script_dir)
    sys.exit(1)

class SystemIntegrationTest:
    """시스템 통합 테스트 클래스"""
    
    def __init__(self):
        self.test_session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.test_results = {
            'session_id': self.test_session_id,
            'start_time': datetime.now().isoformat(),
            'tests_performed': [],
            'overall_success': False,
            'error_summary': [],
            'performance_metrics': {}
        }
        
        # 프로젝트 루트 경로 (Script의 상위 디렉토리)
        self.project_root = script_dir.parent
        self.ledger_dir = self.project_root / "Ledgers"
        
        print(f"=== 시스템 통합 테스트 시작 ===")
        print(f"테스트 세션 ID: {self.test_session_id}")
        print(f"프로젝트 루트: {self.project_root}")
        print(f"원장 디렉토리: {self.ledger_dir}")
        print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    def discover_test_files(self):
        """테스트용 원장 파일 발견"""
        if not self.ledger_dir.exists():
            print(f"❌ 원장 디렉토리를 찾을 수 없습니다: {self.ledger_dir}")
            return []
        
        # Excel 파일 검색
        excel_files = list(self.ledger_dir.glob("*.xlsx"))
        
        # 임시 파일 제외
        test_files = [f for f in excel_files if not f.name.startswith('~$')]
        
        print(f"발견된 테스트 파일 ({len(test_files)}개):")
        for i, file_path in enumerate(test_files, 1):
            file_size = file_path.stat().st_size / (1024 * 1024)  # MB
            print(f"  {i}. {file_path.name} ({file_size:.1f} MB)")
        
        return test_files
    
    def run_basic_system_test(self):
        """기본 시스템 기능 테스트"""
        print("--- 기본 시스템 테스트 ---")
        
        test_result = {
            'test_name': 'basic_system_test',
            'start_time': datetime.now().isoformat(),
            'success': False,
            'details': {}
        }
        
        try:
            # 메인 프로세서 초기화 테스트
            print("1. 메인 프로세서 초기화...")
            processor = MainProcessor()
            print("✅ 메인 프로세서 초기화 성공")
            
            # 설정 로드 테스트
            print("2. 설정 검증...")
            config = processor.config
            required_sections = ['processing', 'validation', 'output']
            
            for section in required_sections:
                if section not in config:
                    raise Exception(f"필수 설정 섹션 누락: {section}")
            
            print("✅ 설정 검증 완료")
            
            # 컴포넌트 초기화 테스트
            print("3. 시스템 컴포넌트 검증...")
            components = {
                'logger': processor.logger,
                'validator': processor.validator,
                'marker': processor.marker,
                'mcp': processor.mcp,
                'batch_processor': processor.batch_processor
            }
            
            for comp_name, comp_instance in components.items():
                if comp_instance is None:
                    raise Exception(f"컴포넌트 초기화 실패: {comp_name}")
            
            print("✅ 모든 컴포넌트 정상 초기화")
            
            test_result['success'] = True
            test_result['details'] = {
                'components_initialized': list(components.keys()),
                'config_sections': list(config.keys())
            }
            
        except Exception as e:
            print(f"❌ 기본 시스템 테스트 실패: {e}")
            test_result['details']['error'] = str(e)
            test_result['details']['traceback'] = traceback.format_exc()
        
        test_result['end_time'] = datetime.now().isoformat()
        test_result['duration'] = (datetime.fromisoformat(test_result['end_time']) - 
                                  datetime.fromisoformat(test_result['start_time'])).total_seconds()
        
        self.test_results['tests_performed'].append(test_result)
        return test_result['success']
    
    def run_file_processing_test(self, test_file_path: Path):
        """실제 파일 처리 테스트"""
        print(f"--- 파일 처리 테스트: {test_file_path.name} ---")
        
        test_result = {
            'test_name': 'file_processing_test',
            'file_name': test_file_path.name,
            'file_size_mb': test_file_path.stat().st_size / (1024 * 1024),
            'start_time': datetime.now().isoformat(),
            'success': False,
            'details': {}
        }
        
        try:
            # 출력 파일 경로 설정
            output_dir = self.project_root / "Output"
            output_dir.mkdir(exist_ok=True)
            
            output_file = output_dir / f"test_output_{self.test_session_id}_{test_file_path.stem}.xlsx"
            
            print(f"1. 파일 처리 시작: {test_file_path.name}")
            print(f"2. 출력 경로: {output_file}")
            
            # 메인 프로세서 실행
            processor = MainProcessor()
            processing_start = datetime.now()
            
            result = processor.process_ledger_file(str(test_file_path), str(output_file))
            
            processing_end = datetime.now()
            processing_duration = (processing_end - processing_start).total_seconds()
            
            # 결과 검증
            print("3. 처리 결과 검증...")
            
            if not result['processing_successful']:
                raise Exception("처리가 실패했습니다")
            
            if not Path(result['output_file']).exists():
                raise Exception("출력 파일이 생성되지 않았습니다")
            
            # 성능 메트릭 수집
            performance_metrics = {
                'processing_time_seconds': processing_duration,
                'file_size_mb': test_result['file_size_mb'],
                'throughput_mb_per_sec': test_result['file_size_mb'] / processing_duration,
                'total_accounts': result['processing_stats']['total_accounts'],
                'processed_accounts': result['processing_stats']['processed_accounts'],
                'marked_cells': result['marked_cells_count'],
                'contamination_alerts': result['contamination_alerts']
            }
            
            # 품질 메트릭 검증
            quality_score = result['quality_assessment'].get('overall_score', 0)
            quality_grade = result['quality_assessment'].get('quality_grade', 'F')
            
            print(f"✅ 파일 처리 완료")
            print(f"   - 처리 시간: {processing_duration:.1f}초")
            print(f"   - 품질 점수: {quality_score}점 ({quality_grade})")
            print(f"   - 처리 계정: {result['processing_stats']['processed_accounts']}/{result['processing_stats']['total_accounts']}")
            print(f"   - 마킹된 셀: {result['marked_cells_count']}개")
            print(f"   - 교차 오염: {result['contamination_alerts']}건")
            
            test_result['success'] = True
            test_result['details'] = {
                'processing_result': result,
                'performance_metrics': performance_metrics,
                'output_file_created': True,
                'quality_assessment': result['quality_assessment']
            }
            
            # 성능 메트릭 저장
            self.test_results['performance_metrics'][test_file_path.name] = performance_metrics
            
        except Exception as e:
            print(f"❌ 파일 처리 테스트 실패: {e}")
            test_result['details']['error'] = str(e)
            test_result['details']['traceback'] = traceback.format_exc()
            self.test_results['error_summary'].append({
                'file': test_file_path.name,
                'error': str(e)
            })
        
        test_result['end_time'] = datetime.now().isoformat()
        test_result['duration'] = (datetime.fromisoformat(test_result['end_time']) - 
                                  datetime.fromisoformat(test_result['start_time'])).total_seconds()
        
        self.test_results['tests_performed'].append(test_result)
        return test_result['success']
    
    def run_claude_md_compliance_test(self):
        """CLAUDE.md 규칙 준수 테스트"""
        print("--- CLAUDE.md 규칙 준수 테스트 ---")
        
        test_result = {
            'test_name': 'claude_md_compliance_test',
            'start_time': datetime.now().isoformat(),
            'success': False,
            'details': {}
        }
        
        compliance_checks = {
            'utf8_encoding': False,
            'data_integrity_priority': False,
            'yellow_marking_system': False,
            'contamination_prevention': False,
            'no_estimation_rule': False
        }
        
        try:
            print("1. UTF-8 인코딩 보장 검증...")
            
            # 임시 로거 생성하여 UTF-8 테스트
            temp_logger = UTF8LoggingSystem("./temp_test_log")
            
            # 한글 텍스트 로깅 테스트
            korean_test_message = "한글 테스트: 데이터 완결성 최우선 원칙"
            temp_logger.log_validation_event('INFO', '테스트계정', '한글테스트', korean_test_message)
            
            # UTF-8 인코딩 검증
            encoding_check = temp_logger.validate_utf8_encoding()
            compliance_checks['utf8_encoding'] = encoding_check['all_files_utf8']
            
            temp_logger.close_session()
            
            if compliance_checks['utf8_encoding']:
                print("✅ UTF-8 인코딩 보장")
            else:
                print("❌ UTF-8 인코딩 실패")
            
            print("2. 데이터 완결성 우선 원칙 검증...")
            
            # 데이터 검증 프레임워크 확인
            from validation_framework import DataValidator
            validator = DataValidator()
            
            # 불확실한 데이터 처리 시뮬레이션
            test_workbook_path = self.ledger_dir / "test_sample.xlsx"
            
            # DataValidator의 핵심 메서드 존재 확인
            required_methods = [
                'extract_account_code',
                'classify_account_type',
                'validate_carry_forward',
                'detect_cross_contamination'
            ]
            
            for method in required_methods:
                if not hasattr(validator, method):
                    raise Exception(f"필수 검증 메서드 누락: {method}")
            
            compliance_checks['data_integrity_priority'] = True
            print("✅ 데이터 완결성 우선 원칙")
            
            print("3. 노란색 마킹 시스템 검증...")
            
            from marking_system import YellowMarkingSystem
            marker = YellowMarkingSystem()
            
            # 마킹 시스템 핵심 기능 확인
            if hasattr(marker, 'mark_uncertain_cell') and hasattr(marker, 'yellow_fill'):
                compliance_checks['yellow_marking_system'] = True
                print("✅ 노란색 마킹 시스템")
            else:
                print("❌ 노란색 마킹 시스템 불완전")
            
            print("4. 교차 오염 방지 시스템 검증...")
            
            # 교차 오염 감지 기능 확인
            if hasattr(validator, 'detect_cross_contamination'):
                compliance_checks['contamination_prevention'] = True
                print("✅ 교차 오염 방지 시스템")
            else:
                print("❌ 교차 오염 방지 시스템 누락")
            
            print("5. 추정값 입력 금지 규칙 검증...")
            
            # 마킹 시 값 비우기 규칙 확인
            from openpyxl import Workbook
            temp_wb = Workbook()
            temp_sheet = temp_wb.active
            temp_sheet['A1'].value = "테스트값"
            
            # 마킹 수행
            marker.mark_uncertain_cell(
                temp_wb, temp_sheet.title, 'A1', 'TEST', 
                '테스트이슈', '추정금지테스트', "원본값"
            )
            
            # 값이 비워졌는지 확인
            if temp_sheet['A1'].value is None:
                compliance_checks['no_estimation_rule'] = True
                print("✅ 추정값 입력 금지")
            else:
                print("❌ 추정값 입력 금지 미준수")
            
            # 전체 준수 여부 판단
            all_compliant = all(compliance_checks.values())
            
            if all_compliant:
                print("✅ 모든 CLAUDE.md 규칙 준수")
            else:
                failed_checks = [k for k, v in compliance_checks.items() if not v]
                print(f"❌ 일부 규칙 미준수: {failed_checks}")
            
            test_result['success'] = all_compliant
            test_result['details'] = compliance_checks
            
        except Exception as e:
            print(f"❌ CLAUDE.md 준수 테스트 실패: {e}")
            test_result['details']['error'] = str(e)
            test_result['details']['compliance_checks'] = compliance_checks
        
        test_result['end_time'] = datetime.now().isoformat()
        self.test_results['tests_performed'].append(test_result)
        return test_result['success']
    
    def run_performance_benchmark(self, test_files):
        """성능 벤치마크 테스트"""
        print("--- 성능 벤치마크 테스트 ---")
        
        if not test_files:
            print("❌ 테스트 파일이 없어 성능 테스트를 건너뜁니다")
            return False
        
        # 가장 큰 파일로 성능 테스트
        largest_file = max(test_files, key=lambda f: f.stat().st_size)
        file_size_mb = largest_file.stat().st_size / (1024 * 1024)
        
        print(f"성능 테스트 대상: {largest_file.name} ({file_size_mb:.1f} MB)")
        
        benchmark_start = datetime.now()
        success = self.run_file_processing_test(largest_file)
        benchmark_end = datetime.now()
        
        if success and largest_file.name in self.test_results['performance_metrics']:
            metrics = self.test_results['performance_metrics'][largest_file.name]
            
            print(f"성능 벤치마크 결과:")
            print(f"  - 파일 크기: {metrics['file_size_mb']:.1f} MB")
            print(f"  - 처리 시간: {metrics['processing_time_seconds']:.1f}초")
            print(f"  - 처리량: {metrics['throughput_mb_per_sec']:.2f} MB/초")
            print(f"  - 계정당 평균 처리시간: {metrics['processing_time_seconds']/max(metrics['total_accounts'], 1):.2f}초")
            
            # 성능 기준 평가
            performance_rating = "우수"
            if metrics['throughput_mb_per_sec'] < 0.1:
                performance_rating = "개선필요"
            elif metrics['throughput_mb_per_sec'] < 0.5:
                performance_rating = "보통"
            
            print(f"  - 성능 평가: {performance_rating}")
            
            return True
        else:
            print("❌ 성능 벤치마크 실패")
            return False
    
    def generate_final_report(self):
        """최종 테스트 보고서 생성"""
        print("--- 최종 테스트 보고서 생성 ---")
        
        self.test_results['end_time'] = datetime.now().isoformat()
        self.test_results['total_duration'] = (
            datetime.fromisoformat(self.test_results['end_time']) - 
            datetime.fromisoformat(self.test_results['start_time'])
        ).total_seconds()
        
        # 전체 성공 여부 판단
        successful_tests = sum(1 for test in self.test_results['tests_performed'] if test['success'])
        total_tests = len(self.test_results['tests_performed'])
        
        self.test_results['overall_success'] = (successful_tests == total_tests and 
                                               len(self.test_results['error_summary']) == 0)
        
        self.test_results['summary'] = {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': total_tests - successful_tests,
            'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0
        }
        
        # 보고서 파일 생성
        report_dir = self.project_root / "log"
        report_dir.mkdir(exist_ok=True)
        
        report_file = report_dir / f"system_test_report_{self.test_session_id}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 테스트 보고서 생성: {report_file}")
            
            # 요약 출력
            print("\n=== 최종 테스트 결과 ===")
            print(f"전체 테스트 수: {total_tests}")
            print(f"성공한 테스트: {successful_tests}")
            print(f"실패한 테스트: {total_tests - successful_tests}")
            print(f"성공률: {self.test_results['summary']['success_rate']:.1f}%")
            print(f"총 소요 시간: {self.test_results['total_duration']:.1f}초")
            
            if self.test_results['overall_success']:
                print("🎉 모든 테스트 성공! 시스템이 준비되었습니다.")
            else:
                print("⚠️  일부 테스트 실패. 오류를 검토해주세요.")
                
                if self.test_results['error_summary']:
                    print("\n오류 요약:")
                    for error in self.test_results['error_summary']:
                        print(f"  - {error['file']}: {error['error']}")
            
            return report_file
            
        except Exception as e:
            print(f"❌ 보고서 생성 실패: {e}")
            return None
    
    def run_full_integration_test(self):
        """전체 통합 테스트 실행"""
        try:
            # 1. 테스트 파일 발견
            test_files = self.discover_test_files()
            
            # 2. 기본 시스템 테스트
            basic_test_success = self.run_basic_system_test()
            
            if not basic_test_success:
                print("❌ 기본 시스템 테스트 실패로 인한 조기 종료")
                return False
            
            # 3. CLAUDE.md 준수 테스트
            compliance_success = self.run_claude_md_compliance_test()
            
            # 4. 실제 파일 처리 테스트 (최대 3개 파일)
            file_test_success = True
            test_file_limit = min(3, len(test_files))
            
            for i, test_file in enumerate(test_files[:test_file_limit]):
                print(f"\n파일 테스트 {i+1}/{test_file_limit}")
                file_success = self.run_file_processing_test(test_file)
                if not file_success:
                    file_test_success = False
            
            # 5. 성능 벤치마크 (선택사항)
            if test_files:
                print(f"\n성능 벤치마크 테스트")
                self.run_performance_benchmark(test_files)
            
            # 6. 최종 보고서 생성
            print(f"\n최종 보고서 생성")
            report_file = self.generate_final_report()
            
            return self.test_results['overall_success']
            
        except Exception as e:
            print(f"❌ 통합 테스트 실행 중 치명적 오류: {e}")
            print(traceback.format_exc())
            return False

def main():
    """메인 실행 함수"""
    print("재무데이터 처리 시스템 - 통합 테스트")
    print("=" * 50)
    
    # 통합 테스트 실행
    integration_test = SystemIntegrationTest()
    success = integration_test.run_full_integration_test()
    
    # 종료 코드 설정
    exit_code = 0 if success else 1
    
    print(f"\n테스트 완료. 종료 코드: {exit_code}")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())