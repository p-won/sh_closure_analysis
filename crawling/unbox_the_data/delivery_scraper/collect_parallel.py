# ============================================================
# collect_parallel.py
# 소상공인365 배달분석 데이터 수집 - 메인 실행 파일
#
# ※ parallel_worker.py 와 같은 폴더에 있어야 함
# ============================================================

import os
from multiprocessing import Pool
import pandas as pd


from config import INDUSTRY_CODES
from parallel_worker import crawl_industry_group

# ============================================================
# ★ 여기만 바꾸면 됩니다
# ============================================================
GU_NAME    = "강서구"
GU_VALUE   = "1150"
COLS       = 15
ROWS       = 14
USE_ZOOM   = False
DONG_COUNT = 20
OUTPUT_DIR = "/Users/joungwon/Documents/sh_closure_analysis/crawling/unbox_the_data/delivery_data"
PARALLEL   = 3
# ============================================================


# ============================================================
# 업종별 임시 CSV → 최종 파일 하나로 합산
# ============================================================
def merge_temp_files(output_file):
    all_dfs = []
    for industry_name in INDUSTRY_CODES.keys():
        safe_name = industry_name.replace("/", "_").replace(">", "_")
        temp_file = os.path.join(OUTPUT_DIR, f"temp_{GU_NAME}_{safe_name}.csv")  # ← 구 이름 포함
        if os.path.exists(temp_file):
            df = pd.read_csv(temp_file, encoding="utf-8-sig")
            all_dfs.append(df)

    if all_dfs:
        merged = pd.concat(all_dfs, ignore_index=True)
        merged.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"✓ 합산 완료: {len(merged)}행 → {output_file}")
    else:
        print("합산할 데이터가 없습니다.")


# ============================================================
# 메인 실행
# ============================================================
if __name__ == "__main__":

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_file = os.path.join(OUTPUT_DIR, f"seoul_delivery_{GU_NAME}.csv")

    industry_list = [
        (name, big_val, sub_code)
        for name, (big_val, sub_code) in INDUSTRY_CODES.items()
    ]

    chunk_size = len(industry_list) // PARALLEL
    chunks = [
        industry_list[i: i + chunk_size]
        for i in range(0, len(industry_list), chunk_size)
    ]
    if len(chunks) > PARALLEL:
        chunks[PARALLEL - 1].extend(chunks[PARALLEL])
        chunks = chunks[:PARALLEL]

    args_list = [
        (chunk, GU_NAME, GU_VALUE, COLS, ROWS, USE_ZOOM, DONG_COUNT, OUTPUT_DIR)
        for chunk in chunks
    ]

    print(f"{'='*60}")
    print(f"  {GU_NAME} (value: {GU_VALUE}) 수집 시작")
    print(f"  격자: {COLS}x{ROWS} | zoom: {'O' if USE_ZOOM else 'X'} | 동 수: {DONG_COUNT}")
    print(f"  업종 {len(industry_list)}개 → {PARALLEL}개 프로세스로 분배")
    for i, chunk in enumerate(chunks):
        names = [c[0] for c in chunk]
        print(f"  프로세스{i+1}: {names[0]} ~ {names[-1]} ({len(chunk)}개)")
    print(f"{'='*60}\n")

    with Pool(processes=PARALLEL) as pool:
        pool.map(crawl_industry_group, args_list)

    print(f"\n{'='*60}")
    print(f"  모든 업종 수집 완료 → 파일 합산 중...")
    print(f"{'='*60}")

    merge_temp_files(output_file)

    print(f"\n✓ {GU_NAME} 전체 수집 완료 → {output_file}")

