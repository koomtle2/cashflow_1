#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
수동 검수 지원 도구
Excel vs CSV 비교를 위한 간편한 도구

사용법: python manual_verification_helper.py
"""

import pandas as pd
from pathlib import Path
import json

class ManualVerificationHelper:
    """수동 검수를 지원하는 도구"""
    
    def __init__(self):
        self.excel_dir = Path("C:/K04_cashflow_1/Ledgers")
        self.csv_dir = Path("C:/K04_cashflow_1/CSV_Data")
    
    def suggest_sample_sheets(self):
        """검수용 샘플 시트 추천"""
        recommendations = {
            "2022년": {
                "소형": "1_정기예.적금(10500)",
                "중형": "42_접대비(81300)", 
                "대형": "0_보통예금(10300)"
            },
            "2023년": {
                "소형": "42_접대비(81300)",
                "중형": "9_차량운반구(14400)",
                "대형": "0_보통예금(10300)"
            },
            "2024년": {
                "소형": "49_접대비(기업업무추진비)(81300)",
                "중형": "24_건물(13100)",
                "대형": "1_보통예금(10300)"
            },
            "2025년": {
                "소형": "접대비(기업업무추진비)(81300)",
                "중형": "차량운반구(14400)",
                "대형": "1_보통예금(10300)"
            }
        }
        
        print("🎯 추천 검수 샘플 (총 12개):")
        for year, sheets in recommendations.items():
            print(f"\n📅 {year}:")
            for size, sheet in sheets.items():
                excel_path = self._find_excel_file(year)
                csv_path = self.csv_dir / year / f"{sheet}.csv"
                print(f"  {size:4} | {sheet}")
                print(f"       Excel: {excel_path}")
                print(f"       CSV:   {csv_path}")
        
        return recommendations
    
    def compare_specific_sheet(self, year, sheet_name):
        """특정 시트 비교 출력"""
        excel_file = self._find_excel_file(year)
        csv_file = self.csv_dir / year / f"{sheet_name}.csv"
        
        if not excel_file or not csv_file.exists():
            print(f"❌ 파일을 찾을 수 없습니다: {year} - {sheet_name}")
            return
        
        try:
            # Excel 시트 읽기
            excel_data = pd.read_excel(excel_file, sheet_name=sheet_name, engine='openpyxl')
            csv_data = pd.read_csv(csv_file, encoding='utf-8-sig')
            
            print(f"\n🔍 {year} - {sheet_name} 비교:")
            print(f"Excel 크기: {excel_data.shape}")
            print(f"CSV 크기:   {csv_data.shape}")
            
            # 처음 5행 비교 출력
            print(f"\n📋 Excel 처음 5행:")
            print(excel_data.head().to_string())
            
            print(f"\n📋 CSV 처음 5행:")
            print(csv_data.head().to_string())
            
            # 합계 비교 (숫자 컬럼)
            numeric_cols = ['차변', '대변', '잔액']
            for col in numeric_cols:
                if col in csv_data.columns:
                    csv_sum = csv_data[col].sum()
                    print(f"{col} 합계: {csv_sum:,}")
            
        except Exception as e:
            print(f"❌ 비교 실패: {e}")
    
    def _find_excel_file(self, year):
        """연도에 해당하는 Excel 파일 찾기"""
        for excel_file in self.excel_dir.glob("*.xlsx"):
            if year.replace('년', '') in excel_file.name:
                return excel_file
        return None
    
    def generate_verification_checklist(self):
        """검수 체크리스트 생성"""
        checklist = {
            "mandatory_checks": [
                "[ ] 금액 합계 일치 (차변, 대변, 잔액)",
                "[ ] 전체 행 수 일치", 
                "[ ] 한글 텍스트 정상 표시",
                "[ ] 특수문자 깨짐 없음",
                "[ ] 날짜 형식 확인 (알려진 버그)"
            ],
            "sample_sheets": self.suggest_sample_sheets(),
            "critical_accounts": [
                "보통예금(10300) - 거래량 최대",
                "접대비(81300) - 날짜 데이터 많음",
                "차량운반구(14400) - 중간 규모"
            ]
        }
        
        # 체크리스트 파일 저장
        with open("./manual_verification_checklist.json", 'w', encoding='utf-8') as f:
            json.dump(checklist, f, ensure_ascii=False, indent=2)
        
        print("📝 체크리스트가 생성되었습니다: manual_verification_checklist.json")
        return checklist

def main():
    """메인 실행"""
    helper = ManualVerificationHelper()
    
    print("🔧 수동 검수 지원 도구")
    print("=" * 50)
    
    # 샘플 추천
    helper.suggest_sample_sheets()
    
    # 체크리스트 생성
    print(f"\n" + "=" * 50)
    helper.generate_verification_checklist()
    
    # 사용법 안내
    print(f"\n📖 사용법:")
    print(f"python manual_verification_helper.py")
    print(f"특정 시트 비교: helper.compare_specific_sheet('2022년', '1_정기예.적금(10500)')")

if __name__ == "__main__":
    main()