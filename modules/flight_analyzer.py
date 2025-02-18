from bs4 import BeautifulSoup
import json
from .utils import openai_req_generator, save_output
import os
import pandas as pd

import os

def load_prompt(prompt_name):
    """Load prompt from prompts directory"""
    prompt_path = os.path.join('prompts', f'{prompt_name}.md')
    with open(prompt_path, 'r', encoding='utf-8') as file:
        return file.read()
    
def extract_flights_listings_llm_v2(image_urls, i):
    prompt = load_prompt('extract_flights_images')
    
    # Ensure image_urls is a list
    if isinstance(image_urls, str):
        image_urls = [image_urls]
    
    # ignore last two items becuase buttom of page
    image_urls = image_urls[:-2] if len(image_urls) > 4 else image_urls
    
    # Process images in batches of 3
    batch_size = 3
    all_flights = []
    
    for i in range(0, len(image_urls), batch_size):
        batch = image_urls[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1} ({len(batch)} images)...")
        
        response = openai_req_generator(
            system_prompt=prompt,
            user_prompt=f"Please analyze these sequential screenshots (batch {i//batch_size + 1}) of the flight search results webpage and provide a consolidated list.",
            files=batch,
            json_output=True,
            model_name="gpt-4o",
            temperature=0.1
        )
        
        # Convert response to proper format if needed
        if isinstance(response, str):
            response = json.loads(response)
        
        # Extract flights from batch response and add to main list
        batch_flights = response.get('flights', [])
        all_flights.extend(batch_flights)
    
    # Create final consolidated output
    final_output = {
        "flights": all_flights
    }
    
    # Save formatted output
    save_output(
        final_output,
        f'crawledflights_{i}.json',
        'analyzed_data'
    )

    # json_to_md_table(final_output)

    # df = pd.DataFrame.from_records(final_output['flights'])
    # df.to_excel('output/analyzed_data/all_crawledflights.xlsx', index=False)
    # print(f"\nFiltered flights have been saved to output/analyzed_data/all_crawledflights.xlsx")    

    
    return final_output


def json_to_md_table(json_data):
    """
    Convert flight JSON data to a markdown table format.
    
    Args:
        json_data (dict): Dictionary containing flight information
        
    Returns:
        str: Markdown formatted table string
    """
    if not json_data.get('flights') or len(json_data['flights']) == 0:
        md_table = "No flight data available"
        return
    
    # Get headers from the first flight's keys
    headers = list(json_data['flights'][0].keys())
    md_table = "\n"
    # Create table header
    md_table += "| " + " | ".join(headers) + " |\n"
    md_table += "|" + "|".join(["-------------" for _ in headers]) + "|\n"
    
    # Add each flight as a row
    for flight in json_data['flights']:
        row = [str(flight.get(header, '')) for header in headers]
        md_table += "| " + " | ".join(row) + " |\n"

    save_output(
        md_table,
        'step3_all_crawledflights.md',
    )
    

def extract_flights_listings_llm(html_content):
    """
    Extract flight information from HTML content using the specified prompt
    Returns the filtered flight listings
    """
    # try:
    # Parse HTML and extract just the flight results wrapper content
    soup = BeautifulSoup(html_content, 'html.parser')
    flight_results = soup.find('div', id='flight-results-list-wrapper')
    # body_content = soup.body
    
    if not flight_results:
        print("No flight results content found in HTML")
        return None
        
    # Convert flight results content to string
    flights_html = str(flight_results)
    print(len(flights_html))
    
    #save the content in debug html
    temp_html_path = 'debug_html.html'
    with open(temp_html_path, 'w', encoding='utf-8') as file:
        file.write(flights_html)
    
    # Load the extraction prompt
    prompt = load_prompt('extract_flights')
    
    # Send HTML file along with prompt to LLM
    response = openai_req_generator(
        system_prompt=prompt,
        user_prompt="Please analyze the HTML file containing flight listings.",
        files=[temp_html_path],
        json_output=False,
        temperature=0.1
    )
    
    # Save formatted table
    save_output(
        response,
        'all_crawledflights.md',
    )
    
    return response
        
    # except Exception as e:
    #     print(f"Error preprocessing HTML content: {str(e)}")
    #     return None

def extract_flight_listings_manually(html_content):
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
            # Save extracted flights
        save_output(
            filtered_flights,
            'extracted_flights.json',
        )
        
        flights_text = json.dumps(filtered_flights, ensure_ascii=False, indent=2)
        
        return flights_text
    
    except Exception as e:
        print(f"Error extracting flight listings: {str(e)}")
        return None
    
    # Existing analysis code
    # ... existing code ...
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
    # Save analysis results
    save_output(
        response,
        'flight_analysis.json',
        'analyzed_data'
    )
    
    return response

def create_flights_table_llm(flights_text):
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
    
    # Save formatted table
    save_output(
        response,
        'step3_ll_crawledflights_table.md',
    )
    
    return response 