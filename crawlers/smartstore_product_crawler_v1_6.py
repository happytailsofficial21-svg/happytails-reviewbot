"""
스마트스토어 상품 목록 크롤러 v1_6
- 전체 상품 URL, 상품명, 상품번호 수집
- 주간 실행하여 신상품 감지
- CSV로 저장 (날짜 + 버전 파일명)

v1_5 → v1_6 변경사항:
- 상품명 있는 링크 우선 저장 (중복 상품 처리 개선)
- 프로모션 배너 링크보다 상품 카드 링크 우선
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import json
from datetime import datetime
import os
import glob

# ============== 설정 ==============
STORE_URL = "https://brand.naver.com/happytails"
OUTPUT_DIR = "./"
# ==================================


def setup_driver():
    """크롬 드라이버 설정"""
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    })
    return driver


def get_output_filename(prefix, ext):
    """날짜 + 버전 기반 파일명 생성"""
    date_str = datetime.now().strftime("%y%m%d")
    base_pattern = f"{prefix}_{date_str}"
    
    existing_files = glob.glob(os.path.join(OUTPUT_DIR, f"{base_pattern}*.{ext}"))
    
    if not existing_files:
        return f"{base_pattern}.{ext}"
    else:
        versions = []
        for f in existing_files:
            fname = os.path.basename(f)
            if fname == f"{base_pattern}.{ext}":
                versions.append(1)
            else:
                try:
                    ver_part = fname.replace(f"{base_pattern}_", "").replace(f".{ext}", "")
                    versions.append(int(ver_part))
                except:
                    pass
        
        next_version = max(versions) + 1
        return f"{base_pattern}_{next_version}.{ext}"


def scroll_to_bottom(driver, max_scrolls=20):
    """페이지 끝까지 스크롤"""
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_count = 0
    
    while scroll_count < max_scrolls:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        scroll_count += 1
        print(f"    스크롤 {scroll_count}회...")
    
    return scroll_count


def save_html(driver, filename):
    """HTML 저장"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"    ✓ HTML 저장: {filename}")


def crawl_products(driver, url):
    """상품 목록 크롤링"""
    print(f"[1] 페이지 접속: {url}")
    driver.get(url)
    time.sleep(4)
    
    print("[2] 전체 상품 로딩 중 (스크롤)...")
    scroll_to_bottom(driver)
    
    # HTML 저장 (분석용)
    html_filename = get_output_filename("store_page", "html")
    save_html(driver, html_filename)
    
    print("[3] 상품 정보 추출 중...")
    products = []
    
    # 상품 링크 찾기
    product_links = []
    all_links = driver.find_elements(By.TAG_NAME, "a")
    product_links = [a for a in all_links if "/products/" in (a.get_attribute("href") or "")]
    print(f"    → {len(product_links)}개 상품 링크 발견")
    
    # v1_6: 상품명 있는 링크 우선 저장 (dict로 관리)
    products_dict = {}
    
    for link in product_links:
        try:
            href = link.get_attribute("href")
            if not href or "/products/" not in href:
                continue
            
            product_id = href.split("/products/")[-1].split("?")[0].split("/")[0]
            
            if not product_id.isdigit():
                continue
            
            product_name = ""
            
            # v1_5: data-shp-contents-dtl 속성에서 상품명 추출 (가장 정확)
            try:
                dtl_attr = link.get_attribute("data-shp-contents-dtl")
                if dtl_attr:
                    dtl_data = json.loads(dtl_attr)
                    for item in dtl_data:
                        if item.get("key") == "chnl_prod_nm":
                            product_name = item.get("value", "").strip()
                            break
            except:
                pass
            
            # 폴백 1: strong 태그
            if not product_name:
                try:
                    name_elem = link.find_element(By.CSS_SELECTOR, "strong.xSW7C99vO3")
                    product_name = name_elem.text.strip()
                except:
                    try:
                        name_elem = link.find_element(By.TAG_NAME, "strong")
                        product_name = name_elem.text.strip()
                    except:
                        pass
            
            # 폴백 2: 링크 텍스트
            if not product_name:
                try:
                    product_name = link.text.strip()[:80]
                except:
                    product_name = ""
            
            # "상품 바로가기", "품절" 같은 잘못된 텍스트 제거
            if product_name in ["상품 바로가기", "품절", ""]:
                product_name = ""
            
            # v1_6: 이미 있는 상품이면 상품명 있는 것으로 업데이트
            if product_id in products_dict:
                if product_name and not products_dict[product_id]["product_name"]:
                    products_dict[product_id]["product_name"] = product_name
            else:
                products_dict[product_id] = {
                    "product_id": product_id,
                    "product_name": product_name,
                    "url": f"https://brand.naver.com/happytails/products/{product_id}",
                }
            
        except Exception as e:
            continue
    
    # dict → list 변환
    products = list(products_dict.values())
    
    print(f"    ✓ 총 {len(products)}개 상품 추출 완료")
    
    # 상품명 누락 통계
    missing_names = sum(1 for p in products if not p["product_name"])
    if missing_names > 0:
        print(f"    ⚠ 상품명 누락: {missing_names}개 (HTML 분석 필요)")
    
    return products, html_filename


