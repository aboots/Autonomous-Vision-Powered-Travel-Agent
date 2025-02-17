from modules.flight_extractor import extract_flight_info
from modules.flight_augmentor import augment_search_options
from modules.flight_crawler import crawl_flight_data_kayak
from modules.flight_analyzer import (
    extract_flight_listings_manually,
    create_flights_table,
    extract_flights_listings_llm,
    extract_flights_listings_llm_v2
)
from modules.flight_filter import interactive_flight_filter
import json

def main():
    # try:
    # Step 1: Extract flight info from user query
    # with open('test.txt', 'r', encoding='utf-8') as file:
    #     user_query = file.read().strip()
    # flight_info = extract_flight_info(user_query)
    # print("flight info extracted")
    # with open('output/flight_info.json', 'r', encoding='utf-8') as file:
    #     flight_info = json.load(file)
    # Step 2: Augment search options (new step)
    # augmented_searches = augment_search_options(flight_info)
    # print("augmented searches done")

    with open('output/augmented_searches.json', 'r', encoding='utf-8') as file:
        augmented_searches = json.load(file)
    augmented_searches = [augmented_searches[0]]
    # # Step 3: Crawl flight data for each search option
    for i, search in enumerate(augmented_searches):
        html_content = crawl_flight_data_kayak(search, i)
        
        # Step 4: Extract and analyze flight information
        # if html_content:
        #     flights_text = extract_flight_listings(html_content)
        #     analysis = analyze_flights(flights_text)
        #     table_output = analyze_flights_table(flights_text)
    # for i in range(len(augmented_searches)):
    #     with open(f'output/crawled_data/skyscanner_results_{i}.html', 'r', encoding='utf-8') as file:
    #         html_content = file.read()
        # analysis = analyze_flights(flights_text)
        # table_output = analyze_flights_table(flights_text)
    
    # flights_data = extract_flights_listings_llm_v2('kayak_results_0.png')

    # # Step 5: Interactive filtering
    # interactive_flight_filter()
        
    # except Exception as e:
    #     print(f"Error in main process: {str(e)}")

if __name__ == "__main__":
    main() 