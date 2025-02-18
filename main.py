from modules.flight_extractor import extract_flight_info
from modules.flight_augmentor import augment_search_options
from modules.flight_crawler import crawl_flight_data_kayak
from modules.flight_analyzer import (
    json_to_md_table,
    extract_flights_listings_llm_v2
)
from modules.flight_filter import interactive_flight_filter
from modules.utils import save_output
import json
import os
import pandas as pd

def main():
    # Step 1: Extract flight info from user query
    # with open('input.txt', 'r', encoding='utf-8') as file:
    #     user_query = file.read().strip()
    # flight_info = extract_flight_info(user_query)
    # print("Step 1 Completed:flight info extracted")
    # with open('output/step1_flight_info.json', 'r', encoding='utf-8') as file:
    #     flight_info = json.load(file)
    # #Step 2: Augment search options (new step)
    # augmented_searches = augment_search_options(flight_info)
    # print("Step 2 Completed: augmented searches done")

    # with open('output/step2_augmented_searches.json', 'r', encoding='utf-8') as file:
    #     augmented_searches = json.load(file)
    # # Step 3: Crawl flight data for each search option
    # all_flights = {"flights": []}
    # for i, search in enumerate(augmented_searches):
    #     print(f"\nProcessing search option {i+1}/{len(augmented_searches)}...")
    #     crawl_flight_data_kayak(search, i)        
    #     # Step 4: Extract and analyze flight information
        
    #     image_files = []
    #     section = 1
    #     while True:
    #         image_path = f'output/images/kayak_results_{i}_section_{section}.png'
    #         if not os.path.exists(image_path):
    #             break
    #         image_files.append(image_path)
    #         section += 1
        
    #     if not image_files:
    #         print(f"No screenshots found for search option {i+1}")
    #         continue
            
    #     print(f"Processing {len(image_files)} screenshots for search {i+1}...")
        
    #     # Process screenshots for this search
    #     search_flights = extract_flights_listings_llm_v2(image_files, i)

    #     # add date to them
    #     for flight in search_flights["flights"]:
    #         flight['start_date'] = search['start_date']
    #         flight['return_date'] = search['return_date']
    #         flight['number_of_passengers'] = search['number_of_passengers']
    #         flight['other_data'] = search['other_data']
        
    #     # Merge flights from this search into main list
    #     if search_flights and "flights" in search_flights:
    #         all_flights["flights"].extend(search_flights["flights"])
        
        
    # save_output(
    #     all_flights,
    #     'step3_all_crawledflights.json',
    # )
    
    # print(f"\nStep 3 Completed: Total flights collected: {len(all_flights['flights'])}")
    
    # Create table from merged data
    # json_to_md_table(all_flights)
    
    # df = pd.DataFrame.from_records(all_flights['flights'])
    # df.to_excel('output/step3_all_crawledflights.xlsx', index=False)
    # print(f"\nFiltered flights have been saved to xlsx file")    

    # Start interactive filtering with merged data
    interactive_flight_filter("step3_all_crawledflights.json")

    

if __name__ == "__main__":
    main() 