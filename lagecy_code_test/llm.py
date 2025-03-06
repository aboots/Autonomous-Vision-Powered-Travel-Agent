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
import pandas as pd

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

        homedir = os.path.expanduser("~")
        chrome_options.binary_location = f"{homedir}/chrome-linux64/chrome"
        webdriver_service = Service(f"{homedir}/chromedriver-linux64/chromedriver")

        # Choose Chrome Browser
        browser = webdriver.Chrome(service=webdriver_service, options=chrome_options)
        
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
        
        # Find all flight listing elements using the specific class
        flight_elements = soup.find_all('div', class_='itinerary_wrapper__NZYJF')
        
        # Extract relevant information from each flight
        filtered_flights = []
        for flight in flight_elements:
            try:
                # Extract airline info
                airline_name = flight.find('p', class_='route-airline-name_airlineName__UMWN5')
                flight_number = flight.find('p', class_='route-airline-name_flightNo__HJ2Iq')
                
                # Extract times
                time_elements = flight.find_all('div', class_='route-two-line-part_routeTwoLineTopPart__JWDky')
                departure_time = time_elements[0].get_text().strip() if len(time_elements) > 0 else None
                arrival_time = time_elements[1].get_text().strip() if len(time_elements) > 1 else None
                
                # Extract cities
                city_elements = flight.find_all('div', class_='route-two-line-part_routeTwoLineBottomPart__XD5_T')
                departure_city = city_elements[0].get_text().strip() if len(city_elements) > 0 else None
                arrival_city = city_elements[1].get_text().strip() if len(city_elements) > 1 else None
                
                # Extract duration
                duration = flight.find('span', class_='route-image_durationTime__vPpj0')
                
                # Extract price
                price_element = flight.find('div', class_='itinerary_price__mBl5A')
                
                # Extract remaining seats
                remaining_seats = flight.find('span', class_='mx-1 text-xs text-green-secondary text-nowrap')
                
                flight_info = {
                    'airline': airline_name.text.strip() if airline_name else None,
                    'flight_number': flight_number.text.strip() if flight_number else None,
                    'departure_time': departure_time,
                    'departure_city': departure_city,
                    'arrival_time': arrival_time,
                    'arrival_city': arrival_city,
                    'duration': duration.text.strip() if duration else None,
                    'price': price_element.text.strip() if price_element else None,
                    'remaining_seats': remaining_seats.text.strip() if remaining_seats else None
                }
                filtered_flights.append(flight_info)
            except AttributeError as e:
                print(f"Error processing flight element: {str(e)}")
                continue
        
        # Convert to a formatted string for LLM input
        # Save directly as JSON
        with open('extracted_flights.json', 'w', encoding='utf-8') as f:
            json.dump(filtered_flights, f, ensure_ascii=False, indent=2)
        flights_text = json.dumps(filtered_flights, ensure_ascii=False, indent=2)
        
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

def analyze_flights_table(flights_text):
    """Format flight information in a readable table format"""
    # Read the system prompt from file
    with open('prompts/format_table.md', 'r', encoding='utf-8') as file:
        system_prompt = file.read()
    
    # Get formatted table from LLM
    response = openai_req_generator(
        system_prompt=system_prompt,
        user_prompt=flights_text,
        json_output=False,  # We want markdown table output
        temperature=0.1
    )
    
    # Write output to file
    with open('all_flights_table.md', 'w', encoding='utf-8') as file:
        file.write("# Available Flights\n\n")
        file.write(response)
    
    return response

def interactive_flight_filter():
    """Handle interactive conversation with user for flight filtering"""
    # Load the flights data
    with open('extracted_flights.json', 'r', encoding='utf-8') as f:
        flights_data = f.read()
    
    # Read the system prompt for interactive filtering
    with open('prompts/interactive_filter.md', 'r', encoding='utf-8') as file:
        system_prompt = file.read()
    
    print("\nWelcome to the flight filtering system!")
    print("You can ask questions like:")
    print("- Show me flights under $500")
    print("- Which morning flights are available?")
    print("- I prefer direct flights with Emirates")
    print("Type 'exit' to end the conversation.\n")
    
    query_count = 1
    while True:
        user_input = input("\nWhat would you like to know about the flights? ")
        
        if user_input.lower() == 'exit':
            break
        
        # Combine flights data with user query
        combined_prompt = f"Available flights data:\n{flights_data}\n\nUser query: {user_input}"
        
        # Get filtered results from LLM
        response = openai_req_generator(
            system_prompt=system_prompt,
            user_prompt=combined_prompt,
            json_output=True,  # Changed to True to get JSON response
            temperature=0.1
        )
        
        # Convert response to DataFrame and save to Excel
        if isinstance(response, str):
            filtered_flights = json.loads(response)
        else:
            filtered_flights = response
            
        if filtered_flights and len(filtered_flights) > 0:
            flights_data = filtered_flights["flights"]

            # Create DataFrame directly from the list of flight dictionaries
            df = pd.DataFrame.from_records(flights_data)
            excel_filename = f'filtered_flights_query_{query_count}.xlsx'
            df.to_excel(excel_filename, index=False)
            print(f"\nFiltered flights have been saved to {excel_filename}")
            
            # Also display the results in a nice format
            with open(f'output_filtered.md', 'w', encoding='utf-8') as file:
                file.write("# Available Flights\n\n")
                file.write(response)
        else:
            print("\nNo flights found matching your criteria.")
        
        query_count += 1

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
        # with open('flight_search_results.html', 'r', encoding='utf-8') as f:
        #     html_content = f.read()
        # print('HTML content loaded for debugging')
        
        # # Extract relevant flight information
        # flights_text = extract_flight_listings(html_content)
        # print('Flight Information Extracted')
        
        # # Format and display flights in table format
        # table_output = analyze_flights_table(flights_text)
        # print('Flight Table Generated')
        
        # Start interactive filtering session
        interactive_flight_filter()
        
    except Exception as e:
        print(f"Error processing input: {str(e)}")
        return None

if __name__ == "__main__":
    process_input_file()
