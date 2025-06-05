from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import os
import requests

# 드라이버 설정
driver_path = r"C:\Program Files\Google\chromedriver-win64\chromedriver.exe"
service = Service(driver_path)
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, 10)

# Kakao Map 접속
driver.get("https://map.kakao.com/")
search_input = wait.until(EC.presence_of_element_located((By.ID, "search.keyword.query")))
search_input.send_keys("세종대학교 맛집")
search_input.send_keys(Keys.RETURN)

wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.PlaceItem")))

data = []
page_count = 0
# 이미지 저장 폴더
img_dir = "images"
os.makedirs(img_dir, exist_ok=True)

while page_count < 25:
    print(f"📄 페이지 {page_count + 1} 크롤링 중...")
        #  장소 목록 수집
    places = driver.find_elements(By.CSS_SELECTOR, "li.PlaceItem")
    for place in places:
        try:
            name = place.find_element(By.CSS_SELECTOR, ".tit_name .link_name").text
            address = place.find_element(By.CSS_SELECTOR, '.addr p[data-id="address"]').text
            phone = place.find_element(By.CSS_SELECTOR, '.contact .phone').text
            rating = place.find_element(By.CSS_SELECTOR, '.rating .num').text
            reviews = place.find_element(By.CSS_SELECTOR, '.review em').text
            link = place.find_element(By.CSS_SELECTOR, '.moreview').get_attribute('href')
        except Exception as e:
            print("⚠️ 기본 정보 수집 실패:", e)
            continue

        # 상세페이지 새 탭 열기
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(link)
        time.sleep(2)

        sample_reviews = []
        image_url = ""
        # 장소 카테고리 (tag) 수집
        try:
            tag_el = driver.find_element(By.CSS_SELECTOR, 'span.info_cate')
            tag_text = tag_el.get_attribute("innerText").strip().replace("장소 카테고리", "").strip()
        except Exception as e:
            print("  장소 태그 수집 실패:", e)
            tag_text = "정보 없음"

        try:
            # ▶ 사진 탭 클릭
            photo_tab = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.link_tab[href="#photoview"]'))
            )
            photo_tab.click()
            time.sleep(2)

            # ▶ 이미지 src 추출
            img = driver.find_element(By.CSS_SELECTOR, 'ul.list_photo li a.link_photo > img')
            image_url = img.get_attribute('src')

            # ▶ 이미지 다운로드
            if image_url:
                response = requests.get(image_url)
                img_path = os.path.join(img_dir, f"{name}.jpg")
                with open(img_path, "wb") as f:
                    f.write(response.content)
        except Exception as e:
            print(" 이미지 수집 실패:", e)

         # 메뉴 탭 
        try:
        # 메뉴 탭 클릭
            menu_tab = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.link_tab[href="#menuInfo"]'))
            )
            menu_tab.click()
    
        # 메뉴 정보가 로드될 때까지 대기
            WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'p.desc_item'))
            )
    
        #  첫 번째 가격 정보 가져오기
            menu_price_el = driver.find_element(By.CSS_SELECTOR, 'p.desc_item')
            menu_price = menu_price_el.text.strip()
    
        except Exception as e:
            print(" ⚠️ 메뉴 가격 수집 실패:", e)
            menu_price = "정보 없음"

        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        
        data.append({
            "name": name,
            "address": address,
            "phone": phone,
            "rating": rating,
            "review_count": reviews,
            "detail_link": link,
            "image_url": image_url,
            "tag": tag_text, 
            "menu_price": menu_price  
        })
    print(f"📄 페이지 {page_count + 1} 크롤링 완료, {len(places)}개 장소 수집됨.")
    # 1페이지 -> 2페이지 넘어가는 경우 '더보기' 버튼 클릭
    # 페이지 1 = page_count 0
    # 페이지 2 = page_count 1   
    # 페이지 3 = page_count 2
    # 페이지 4 = page_count 3
    # 페이지 5 = page_count 4 -> 이 때 next_btn

    # 첫 페이지 크롤링 이후 2페이지로 갈 때 더보기 버튼
    if page_count == 0: 
        try:
            more_btn = driver.find_element(By.ID, "info.search.place.more")
            driver.execute_script("arguments[0].scrollIntoView(true);", more_btn)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", more_btn)
            time.sleep(2)
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.PlaceItem")))
        except Exception as e:
            print(" 더보기 버튼 클릭 실패:", e)
            break
    # 5페이지 일 때는 다음 버튼 클릭 
    elif page_count > 1 and page_count %4 == 0:
        print(" 5페이지 이상일 때는 다음 버튼 클릭")
        try:
            next_group_btn = driver.find_element(By.ID, "info.search.page.next")
            driver.execute_script("arguments[0].click();", next_group_btn)
            time.sleep(2)
            next_btn_id = f"info.search.page.no{(page_count + 1)% 5 + 1}"
            next_btn = driver.find_element(By.ID, next_btn_id)
            driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(2)
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.PlaceItem")))
        except Exception as e:
            print(" 다음 페이지 이동 실패:", e)
            break

    # 5페이지가 아닌 경우
    elif page_count > 1:
        try:
            next_btn_id = f"info.search.page.no{(page_count + 1)% 5 + 1}"
            next_btn = driver.find_element(By.ID, next_btn_id)
            driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(2)
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.PlaceItem")))
        except Exception as e:
            print(" 다음 페이지 이동 실패:", e)
            break

    # 카운트 증가는 마지막에!
    page_count += 1
# 저장
with open("세종대_맛집_리스트_with_리뷰_이미지.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(" 크롤링 및 저장 완료!")
driver.quit()
