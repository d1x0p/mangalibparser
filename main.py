import pickle
import os
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import requests
import shutil
from time import sleep
from config import data
from fake_useragent import UserAgent

useragent = UserAgent()

#Получаем переменные из конфига
email = data['email']
password = data['password']
directory = data['directory']
cookies = data['cookies']
urlmanga = data['url']
chrome_driver_path = directory + "/chromedriver.exe"
headless = data['headless']
delay = data['delay']

#Явное ожидание нажатия
def click(driver, locator):
    WebDriverWait(driver, 10).until(EC.presence_of_element_located(locator)).click()

#Явное ожидание отправки ключей
def send_keys(driver,locator, value):
    WebDriverWait(driver, 10).until(EC.presence_of_element_located(locator)).clear()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located(locator)).send_keys(value)

#Функция для скачивания изображения
def download_image(url, name, folder):
    #Меняем директорию
    os.chdir(directory)

    #Проверяем существование папки
    if not os.path.isdir(folder):
        os.mkdir(folder)

    #Сохраняем изображение
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(directory+"/"+folder+"/"+name+".png", 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

def get_manga_image(urlmanga):

    #Настройки для браузера
    options = webdriver.ChromeOptions()

    #Добавляем user agent
    options.add_argument(f"user-agent={useragent.random}")
    
    options.add_argument("--disable-blink-features=AutomationControlled")

    service = webdriver.chrome.service.Service(chrome_driver_path)

    #Скрывать браузер или нет
    if headless == 1:
       options.add_argument("--headless")

    #Создание драйвера
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get("https://mangalib.me/")
        driver.maximize_window()
        driver.implicitly_wait(1)
        #Пробуем найти куки 
        try:
            for cookie in pickle.load(open(f"{cookies}/{email}", "rb")):
                driver.add_cookie(cookie)
        #Если их нет, то создаём
        except: 
            click(driver, (By.CLASS_NAME, "button.header__sign.header__sign-in"))
            send_keys(driver, (By.XPATH, '//input[@name="email"]'), email)
            send_keys(driver, (By.XPATH, '//input[@name="password"]'), password)
            click(driver, (By.CLASS_NAME, 'button.button_primary.button_md.button_block'))
            pickle.dump(driver.get_cookies(), open(f"{cookies}/{email}", "wb"))

        #Переходим по ссылке на страницу манги
        driver.get(urlmanga)

        #Сохраняем название манги
        manga_name_ru = driver.find_element(By.CLASS_NAME, 'media-name__main').text
        manga_name_jpn = driver.find_element(By.CLASS_NAME, 'media-name__alt').text

        #Переходим к главам манги
        click(driver, (By.XPATH, '//li[@data-key="chapters"]'))

        #Если имеются переводы, то выбираем самый первый
        if driver.find_elements(By.CLASS_NAME, "media-section.media-chapters-teams"):
            click(driver, (By.XPATH, '//div[@class="team-list-item"]'))
        
        #Пролистываем в самый низ страницы, чтобы прогрузилась первая глава манги
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        #Переходим на самую первую главу
        chapters = driver.find_elements(By.XPATH, '//div[@class="media-chapter__name text-truncate"]/a[@class="link-default"]')
        chapters[-1].click()
        
        #Начинаем скачивать главы по очереди
        for chapter in range(len(chapters)):

            #Находим количество скрытых глав
            container = driver.find_elements(By.CLASS_NAME, "reader-view__wrap.hidden")

            #Создаём переменную с путём для глав манги
            folder = f"Глава {chapter+1}"
            folder = f"{manga_name_ru} ({manga_name_jpn})/" + folder
            for page in range(1,len(container)+2):
                print("Парсим: "+ str(chapter+1)+ " глава, " + str(page) + "/" + str(len(container)+1) + " страниц")
                sleep(0.5)

                #Получаем ссылку на страницу манги
                url = driver.find_element(By.XPATH, '//div[@data-p="' + str(page) + '"]/img').get_attribute('src')
                name = str(page)

                #Меняем директорию 
                os.chdir(directory)

                #Проверяем существует ли директория, если нет, то создаём
                if not os.path.isdir(f"{manga_name_ru} ({manga_name_jpn})"):
                    os.mkdir(f"{manga_name_ru} ({manga_name_jpn})")

                #Скачиваем страницу
                download_image(url, name, folder)
                
                #Переходим на следующий фрейм
                click(driver, (By.XPATH, '//div[@data-p="'+str(page)+'"]'))
            sleep(delay)
    except Exception as ex:
        print(ex)
    finally:
        print("Парсинг окончен")
        driver.close()
        driver.quit()
def main():
    get_manga_image(urlmanga=urlmanga)
if __name__ == "__main__":
    main()