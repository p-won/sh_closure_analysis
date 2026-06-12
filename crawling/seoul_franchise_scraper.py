"""
서울시 외식업 프랜차이즈 비율 수집기
- 기간: 2019년 1분기 ~ 2023년 4분기
- 조건: 외식업 / 전체 / 조회분기=동분기
- 특징: 동분기 검색으로 한 번에 3개 연도 수집 → 총 8번 검색

실행: python seoul_franchise_scraper.py
"""

import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

URL = "https://golmok.seoul.go.kr/stateArea.do"

# 동분기 검색: 기준년 검색 시 → [기준-2년, 기준-1년, 기준년] 순서로 컬럼 출력
# td[2,3]=기준-2년 / td[5,6]=기준-1년 / td[8,9]=기준년
SEARCH_PLAN = [
    ("2025", "1", ["2023", "2024", "2025"]),
    ("2025", "2", ["2023", "2024", "2025"]),
    ("2025", "3", ["2023", "2024", "2025"]),
    ("2025", "4", ["2023", "2024", "2025"]),
    ("2022", "1", ["2020", "2021", "2022"]),
    ("2022", "2", ["2020", "2021", "2022"]),
    ("2022", "3", ["2020", "2021", "2022"]),
    ("2022", "4", ["2020", "2021", "2022"]),
    ("2020", "1", ["2018", "2019", "2020"]),  # 2018 제외
    ("2020", "2", ["2018", "2019", "2020"]),
    ("2020", "3", ["2018", "2019", "2020"]),
    ("2020", "4", ["2018", "2019", "2020"]),
]
TARGET_YEARS = {"2019", "2020", "2021", "2022", "2023", "2024", "2025"}


def get_driver():
    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )


def wait_click(driver, by, sel, timeout=15):
    el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, sel)))
    driver.execute_script("arguments[0].click();", el)


def wait_select(driver, el_id, value, timeout=15):
    def option_available(d):
        try:
            opts = [o.get_attribute("value")
                    for o in Select(d.find_element(By.ID, el_id)).options]
            return value in opts
        except Exception:
            return False
    WebDriverWait(driver, timeout).until(option_available)
    Select(driver.find_element(By.ID, el_id)).select_by_value(value)


def get_first_cell_text(driver):
    """현재 테이블 첫 번째 데이터 td[2] 값 반환 (변경 감지용)"""
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        space = soup.find(id="tableSpace")
        if not space:
            return ""
        rows = space.find_all("tr", attrs={"data-tt-parent-id": "1"})
        if not rows:
            return ""
        cells = rows[0].find_all("td")
        return cells[2].get_text(strip=True) if len(cells) > 2 else ""
    except Exception:
        return ""


def wait_table_refresh(driver, prev_value, timeout=30):
    """
    검색 후 테이블이 실제로 새 데이터로 바뀔 때까지 대기.
    이전 첫 번째 셀 값과 달라지는 순간 통과.
    """
    def is_refreshed(d):
        try:
            space = d.find_element(By.ID, "tableSpace")
            rows = space.find_elements(By.XPATH, ".//tr[@data-tt-parent-id='1']")
            if not rows:
                return False
            # 첫 번째 자치구 행의 td[2] 값이 이전과 달라졌는지 확인
            cells = rows[0].find_elements(By.TAG_NAME, "td")
            if len(cells) < 3:
                return False
            current = cells[2].text.strip().replace(",", "")
            prev = prev_value.replace(",", "")
            return current != prev and current != ""
        except Exception:
            return False

    WebDriverWait(driver, timeout).until(is_refreshed)


def wait_table_load(driver, timeout=30):
    """최초 테이블 로딩 대기"""
    def has_rows(d):
        try:
            space = d.find_element(By.ID, "tableSpace")
            return len(space.find_elements(
                By.XPATH, ".//tr[@data-tt-parent-id='1']")) > 0
        except Exception:
            return False
    WebDriverWait(driver, timeout).until(has_rows)