def load_previous_products(filepath):
    """이전 상품 목록 로드"""
    if not os.path.exists(filepath):
        return []
    
    products = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append(row)
    return products


def compare_products(current, previous):
    """신상품 감지"""
    prev_ids = {p["product_id"] for p in previous}
    new_products = [p for p in current if p["product_id"] not in prev_ids]
    removed_products = [p for p in previous if p["product_id"] not in {c["product_id"] for c in current}]
    return new_products, removed_products


def save_products(products, filepath):
    """상품 목록 CSV 저장"""
    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["product_id", "product_name", "url", "crawled_at"])
        writer.writeheader()
        
        crawled_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        for p in products:
            p["crawled_at"] = crawled_at
            writer.writerow(p)


def main():
    csv_filename = get_output_filename("products_list", "csv")
    
    print("=" * 60)
    print("해피테일즈 스마트스토어 상품 목록 크롤러 v1_6")
    print(f"실행일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    driver = setup_driver()
    
    try:
        products, html_filename = crawl_products(driver, STORE_URL)
        
        if not products:
            print("\n⚠ 상품을 찾지 못했습니다.")
            return
        
        # 이전 데이터와 비교
        prev_files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith("products_list_") and f.endswith(".csv")]
        previous = []
        if prev_files:
            prev_files.sort(reverse=True)
            for pf in prev_files:
                if pf != csv_filename:
                    previous = load_previous_products(os.path.join(OUTPUT_DIR, pf))
                    break
        
        if previous:
            new_products, removed_products = compare_products(products, previous)
            
            print("\n" + "=" * 60)
            print("📊 변동 사항")
            print("=" * 60)
            print(f"이전: {len(previous)}개 → 현재: {len(products)}개")
            
            if new_products:
                print(f"\n🆕 신상품 {len(new_products)}개!")
                for p in new_products:
                    print(f"   - [{p['product_id']}] {p['product_name'] or '(상품명 없음)'}")
            
            if removed_products:
                print(f"\n❌ 삭제 {len(removed_products)}개")
                for p in removed_products:
                    print(f"   - [{p['product_id']}] {p.get('product_name', '')}")
        
        # 저장
        save_products(products, csv_filename)
        
        # 상품명 누락 체크
        missing_names = sum(1 for p in products if not p["product_name"])
        
        # ========== 결과 ==========
        print("\n" + "=" * 60)
        print("✅ 크롤링 완료!")
        print("=" * 60)
        print(f"📦 총 상품: {len(products)}개")
        print(f"📁 CSV: {csv_filename}")
        print(f"📁 HTML: {html_filename}")
        
        if missing_names > 0:
            print(f"\n⚠ 상품명 누락 {missing_names}개")
            print(f"   → HTML 파일도 함께 클로드에게 전달하세요!")
        
        print("\n")
        print("🔔 " * 15)
        print("")
        if missing_names > 0:
            print(f"  👉 '{csv_filename}' 와")
            print(f"     '{html_filename}' 를")
            print(f"     클로드에게 전달하세요!")
        else:
            print(f"  👉 '{csv_filename}' 파일을")
            print(f"     클로드에게 전달하세요!")
        print("")
        print("🔔 " * 15)
        
    finally:
        input("\n엔터를 누르면 브라우저 종료...")
        driver.quit()


if __name__ == "__main__":
    main()
