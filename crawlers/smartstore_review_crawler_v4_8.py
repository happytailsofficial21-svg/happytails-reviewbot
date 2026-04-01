"""
ìŠ¤ë§ˆíŠ¸ìŠ¤í† ì–´ ë¦¬ë·° í¬ë¡¤ëŸ¬ v4.8 (ë‹µë³€ DBìš©)
- ë‹µê¸€ ìžˆëŠ” ë¦¬ë·°ë§Œ ì €ìž¥ (íŒ¨í„´ í•™ìŠµìš©)
- ìƒì„¸ ë””ë²„ê·¸ ë¡œê·¸ íŒŒì¼ ì €ìž¥

v4.7 â†’ v4.8 ë³€ê²½ì‚¬í•­:
- ë”œë ˆì´ ì¦ê°€ (2ì´ˆ â†’ 4ì´ˆ)
- ëžœë¤ ë”œë ˆì´ ì¶”ê°€ (ë´‡ ê°ì§€ ìš°íšŒ)
- ì—°ê²° ëŠê¹€ ì‹œ ìž¬ì‹œë„ ë¡œì§
- 100ì—°ì† 0ê°œê¹Œì§€ íƒìƒ‰ (ë’¤ìª½ ë‹µê¸€ ë†“ì¹˜ì§€ ì•Šê²Œ)

v4.8 - 2026.01.07
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import re
from datetime import datetime
import os
import glob
import traceback
import logging
import random

# ============== ì„¤ì • ==============
STORE_URL = "https://brand.naver.com/happytails"
OUTPUT_DIR = "./"
SAVE_INTERVAL = 5
PAGE_DELAY = 4  # íŽ˜ì´ì§€ ê°„ ë”œë ˆì´ (ì´ˆ) - ë´‡ ê°ì§€ ìš°íšŒ
RANDOM_DELAY = (1, 3)  # ì¶”ê°€ ëžœë¤ ë”œë ˆì´ ë²”ìœ„
MAX_NO_NEW = 50  # Nì—°ì† ì‹ ê·œ ì—†ìœ¼ë©´ ì¢…ë£Œ
MAX_RETRIES = 3  # ì—ëŸ¬ ì‹œ ìž¬ì‹œë„ íšŸìˆ˜
# ==================================

# ============== ë¡œê¹… ì„¤ì • ==============
LOG_FILENAME = f"crawler_{datetime.now().strftime('%y%m%d_%H%M%S')}.log"

# ë¡œê±° ìƒì„±
logger = logging.getLogger("ReviewCrawler")
logger.setLevel(logging.DEBUG)

# íŒŒì¼ í•¸ë“¤ëŸ¬ (ìƒì„¸ ë¡œê·¸)
file_handler = logging.FileHandler(LOG_FILENAME, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_format = logging.Formatter('%(asctime)s [%(levelname)s] %(funcName)s:%(lineno)d - %(message)s')
file_handler.setFormatter(file_format)

# ì½˜ì†” í•¸ë“¤ëŸ¬ (ìš”ì•½ë§Œ)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_format = logging.Formatter('%(message)s')
console_handler.setFormatter(console_format)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
# ======================================

def save_html_snapshot(driver, name):
    """HTML ìŠ¤ëƒ…ìƒ· ì €ìž¥"""
    filename = f"snapshot_{name}_{datetime.now().strftime('%H%M%S')}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    logger.debug(f"HTML ìŠ¤ëƒ…ìƒ· ì €ìž¥: {filename}")
    return filename


def random_sleep():
    """ë´‡ ê°ì§€ ìš°íšŒìš© ëžœë¤ ë”œë ˆì´"""
    delay = PAGE_DELAY + random.uniform(RANDOM_DELAY[0], RANDOM_DELAY[1])
    logger.debug(f"ë”œë ˆì´: {delay:.1f}ì´ˆ")
    time.sleep(delay)

# ìƒí’ˆ ëª©ë¡ - ì „ì²´ 52ê°œ (ë°”ë””í•„ë¡œìš° ë¨¼ì €)
PRODUCTS = [
    # ë°”ë””í•„ë¡œìš° (ë¦¬ë·° ë§ŽìŒ)
    {"id": "529282963", "name": "ìž„ì‚°ë¶€ ë°”ë””í•„ë¡œìš° ìž„ì‹ ì¶•í•˜ì„ ë¬¼ AirTex í—ˆë¦¬í†µì¦"},
    {"id": "11645004131", "name": "í”„ë¦¬ë¯¸ì—„ ë…¸ë¸”ë ˆìŠ¤í‹°ì–´ ìž„ì‚°ë¶€ (í­ì¡°ì ˆ) ë°”ë””í•„ë¡œìš° 100ìˆ˜"},
    # ë‚˜ë¨¸ì§€
    {"id": "12664700142", "name": "ê³°ëŒì´ ì›ëª© ì˜·ê±¸ì´"},
    {"id": "12664661643", "name": "ê³°ëŒì´ ë¨¸ë¦¬í•€"},
    {"id": "12629305526", "name": "ê³°ëŒì´ ìœ ëª¨ì°¨ ê°€ë°© ê±¸ì´"},
    {"id": "11676656818", "name": "ë°©ìˆ˜ ë³„ ì‹¤ë¦¬ì½˜ ë©€í‹° ìˆ˜ë‚© ì¼€ì´ìŠ¤"},
    {"id": "5672588938", "name": "ë¬¸ ë‹«íž˜ ë°©ì§€ ì¸í˜•"},
    {"id": "9908173752", "name": "ì¿¨ë¦¬ë² ì–´ ì¶”ê°€ì»¤ë²„"},
    {"id": "5612673824", "name": "ì¿¨ë¦¬ ë² ê°œ ìžìˆ˜ ì»¤ë²„"},
    {"id": "12422865666", "name": "ì‹ì²¨ë“±ê¸‰ ì•ŒëŸ¬ì§€ì œë¡œ ì£¼ë°©ì„¸ì œ ê²¸ìš© ì –ë³‘ì„¸ì œ ë¦¬í•„íŒ© 500ml"},
    {"id": "5497784807", "name": "ë°”ë””í•„ë¡œìš° ì¼ìží˜• ëª¨ë…¸ ì»¤ë²„"},
    {"id": "2555982942", "name": "ìž„ì‚°ë¶€ ë°”ë””í•„ë¡œìš° ì»¤ë²„ ë‹¨í’ˆ ì œí’ˆ"},
    {"id": "6315631037", "name": "ìž„ì‚°ë¶€ ë°”ë””í•„ë¡œìš° ê°€ë°©"},
    {"id": "12651036747", "name": "ë² ì´ë¹„ìˆ˜íŠ¸ ìŠ¤í‚¨ì¼€ì–´ 2ì¢… ì„ ë¬¼ì„¸íŠ¸"},
    {"id": "12010805364", "name": "ìžê¸°ì£¼ë„ ì•„ê¸° ì‹¤ë¦¬ì½˜ í…Œì´ë¸” ë§¤íŠ¸"},
    {"id": "8240676662", "name": "2in1 ìœ ëª¨ì°¨ ì»µí™€ë” í…€ë¸”ëŸ¬í™€ë” íœ´ëŒ€í° ê±°ì¹˜ëŒ€"},
    {"id": "5854635220", "name": "ì•„ê¸° ì‹ ìƒì•„ ì†í†±ê¹Žì´ ê°€ìœ„ ì†í†±ìžë¥´ê¸°"},
    {"id": "5720116230", "name": "ì‹¤ë¦¬ì½˜ ì –ë³‘ì†” ì„¸ì²™ ë¸ŒëŸ¬ì‰¬ ì„¸íŠ¸"},
    {"id": "6930122966", "name": "ëª¨ëž˜ë†€ì´ ì„¸íŠ¸ ì‹¤ë¦¬ì½˜ ìž¥ë‚œê° ì•„ê¸° ë¬¼ë†€ì´ BPA FREE"},
    {"id": "12580013764", "name": "í•˜í”¼ ë³´ë³´ ë² ì´ë¹„ ìˆ˜íŠ¸"},
    {"id": "11672445548", "name": "ìžê¸°ì£¼ë„ ì¼ì²´í˜• í„±ë°›ì´ ì•„ê¸° ì´ìœ ì‹ ê°€ìš´ ë°©ìˆ˜"},
    {"id": "5598629901", "name": "ì•„ê¸° ì¿¨ë§¤íŠ¸ ì§ˆì‹ì˜ˆë°© ì•ˆì „íŒ¨ë“œ ì¸ê²¬ ë©”ì‰¬ ì‹ ìƒì•„ ì´ë¶ˆ"},
    {"id": "11605240901", "name": "ì•„ì¿ ì•„GG 2x ê³ ë†ì¶• ìˆ˜ë¶„ ì§„ì • ë²„ë¸”í† ë„ˆ 150ml"},
    {"id": "5712725509", "name": "ì•ŒëŸ¬ì§€ì œë¡œ ê°ˆë½ì†Œë¼ì´ë“œFree ê±´ì¡°ê¸°ì‹œíŠ¸ (40pcs)"},
    {"id": "12611696945", "name": "ì‹ì²¨ë“±ê¸‰ ì•ŒëŸ¬ì§€ì œë¡œ ì£¼ë°©ì„¸ì œ ê²¸ìš© ì –ë³‘ì„¸ì œ ë³¸í’ˆ + ë¦¬í•„íŒ© SET"},
    {"id": "8247877329", "name": "ì‹ì²¨ë“±ê¸‰ ì•ŒëŸ¬ì§€ì œë¡œ ì‹ê¸°ì„¸ì²™ê¸° ì –ë³‘ì„¸ì œ 600ml"},
    {"id": "8674917685", "name": "ì‹ì²¨ë“±ê¸‰ ì•ŒëŸ¬ì§€ì œë¡œ ì£¼ë°©ì„¸ì œ ê²¸ìš© ì –ë³‘ì„¸ì œ"},
    {"id": "10194058228", "name": "ì‹ì²¨ë“±ê¸‰ ì•ŒëŸ¬ì§€ì œë¡œ ì„¸íƒì„¸ì œ ìœ ì•„ê²¸ìš© 1L"},
    {"id": "12764535051", "name": "íŒŒìš°ë”ë¦¬ í”¼ë‹ˆì‰¬ ë² ì´ë¹„ ìˆ˜ë”©ì ¤ 150ml 2ê°œ SET"},
    {"id": "12764537589", "name": "íŒŒìš°ë”ë¦¬ í”¼ë‹ˆì‰¬ ë² ì´ë¹„ ìˆ˜ë”©ì ¤ 150ml 3ê°œ SET"},
    {"id": "12579700028", "name": "íŒŒìš°ë”ë¦¬ í”¼ë‹ˆì‰¬ ë² ì´ë¹„ ìˆ˜ë”©ì ¤ 150ml"},
    {"id": "12651670173", "name": "ë² ì´ë¹„í¬ë¦¼ 2ê°œ SET"},
    {"id": "12664385550", "name": "ë² ì´ë¹„í¬ë¦¼ 3ê°œ SET"},
    {"id": "11692846089", "name": "ì•„ê¸°í¬ë¦¼ ì•„ì¿ ì•„ ë¶ ë² ì´ë¹„í¬ë¦¼ ì—¬í–‰ìš© ì¼íšŒìš© ì„¸íŠ¸ 15ê°œ"},
    {"id": "12664155554", "name": "ë…¸í‘¸ ì˜¤ì¼ë°œíš¨ ìˆœë¹„ëˆ„ 3ê°œ SET ë°”ë””ì›Œì‹œ ë² ì´ë¹„ ìƒ´í‘¸"},
    {"id": "10774237735", "name": "ë…¸í‘¸ ì˜¤ì¼ë°œíš¨ ìˆœë¹„ëˆ„ 300ml ë°”ë””ì›Œì‹œ ë² ì´ë¹„ ìƒ´í‘¸"},
    {"id": "11892200047", "name": "ì•„ê¸°í¬ë¦¼ ì•„ì¿ ì•„ ë¶ + ë°”ìŠ¤ì•¤ìƒ´í‘¸ SET"},
    {"id": "6567813630", "name": "ì•„ê¸°í¬ë¦¼ ìœ ì•„ ì‹ ìƒì•„ ë² ì´ë¹„ ì„±ì¸ ë³´ìŠµí¬ë¦¼ 150ml"},
    {"id": "7911275007", "name": "ì˜†ëˆ•ë² ê°œ ë©”ëª¨ë¦¬í¼ ê²½ì¶”ë² ê°œ ìˆ˜ë©´ ê±°ë¶ëª© ì¼ìžëª© ê¸°ëŠ¥ì„±"},
    {"id": "5763374051", "name": "ì‚¼ê° ë“±ë°›ì´ ì¿ ì…˜ ì‡¼íŒŒ í—ˆë¦¬ ì¹¨ëŒ€ ëŒ€í˜•"},
    {"id": "11433523813", "name": "[3ê°œ ì„¸íŠ¸] êµ­ì‚° ìž„ì‚°ë¶€ ì–‘ë§ ì¡°ë¦¬ì› ë¬´ì••ë°• ë„í†° ì‚°ëª¨"},
    {"id": "5550554478", "name": "ë°ì¼ë¦¬ 3ë¶€ ìž„ì‚°ë¶€ ì†ë°”ì§€ ìž„ë¶€ì†ì˜· ë“œë¡œì¦ˆ"},
    {"id": "5579372576", "name": "ìˆ˜ìœ ë¸Œë¼ ê³¨ì§€ ë˜‘ë”±ì´ ìž„ì‹  ì†ì˜· ìž„ì‚°ë¶€ ë¸Œë¼ë ›"},
    {"id": "5579539983", "name": "ìž„ì‚°ë¶€ ì†ì˜· íŒ¬í‹° ì‚°ëª¨ ì‹¬ë¦¬ìŠ¤ ê³¨ì§€"},
    {"id": "5814413256", "name": "ìž„ì‚°ë¶€ ì•ˆì „ë²¨íŠ¸ ì„ ë¬¼ ìž„ì‹ ì¶•í•˜ ìž„ë¶€ìš©í’ˆ ë§Œì‚­"},
    {"id": "12650749282", "name": "ì‹ ìƒì•„ ì†ì‹¸ê°œ í† ë‹¥ìŠˆíŠ¸(ëª¨ë¡œë°˜ì‚¬ë°©ì§€)"},
    {"id": "10923706558", "name": "ì¶”ê°€ê°€ìŠ´íŒŒì¸  ìŠ¤ì™€ë“¤ íƒœì—´ ì•„ê¸° ëª¨ë¡œë°˜ì‚¬ ë‚˜ë¹„ìž  ìˆ˜ë©´ì¡°ë¼ ì¤‘ë ¥ìŠ¤ì™€ë“¤"},
    {"id": "6502723089", "name": "ìŠ¤ì™€ë“¤ ìŠ¤íŠ¸ëž© í† ë‹¥ ì†ì‹¸ê°œ ì‹ ìƒì•„ ì•„ê¸° ëª¨ë¡œë°˜ì‚¬"},
    {"id": "8283048868", "name": "ì‹ ìƒì•„ ì˜†ìž  ë² ê°œ ì§±êµ¬ ì•„ê¸° ë‘ìƒ íƒœì—´ ë°”ë””í•„ë¡œìš° ëª¨ë¡œë°˜ì‚¬"},
    {"id": "5547701797", "name": "ëª©ë†’ì´ 0cm ì‹ ìƒì•„ ë² ê°œ ì´ˆëƒ‰ë ¥ ì¿¨ë¦¬ ì•„ê¸° ë‘ìƒ íƒœì—´ ì§±êµ¬ ìœ ì•„"},
    {"id": "4841256802", "name": "ì‹ ìƒì•„ ëª¨ë¡œë°˜ì‚¬ ë°©ì§€ í†µìž ì´ë¶ˆ ì½”ì½”í…Œì¼ì¦ˆ ì•„ê¸° íƒœì—´ ì¢ìŒ€ ì¹¨êµ¬"},
    {"id": "10740041004", "name": "ë¶„ë¦¬ìˆ˜ë©´ ì‹ ìƒì•„ ì†ì‹¸ê°œ ëª¨ë¡œë°˜ì‚¬ ì•„ê¸° ìŠ¤íŠ¸ëž© ìŠ¤ì™€ë“¤ ì–‘ë§‰ì£¼ë¨¸ë‹ˆ"},
]


def setup_driver():
    """í¬ë¡¬ ë“œë¼ì´ë²„ ì„¤ì •"""
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
    """ë‚ ì§œ ê¸°ë°˜ íŒŒì¼ëª… ìƒì„±"""
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
        next_version = max(versions) + 1 if versions else 1
        return f"{base_pattern}_{next_version}.{ext}"


def get_total_review_count(driver):
    """ì´ ë¦¬ë·° ìˆ˜ ì¶”ì¶œ"""
    try:
        review_tab = driver.find_element(By.XPATH, "//a[contains(text(), 'ë¦¬ë·°')]")
        tab_text = review_tab.text
        numbers = re.findall(r'[\d,]+', tab_text)
        if numbers:
            return int(numbers[0].replace(',', ''))
    except:
        pass
    return 0


def extract_reviews_with_reply(driver, product_id, product_name):
    """ë‹µê¸€ ìžˆëŠ” ë¦¬ë·°ë§Œ ì¶”ì¶œ (ì •í™•í•œ ì…€ë ‰í„° ì‚¬ìš©)"""
    logger.debug("=" * 50)
    logger.debug("extract_reviews_with_reply ì‹œìž‘")
    reviews = []
    
    # í˜„ìž¬ URL ê¸°ë¡
    current_url = driver.current_url
    logger.debug(f"í˜„ìž¬ URL: {current_url}")
    
    # ì „ì²´ ë¦¬ë·° ì•„ì´í…œ
    review_items = driver.find_elements(By.CSS_SELECTOR, ".PxsZltB5tV")
    logger.debug(f"ì…€ë ‰í„° '.PxsZltB5tV' â†’ {len(review_items)}ê°œ ë°œê²¬")
    
    if len(review_items) == 0:
        logger.warning("ë¦¬ë·° ì•„ì´í…œ 0ê°œ! HTML ìŠ¤ëƒ…ìƒ· ì €ìž¥")
        save_html_snapshot(driver, f"no_reviews_{product_id}")
    
    reply_found_count = 0
    valid_review_count = 0
    
    for idx, item in enumerate(review_items):
        logger.debug(f"--- ë¦¬ë·° #{idx+1}/{len(review_items)} ì²˜ë¦¬ ---")
        try:
            # ë‹µê¸€ ì˜ì—­ í™•ì¸
            reply_elems = item.find_elements(By.CSS_SELECTOR, ".Wsm9me_nCc")
            logger.debug(f"  ì…€ë ‰í„° '.Wsm9me_nCc' â†’ {len(reply_elems)}ê°œ")
            
            if not reply_elems:
                logger.debug(f"  â†’ ë‹µê¸€ ì—†ìŒ, ìŠ¤í‚µ")
                continue
            
            reply_found_count += 1
            logger.debug(f"  â†’ ë‹µê¸€ ì˜ì—­ ë°œê²¬!")
            
            review = {
                "product_id": product_id,
                "product_name": product_name,
                "review_index": idx + 1,
                "username": "",
                "date": "",
                "rating": "",
                "option": "",
                "content": "",
                "reply": "",
                "reply_date": "",
            }
            
            # ë³„ì 
            try:
                rating_elem = item.find_element(By.CSS_SELECTOR, "em.n6zq2yy0KA")
                review["rating"] = rating_elem.text.strip()
                logger.debug(f"  ë³„ì : '{review['rating']}'")
            except Exception as e:
                logger.debug(f"  ë³„ì : ì‹¤íŒ¨ - {type(e).__name__}: {e}")
            
            # ìž‘ì„±ìž
            try:
                username_elem = item.find_element(By.CSS_SELECTOR, ".Db9Dtnf7gY strong.MX91DFZo2F")
                review["username"] = username_elem.text.strip()
                logger.debug(f"  ìž‘ì„±ìž: '{review['username']}'")
            except Exception as e:
                logger.debug(f"  ìž‘ì„±ìž: ì‹¤íŒ¨ - {type(e).__name__}: {e}")
            
            # ë‚ ì§œ
            try:
                date_elem = item.find_element(By.CSS_SELECTOR, ".Db9Dtnf7gY span.MX91DFZo2F")
                review["date"] = date_elem.text.strip()
                logger.debug(f"  ë‚ ì§œ: '{review['date']}'")
            except Exception as e:
                logger.debug(f"  ë‚ ì§œ: ì‹¤íŒ¨ - {type(e).__name__}: {e}")
            
            # ì˜µì…˜
            try:
                option_elem = item.find_element(By.CSS_SELECTOR, ".b_caIle8kC")
                option_text = option_elem.text.split('\n')[0].strip()
                review["option"] = option_text
                logger.debug(f"  ì˜µì…˜: '{review['option'][:50]}'")
            except Exception as e:
                logger.debug(f"  ì˜µì…˜: ì‹¤íŒ¨ - {type(e).__name__}: {e}")
            
            # ë¦¬ë·° ë‚´ìš©
            try:
                content_elem = item.find_element(By.CSS_SELECTOR, ".KqJ8Qqw082 span.MX91DFZo2F")
                review["content"] = content_elem.text.strip()
                logger.debug(f"  ë‚´ìš©: '{review['content'][:50]}...' (len={len(review['content'])})")
            except Exception as e:
                logger.debug(f"  ë‚´ìš©: ì‹¤íŒ¨ - {type(e).__name__}: {e}")
            
            # ë‹µê¸€ ë‚´ìš©
            try:
                reply_content = reply_elems[0].find_element(By.CSS_SELECTOR, "p.gF203kDj_q")
                review["reply"] = reply_content.text.strip()
                logger.debug(f"  ë‹µê¸€: '{review['reply'][:50]}...' (len={len(review['reply'])})")
            except Exception as e1:
                logger.debug(f"  ë‹µê¸€(p.gF203kDj_q): ì‹¤íŒ¨ - {type(e1).__name__}: {e1}")
                # í´ë°±
                try:
                    reply_text = reply_elems[0].text
                    logger.debug(f"  ë‹µê¸€(í´ë°±) ì›ë³¸: '{reply_text[:100]}...'")
                    reply_text = re.sub(r'^íŒë§¤ìž\s*', '', reply_text)
                    reply_text = re.sub(r'\d{2}\.\d{2}\.\d{2}\.?\s*', '', reply_text, count=1)
                    reply_text = re.sub(r'ì‹ ê³ \s*', '', reply_text)
                    reply_text = re.sub(r'ë”ë³´ê¸°\s*$', '', reply_text)
                    review["reply"] = reply_text.strip()
                    logger.debug(f"  ë‹µê¸€(í´ë°±) ì •ì œ: '{review['reply'][:50]}...'")
                except Exception as e2:
                    logger.debug(f"  ë‹µê¸€(í´ë°±): ì‹¤íŒ¨ - {type(e2).__name__}: {e2}")
            
            # ë‹µê¸€ ë‚ ì§œ
            try:
                reply_date_elem = reply_elems[0].find_element(By.CSS_SELECTOR, "span.zi5UNys_9u")
                date_text = reply_date_elem.text.strip()
                logger.debug(f"  ë‹µê¸€ë‚ ì§œ ì›ë³¸: '{date_text}'")
                if re.match(r'\d{2}\.\d{2}\.\d{2}', date_text):
                    review["reply_date"] = date_text
                else:
                    spans = reply_elems[0].find_elements(By.CSS_SELECTOR, "span.zi5UNys_9u")
                    logger.debug(f"  ë‹µê¸€ë‚ ì§œ span ê°œìˆ˜: {len(spans)}")
                    for span in spans:
                        if re.match(r'\d{2}\.\d{2}\.\d{2}', span.text.strip()):
                            review["reply_date"] = span.text.strip()
                            break
                logger.debug(f"  ë‹µê¸€ë‚ ì§œ: '{review['reply_date']}'")
            except Exception as e:
                logger.debug(f"  ë‹µê¸€ë‚ ì§œ: ì‹¤íŒ¨ - {type(e).__name__}: {e}")
            
            # ìœ íš¨ì„± ì²´í¬
            has_content = bool(review["content"])
            has_reply = bool(review["reply"])
            logger.debug(f"  ìœ íš¨ì„±: content={has_content}, reply={has_reply}")
            
            if has_content and has_reply:
                reviews.append(review)
                valid_review_count += 1
                logger.debug(f"  â†’ âœ“ ì¶”ê°€ë¨!")
            else:
                logger.debug(f"  â†’ âœ— ë¬´íš¨ (content ë˜ëŠ” reply ì—†ìŒ)")
                
        except Exception as e:
            logger.error(f"  ë¦¬ë·° #{idx+1} ì²˜ë¦¬ ì¤‘ ì—ëŸ¬: {e}")
            logger.error(traceback.format_exc())
            continue
    
    logger.debug(f"ì¶”ì¶œ ì™„ë£Œ: ì „ì²´ {len(review_items)}ê°œ â†’ ë‹µê¸€ìžˆìŒ {reply_found_count}ê°œ â†’ ìœ íš¨ {valid_review_count}ê°œ")
    return reviews


def crawl_all_pages(driver, product_id, product_name, total_reviews):
    """íŽ˜ì´ì§€ë„¤ì´ì…˜ìœ¼ë¡œ ì „ì²´ ë¦¬ë·° í¬ë¡¤ë§ (ë‹µê¸€ ìžˆëŠ” ê²ƒë§Œ)"""
    logger.info(f"  í¬ë¡¤ë§ ì‹œìž‘: product_id={product_id}")
    logger.debug(f"ì´ ë¦¬ë·° ìˆ˜: {total_reviews}, ì˜ˆìƒ íŽ˜ì´ì§€: {(total_reviews // 20) + 1}")
    
    all_reviews = []
    page = 1
    max_pages = (total_reviews // 20) + 1
    no_new_count = 0
    
    while page <= max_pages:
        logger.debug("=" * 60)
        logger.debug(f"========== íŽ˜ì´ì§€ {page} ì‹œìž‘ ==========")
        
        # í˜„ìž¬ URL ê¸°ë¡
        current_url = driver.current_url
        logger.debug(f"í˜„ìž¬ URL: {current_url}")
        
        # ìŠ¤í¬ë¡¤
        logger.debug("ìŠ¤í¬ë¡¤ ì‹¤í–‰: window.scrollTo(0, 1500)")
        driver.execute_script("window.scrollTo(0, 1500);")
        time.sleep(0.5)
        
        # í˜„ìž¬ íŽ˜ì´ì§€ ì „ì²´ ë¦¬ë·° ê°œìˆ˜ í™•ì¸
        all_review_items = driver.find_elements(By.CSS_SELECTOR, ".PxsZltB5tV")
        total_on_page = len(all_review_items)
        logger.debug(f"í˜„ìž¬ íŽ˜ì´ì§€ ë¦¬ë·° ì•„ì´í…œ: {total_on_page}ê°œ")
        
        if total_on_page == 0:
            logger.warning(f"íŽ˜ì´ì§€ {page}: ë¦¬ë·° ì•„ì´í…œ 0ê°œ! HTML ìŠ¤ëƒ…ìƒ· ì €ìž¥")
            save_html_snapshot(driver, f"page{page}_no_items_{product_id}")
        
        # ë‹µê¸€ ìžˆëŠ” ë¦¬ë·°ë§Œ ì¶”ì¶œ
        logger.debug("extract_reviews_with_reply í˜¸ì¶œ")
        reviews = extract_reviews_with_reply(driver, product_id, product_name)
        logger.debug(f"ì¶”ì¶œ ê²°ê³¼: {len(reviews)}ê°œ")
        
        # ìƒˆë¡œ ì¶”ì¶œëœ ë¦¬ë·° ì¤‘ ì¤‘ë³µ ì œê±°
        new_reviews = []
        existing_contents = {r["content"][:50] for r in all_reviews}
        logger.debug(f"ê¸°ì¡´ ë¦¬ë·° ìˆ˜: {len(all_reviews)}, ì¤‘ë³µì²´í¬ìš© ì½˜í…ì¸ : {len(existing_contents)}ê°œ")
        
        for r in reviews:
            content_key = r["content"][:50]
            if content_key not in existing_contents:
                new_reviews.append(r)
                existing_contents.add(content_key)
                logger.debug(f"  ì‹ ê·œ: '{content_key}...'")
            else:
                logger.debug(f"  ì¤‘ë³µ: '{content_key}...'")
        
        logger.debug(f"ì‹ ê·œ ë¦¬ë·°: {len(new_reviews)}ê°œ")
        
        if not new_reviews:
            no_new_count += 1
            logger.info(f"  âš  íŽ˜ì´ì§€ {page}: ì „ì²´ {total_on_page}ê°œ, ë‹µê¸€ {len(reviews)}ê°œ, ì‹ ê·œ 0ê°œ (no_new={no_new_count})")
            
            if no_new_count == MAX_NO_NEW - 1:
                logger.warning(f"{MAX_NO_NEW - 1}ì—°ì† ì‹ ê·œ ì—†ìŒ! HTML ìŠ¤ëƒ…ìƒ· ì €ìž¥")
                save_html_snapshot(driver, f"page{page}_9consecutive_{product_id}")
            
            if no_new_count >= MAX_NO_NEW:
                logger.info(f"  âŒ {MAX_NO_NEW}ì—°ì† ìƒˆ ë¦¬ë·° ì—†ìŒ â†’ ì¢…ë£Œ")
                break
        else:
            no_new_count = 0
            all_reviews.extend(new_reviews)
            logger.info(f"  ðŸ“„ íŽ˜ì´ì§€ {page}: ì „ì²´ {total_on_page}ê°œ, ë‹µê¸€ {len(reviews)}ê°œ, ì‹ ê·œ +{len(new_reviews)}ê°œ (ì´ {len(all_reviews)}ê°œ)")
        
        # ë‹¤ìŒ íŽ˜ì´ì§€ë¡œ ì´ë™
        logger.debug("ë‹¤ìŒ íŽ˜ì´ì§€ ì´ë™ ì‹œë„")
        
        # í˜„ìž¬ URL ì €ìž¥ (íŽ˜ì´ì§€ ì „í™˜ ê²€ì¦ìš©)
        url_before = driver.current_url
        product_id_before = url_before.split("/products/")[-1].split("?")[0]
        logger.debug(f"ì´ë™ ì „ URL: {url_before}")
        logger.debug(f"ì´ë™ ì „ product_id: {product_id_before}")
        
        try:
            next_num = page + 1
            
            # ðŸ”´ í•µì‹¬ ìˆ˜ì •: ë¦¬ë·° ì˜ì—­ ì•ˆì—ì„œë§Œ íŽ˜ì´ì§€ë„¤ì´ì…˜ ì°¾ê¸°
            # ë¦¬ë·° ì˜ì—­ ì»¨í…Œì´ë„ˆ ì°¾ê¸°
            review_section = None
            try:
                # ë°©ë²• 1: ë¦¬ë·° ëª©ë¡ ë¶€ëª¨ ì˜ì—­
                review_section = driver.find_element(By.CSS_SELECTOR, ".sMaXQxwPUP")
                logger.debug("ë¦¬ë·° ì˜ì—­ '.sMaXQxwPUP' ë°œê²¬")
            except:
                try:
                    # ë°©ë²• 2: ë¦¬ë·° ì•„ì´í…œì˜ ë¶€ëª¨
                    review_items = driver.find_elements(By.CSS_SELECTOR, ".PxsZltB5tV")
                    if review_items:
                        review_section = review_items[0].find_element(By.XPATH, "./ancestor::div[contains(@class, 'review')]")
                        logger.debug("ë¦¬ë·° ì•„ì´í…œ ë¶€ëª¨ ì˜ì—­ ë°œê²¬")
                except:
                    pass
            
            # íŽ˜ì´ì§€ ë²„íŠ¼ ì°¾ê¸° (ë¦¬ë·° ì˜ì—­ ë‚´ë¶€ ìš°ì„ )
            if review_section:
                page_btns = review_section.find_elements(By.CSS_SELECTOR, "a.hyY6CXtbcn")
                logger.debug(f"ë¦¬ë·° ì˜ì—­ ë‚´ íŽ˜ì´ì§€ ë²„íŠ¼: {len(page_btns)}ê°œ")
            else:
                page_btns = driver.find_elements(By.CSS_SELECTOR, "a.hyY6CXtbcn")
                logger.debug(f"ì „ì²´ íŽ˜ì´ì§€ ë²„íŠ¼: {len(page_btns)}ê°œ")
            
            btn_texts = [btn.text.strip() for btn in page_btns]
            logger.debug(f"íŽ˜ì´ì§€ ë²„íŠ¼ë“¤: {btn_texts}")
            
            clicked = False
            for btn in page_btns:
                if btn.text.strip() == str(next_num):
                    logger.debug(f"'{next_num}' ë²„íŠ¼ ë°œê²¬, í´ë¦­ ì‹œë„")
                    driver.execute_script("arguments[0].click();", btn)
                    logger.debug(f"í´ë¦­ ì™„ë£Œ, {PAGE_DELAY}ì´ˆ ëŒ€ê¸°")
                    random_sleep()
                    
                    # ðŸ”´ URL ë³€ê²½ ê°ì§€
                    url_after = driver.current_url
                    product_id_after = url_after.split("/products/")[-1].split("?")[0]
                    logger.debug(f"ì´ë™ í›„ URL: {url_after}")
                    logger.debug(f"ì´ë™ í›„ product_id: {product_id_after}")
                    
                    if product_id_before != product_id_after:
                        logger.error(f"ðŸ”´ ìƒí’ˆ ID ë³€ê²½ë¨! {product_id_before} â†’ {product_id_after}")
                        logger.error("ë‹¤ë¥¸ ìƒí’ˆ íŽ˜ì´ì§€ë¡œ ì´ë™í•¨ - ì¤‘ë‹¨")
                        save_html_snapshot(driver, f"wrong_product_{product_id}_{page}")
                        # ì›ëž˜ ìƒí’ˆìœ¼ë¡œ ëŒì•„ê°€ê¸°
                        driver.get(f"{STORE_URL}/products/{product_id}")
                        time.sleep(3)
                        break
                    
                    page += 1
                    clicked = True
                    logger.debug(f"íŽ˜ì´ì§€ {page}ë¡œ ì´ë™ ì„±ê³µ")
                    break
            
            if not clicked:
                logger.debug(f"íŽ˜ì´ì§€ {next_num} ë²„íŠ¼ ì—†ìŒ, 'ë‹¤ìŒ' ë²„íŠ¼ ì‹œë„")
                logger.info(f"  â†’ íŽ˜ì´ì§€ {next_num} ë²„íŠ¼ ì—†ìŒ (í˜„ìž¬: {btn_texts}), 'ë‹¤ìŒ' ë²„íŠ¼ ì‹œë„...")
                try:
                    # ë¦¬ë·° ì˜ì—­ ë‚´ë¶€ì—ì„œ 'ë‹¤ìŒ' ë²„íŠ¼ ì°¾ê¸°
                    if review_section:
                        next_btn = review_section.find_element(By.CSS_SELECTOR, "a.I3i1NSoFdB")
                    else:
                        next_btn = driver.find_element(By.CSS_SELECTOR, "a.I3i1NSoFdB")
                    
                    aria_hidden = next_btn.get_attribute("aria-hidden")
                    logger.debug(f"'ë‹¤ìŒ' ë²„íŠ¼ ë°œê²¬, aria-hidden={aria_hidden}")
                    
                    if aria_hidden == "true":
                        logger.info(f"  âŒ ë§ˆì§€ë§‰ íŽ˜ì´ì§€ ë„ë‹¬")
                        break
                    
                    logger.debug("'ë‹¤ìŒ' ë²„íŠ¼ í´ë¦­ ì‹œë„")
                    driver.execute_script("arguments[0].click();", next_btn)
                    logger.debug(f"í´ë¦­ ì™„ë£Œ, {PAGE_DELAY}ì´ˆ ëŒ€ê¸°")
                    random_sleep()
                    
                    # URL ë³€ê²½ ê°ì§€
                    url_after = driver.current_url
                    product_id_after = url_after.split("/products/")[-1].split("?")[0]
                    if product_id_before != product_id_after:
                        logger.error(f"ðŸ”´ ìƒí’ˆ ID ë³€ê²½ë¨! {product_id_before} â†’ {product_id_after}")
                        break
                    
                    page += 1
                    logger.info(f"  â†’ 'ë‹¤ìŒ' í´ë¦­ ì„±ê³µ! íŽ˜ì´ì§€ {page}")
                except Exception as e:
                    logger.error(f"'ë‹¤ìŒ' ë²„íŠ¼ í´ë¦­ ì‹¤íŒ¨: {type(e).__name__}: {e}")
                    logger.error(traceback.format_exc())
                    save_html_snapshot(driver, f"page{page}_next_fail_{product_id}")
                    break
        except Exception as e:
            logger.error(f"íŽ˜ì´ì§€ ì´ë™ ì‹¤íŒ¨: {type(e).__name__}: {e}")
            logger.error(traceback.format_exc())
            save_html_snapshot(driver, f"page{page}_nav_fail_{product_id}")
            break
    
    logger.info(f"  í¬ë¡¤ë§ ì™„ë£Œ: ì´ {len(all_reviews)}ê°œ ìˆ˜ì§‘")
    return all_reviews


def crawl_product_reviews(driver, product_id, product_name, product_idx, total_products):
    """ë‹¨ì¼ ìƒí’ˆ ë¦¬ë·° í¬ë¡¤ë§ (ìž¬ì‹œë„ í¬í•¨)"""
    url = f"{STORE_URL}/products/{product_id}"
    
    logger.info(f"\n[{product_idx}/{total_products}] {product_name[:30]}...")
    logger.info(f"    URL: {url}")
    logger.debug(f"ìƒí’ˆ í¬ë¡¤ë§ ì‹œìž‘: {product_id} - {product_name}")
    
    for retry in range(MAX_RETRIES):
        try:
            if retry > 0:
                logger.info(f"    ðŸ”„ ìž¬ì‹œë„ {retry}/{MAX_RETRIES}...")
                time.sleep(5)  # ìž¬ì‹œë„ ì „ ëŒ€ê¸°
            
            logger.debug(f"íŽ˜ì´ì§€ ì ‘ì†: {url}")
            driver.get(url)
            time.sleep(3)
            logger.debug("íŽ˜ì´ì§€ ë¡œë“œ ì™„ë£Œ")
            
            # ë¦¬ë·° íƒ­ í´ë¦­
            try:
                logger.debug("ë¦¬ë·° íƒ­ ì°¾ëŠ” ì¤‘...")
                review_tab = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'ë¦¬ë·°')]"))
                )
                logger.debug("ë¦¬ë·° íƒ­ ë°œê²¬, í´ë¦­")
                review_tab.click()
                time.sleep(2)
                logger.debug("ë¦¬ë·° íƒ­ í´ë¦­ ì™„ë£Œ")
            except Exception as e:
                logger.warning(f"ë¦¬ë·° íƒ­ ì—†ìŒ: {type(e).__name__}: {e}")
                logger.info(f"    âš  ë¦¬ë·° íƒ­ ì—†ìŒ â†’ ìŠ¤í‚µ")
                return []
            
            # ì´ ë¦¬ë·° ìˆ˜
            total_reviews = get_total_review_count(driver)
            logger.info(f"    ðŸ“Š ì´ ë¦¬ë·°: {total_reviews}ê°œ")
            logger.debug(f"ì´ ë¦¬ë·° ìˆ˜: {total_reviews}")
            
            if total_reviews == 0:
                logger.info(f"    â†’ ìŠ¤í‚µ (ë¦¬ë·° ì—†ìŒ)")
                return []
            
            # ë¦¬ë·° ì˜ì—­ ìŠ¤í¬ë¡¤
            logger.debug("ë¦¬ë·° ì˜ì—­ìœ¼ë¡œ ìŠ¤í¬ë¡¤")
            driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(1)
            
            # í¬ë¡¤ë§
            logger.info(f"    ðŸ”„ ë‹µë³€ ìžˆëŠ” ë¦¬ë·° ìˆ˜ì§‘ ì¤‘...")
            reviews = crawl_all_pages(driver, product_id, product_name, total_reviews)
            
            logger.info(f"    âœ“ ë‹µë³€ ìžˆëŠ” ë¦¬ë·° {len(reviews)}ê°œ ì¶”ì¶œ")
            
            return reviews
            
        except Exception as e:
            logger.error(f"ìƒí’ˆ í¬ë¡¤ë§ ì—ëŸ¬ (ì‹œë„ {retry+1}/{MAX_RETRIES}): {type(e).__name__}: {e}")
            logger.error(traceback.format_exc())
            
            if retry == MAX_RETRIES - 1:
                save_html_snapshot(driver, f"product_error_{product_id}")
                logger.info(f"    âœ— {MAX_RETRIES}íšŒ ì‹¤íŒ¨: {e}")
                return []
    
    return []


def save_reviews(reviews, filename):
    """ë¦¬ë·° CSV ì €ìž¥"""
    if not reviews:
        return
    
    fieldnames = [
        "product_id", "product_name", "review_index", 
        "username", "date", "rating", "option", 
        "content", "reply", "reply_date"
    ]
    
    with open(filename, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in reviews:
            writer.writerow(r)


def main():
    csv_filename = get_output_filename("reviews_replied", "csv")
    
    logger.info("=" * 60)
    logger.info(f"í•´í”¼í…Œì¼ì¦ˆ ë¦¬ë·° í¬ë¡¤ëŸ¬ v4.6 (ë‹µë³€ DBìš©)")
    logger.info(f"ì‹¤í–‰ì¼ì‹œ: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info(f"ë¡œê·¸íŒŒì¼: {LOG_FILENAME}")
    logger.info(f"ëŒ€ìƒ ìƒí’ˆ: {len(PRODUCTS)}ê°œ")
    logger.info("ðŸ’¡ ë‹µë³€ ìžˆëŠ” ë¦¬ë·°ë§Œ ì €ìž¥í•©ë‹ˆë‹¤!")
    logger.info("=" * 60)
    
    # ê¸°ì¡´ íŒŒì¼ ì²´í¬ (ì´ì–´ì„œ í¬ë¡¤ë§)
    done_ids = set()
    existing_reviews = []
    
    existing_csvs = glob.glob(os.path.join(OUTPUT_DIR, "reviews_replied_*.csv"))
    if existing_csvs:
        latest_csv = max(existing_csvs)
        logger.info(f"\nðŸ“‚ ê¸°ì¡´ íŒŒì¼ ë°œê²¬: {latest_csv}")
        user_input = input("   ì´ì–´ì„œ ì§„í–‰? (y/n): ").strip().lower()
        
        if user_input == 'y':
            with open(latest_csv, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing_reviews.append(row)
                    done_ids.add(row["product_id"])
            logger.info(f"   âœ“ {len(existing_reviews)}ê°œ ë¦¬ë·° ë¡œë“œ, {len(done_ids)}ê°œ ìƒí’ˆ ì™„ë£Œ")
            csv_filename = latest_csv
    
    driver = setup_driver()
    logger.debug("ë“œë¼ì´ë²„ ì„¤ì • ì™„ë£Œ")
    all_reviews = existing_reviews.copy()
    
    try:
        for idx, product in enumerate(PRODUCTS, 1):
            product_id = product["id"]
            product_name = product["name"]
            
            if product_id in done_ids:
                logger.info(f"\n[{idx}/{len(PRODUCTS)}] {product_name[:30]}... â†’ ìŠ¤í‚µ (ì™„ë£Œ)")
                continue
            
            reviews = crawl_product_reviews(driver, product_id, product_name, idx, len(PRODUCTS))
            all_reviews.extend(reviews)
            done_ids.add(product_id)
            
            # ì¤‘ê°„ ì €ìž¥
            if idx % SAVE_INTERVAL == 0:
                save_reviews(all_reviews, csv_filename)
                logger.info(f"\n    ðŸ’¾ ì¤‘ê°„ ì €ìž¥: {len(all_reviews)}ê°œ ë¦¬ë·°")
            
            random_sleep()
        
        # ìµœì¢… ì €ìž¥
        save_reviews(all_reviews, csv_filename)
        
        # ========== ê²°ê³¼ ==========
        logger.info("\n" + "=" * 60)
        logger.info("âœ… í¬ë¡¤ë§ ì™„ë£Œ!")
        logger.info("=" * 60)
        logger.info(f"\nðŸ“Š ê²°ê³¼:")
        logger.info(f"   ì´ ìƒí’ˆ: {len(PRODUCTS)}ê°œ")
        logger.info(f"   ë‹µë³€ ìžˆëŠ” ë¦¬ë·°: {len(all_reviews)}ê°œ")
        logger.info(f"\nðŸ“ CSV: {csv_filename}")
        logger.info(f"ðŸ“ ë¡œê·¸: {LOG_FILENAME}")
        
        print("\n")
        print("ðŸ”” " * 15)
        print(f"\n  ðŸ‘‰ '{csv_filename}' íŒŒì¼ì„")
        print(f"     í´ë¡œë“œì—ê²Œ ì „ë‹¬í•˜ì„¸ìš”!")
        print(f"\n  ðŸ‘‰ ë¬¸ì œ ìžˆìœ¼ë©´ '{LOG_FILENAME}'")
        print(f"     ë¡œê·¸ íŒŒì¼ë„ ê°™ì´!")
        print("\n")
        print("ðŸ”” " * 15)
        
    except KeyboardInterrupt:
        logger.warning("\n\nâš  ì¤‘ë‹¨! ì €ìž¥ ì¤‘...")
        save_reviews(all_reviews, csv_filename)
        logger.info(f"   âœ“ {len(all_reviews)}ê°œ ì €ìž¥ ì™„ë£Œ")
        
    finally:
        input("\nì—”í„°ë¥¼ ëˆ„ë¥´ë©´ ì¢…ë£Œ...")
        driver.quit()
        logger.info("ë“œë¼ì´ë²„ ì¢…ë£Œ")


if __name__ == "__main__":
    main()
