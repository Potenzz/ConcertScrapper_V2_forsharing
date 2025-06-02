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

# pre 1


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

        shows_container = wait_show.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "post_wrapper")))

        
        if len(shows_container) == 0:
            return "NO DATA"

        for item in shows_container:
            try:
                # Extract Band Line 1 (Event title)
                Band_Line1 = wait_show.until(EC.visibility_of(item.find_element(By.CSS_SELECTOR, 'h2 a'))).text
            except:
                Band_Line1 = ""

            try:
                # Extract Band Line 2 (Presented by)
                Band_Line2 = item.find_element(By.CSS_SELECTOR, 'header.post-header p').get_attribute("innerHTML").split('<br>')[0]
            except:
                Band_Line2 = ""

            try:
                # Extract Band Line 3 (Support)
                Band_Line3 = item.find_element(By.CSS_SELECTOR, 'header.post-header p').get_attribute("innerHTML").split('<br>')[1].strip()

            except:
                Band_Line3 = ""

            month_mapping = {
                "january": "01", "jan": "01",
                "february": "02", "feb": "02",
                "march": "03", "mar": "03",
                "april": "04", "apr": "04",
                "may": "05", 
                "june": "06", "jun": "06",
                "july": "07", "jul": "07",
                "august": "08", "aug": "08",
                "september": "09", "sep": "09", "sept": "09",
                "october": "10", "oct": "10",
                "november": "11", "nov": "11",
                "december": "12", "dec": "12"
            }

            try:

                date_time = item.find_element(By.CLASS_NAME, 'post_date').text
                lines = date_time.splitlines()

                if len(lines) > 0:
                    full_date = lines[0].strip() + " " + lines[1].strip()  
                    date_parts = full_date.split()  # ["Saturday,", "October", "12th,", "2024"]

                    if len(date_parts) >= 4:
                        month_name = date_parts[1].lower()  
                        Month = month_mapping.get(month_name, "") 
                        Day = re.findall(r"\d+", date_parts[2])[0]

                        Year = date_parts[3]  # "2024"
                    else:
                        Month, Day, Year = "", "", ""

                if len(lines) > 3:
                    Time = lines[3].strip()  
                else:
                    Time = ""

            except:
                Year, Month, Day, Time = "", "", "", ""


            Venue = "Armory"    

            def clean_string(s):
                if isinstance(s, list):
                    s = ' '.join(s)  
                
                if s is None:  
                    return ""
                
                return ' '.join(re.sub(r'\s+', ' ', s.replace(',',';').replace('\n', ' ').strip()).split())

            date_scraped = datetime.now().strftime('%Y%m%d')  

            data = {
                'Date Scraped': date_scraped,
                'Year': Year,
                'Month': Month,
                'Day': Day,
                "Time" : Time,
                'Venue': Venue,
                'Band Line 1': clean_string(Band_Line1),
                'Band Line 2': clean_string(Band_Line2),
                'Band Line 3': clean_string(Band_Line3),
                
            }
            print(data)
            self.shows_data.append(data)  

        return "success"
    
    def save_data_to_excel(self):
        today = datetime.now().strftime('%Y-%m-%d')

        folder_path = os.path.join(os.getcwd(), "Data")  
        file_name = f"Data_{today}_Armory.csv"
        file_path = os.path.join(folder_path, file_name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        count = 1
        while os.path.exists(file_path):
            file_name = f"Data_{today}_Armory_{count}.csv"
            file_path = os.path.join(folder_path, file_name)
            count += 1


        df = pd.DataFrame(self.shows_data)
        df.to_csv(file_path, index=False, encoding='utf-8-sig',  sep='|')

        print(f"Data saved to {file_path}")

        
    def main_workflow(self):
        data_scraper.config_driver()

        url = "https://armorymn.com/events/"
        print("Getting details of :", url)
        self.driver.get(url)
        self.driver.maximize_window()

        time.sleep(1)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        previous_post_count = 0
        while True:
            try:
                posts = self.driver.find_elements(By.CLASS_NAME, "post_wrapper")
                current_post_count = len(posts)

                # Check if the post count has increased after clicking "Load More"
                if current_post_count == previous_post_count:
                    print("No more posts to load.")
                    break  

                previous_post_count = current_post_count

                load_more_button = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.ID, "more_posts")))
                self.driver.execute_script("document.getElementById('more_posts').click();")
                time.sleep(7)
            except Exception as e:
                print(e)
                print("NO more data")
                break



        value = self.scrap_page()
        if value == "NO DATA":
            print("absoulute no data")
            return

        self.save_data_to_excel()
        self.driver.close()


data_scraper = Scraper()
data_scraper.main_workflow()