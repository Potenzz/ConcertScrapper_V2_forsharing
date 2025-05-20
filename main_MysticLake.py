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

#2 of n 


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
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//div[@class='cmp-promos-events__event']")
                    )
                )

        
        if len(shows_container) == 0:
            return "NO DATA"
        
        def clean_string(s):
                if isinstance(s, list):
                    s = ' '.join(s)  
                
                if s is None:  
                    return ""
                
                return ' '.join(re.sub(r'\s+', ' ', s.replace(',',';').replace('\n', ' ').strip()).split())

        def extract_date(show_date, start_year=None):
            """
            Extracts the first occurrence of day, month, and determines the correct year.
            Ensures the year increments if the month resets to an earlier value in sequence.

            :param show_date: Event date string (e.g., "Friday, 11/08-Saturday, 11/09").
            :param start_year: The year to begin tracking from (defaults to current year). as the date has no value of year.
            """
            if show_date == "":
                return {'Year': "", 'Month': "", 'Day': ""}

            if start_year is None:
                start_year = datetime.now().year

            if not hasattr(extract_date, "previous_month"):
                extract_date.previous_month = 0  
                extract_date.current_year = start_year  

            # Take the first date from a range (e.g., "11/08" from "11/08-Saturday, 11/09")
            first_date = show_date.split('-')[0].strip()

            # Extract month and day (e.g., "11/08" -> month=11, day=8)
            month, day = map(int, first_date.split(', ')[-1].split('/'))

            # Check if the month has decreased (meaning we are in the next year)
            if month < extract_date.previous_month:
                extract_date.current_year += 1  

            extract_date.previous_month = month
            return {'Year': extract_date.current_year, 'Month': month, 'Day': day}


        for show in shows_container:

            try:
                Band_Line1 = show.find_element(
                            By.XPATH, ".//div[@class='cmp-promos-events__event-title h3']//a"
                        ).text
            except:
                Band_Line1 = "" 


            try:
                date_text = show.find_element(
                            By.XPATH, ".//p[@class='cmp-promos-events__event-date h6']"
                        ).text
            except:
                date_text = ""     

            
            formatted_date = extract_date(date_text)
            date_scraped = datetime.now().strftime('%Y%m%d')  


            data = {
                'Date Scraped': date_scraped,
                'Year': formatted_date['Year'],
                'Month': formatted_date['Month'],
                'Day': formatted_date['Day'],
                'Venue': "Mystic Lake",
                'Band Line 1': clean_string(Band_Line1),
                
            }
            print(data)
            self.shows_data.append(data) 


        return "success"
    
    def save_data_to_excel(self):
        today = datetime.now().strftime('%Y-%m-%d')

        folder_path = os.path.join(os.getcwd(), "Data")  
        file_name = f"Data_{today}_MysticLake.csv"
        file_path = os.path.join(folder_path, file_name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        count = 1
        while os.path.exists(file_path):
            file_name = f"Data_{today}_MysticLake_{count}.csv"
            file_path = os.path.join(folder_path, file_name)
            count += 1


        df = pd.DataFrame(self.shows_data)
        df.to_csv(file_path, index=False, encoding='utf-8-sig',  sep='|')

        print(f"Data saved to {file_path}")

        
    def main_workflow(self):
        data_scraper.config_driver()
        
        url = "https://mysticlake.com/shows-and-events"
        print("Getting details of :", url)
        self.driver.get(url)
        self.driver.maximize_window()

        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "closeIconContainer"))
            )
            self.driver.execute_script("""
                    const el = document.evaluate('/html/body/div[2]/div/main/div/div/div/button', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    el && el.click();
                """)
        except:
            self.driver.execute_script("""
                const el = document.evaluate('/html/body/div[2]/div/main/div/div/div/button', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                el && el.click();
            """)
            self.driver.refresh()
            pass
        
        time.sleep(3)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")


        value = self.scrap_page()
        if value == "NO DATA":
            print("absoulute no data")
            return

        self.save_data_to_excel()
        self.driver.close()


data_scraper = Scraper()
data_scraper.main_workflow()