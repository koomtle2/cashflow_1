#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
정밀 Excel-CSV 비교 검증 도구
모든 변환 결과를 자동으로 비교하여 차이점 탐지

작성일: 2025-08-23
목적: 날짜 외 다른 변환 이슈 발견
"""

import os
import pandas as pd
from pathlib import Path
import json
from datetime import datetime
import logging

# UTF-8 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

class ExcelCSVComparator:
    """Excel 원본과 CSV 변환 결과를 정밀 비교하는 클래스"""
    
    def __init__(self):
        self.excel_dir = Path("C:/K04_cashflow_1/Ledgers")
        self.csv_dir = Path("C:/K04_cashflow_1/CSV_Data")
        self.comparison_results = {
            'total_comparisons': 0,
            'perfect_matches': 0,
            'date_only_issues': 0,
            'other_issues': 0,
            'detailed_issues': [],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def compare_all_files(self):
        """모든 Excel-CSV 쌍을 비교"""
        excel_files = list(self.excel_dir.glob("*.xlsx"))
        
        for excel_file in excel_files:
            if not excel_file.name.startswith('~$'):
                year = self._extract_year(excel_file.name)
                year_csv_dir = self.csv_dir / f"{year}년"
                
                if year_csv_dir.exists():
                    self._compare_single_file(excel_file, year_csv_dir)
        
        return self._generate_final_report()
    
    def _extract_year(self, filename):
        """파일명에서 연도 추출"""
        for year in ['2022', '2023', '2024', '2025']:
            if year in filename:
                return year
        return "기타"
    
    def _compare_single_file(self, excel_file, csv_dir):
        """단일 Excel 파일과 해당 CSV 파일들 비교"""
        print(f"🔍 {excel_file.name} 정밀 검사 중...")
        
        try:
            excel_data = pd.read_excel(excel_file, sheet_name=None, engine='openpyxl')
            
            for sheet_name, excel_df in excel_data.items():
                # 해당하는 CSV 파일 찾기
                csv_filename = self._sanitize_filename(sheet_name) + ".csv"
                csv_path = csv_dir / csv_filename
                
                if csv_path.exists():
                    self._compare_sheet_data(excel_df, csv_path, sheet_name, excel_file.name)
                else:
                    self.comparison_results['detailed_issues'].append({
                        'type': 'missing_csv',
                        'file': excel_file.name,
                        'sheet': sheet_name,
                        'issue': f"CSV 파일 없음: {csv_filename}"
                    })
                    
        except Exception as e:
            logging.error(f"파일 비교 실패: {excel_file.name} - {str(e)}")
    
    def _compare_sheet_data(self, excel_df, csv_path, sheet_name, excel_filename):
        """시트 데이터 정밀 비교"""
        self.comparison_results['total_comparisons'] += 1
        
        try:
            csv_df = pd.read_csv(csv_path, encoding='utf-8-sig')
            
            # Excel 데이터 전처리 (CSV 변환 로직과 동일하게)
            processed_excel_df = self._preprocess_excel_like_csv(excel_df.copy())
            
            # 비교 수행
            comparison_result = self._detailed_comparison(processed_excel_df, csv_df, sheet_name, excel_filename)
            
            if comparison_result['is_perfect']:
                self.comparison_results['perfect_matches'] += 1
            elif comparison_result['date_only']:
                self.comparison_results['date_only_issues'] += 1
            else:
                self.comparison_results['other_issues'] += 1
                self.comparison_results['detailed_issues'].append(comparison_result)
                
        except Exception as e:
            self.comparison_results['detailed_issues'].append({
                'type': 'comparison_error',
                'file': excel_filename,
                'sheet': sheet_name,
                'issue': f"비교 실패: {str(e)}"
            })
    
    def _preprocess_excel_like_csv(self, df):
        """Excel 데이터를 CSV 변환 로직과 동일하게 전처리"""
        # 컬럼명 표준화
        if len(df.columns) >= 7:
            df.columns = ['날짜', '적요', '코드', '거래처', '차변', '대변', '잔액'] + list(df.columns[7:])
        
        # 헤더 행 제거
        data_start_row = 0
        for idx, row in df.iterrows():
            if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip() == '날짜':
                data_start_row = idx + 1
                break
        
        if data_start_row > 0:
            df = df.iloc[data_start_row:].copy()
        
        # 빈 행 제거
        df = df.dropna(how='all')
        
        # 숫자 컬럼 처리
        numeric_columns = ['차변', '대변', '잔액']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    
    def _detailed_comparison(self, excel_df, csv_df, sheet_name, excel_filename):
        """상세 비교 수행"""
        issues = []
        is_perfect = True
        date_only = True
        
        # 행 수 비교
        if len(excel_df) != len(csv_df) - 0:  # CSV는 계정코드 컬럼이 추가됨
            issues.append(f"행 수 불일치: Excel {len(excel_df)} vs CSV {len(csv_df)}")
            is_perfect = False
            date_only = False
        
        # 컬럼별 비교 (공통 컬럼만)
        common_columns = ['날짜', '적요', '코드', '거래처', '차변', '대변', '잔액']
        
        min_rows = min(len(excel_df), len(csv_df))
        for i in range(min_rows):
            for col in common_columns:
                if col in excel_df.columns and col in csv_df.columns:
                    excel_val = excel_df.iloc[i][col] if i < len(excel_df) else None
                    csv_val = csv_df.iloc[i][col] if i < len(csv_df) else None
                    
                    if col == '날짜':
                        # 날짜 비교 (알려진 버그)
                        if not self._compare_dates(excel_val, csv_val):
                            is_perfect = False
                            # 날짜 이슈는 이미 알려진 문제이므로 상세 기록 안함
                    else:
                        # 다른 컬럼 비교
                        if not self._values_equal(excel_val, csv_val):
                            issues.append(f"행 {i+1}, {col}열: Excel '{excel_val}' vs CSV '{csv_val}'")
                            is_perfect = False
                            date_only = False
        
        return {
            'type': 'data_difference',
            'file': excel_filename,
            'sheet': sheet_name,
            'issues': issues,
            'is_perfect': is_perfect,
            'date_only': date_only
        }
    
    def _compare_dates(self, excel_val, csv_val):
        """날짜 비교 (알려진 버그 패턴 확인)"""
        if pd.isna(excel_val) and pd.isna(csv_val):
            return True
        
        excel_str = str(excel_val).strip()
        csv_str = str(csv_val).strip()
        
        # 알려진 날짜 버그 패턴인지 확인
        if excel_str.startswith('0') and len(excel_str) >= 4:
            expected_csv = excel_str.replace('0', '', 1)  # 첫 번째 0만 제거
            return csv_str == expected_csv
        
        return excel_str == csv_str
    
    def _values_equal(self, val1, val2):
        """값 동등성 비교"""
        # NaN 처리
        if pd.isna(val1) and pd.isna(val2):
            return True
        if pd.isna(val1) or pd.isna(val2):
            return False
        
        # 숫자 비교
        try:
            return float(val1) == float(val2)
        except:
            # 문자열 비교
            return str(val1).strip() == str(val2).strip()
    
    def _sanitize_filename(self, sheet_name):
        """시트명을 파일명으로 변환"""
        safe_name = sheet_name.replace('/', '_').replace('\\', '_').replace(':', '_')
        safe_name = safe_name.replace('*', '_').replace('?', '_').replace('"', '_')
        safe_name = safe_name.replace('<', '_').replace('>', '_').replace('|', '_')
        return safe_name
    
    def _generate_final_report(self):
        """최종 비교 보고서 생성"""
        total = self.comparison_results['total_comparisons']
        perfect = self.comparison_results['perfect_matches']
        date_only = self.comparison_results['date_only_issues']
        other = self.comparison_results['other_issues']
        
        report = {
            'summary': {
                '총_비교_시트': total,
                '완벽_일치': perfect,
                '날짜만_문제': date_only,
                '다른_문제': other,
                '완벽_일치율': f"{(perfect/max(1,total)*100):.1f}%",
                '날짜만_문제율': f"{(date_only/max(1,total)*100):.1f}%",
                '기타_문제율': f"{(other/max(1,total)*100):.1f}%"
            },
            'detailed_issues': self.comparison_results['detailed_issues'],
            'timestamp': self.comparison_results['timestamp']
        }
        
        # 보고서 저장
        report_path = f"./log/detailed_comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report

def main():
    """메인 실행"""
    print("🔍 정밀 Excel-CSV 비교 검사 시작...")
    
    comparator = ExcelCSVComparator()
    report = comparator.compare_all_files()
    
    print("\n📊 정밀 비교 결과:")
    print(f"📋 총 비교 시트: {report['summary']['총_비교_시트']}개")
    print(f"✅ 완벽 일치: {report['summary']['완벽_일치']}개 ({report['summary']['완벽_일치율']})")
    print(f"📅 날짜만 문제: {report['summary']['날짜만_문제']}개 ({report['summary']['날짜만_문제율']})")
    print(f"⚠️  기타 문제: {report['summary']['다른_문제']}개 ({report['summary']['기타_문제율']})")
    
    if report['summary']['다른_문제'] > 0:
        print(f"\n🚨 날짜 외 문제 발견:")
        for issue in report['detailed_issues']:
            if issue.get('type') != 'date_issue':
                print(f"  📁 {issue['file']} - {issue['sheet']}")
                for problem in issue.get('issues', []):
                    print(f"    🔸 {problem}")
    else:
        print(f"\n✅ 날짜 변환 버그 외에는 문제가 발견되지 않았습니다!")

if __name__ == "__main__":
    main()