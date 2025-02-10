import json
import pandas as pd
import os
from .utils import openai_req_generator, save_output

def interactive_flight_filter():
    # Modified version of existing code
    query_count = 1
    
    # Load the flights data from analyzed_data directory
    with open('output/extracted_flights.json', 'r', encoding='utf-8') as f:
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
                # Save filtered results

            os.makedirs('output/excel', exist_ok=True)
            excel_filename = f'output/excel/filtered_flights_query_{query_count}.xlsx'
            df.to_excel(excel_filename, index=False)
            print(f"\nFiltered flights have been saved to {excel_filename}")
            
            # Also display the results in a nice format
            save_output(
                flights_data,
                f'filtered_flights_query_{query_count}.json',
                'filtered_results'
            ) 
        else:
            print("\nNo flights found matching your criteria.")
        
        query_count += 1