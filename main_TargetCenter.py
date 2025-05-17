from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import os
import pandas as pd
from datetime import datetime

# 5 of n sites

class Scraper:      
    def __init__(self):
        self.headless = False
        self.driver = None
        self.shows_data = []

    def config_driver(self):
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
        s = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=s, options=options)
        self.driver = driver

    def scrap_page(self):

        wait_show = WebDriverWait(self.driver, 15)

        shows_container = wait_show.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//div[@class='eventList__wrapper list is-filtered']")
                    )
                )

        shows = shows_container.find_elements(By.XPATH, "//div[@class='eventList__wrapper list is-filtered']//div[contains(@class, 'eventItem') and not(ancestor::div[contains(@class, 'current_events false hide')])]")

        if len(shows) == 0 :
            return "NO DATA"


        def clean_string(s):
                if isinstance(s, list):
                    s = ' '.join(s)  
                
                if s is None:  
                    return ""
                
                return ' '.join(re.sub(r'\s+', ' ', s.replace(',',';').replace('\n', ' ').strip()).split())
        
        def extract_date(day_, month_, year_, hour_):

            if day_ == "":
                return "", "", "", ""
            
            day = day_.strip()
            month = month_.strip()
            year = year_.strip()
            hour = hour_.strip().replace('-', '').strip()

            try:
                month_numeric = datetime.strptime(month, "%b").month  # Converts 'Nov' to 11
            except ValueError:
                return year, month, f"{int(day):02}", hour
            
            return year, f"{month_numeric:02}", f"{int(day):02}", hour




        for show in shows:
            # presented by
            try:
                Band_Line1 = show.find_element(
                            By.XPATH, ".//div[contains(normalize-space(@class), 'presented-by')]"
                        ).text
            except:
                Band_Line1 = "" 

            # title
            try:
                Band_Line2 = show.find_element(
                            By.XPATH, ".//h3[contains(normalize-space(@class), 'title')]"
                        ).text
            except:
                Band_Line2 = "" 
            
            # tag line
            try:
                Band_Line3 = show.find_element(
                            By.XPATH, ".//h4[contains(normalize-space(@class), 'tagline')]"
                        ).text
            except:
                Band_Line3 = "" 

            # date first case, 
            try:
                month_ = show.find_element(By.XPATH, ".//span[@class='m-date__month']").text.strip()
                day_ = show.find_element(By.XPATH, ".//span[@class='m-date__day']").text.strip()
                year_ = show.find_element(By.XPATH, ".//span[@class='m-date__year']").text.strip().replace(',', '')
                hour_ = show.find_element(By.XPATH, ".//span[@class='m-date__hour']").text.strip().replace(',', '')
            except:
                pass

            year, month, day, hour = extract_date(day_, month_, year_, hour_)
            date_scraped = datetime.now().strftime('%Y%m%d')  


            data = {
                'Date Scraped': date_scraped,
                'Year': year,
                'Month': month,
                'Day': day,
                'Time' : hour, 
                'Venue': "Target Center",
                'Band Line 1': clean_string(Band_Line1),
                'Band Line 2' : clean_string((Band_Line2)),
                'Band Line 3' : clean_string((Band_Line3))
                
            }
            print(data)
            self.shows_data.append(data) 

        return "success"
    
    def save_data_to_excel(self):
        today = datetime.now().strftime('%Y-%m-%d')

        folder_path = os.path.join(os.getcwd(), "Data")  
        file_name = f"Data_{today}_TargetCenter.csv"
        file_path = os.path.join(folder_path, file_name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        count = 1
        while os.path.exists(file_path):
            file_name = f"Data_{today}_TargetCenter_{count}.csv"
            file_path = os.path.join(folder_path, file_name)
            count += 1


        df = pd.DataFrame(self.shows_data)
        df.to_csv(file_path, index=False, encoding='utf-8-sig',  sep='|')

        print(f"Data saved to {file_path}")

        
    def main_workflow(self):
        data_scraper.config_driver()
        
        url = "https://www.targetcenter.com/index.php/events/all"
        print("Getting details of :", url)
        self.driver.get(url)
        self.driver.maximize_window()


        time.sleep(2)
        wait = WebDriverWait(self.driver, 20)

        # choosing filter
        filter_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'select')]"))
        )
        self.driver.execute_script("arguments[0].click();", filter_button)

        concert_option = wait.until(
            EC.presence_of_element_located((By.XPATH, "//span[text()='Concerts']"))
        )
        self.driver.execute_script("arguments[0].click();", concert_option)


        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        value = self.scrap_page()
        if value == "NO DATA":
            print("absoulute no data")
            return

        self.save_data_to_excel()
        self.driver.close()


data_scraper = Scraper()
data_scraper.main_workflow()