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

# 4 of n sites

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
                        (By.XPATH, "//li[@data-hook='side-by-side-item']")
                    )
                )


        if len(shows_container) == 0:
            return "NO DATA"
        
        def filter_shows(shows_container):

            only_shows = []
            with open("unwanted_keywords_for_ledgeamp.txt", 'r') as file:
                unwanted_keywords = [line.strip().lower() for line in file.readlines()]

            print(unwanted_keywords)
            for show in shows_container:
                try:
                    title = show.find_element(By.XPATH, ".//a[@data-hook='title']").text.lower()
                except Exception as e:
                    continue

                if not any(keyword in title for keyword in unwanted_keywords):  
                    only_shows.append(show)  

            return only_shows

        def clean_string(s):
                if isinstance(s, list):
                    s = ' '.join(s)  
                
                if s is None:  
                    return ""
                
                return ' '.join(re.sub(r'\s+', ' ', s.replace(',',';').replace('\n', ' ').strip()).split())
        
        def extract_date(text):
            try:
                current_year = datetime.now().year
                date_obj = datetime.strptime(text + f" {current_year}", "%a, %b %d %Y")
                
                if date_obj.date() < datetime.now().date():
                    date_obj = datetime.strptime(text + f" {current_year + 1}", "%a, %b %d %Y")

                return date_obj.strftime("%Y"), date_obj.strftime("%m"), date_obj.strftime("%d")
            except Exception as e:
                print(f"Date parsing error: {e}")
                return "", "", ""


        only_shows = filter_shows(shows_container)

        for show in only_shows:

            try:
                Band_Line1 = show.find_element(
                            By.XPATH, ".//a[@data-hook='title']"
                        ).text
            except:
                Band_Line1 = "" 

            # date first case, 
            try:
                date_text = show.find_element(By.XPATH, ".//div[@data-hook='short-date']").text.strip()
                year, month, day = extract_date(date_text)
            except:
                continue
            
            try:
                venue = show.find_element(By.XPATH, ".//div[@data-hook='short-location']").text.strip()
            except:
                venue = "Unknown"

            date_scraped = datetime.now().strftime('%Y%m%d')

            data = {
                'Date Scraped': date_scraped,
                'Year': year,
                'Month': month,
                'Day': day,
                'Venue': clean_string(venue),
                'Band Line 1': clean_string(Band_Line1),
                
            }
            print(data)
            self.shows_data.append(data) 


        return "success"
    
    def save_data_to_excel(self):
        today = datetime.now().strftime('%Y-%m-%d')

        folder_path = os.path.join(os.getcwd(), "Data")  
        file_name = f"Data_{today}_Ledge_Amp.csv"
        file_path = os.path.join(folder_path, file_name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        count = 1
        while os.path.exists(file_path):
            file_name = f"Data_{today}_Ledge_Amp_{count}.csv"
            file_path = os.path.join(folder_path, file_name)
            count += 1


        df = pd.DataFrame(self.shows_data)
        df.to_csv(file_path, index=False, encoding='utf-8-sig',  sep='|')

        print(f"Data saved to {file_path}")

        
    def main_workflow(self):
        data_scraper.config_driver()
        
        url = "https://www.theledgeamp.com/ledgeevents"
        print("Getting details of :", url)
        self.driver.get(url)
        self.driver.maximize_window()


        time.sleep(1)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        previous_post_count = 0 
        while True:
            try:
                posts = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//li[@data-hook='side-by-side-item']")
                    )
                )
                current_post_count = len(posts)
                print(current_post_count)

                # Check if the post count has increased after clicking "Load More"
                if current_post_count == previous_post_count:
                    print("No more posts to load.")
                    break  

                previous_post_count = current_post_count
                try:
                    load_more_button = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//button[@data-hook='load-more-button']")
                        )
                    )
                    self.driver.execute_script("arguments[0].click();", load_more_button)
                    time.sleep(1.5)  

                except Exception as e:
                    print("Load more button not found. No more events to load.")
                    break
            except Exception as e:
                print(e)
                print("Either no data, or could be error!")
                break
        
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        value = self.scrap_page()
        if value == "NO DATA":
            print("absoulute no data")
            return

        self.save_data_to_excel()
        self.driver.close()


data_scraper = Scraper()
data_scraper.main_workflow()