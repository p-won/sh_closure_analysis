# ============================================================
# parallel_worker.py
# 병렬 수집 worker 함수 모듈
# ※ Windows multiprocessing pickle 문제 해결을 위해 분리
# ※ 이 파일은 직접 실행하지 않음 → collect_parallel.py에서 import
# ============================================================

import time
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config import TARGET_DATES
from crawler_utils import (
    select_gu, select_industry, go_to_date,
    get_map_rect, collect_dong_data,
    flatten_dong_data, load_existing, save_csv
)


def crawl_industry_group(args):
    """
    크롬 1개를 유지하면서 담당 업종 묶음을 순서대로 수집
    args: (industry_list, gu_name, gu_value, cols, rows,
           use_zoom, dong_count, output_dir)
    industry_list: [(industry_name, big_val, sub_code), ...]
    """
    (industry_list, gu_name, gu_value,
     cols, rows, use_zoom, dong_count, output_dir) = args

    # ── 헤드리스 크롬 시작 (프로세스당 1회만) ────────────────
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")

    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)

    try:
        driver.get("https://bigdata.sbiz.or.kr/#/gis/delivery")
        time.sleep(8)

        # ── iframe 진입 ───────────────────────────────────────
        iframes = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "iframe"))
        )
        driver.switch_to.frame(iframes[0])
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "megaSelect"))
        )

        # ── 구 선택 (1회만) ───────────────────────────────────
        select_gu(driver, gu_value)
        print(f"[프로세스] {gu_name} 선택 완료")

        # ── body/map 크기 측정 (1회만) ────────────────────────
        body_w, body_h, map_rect = get_map_rect(driver)

        # ── 업종 순회 (크롬 유지) ─────────────────────────────
        for industry_name, big_val, sub_code in industry_list:

            safe_name = industry_name.replace("/", "_").replace(">", "_")
            temp_file = os.path.join(output_dir, f"temp_{gu_name}_{safe_name}.csv")

            # 업종별 임시 CSV에서 기존 데이터 로드
            all_results, done_set, dong_counts, done_dong = load_existing(temp_file)

            # 이 업종 전체 날짜가 이미 완료됐으면 skip
            if all(
                dong_counts.get((date, industry_name), 0) >= dong_count
                for date in TARGET_DATES
            ):
                print(f"[{industry_name}] 전체 skip (이미 완료)")
                continue

            # ── 업종 선택 ─────────────────────────────────────
            select_industry(driver, big_val, sub_code)
            print(f"\n[{industry_name}] 업종 선택 완료")

            # ── 2023년 12월로 이동 ────────────────────────────
            go_to_date(driver, "2023년 12월")

            # ── bbox 가져오기 ─────────────────────────────────
            bbox = driver.execute_script("""
                var paths = document.querySelectorAll('#map svg path');
                if (!paths.length) return null;
                var minX=Infinity, minY=Infinity, maxX=-Infinity, maxY=-Infinity;
                paths.forEach(function(p) {
                    var r = p.getBoundingClientRect();
                    if (r.width===0 || r.height===0) return;
                    minX=Math.min(minX,r.left); minY=Math.min(minY,r.top);
                    maxX=Math.max(maxX,r.right); maxY=Math.max(maxY,r.bottom);
                });
                return {minX:minX, minY:minY, maxX:maxX, maxY:maxY};
            """)

            # ── 날짜별 수집 (2023.12 → 2020.01) ──────────────
            for date in TARGET_DATES:

                if (date, industry_name) in done_set:
                    count = dong_counts.get((date, industry_name), 0)
                    if count >= dong_count:
                        print(f"  [{industry_name}] skip: {date} ({count}개 동)")
                        btn = driver.find_element(By.CSS_SELECTOR, ".prev-btn")
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(3)
                        continue

                cur = driver.find_element(By.CLASS_NAME, "current-date").text
                print(f"  [{industry_name}] 수집 중: {cur}")

                dong_data = collect_dong_data(
                    driver, body_w, body_h, map_rect, cols, rows, bbox
                )

                rows_data = flatten_dong_data(
                    dong_data, date, gu_name, industry_name, sub_code
                )
                new_rows = []
                for r in rows_data:
                    key = (r["날짜"], r["업종"], r["동"])
                    if key not in done_dong:
                        done_dong.add(key)
                        new_rows.append(r)

                all_results.extend(new_rows)
                dong_counts[(date, industry_name)] = \
                    dong_counts.get((date, industry_name), 0) + len(new_rows)
                done_set.add((date, industry_name))

                save_csv(all_results, temp_file)
                print(f"  [{industry_name}] {date} 완료: {len(dong_data)}개 동")

                if date != "2020년 01월":
                    btn = driver.find_element(By.CSS_SELECTOR, ".prev-btn")
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(0.8)

            print(f"[{industry_name}] ✓ 완료")

    except Exception as e:
        print(f"[오류] {e}")

    finally:
        driver.quit()