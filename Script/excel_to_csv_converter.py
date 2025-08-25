#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel to CSV 변환기
c:\K04_cashflow_1\Ledgers의 모든 Excel 파일을 CSV로 변환

작성일: 2025-08-22
목적: 원장 데이터 처리 속도 향상 및 범용성 확보
"""

import os
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

# UTF-8 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./log/csv_conversion.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class ExcelToCSVConverter:
    """Excel 파일을 CSV로 변환하는 클래스"""
    
    def __init__(self, source_dir="C:\\K04_cashflow_1\\Ledgers", 
                 target_dir="C:\\K04_cashflow_1\\CSV_Data"):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.conversion_stats = {
            'total_files': 0,
            'converted_files': 0,
            'total_sheets': 0,
            'converted_sheets': 0,
            'failed_conversions': [],
            'start_time': datetime.now()
        }
        
        # CSV 출력 디렉토리 생성
        self.target_dir.mkdir(exist_ok=True)
        
        logging.info(f"[CSV변환기초기화] [원본디렉토리_{self.source_dir}] [출력디렉토리_{self.target_dir}]")
    
    def convert_all_excel_files(self):
        """Ledgers 폴더의 모든 Excel 파일을 CSV로 변환"""
        excel_files = list(self.source_dir.glob("*.xlsx"))
        self.conversion_stats['total_files'] = len(excel_files)
        
        logging.info(f"[변환시작] [파일수_{len(excel_files)}개]")
        
        for excel_file in excel_files:
            if not excel_file.name.startswith('~$'):  # 임시 파일 제외
                try:
                    self._convert_single_file(excel_file)
                    self.conversion_stats['converted_files'] += 1
                except Exception as e:
                    error_info = f"{excel_file.name}: {str(e)}"
                    self.conversion_stats['failed_conversions'].append(error_info)
                    logging.error(f"[파일변환실패] [파일_{excel_file.name}] [오류_{str(e)}]")
        
        self._generate_conversion_report()
    
    def _convert_single_file(self, excel_file):
        """단일 Excel 파일 변환"""
        logging.info(f"[파일변환시작] [파일_{excel_file.name}]")
        
        # 연도별 폴더 생성
        year = self._extract_year_from_filename(excel_file.name)
        year_dir = self.target_dir / f"{year}년"
        year_dir.mkdir(exist_ok=True)
        
        # Excel 파일 읽기 (모든 시트)
        excel_data = pd.read_excel(excel_file, sheet_name=None, engine='openpyxl')
        
        converted_sheets = 0
        for sheet_name, df in excel_data.items():
            try:
                # CSV 파일명 생성
                safe_sheet_name = self._sanitize_filename(sheet_name)
                csv_filename = f"{safe_sheet_name}.csv"
                csv_path = year_dir / csv_filename
                
                # 데이터 전처리
                processed_df = self._preprocess_sheet_data(df, sheet_name)
                
                # CSV로 저장 (UTF-8 인코딩)
                processed_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                
                converted_sheets += 1
                self.conversion_stats['converted_sheets'] += 1
                
                logging.info(f"[시트변환완료] [시트_{sheet_name}] [행수_{len(processed_df)}] [파일_{csv_filename}]")
                
            except Exception as e:
                logging.error(f"[시트변환실패] [시트_{sheet_name}] [오류_{str(e)}]")
        
        logging.info(f"[파일변환완료] [파일_{excel_file.name}] [변환시트수_{converted_sheets}개]")
        self.conversion_stats['total_sheets'] += len(excel_data)
    
    def _extract_year_from_filename(self, filename):
        """파일명에서 연도 추출"""
        if "2022" in filename:
            return "2022"
        elif "2023" in filename:
            return "2023"
        elif "2024" in filename:
            return "2024"
        elif "2025" in filename:
            return "2025"
        else:
            return "기타"
    
    def _sanitize_filename(self, sheet_name):
        """시트명을 파일명으로 사용 가능하도록 정리"""
        # 특수문자 제거 및 대체
        safe_name = sheet_name.replace('/', '_').replace('\\', '_').replace(':', '_')
        safe_name = safe_name.replace('*', '_').replace('?', '_').replace('"', '_')
        safe_name = safe_name.replace('<', '_').replace('>', '_').replace('|', '_')
        
        # 괄호는 유지 (계정코드 구분용)
        return safe_name
    
    def _preprocess_sheet_data(self, df, sheet_name):
        """시트 데이터 전처리"""
        # 1. 컬럼명 표준화
        if len(df.columns) >= 7:
            df.columns = ['날짜', '적요', '코드', '거래처', '차변', '대변', '잔액'] + list(df.columns[7:])
        
        # 2. 헤더 행 제거 (실제 데이터만 유지)
        # "날짜" 헤더가 있는 행 이후부터 데이터 시작
        data_start_row = 0
        for idx, row in df.iterrows():
            if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip() == '날짜':
                data_start_row = idx + 1
                break
        
        if data_start_row > 0:
            df = df.iloc[data_start_row:].copy()
        
        # 3. 빈 행 제거
        df = df.dropna(how='all')
        
        # 4. 계정 정보 메타데이터 추가
        account_code = self._extract_account_code(sheet_name)
        df.insert(0, '계정코드', account_code)
        
        # 5. 데이터 타입 정리
        numeric_columns = ['차변', '대변', '잔액']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 6. 날짜 형식 정리
        if '날짜' in df.columns:
            df['날짜'] = df['날짜'].astype(str).str.replace('0', '', regex=False)
        
        return df
    
    def _extract_account_code(self, sheet_name):
        """시트명에서 계정코드 추출"""
        import re
        # "숫자_이름(계정코드)" 패턴에서 계정코드 추출
        match = re.search(r'\((\d+)\)', sheet_name)
        if match:
            return match.group(1)
        
        # 패턴이 없으면 시트명 앞의 숫자 사용
        if '_' in sheet_name:
            parts = sheet_name.split('_')
            if len(parts) > 1 and parts[1].replace('(', '').replace(')', '').isdigit():
                return parts[1].replace('(', '').replace(')', '')[:5]
        
        return "UNKNOWN"
    
    def convert_specific_file(self, filename):
        """특정 파일만 변환"""
        excel_file = self.source_dir / filename
        if excel_file.exists():
            self._convert_single_file(excel_file)
            logging.info(f"[개별파일변환완료] [파일_{filename}]")
        else:
            logging.error(f"[파일없음] [파일_{filename}]")
    
    def create_consolidated_csv(self):
        """모든 CSV 파일을 통합한 마스터 CSV 생성"""
        all_data = []
        
        for year_dir in self.target_dir.iterdir():
            if year_dir.is_dir():
                for csv_file in year_dir.glob("*.csv"):
                    try:
                        df = pd.read_csv(csv_file, encoding='utf-8-sig')
                        df['연도'] = year_dir.name.replace('년', '')
                        df['원본파일'] = csv_file.name
                        all_data.append(df)
                    except Exception as e:
                        logging.error(f"[통합CSV생성실패] [파일_{csv_file}] [오류_{str(e)}]")
        
        if all_data:
            consolidated_df = pd.concat(all_data, ignore_index=True)
            consolidated_path = self.target_dir / "전체_원장데이터_통합.csv"
            consolidated_df.to_csv(consolidated_path, index=False, encoding='utf-8-sig')
            
            logging.info(f"[통합CSV생성완료] [경로_{consolidated_path}] [총행수_{len(consolidated_df)}]")
            return consolidated_path
        
        return None
    
    def _generate_conversion_report(self):
        """변환 결과 보고서 생성"""
        end_time = datetime.now()
        duration = end_time - self.conversion_stats['start_time']
        
        report = {
            "변환완료시간": end_time.strftime('%Y-%m-%d %H:%M:%S'),
            "총처리시간": str(duration),
            "처리통계": {
                "총파일수": self.conversion_stats['total_files'],
                "변환성공파일": self.conversion_stats['converted_files'],
                "총시트수": self.conversion_stats['total_sheets'],
                "변환성공시트": self.conversion_stats['converted_sheets']
            },
            "성공률": {
                "파일성공률": f"{(self.conversion_stats['converted_files'] / max(1, self.conversion_stats['total_files']) * 100):.1f}%",
                "시트성공률": f"{(self.conversion_stats['converted_sheets'] / max(1, self.conversion_stats['total_sheets']) * 100):.1f}%"
            },
            "실패목록": self.conversion_stats['failed_conversions']
        }
        
        # JSON 보고서 저장
        report_path = self.target_dir / f"conversion_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import json
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 콘솔 출력
        print(f"\n📊 CSV 변환 완료 보고서")
        print(f"📁 출력 디렉토리: {self.target_dir}")
        print(f"📈 파일 성공률: {report['성공률']['파일성공률']}")
        print(f"📋 시트 성공률: {report['성공률']['시트성공률']}")
        print(f"⏱️  총 처리시간: {report['총처리시간']}")
        
        if report['실패목록']:
            print(f"⚠️  실패 항목: {len(report['실패목록'])}개")
            for failure in report['실패목록']:
                print(f"   - {failure}")
        
        logging.info(f"[변환보고서생성] [경로_{report_path}]")
        return report_path


def main():
    """메인 실행 함수"""
    print("🔄 Excel to CSV 변환 시작...")
    
    converter = ExcelToCSVConverter()
    
    # 모든 Excel 파일 변환
    converter.convert_all_excel_files()
    
    # 통합 CSV 생성
    print("\n🔗 통합 CSV 파일 생성 중...")
    consolidated_path = converter.create_consolidated_csv()
    
    if consolidated_path:
        print(f"✅ 통합 CSV 생성 완료: {consolidated_path}")
    
    print("\n🎯 CSV 변환 작업 완료!")


if __name__ == "__main__":
    main()