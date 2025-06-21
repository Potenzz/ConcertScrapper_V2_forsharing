# -------------------------------------------
# 👨‍💻 Developed by: Vishnu
# 📧 Email: vishnu10kumar11@gmail.com
# 💼 Open for freelance projects – feel free to reach out!
# -------------------------------------------


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

        try:
            container = wait_show.until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'chakra-tabs__tab-panels')]"))
            )

            shows_container = container.find_elements(By.XPATH, ".//div[@role='group']")
        except Exception as e:
            print(f"Error locating event container: {e}")
            return "NO DATA"

        shows_container = wait_show.until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//div[@role='group']")
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

        def extract_date(datetime_str):
            try:
                dt = datetime.fromisoformat(datetime_str)
                return {
                    "Year": dt.year,
                    "Month": dt.month,
                    "Day": dt.day
                }
            except Exception:
                print(f"Date parse error: Invalid datetime format: '{datetime_str}'")
                return {"Year": "", "Month": "", "Day": ""}


        for show in shows_container:

            try:
                # Skip non-event containers (e.g., venue cards) by checking if a <time> element exists
                time_element = show.find_element(By.XPATH, ".//time")
                date_text = time_element.get_attribute("datetime")
            except:
                continue  # No time element → not an event → skip

            try:
                # First try h2 
                band_el = show.find_element(By.XPATH, ".//h2[contains(@class, 'chakra-heading')]")
                Band_Line1 = band_el.text
            except:
                try:
                    # Fallback to h3 
                    band_el = show.find_element(By.XPATH, ".//h3[contains(@class, 'chakra-heading')]")
                    Band_Line1 = band_el.text
                except:
                    Band_Line1 = ""


            try:
                Band_Line2 = show.find_element(
                    By.XPATH, ".//p[contains(@class, 'chakra-text')]"
                ).text
            except:
                Band_Line2 = ""

            formatted_date = extract_date(date_text)
            date_scraped = datetime.now().strftime('%Y%m%d')  

            data = {
                'Date Scraped': date_scraped,
                'Year': formatted_date['Year'],
                'Month': formatted_date['Month'],
                'Day': formatted_date['Day'],
                'Venue': "Live Nation",
                'Band Line 1': clean_string(Band_Line1),
                'Band Line 2': clean_string(Band_Line2),
            }
            print(data)
            self.shows_data.append(data) 

        return "success"
    
    def save_data_to_excel(self):
        today = datetime.now().strftime('%Y-%m-%d')

        folder_path = os.path.join(os.getcwd(), "Data")  
        file_name = f"Data_{today}_LiveNation.csv"
        file_path = os.path.join(folder_path, file_name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        count = 1
        while os.path.exists(file_path):
            file_name = f"Data_{today}_LiveNation_{count}.csv"
            file_path = os.path.join(folder_path, file_name)
            count += 1


        df = pd.DataFrame(self.shows_data)
        df.to_csv(file_path, index=False, encoding='utf-8-sig',  sep='|')

        print(f"Data saved to {file_path}")

        
    def main_workflow(self):
        data_scraper.config_driver()
        
        url = "https://www.livenation.com/venue/KovZ917APzQ/somerset-amphitheater-events#shows"
        print("Getting details of :", url)
        self.driver.get(url)
        self.driver.maximize_window()

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