def parse(driver, quarter, years):
    """
    동분기 컬럼 구조:
      td[0]=지역명, td[1]=업종
      td[2,3,4] = 기준-2년 (전체, 프랜차이즈, 일반)
      td[5,6,7] = 기준-1년
      td[8,9,10]= 기준년
    years = [기준-2년, 기준-1년, 기준년]
    """
    soup = BeautifulSoup(driver.page_source, "html.parser")
    space = soup.find(id="tableSpace")
    if not space:
        print("    ❌ tableSpace 없음")
        return []

    rows = space.find_all("tr", attrs={"data-tt-parent-id": "1"})
    if not rows:
        print("    ❌ 자치구 행 없음")
        return []

    col_map = {
        years[0]: (2, 3),   # 기준-2년: td[2]=전체, td[3]=프랜차이즈
        years[1]: (5, 6),   # 기준-1년
        years[2]: (8, 9),   # 기준년
    }

    def to_int(cell):
        t = cell.get_text(strip=True).replace(",", "")
        return int(t) if t.isdigit() else 0

    records = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 11:
            continue
        addr = cells[0]
        for tag in addr.find_all(["span", "a"]):
            tag.decompose()
        district = addr.get_text(strip=True)
        if not district or "서울시" in district:
            continue

        for year, (ci_t, ci_f) in col_map.items():
            if year not in TARGET_YEARS:
                continue
            total     = to_int(cells[ci_t])
            franchise = to_int(cells[ci_f])
            records.append({
                "연도":               year,
                "분기":               f"{quarter}분기",
                "자치구":             district,
                "전체_점포수":        total,
                "프랜차이즈_점포수":  franchise,
                "프랜차이즈_비율(%)": round(franchise / total * 100, 2) if total else 0,
            })
    return records


def main():
    driver = get_driver()
    all_records = []

    try:
        t0 = time.time()

        # 초기 설정
        driver.get(URL)
        wait_click(driver, By.CSS_SELECTOR, "button.store")
        print(f"✔ 점포수 탭 클릭 ({time.time()-t0:.1f}s)")

        wait_select(driver, "induL", "CS100000")   # 외식업
        wait_select(driver, "induM", "all")         # 전체
        wait_select(driver, "selectQuCondition", "sameQu")  # 동분기 고정
        print(f"✔ 고정 조건 설정 완료")

        for i, (base_year, quarter, years) in enumerate(SEARCH_PLAN):
            print(f"\n  [{i+1}/8] 기준 {base_year}년 {quarter}분기 → 수집: {[y for y in years if y in TARGET_YEARS]}")

            # 검색 전 현재 테이블 첫 셀 값 저장 (변경 감지용)
            prev_val = get_first_cell_text(driver) if i > 0 else "0"

            wait_select(driver, "selectYear", base_year)
            wait_select(driver, "selectQu", quarter)
            wait_click(driver, By.ID, "presentSearch")

            # 첫 검색은 단순 로딩 대기, 이후는 값 변경 감지
            if i == 0:
                wait_table_load(driver)
            else:
                wait_table_refresh(driver, prev_val)

            print(f"    ✔ 테이블 갱신 확인 ({time.time()-t0:.1f}s)")

            records = parse(driver, quarter, years)
            if records:
                all_records.extend(records)
                for year in [y for y in years if y in TARGET_YEARS]:
                    cnt = sum(1 for r in records if r["연도"] == year)
                    print(f"    ✔ {year}년 {quarter}분기: {cnt}개 자치구")
            else:
                print(f"    ❌ 파싱 실패")

    except Exception as e:
        print(f"\n❌ 오류: {e}")
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("page_source.html 저장")

    finally:
        driver.quit()

    if not all_records:
        print("\n⚠ 수집된 데이터 없음")
        return

    df = pd.DataFrame(all_records)
    df = df.sort_values(["연도", "분기", "자치구"]).reset_index(drop=True)

    # 수집 현황 요약
    print(f"\n✅ 총 {len(df)}개 레코드")
    summary = df.groupby(["연도", "분기"])["자치구"].count().reset_index()
    summary.columns = ["연도", "분기", "자치구수"]
    print(summary.to_string(index=False))

    # 저장
    out_path = "../data/raw data/seoul_franchise_ratio.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n✔ {out_path} 저장 완료")

if __name__ == "__main__":
    main()