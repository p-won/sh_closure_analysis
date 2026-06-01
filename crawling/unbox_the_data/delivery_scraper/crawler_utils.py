# ============================================================
# crawler_utils.py
# 소상공인365 배달분석 수집 공통 함수 모듈
# ============================================================

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import WAIT_POPUP, WAIT_MAP, MENU_X, MAX_DONG
import pandas as pd
import os
import time


# ── 마우스 초기화 (이전 팝업 닫기) ───────────────────────────
def reset_mouse(driver, body):
    try:
        # JS로 팝업 강제 제거
        driver.execute_script("""
            var popup = document.querySelector('section.delivery_layer_pop');
            if (popup) popup.remove();
        """)
        time.sleep(0.1)
    except:
        pass

# ── 격자 탐색: 동별 배달 데이터 수집 ─────────────────────────
def collect_dong_data(driver, body_w, body_h, map_rect, cols, rows, bbox=None):
    if bbox:
        start_x = bbox['minX']
        start_y = bbox['minY']
        width   = bbox['maxX'] - bbox['minX']
        height  = bbox['maxY'] - bbox['minY']
    else:
        start_x = map_rect['left']
        start_y = map_rect['top']
        width   = map_rect['width']
        height  = map_rect['height']

    results   = {}
    body      = driver.find_element(By.TAG_NAME, "body")
    prev_dong = ""

    for row in range(rows):
        for col in range(cols):
            x = start_x + width  * (col + 0.5) / cols
            y = start_y + height * (row + 0.5) / rows

            # 브라우저 절대 좌표 기준 마우스 이동 (원래 방식)
            offset_x = x - body_w / 2
            offset_y = y - body_h / 2

            try:
                reset_mouse(driver, body)
                ActionChains(driver) \
                    .move_to_element(body) \
                    .move_by_offset(offset_x, offset_y) \
                    .perform()
                time.sleep(WAIT_POPUP)

                popup = driver.find_elements(
                    By.CSS_SELECTOR, "section.delivery_layer_pop"
                )
                if popup:
                    p_tags = popup[0].find_elements(By.CSS_SELECTOR, ".con p")
                    dong, sales, count = "", "", ""
                    for p in p_tags:
                        t = p.text.strip()
                        if "평균매출액" in t:
                            sales = t.replace("평균매출액 : ", "")
                        elif "평균배달건수" in t:
                            count = t.replace("평균배달건수 : ", "")
                        elif "배달지역" in t:
                            dong = t.replace("배달지역 : ", "")

                    if dong and dong not in results:
                        results[dong] = {
                            "동": dong,
                            "평균매출액": sales,
                            "평균배달건수": count,
                        }
                    prev_dong = dong

                    if len(results) >= MAX_DONG:
                        return results
                else:
                    prev_dong = ""

            except:
                prev_dong = ""
                continue

    return results

# ── 업종 선택 ─────────────────────────────────────────────────
def select_industry(driver, big_val, sub_code):
    big_btn = driver.find_element(
        By.CSS_SELECTOR, f".listCategory button[value='{big_val}']"
    )
    driver.execute_script("arguments[0].click();", big_btn)
    time.sleep(0.8)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".listCategorySub"))
    )
    sub_btn = driver.find_element(
        By.CSS_SELECTOR, f".listCategorySub button[value='{sub_code}']"
    )
    driver.execute_script("arguments[0].click();", sub_btn)
    time.sleep(WAIT_MAP)

# ── 구 선택 ───────────────────────────────────────────────────
def select_gu(driver, gu_value):
    driver.execute_script("""
        document.getElementById('megaSelect').value = '11';
        document.getElementById('megaSelect').dispatchEvent(new Event('change'));
    """)
    time.sleep(1)
    driver.execute_script(f"""
        document.getElementById('ctySelect').value = '{gu_value}';
        document.getElementById('ctySelect').dispatchEvent(new Event('change'));
    """)
    time.sleep(WAIT_MAP)

# ── 날짜 이동 ─────────────────────────────────────────────────
def go_to_date(driver, target_date):
    for _ in range(80):
        cur = driver.find_element(By.CLASS_NAME, "current-date").text
        if cur == target_date:
            return
        # JS로 클릭 (ElementNotInteractableException 방지)
        btn = driver.find_element(By.CSS_SELECTOR, ".prev-btn")
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(0.5)

# ── map 위치 및 body 크기 측정 ───────────────────────────────
def get_map_rect(driver):
    body_w   = driver.execute_script("return document.body.clientWidth")
    body_h   = driver.execute_script("return document.body.clientHeight")
    map_rect = driver.execute_script("""
        var r = document.getElementById('map').getBoundingClientRect();
        return {left:r.left, top:r.top, width:r.width, height:r.height};
    """)
    return body_w, body_h, map_rect

# ── 동별 데이터 → 리스트로 변환 (합산 없이 그대로) ───────────
def flatten_dong_data(dong_data, date, gu_name, industry_name, sub_code):
    rows = []
    for d in dong_data.values():
        rows.append({
            "날짜":       date,
            "자치구":     gu_name,
            "동":         d["동"],
            "업종":       industry_name,
            "업종코드":   sub_code,
            "평균매출액": d["평균매출액"],
            "평균배달건수": d["평균배달건수"],
        })
    return rows

# ── 기존 수집 데이터 로드 (이어서 수집용) ────────────────────
def load_existing(output_file):
    if os.path.exists(output_file):
        df   = pd.read_csv(output_file, encoding="utf-8-sig")
        # 날짜+업종 조합 (업종 skip용)
        done = set(zip(df["날짜"], df["업종"]))
        # 날짜+업종+동 조합 (중복 방지용)
        done_dong = set(zip(df["날짜"], df["업종"], df["동"]))
        # 날짜+업종별 수집된 동 수
        dong_counts = df.groupby(["날짜", "업종"])["동"].count().to_dict()
        print(f"기존 데이터 {len(df)}행 로드 | 완료 조합 {len(done)}개")
        return df.to_dict("records"), done, dong_counts, done_dong
    return [], set(), {}, set()

# ── CSV 저장 ──────────────────────────────────────────────────
def save_csv(all_results, output_file):
    pd.DataFrame(all_results).to_csv(
        output_file, index=False, encoding="utf-8-sig"
    )
