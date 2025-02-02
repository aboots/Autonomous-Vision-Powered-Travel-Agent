import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import requests
import time
import os.path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

load_dotenv()

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
)

def openai_req_generator(system_prompt, user_prompt, json_output=False, temperature=0.1):
    if json_output:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            temperature=temperature,
        )
    else:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="gpt-4o-mini",
            temperature=temperature,
        )
    return chat_completion.choices[0].message.content


def extract_flight_info(user_query):
    # Read the system prompt from file
    with open('prompts/extract_info.md', 'r', encoding='utf-8') as file:
        system_prompt = file.read()
    
    # Get response from LLM
    response = openai_req_generator(
        system_prompt=system_prompt,
        user_prompt=user_query,
        json_output=True,
        temperature=0.1
    )
    
    # Write output to file
    with open('flight_info_output.md', 'w', encoding='utf-8') as file:
        file.write(f"### Flight Information Extracted\n```json\n{response}\n```")
    
    return response


        
def crawl_flight_data(flight_info):
    # Convert the JSON string to a dictionary if it's a string
    if isinstance(flight_info, str):
        flight_info = json.loads(flight_info)
    
    # Construct the URL with flight information
    base_url = "https://www.flytodayir.com/flight/search"
    params = {
        "departure": f"{flight_info['source_airport']}",
        "arrival": f"{flight_info['destination_airport']}", 
        "departureDate": flight_info['start_date'],
        "adt": flight_info['number_of_passengers'],
        "chd": "0",
        "inf": "0",
        "cabin": "1",
        "isAnyWhere": "false"
    }
    
    try:
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        # chrome_options.add_argument("--headless") # Ensure GUI is off
        
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)

        # homedir = os.path.expanduser("~")
        # chrome_options.binary_location = f"{homedir}/chrome-linux64/chrome"
        # webdriver_service = Service(f"{homedir}/chromedriver-linux64/chromedriver")

        # # Choose Chrome Browser
        # browser = webdriver.Chrome(service=webdriver_service, options=chrome_options)
        
        # Construct and visit the URL
        final_url = requests.Request('GET', base_url, params=params).prepare().url
        print(f"Final URL: {final_url}")
        driver.get(final_url)
        
        # Wait for page to be fully loaded
        print("Waiting for page to load...")
        time.sleep(30)  # Wait 30 seconds for the page to load completely
        
        # Get the page source after waiting
        page_content = driver.page_source
        print("Page content captured")
        
        # Save the HTML response to a file
        with open('flight_search_results.html', 'w', encoding='utf-8') as f:
            f.write(page_content)
            print("HTML saved to file")
            
        driver.quit()
        return page_content
            
    except Exception as e:
        print(f"Error making request: {str(e)}")
        if 'driver' in locals():
            driver.quit()
        return None

def extract_flight_listings(html_content):
    """Extract relevant flight information from the HTML content"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all flight listing elements (you'll need to adjust these selectors based on the actual HTML structure)
        flight_elements = soup.find_all('div', class_='flight-listing')  # Update this selector
        
        # Extract relevant information from each flight
        filtered_flights = []
        for flight in flight_elements:
            try:
                flight_info = {
                    'airline': flight.find('div', class_='airline-name').text.strip(),  # Update selectors
                    'departure_time': flight.find('div', class_='departure-time').text.strip(),
                    'arrival_time': flight.find('div', class_='arrival-time').text.strip(),
                    'price': flight.find('div', class_='price').text.strip(),
                    # Add other relevant fields
                }
                filtered_flights.append(flight_info)
            except AttributeError:
                continue
        
        # Convert to a formatted string for LLM input
        flights_text = "Available Flights:\n"
        for idx, flight in enumerate(filtered_flights, 1):
            flights_text += f"\nFlight {idx}:\n"
            for key, value in flight.items():
                flights_text += f"{key}: {value}\n"
        
        # Save the extracted flight information to a file
        with open('extracted_flights.md', 'w', encoding='utf-8') as f:
            f.write("### Extracted Flight Information\n\n")
            f.write(flights_text)
            
        return flights_text
    
    except Exception as e:
        print(f"Error extracting flight listings: {str(e)}")
        return None

def analyze_flights(flights_text):
    """Send filtered flight information to LLM for analysis"""
    # Read the system prompt from file
    with open('prompts/analyze_flights.md', 'r', encoding='utf-8') as file:
        system_prompt = file.read()
    
    # Save the content being sent to LLM
    with open('llm_input.md', 'w', encoding='utf-8') as file:
        file.write("### System Prompt\n\n")
        file.write(system_prompt)
        file.write("\n\n### User Input (Flight Data)\n\n")
        file.write(flights_text)
    
    # Get response from LLM
    response = openai_req_generator(
        system_prompt=system_prompt,
        user_prompt=flights_text,
        json_output=True,
        temperature=0.1
    )
    
    # Write output to files
    with open('flight_analysis_output.json', 'w', encoding='utf-8') as file:
        json.dump(response, file, ensure_ascii=False, indent=2)
    
    with open('flight_analysis_output.md', 'w', encoding='utf-8') as file:
        file.write("### Flight Analysis Results\n\n```json\n")
        json.dump(response, file, ensure_ascii=False, indent=2)
        file.write("\n```")
    
    return response

def process_input_file():
    try:
        # Read the input query from file
        # with open('test.txt', 'r', encoding='utf-8') as file:
        #     user_query = file.read().strip()
        
        # # Process the query through extract_flight_info
        # result = extract_flight_info(user_query)

        # with open('flight_info_output.json', 'r') as f:
        #     result = json.load(f)
        # print('LLM Answered')
        
        # # Crawl flight data
        # html_content = crawl_flight_data(result)
        # print('Webpage Crawled')

        # For debugging, read the saved HTML content
        with open('flight_info_output.json', 'r', encoding='utf-8') as f:
            html_content = f.read()
        print('HTML content loaded for debugging')
        
        # Extract relevant flight information
        flights_text = extract_flight_listings(html_content)
        if flights_text:
            print('Flight Information Extracted')
            
            # Analyze flights using LLM
            analysis = analyze_flights(flights_text)
            print('Flight Analysis Complete')
            return analysis
        
    except Exception as e:
        print(f"Error processing input: {str(e)}")
        return None

if __name__ == "__main__":
    process_input_file()
