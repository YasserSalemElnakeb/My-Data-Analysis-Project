from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd

def scrape_jumia_experiment(target_count=100):
    print(f"Starting Real-Life Experiment: Scraping {target_count} phones between 15k - 20k EGP ...\n")

    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")  # Run in maximized mode

    # Initialize the Chrome driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    scraped_data = []
    page_number = 1

    try:
        while len(scraped_data) < target_count:
            print(f"Scraping page {page_number}...")
            
            #1. Navigate to the Jumia smartphones page with price filter
            url = f"https://www.jumia.com.eg/smartphones/?price=15000-20000&page={page_number}"
            driver.get(url)
            time.sleep(3)  # Wait for the page to load

            #3. simulate Human scrolling to load products - Images & Elements
            for scroll in range(1, 4):  # Scroll down 3 times
                driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight/{scroll});")
                time.sleep(2)  # Wait for the page to load completely

            #4. Find Elements Using Class Name , XPath, CSS Selector, or other locators
            product_elements = driver.find_elements(By.XPATH, "//article[contains(@class, 'prd')]")
            print(f"Found {len(product_elements)} products on page {page_number}.")

            if len(product_elements) == 0:
                print("No more products found. Ending scraping.")
                break  # Exit the loop if no products are found
            for item in product_elements:
                if len(scraped_data) >= target_count:
                    break  # Stop if we have reached the target count
                
            #5. Extract Product Name and Price - URL
                try:
                    name = item.find_element(By.CLASS_NAME, "name").get_attribute("textContent").strip()
                    raw_price = item.find_element(By.CLASS_NAME, "prc").get_attribute("textContent").strip()
                    product_url = item.find_element(By.CLASS_NAME, "core").get_attribute("href")
            #Data Cleaning and Formatting
                    clean_price = raw_price.replace("EGP", "").replace(",", "").strip()  # Remove currency
                    numeric_price = float(clean_price)  # Convert to float for comparison
            #Data Validation
                    if 15000 <= numeric_price <= 20000:
                        scraped_data.append({
                            "Product Name": name,
                            "Product Price": numeric_price,
                            "Product URL": product_url
                        })
                        print(f"[{len(scraped_data)}/{target_count}] valid: {name[:30]}... | {numeric_price}")
                    else:
                        print(f"[Skipped] out of range Ad: EGP {numeric_price})")
                except Exception as e:
                    continue  # Skip this product if there's an error extracting data
            page_number += 1  # Move to the next page
    finally:
        print("\nScraping completed. Closing the browser.")
        time.sleep(3)  # Optional: Wait for a moment before closing
        driver.quit()  # Close the browser
        df = pd.DataFrame(scraped_data)
        file_name = "jumia_phones_15k_20k.csv"
        df.to_csv(file_name, index=False, encoding="utf-8-sig")
        print(f"\nSUCCESS! Cleaned data saved to {file_name}")
        return df  # Return the DataFrame for further use if needed
final_data = scrape_jumia_experiment(target_count=100)
print("\nFinal Dataset Preview:")
print(final_data.head())  # Display the first few rows of the scraped data