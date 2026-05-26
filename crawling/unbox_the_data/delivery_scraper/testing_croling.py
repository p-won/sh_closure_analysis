# ============================================================
# test_gu.py
# 구별 최적 설정 테스트 (zoom, 격자 확인용)
# 사용법: 아래 5줄만 바꿔서 실행
# ============================================================

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from crawler_utils import select_gu, get_map_rect, collect_dong_data
import time

# ── 여기만 수정 ───────────────────────────────────────────────
GU_NAME  = "송파구"
GU_VALUE = "1171"
COLS     = 13
ROWS     = 15
USE_ZOOM = False

# ── 브라우저 시작 ─────────────────────────────────────────────
service = Service(ChromeDriverManager().install())
driver  = webdriver.Chrome(service=service)
driver.maximize_window()
driver.get("https://bigdata.sbiz.or.kr/#/gis/delivery")
time.sleep(8)

iframes = WebDriverWait(driver, 20).until(
    EC.presence_of_all_elements_located((By.TAG_NAME, "iframe"))
)
driver.switch_to.frame(iframes[0])
WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.ID, "map"))
)
print("로딩 완료")

# ── 구 선택 ───────────────────────────────────────────────────
select_gu(driver, GU_VALUE)
print(f"{GU_NAME} 선택 완료")

# ── 업종 선택 (한식 > 곱창전골/구이) ─────────────────────────
big_btn = driver.find_element(By.CSS_SELECTOR, ".listCategory button[value='0']")
driver.execute_script("arguments[0].click();", big_btn)
time.sleep(0.8)
sub_btn = driver.find_element(By.CSS_SELECTOR, ".listCategorySub button[value='I20109']")
driver.execute_script("arguments[0].click();", sub_btn)
time.sleep(3)
print("업종 선택 완료")

# ── zoom ──────────────────────────────────────────────────────
if USE_ZOOM:
    map_el = driver.find_element(By.ID, "map")
    ActionChains(driver)\
        .scroll_from_origin(ScrollOrigin.from_element(map_el), 0, -300)\
        .perform()
    time.sleep(2)
    print("zoom 완료")

# ── body/map 크기 측정 ────────────────────────────────────────
body_w, body_h, map_rect = get_map_rect(driver)

# ── bbox 가져오기 ─────────────────────────────────────────────
bbox = driver.execute_script("""
    var paths = document.querySelectorAll('#map svg path');
    if (!paths.length) return null;
    var minX = Infinity, minY = Infinity;
    var maxX = -Infinity, maxY = -Infinity;
    paths.forEach(function(p) {
        var r = p.getBoundingClientRect();
        if (r.width === 0 || r.height === 0) return;
        minX = Math.min(minX, r.left);
        minY = Math.min(minY, r.top);
        maxX = Math.max(maxX, r.right);
        maxY = Math.max(maxY, r.bottom);
    });
    return {minX: minX, minY: minY, maxX: maxX, maxY: maxY};
""")
print(f"구역 bbox: {bbox}")

# ── 격자 탐색 ─────────────────────────────────────────────────
print(f"\n격자 탐색 시작 ({COLS}x{ROWS})...")
start     = time.time()
dong_data = collect_dong_data(driver, body_w, body_h, map_rect, COLS, ROWS, bbox)
elapsed   = time.time() - start

# ── 격자 포인트 시각화 (iframe 안에서 그리기) ─────────────────
driver.execute_script("""
    var body   = document.body;
    var canvas = document.createElement('canvas');
    canvas.style.position      = 'fixed';
    canvas.style.top           = '0';
    canvas.style.left          = '0';
    canvas.style.zIndex        = '9999';
    canvas.style.pointerEvents = 'none';
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
    body.appendChild(canvas);

    var ctx    = canvas.getContext('2d');
    var cols   = arguments[0];
    var rows   = arguments[1];
    var bbox   = arguments[2];
    var width  = bbox.maxX - bbox.minX;
    var height = bbox.maxY - bbox.minY;

    ctx.strokeStyle = 'blue';
    ctx.lineWidth   = 2;
    ctx.strokeRect(bbox.minX, bbox.minY, width, height);

    for (var r = 0; r < rows; r++) {
        for (var c = 0; c < cols; c++) {
            var x = bbox.minX + width  * (c + 0.5) / cols;
            var y = bbox.minY + height * (r + 0.5) / rows;

            ctx.beginPath();
            ctx.arc(x, y, 5, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(255,0,0,0.7)';
            ctx.fill();

            ctx.fillStyle = 'white';
            ctx.font      = '8px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(r + ',' + c, x, y + 3);
        }
    }
""", COLS, ROWS, bbox)

time.sleep(1)
#
# # ── 스크린샷은 iframe 밖에서 찍기 ────────────────────────────
# driver.switch_to.default_content()
# screenshot_path = f"C:/Users/SUJIS/unbox_the_data/delivery_scraper/preview_png/test_{GU_NAME}_{COLS}x{ROWS}_zoom{'O' if USE_ZOOM else 'X'}.png"
# driver.save_screenshot(screenshot_path)
# print(f"격자 포인트 스크린샷 저장: {screenshot_path}")

# ── 결과 출력 ─────────────────────────────────────────────────
print(f"\n{'='*40}")
print(f"구: {GU_NAME} | 격자: {COLS}x{ROWS} | zoom: {'O' if USE_ZOOM else 'X'}")
print(f"수집 동: {len(dong_data)}개 | 소요시간: {elapsed:.1f}초")
print(f"{'='*40}")
for d in dong_data.values():
    print(f"  {d['동']}")

input("\n확인 후 엔터...")
driver.quit()