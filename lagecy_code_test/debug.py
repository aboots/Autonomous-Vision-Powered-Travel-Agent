import os
import json
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../modules')))


step2_file = 'output/step2_augmented_searches.json'
if os.path.exists(step2_file):
    with open(step2_file, 'r') as f:
        augmented_searches = json.load(f)
    print("Step 2: Loading existing augmented searches from file")

search = augmented_searches[0]
i = 0

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import json
import requests
import time
from utils import save_output, openai_req_generator
from selenium.webdriver.chrome.service import Service
import os
from PIL import Image
import io

def crawl_flight_data_kayak(flight_info, i):
    # Construct Kayak URL with proper format
    base_url = "https://www.kayak.com/flights/"
    
    # Format airports (add 'nearby' suffix for broader search)
    source = f"{flight_info['source_airport'].upper()},nearby"
    destination = f"{flight_info['destination_airport'].upper()},nearby"
    
    # Format date (YYYY-MM-DD)
    date_str = flight_info['start_date']
    
    # Format passengers
    passengers = f"{flight_info['number_of_passengers']}adults"
    
    # Construct URL path
    url_path = f"{source}-{destination}/{date_str}/{passengers}?sort=bestflight_a"
    
    url = base_url + url_path
    try:
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add random user agent
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

        homedir = os.path.expanduser("~")
        chrome_options.binary_location = f"{homedir}/chrome-linux64/chrome"
        webdriver_service = Service(f"{homedir}/chromedriver-linux64/chromedriver")

        # Initialize driver
        driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
        
        # Execute CDP commands to modify navigator.webdriver flag
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'})
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print(f"Kayak URL: {url}")
        driver.get(url)
        
        # Handle cookie consent
        try:
            wait = WebDriverWait(driver, 10)
            cookie_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.RxNS')))
            accept_buttons = driver.find_elements(By.CSS_SELECTOR, 'button.RxNS')
            for button in accept_buttons:
                if button.text.strip().lower() == 'accept all':
                    button.click()
                    print("Accepted cookies")
                    break
        except TimeoutException:
            print("Cookie consent button not found or not clickable")
        
        print("Waiting for page to load...")
        time.sleep(10)
        
        
        # Set window size for consistent screenshots
        driver.set_window_size(1920, 1200)
        
        # Scroll to the filters section (left sidebar)
        driver.execute_script("window.scrollTo(0, 450)")
        time.sleep(2)

               # Save the HTML content of the page
        page_content = driver.page_source
        html_file_path = f'output/step3_images/kayak_page_{i}.html'
        with open(html_file_path, 'w', encoding='utf-8') as html_file:
            html_file.write(page_content)
        print(f"Saved HTML content to {html_file_path}")

        # Take screenshot of the filters section
        filters_screenshot_path = f'output/step3_images/kayak_filters_{i}.png'
        driver.save_screenshot(filters_screenshot_path)
        
        # Enhance screenshot quality
        img = Image.open(filters_screenshot_path)
        img = img.convert('RGB')
        img = img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS)
        img.save(filters_screenshot_path, 'PNG', quality=100, optimize=False)
        
        # Create system and user prompts for GPT-4o
        system_prompt = """
        You are an expert in web automation. Analyze the screenshot of a Kayak flight search page 
        and identify the exact XPath or CSS selector for the Air Canada checkbox in the airlines filter section.
        Return ONLY the most reliable selector that can be used with Selenium to click on the Air Canada checkbox.
        Format your response as a JSON object with keys 'selector_type' (either 'xpath' or 'css') and 'selector' (the actual selector string).
        """
        
        user_prompt = "Find the Air Canada filter checkbox in this Kayak flight search page and provide the selector to click it."
        
        gpt_response = openai_req_generator(
            system_prompt, 
            user_prompt, 
            files=[filters_screenshot_path], 
            json_output=True, 
            model_name="gpt-4o"
        )

        gpt_response = json.loads(gpt_response)
        print(gpt_response)
        
        # Extract selector information
        try:
            selector_type = gpt_response.get('selector_type', 'xpath')
            selector = gpt_response.get('selector', '')
            
            print(f"Using {selector_type} selector: {selector}")
            
            # Click on the Air Canada filter
            wait = WebDriverWait(driver, 10)
            if selector_type.lower() == 'xpath':
                air_canada_checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
            else:  # CSS selector
                air_canada_checkbox = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            
            # Click the checkbox
            air_canada_checkbox.click()
            print("Successfully clicked on Air Canada filter")
            
            # Wait for results to update
            time.sleep(5)
        except Exception as e:
            print(f"Error clicking Air Canada filter: {str(e)}")
            # Fallback: try a more generic approach if the specific selector fails
            try:
                # Look for checkboxes near "Air Canada" text
                air_canada_elements = driver.find_elements(By.XPATH, "//span[contains(text(), 'Air Canada')]/ancestor::label//input[@type='checkbox']")
                if air_canada_elements:
                    driver.execute_script("arguments[0].click();", air_canada_elements[0])
                    print("Clicked Air Canada filter using fallback method")
                    time.sleep(5)
            except Exception as fallback_error:
                print(f"Fallback method also failed: {str(fallback_error)}")
        return
        # Get total page height after filtering
        total_height = driver.execute_script("return document.body.scrollHeight")
        
        # Create output directory
        os.makedirs('output/step3_images', exist_ok=True)
        
        # Screenshot parameters
        viewport_height = 1000
        overlap = 100
        current_position = 0
        section = 0
        
        # Take screenshots of filtered results
        while current_position < total_height:
            driver.execute_script(f"window.scrollTo(0, {current_position})")
            time.sleep(2)
            
            screenshot_path = f'output/step3_images/kayak_results_{i}_section_{section + 1}.png'
            driver.save_screenshot(screenshot_path)
            
            # Enhance screenshot quality
            img = Image.open(screenshot_path)
            img = img.convert('RGB')
            img = img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS)
            img.save(screenshot_path, 'PNG', quality=100, optimize=False)
            
            print(f"Captured section {section + 1} at position {current_position}/{total_height}")
            
            current_position += (viewport_height - overlap)
            section += 1
        
        driver.quit()
        return f'output/step3_images/kayak_results_{i}_section_*.png'
        
    except Exception as e:
        print(f"Error crawling Kayak: {str(e)}")
        if 'driver' in locals():
            driver.quit()
        return None


crawl_flight_data_kayak(search, i)
