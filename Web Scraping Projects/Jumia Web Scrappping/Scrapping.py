from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd

def scrape_jumia_live():
    print("Launching live browser via Selenium...")

    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")  # Run in maximized mode

    # Initialize the Chrome driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        #1. Navigate to the Jumia live page
        url = "https://www.jumia.com.eg/smartphones/"
        driver.get(url)

        #2. Time to scrape the data
        print("page loaded, waiting for 5 seconds...")
        time.sleep(5)  # Wait for the page to load completely

        #3. simulate Human scrolling to load products - Images & Elements
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)  # Wait for the page to load completely

        #4. Find Elements Using Class Name , XPath, CSS Selector, or other locators
        product_elements = driver.find_elements(By.XPATH, "//article[contains(@class, 'prd')]")
        print(f"Found {len(product_elements)} products on the page.\n")

        scraped_data = []

        #5. Extract Data from Each Product Element
        for item in product_elements[:5]:  # Limit to first 5 products for demonstration
            try:
                name = item.find_element(By.CLASS_NAME, "name").get_attribute("textContent").strip()
                price = item.find_element(By.CLASS_NAME, "prc").get_attribute("textContent").strip()
                scraped_data.append({
                    "Product Name": name,
                    "Product Price": price,
                })
                print(f"Live Extracted: {name} - {price}")
                product_link = item.get_attribute("href")

            except Exception as e:
                continue  # Skip this product if there's an error extracting data

        return pd.DataFrame(scraped_data)

    finally:
            # keep the browser open for 5 seconds to view the results , then close it
            print("\nScraping complete. Closing browser in 5 seconds...")
            time.sleep(5)
            driver.quit()
df_live = scrape_jumia_live()
print("\nfinal Data:")
print(df_live)