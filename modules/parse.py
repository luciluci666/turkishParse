from distutils.debug import DEBUG
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from bs4 import BeautifulSoup
import time
import ciso8601
import re


class Flights():
    url = "https://www.turkishairlines.com/"
    DEBUG = True

    def __init__(self, flightDates=[]):
        self.flightDates = flightDates

    
    def dates(self):
        unixDates = []
        for date in self.flightDates:
            t = date + " 00:00:00-03"    #format  "2022-08-26"
            ts = ciso8601.parse_datetime(t)
            date = int(time.mktime(ts.timetuple())) * 1000
            unixDates.append(str(date))

        return unixDates


    def choose_date(self, driver, unixDate):
        WebDriverWait(driver, 10).until(ec.element_to_be_clickable((By.CLASS_NAME, 'ui-state-default')))
        date_pick = False
        while not date_pick:
            dates = driver.find_elements(By.CLASS_NAME, 'ui-state-default')     
            for date in dates:        
                if date.get_attribute('data-timestamp') == unixDate:
                    date.click()
                    date_pick = True
                    break
            if not date_pick:
                driver.find_element(By.CLASS_NAME, 'ui-datepicker-next').click()
   

    def selenium(self):
        # webdriver on and options
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
        options = Options()
        # options.add_argument('--headless')
        options.add_argument("--proxy-server='direct://'")
        options.add_argument("--proxy-bypass-list=*")

        options.add_argument('user-agent={0}'.format(user_agent))
        options.add_argument('--ignore-certificate-errors')
        options.add_argument("start-maximized")
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-extensions")
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--window-size=1920,1200")
        # options.add_argument('--incognito')

        driver = webdriver.Chrome(options=options)
        driver.get(self.url)

        # choosing flight
        WebDriverWait(driver, 10).until(ec.element_to_be_clickable((By.ID, "cookieWarningAcceptId"))).click()
        input_to = WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.ID, "portInputTo")))
        WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.CLASS_NAME, "focused")))  
        input_to.send_keys('helsinki')
        input_to.send_keys(Keys.ARROW_DOWN, Keys.ENTER)

        # flight dates
        unixDates = self.dates()
        for date in unixDates:
            self.choose_date(driver, date)

        driver.find_element(By.CLASS_NAME, "focusable-calendar-item").click()
        driver.find_element(By.LINK_TEXT, "OK").click()
    
        submit_btn = WebDriverWait(driver, 10).until(ec.element_to_be_clickable((By.ID, "executeSingleCitySubmit")))
        submit_btn.click()

        time.sleep(3)

        if self.DEBUG:
            i = 0
            while driver.current_url == 'https://www.turkishairlines.com/':
                submit_btn.click()
                i += 1
                print(f'{i} попытка редиректа.')
                if i == 3:
                    return driver.page_source
                time.sleep(1)


        # close window if
        WebDriverWait(driver, 60).until(ec.presence_of_element_located((By.CLASS_NAME, "lightcolored ")))  

        return driver.page_source
        

    def bs4(self, page):
        soup = BeautifulSoup(page, 'html.parser')
        elements = soup.find_all(class_="lightcolored")
        if elements:
            prices = []
            for elem in elements:
                prices.append(elem.get_text())
            return prices
        else:
            return soup

    def save(self):
        prices = self.bs4(self.selenium())
        if isinstance(prices, list):
            formated_prices = []
            for price in prices:
                price = price.replace("\n", "")
                price = price.replace("ILS", "")
                price = int(float(price.replace(',', '')))
                formated_prices.append(price)
                
            print(f'Минимальная цена билета: {min(formated_prices)} ILS.')
        else:
            with open('errors.txt', 'w', encoding = 'utf-8') as file:
                file.write(prices.prettify())
        


    def main(self):
        self.save()



if __name__ == "__main__":
    Flights(["2022-08-28", "2022-11-09"]).main()


