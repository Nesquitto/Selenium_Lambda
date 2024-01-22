import json
from selenium.webdriver.chrome.service import Service
from selenium import webdriver # 크롬 창을 조종하기 위한 모듈입니다.
from selenium.webdriver.common.by import By # 웹사이트의 구성요소를 선택하기 위해 By 모듈을 불려옵니다.
from selenium.webdriver.support.ui import WebDriverWait # 웹페이지가 전부 로드될때까지 기다리는 (Explicitly wait) 기능을 하는 모듈입니다.
from selenium.webdriver.support import expected_conditions as EC # 크롬의 어떤 부분의 상태를 확인하는 모듈입니다.
from selenium.webdriver.common.keys import Keys # 크롬 창에서 입력하고, 클릭을 위한 모듈입니다.
import time # 정해진 시간만큼 기다리게 하기 위한 패키지입니다.
from bs4 import BeautifulSoup # html을 파싱하고 자를 모듈입니다.

def searchList(driver, search_word):
    searching_url = "https://m.map.naver.com/search2/search.naver?query=" + search_word
    driver.get(searching_url)  # 검색 링크입니다
    try:
        search_list_component = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".search_list._items"))
        )  # "search_list _items"을 Class로 가지는 요소가 로딩 될 때까지 기다립니다. 30초간 연결이 안되면 에러를 발생시킵니다.
        try:
            html_string = search_list_component.get_attribute('innerHTML')
            component_soup = BeautifulSoup(html_string, 'html.parser')
            place_id = component_soup.select("li")[0].select("div")[0].select("a")[0]["data-cid"]

            return searchInfo(driver, place_id)
        except Exception as e:
            print("검색 결과가 없을 수 있습니다. " + searching_url, str(e))

    except Exception as e:
        print("검색에 너무 오랜 시간이 걸립니다. " + searching_url, str(e))

def searchInfo(driver, place_id):
    ret_json = {}

    place_url = "https://m.place.naver.com/place/" + place_id + "/home"

    ret_json["url"] = str(place_url)
    driver.get(place_url)
    try:
        element = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#app-root > div > div > div > div:nth-child(5) > div > div:nth-child(2) > div > div > div:nth-child(2) > div > a"))
        )
        html_string = element.get_attribute('innerHTML')
        place_soup = BeautifulSoup(html_string, 'html.parser')
        ret_json = info_parsing(driver.page_source, ret_json)
        element.send_keys(Keys.ENTER)
        time.sleep(5)  # 화면 표시 기다리기
        place_html_string = element.get_attribute('innerHTML')

        return business_hour_parsing(place_html_string, ret_json)

    except Exception as e:
        print("Place Id가 잘못되어 페이지를 불러올 수 없거나 내부에 정보가 잘못되었을 수 있습니다. " + place_url, str(e))

def info_parsing(html, ret_json):
    try:
        soup = BeautifulSoup(html, 'html.parser')
        header = soup.select("#_header")
        ret_json['name'] = header[0].text
        div = soup.select("#app-root > div > div > div > div:nth-child(5) > div > div:nth-child(2) > div > div")
        a = div[0].findAll('div', recursive=False)
        address = ""
        phone = ""
        for i in a:
            if "주소" in str(i):
                address = i.find('a').find('span').text
            if "전화번호" in str(i):
                phone = i.find('div').find('span').text

        ret_json['address'] = address
        ret_json['phone'] = phone
        return ret_json
    except Exception as e:
        print("내부에서 정보를 파싱하는 과정에 실패했습니다. " + str(e))
        return ret_json

def business_hour_parsing(html, ret_json):
    try:
        ret_json["time"] = {}
        soup = BeautifulSoup(html, 'html.parser')
        # 바로 하위 태그에 있는 div 태그 가져오기
        div_tags = soup.find_all('div', recursive=False)
        for div in div_tags:
            if (div.find("em")):
                print("pass")
                continue
            ret = div.find("div")
            day = ret.find("span").find("span")
            business_hour = ret.find("div")
            ret_json["time"][str(day.text)] = str(business_hour.text)
        return ret_json
    except Exception as e:
        print("운영시간 정보를 파싱하는 과정에서 실패했습니다. " + str(e))
        return ret_json
def handler(event, context=None):
    search_word = event['word']
    #search_word = input()
    service = Service(executable_path=r'/opt/chromedriver')
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = "/opt/chrome/chrome"
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko")
    chrome_options.add_argument('window-size=1392x1150')
    chrome_options.add_argument("disable-gpu")
    driver = webdriver.Chrome(service=service, options=chrome_options)  # 웹 드라이버를 설치하고, 조종할 수 있는 크롬 창을 실행합니다

    dictionary = searchList(driver, search_word)

    driver.close()

    return {
        "statusCode": 200,
        "body": json.dumps(dictionary),
    }

if __name__ == '__main__':
    handler()