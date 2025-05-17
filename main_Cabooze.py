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

# 7th of 7th site

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

        shows = wait_show.until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//div[@class='vp-event-row vp-widget-reset vp-venue-thecabooze']")
                    )
                )

        if len(shows) == 0 :
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

            :param show_date: Event date string (e.g., "Sat, Nov 02").
            :param start_year: The year to begin tracking from (defaults to current year).
            """
            if not show_date:
                return {'Year': "", 'Month': "", 'Day': ""}

            if start_year is None:
                start_year = datetime.now().year

            if not hasattr(extract_date, "previous_month"):
                extract_date.previous_month = 0
                extract_date.current_year = start_year

            # Parse the input date: "Nov 02"
            try:
                date_parts = show_date.split(' ')  # ['Nov', '02']
                month_str = date_parts[0]
                day = int(date_parts[1])

                # Convert the month abbreviation to a numeric value (e.g., 'Nov' -> 11)
                month = datetime.strptime(month_str, "%b").month
            except (ValueError, IndexError) as e:
                return {'Year': "", 'Month': "", 'Day': ""}

            # Check if the month has decreased (meaning we are in the next year)
            if month < extract_date.previous_month:
                extract_date.current_year += 1

            extract_date.previous_month = month

            return {
                'Year': extract_date.current_year,'Month': month,'Day': day
            }



        for show in shows:
            # Band line 1 (Tagline)
            try:
                Band_Line1 = show.find_element(
                    By.XPATH, ".//div[@class='vp-promoter']"
                ).text
            except:
                Band_Line1 = ""

            # Band line 2 (Event title)
            try:
                Band_Line2 = show.find_element(
                    By.XPATH, ".//div[@class='vp-event-name']"
                ).text
            except:
                Band_Line2 = ""

            # Band line 3 (Event support)
            try:
                Band_Line3 = show.find_element(
                    By.XPATH, ".//div[@class='vp-support']"
                ).text
            except:
                Band_Line3 = ""


            # Extracting date details
            try:
                date_text = show.find_element(
                    By.XPATH, ".//div[@class='vp-event-row-datetime']"
                ).text.replace(",", '')
                print(date_text)

            except:
                pass

            # Extracting time
            try:
                hour = show.find_element(
                    By.XPATH, ".//span[@class='vp-time']"
                ).text.replace('Show:', '').strip()
            except:
                hour = ""

            
            date_obj = extract_date(date_text)
            date_scraped = datetime.now().strftime('%Y%m%d')  


            data = {
                'Date Scraped': date_scraped,
                'Year': date_obj['Year'],
                'Month': date_obj['Month'],
                'Day': date_obj['Day'],
                'Time' : clean_string(hour), 
                'Venue': "Cabooze",
                'Band Line 1': clean_string(Band_Line1),
                'Band Line 2' : clean_string((Band_Line2)),
                'Band Line 3' : clean_string(Band_Line3)
            }
            print(data)
            self.shows_data.append(data) 

        return "success"
    
    def save_data_to_excel(self):
        today = datetime.now().strftime('%Y-%m-%d')

        folder_path = os.path.join(os.getcwd(), "Data")  
        file_name = f"Data_{today}_Cabooze.csv"
        file_path = os.path.join(folder_path, file_name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        count = 1
        while os.path.exists(file_path):
            file_name = f"Data_{today}_Cabooze_{count}.csv"
            file_path = os.path.join(folder_path, file_name)
            count += 1


        df = pd.DataFrame(self.shows_data)
        df.to_csv(file_path, index=False, encoding='utf-8-sig',  sep='|')

        print(f"Data saved to {file_path}")

        
    def main_workflow(self):
        data_scraper.config_driver()
        
        url = "https://cabooze.com/#/events"
        print("Getting details of :", url)
        self.driver.get(url)
        self.driver.maximize_window()

        time.sleep(3)

        value = self.scrap_page()
        if value == "NO DATA":
            print("absoulute no data")
            return

        self.save_data_to_excel()
        self.driver.close()


data_scraper = Scraper()
data_scraper.main_workflow()