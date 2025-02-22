import json
import pandas as pd
import os
from .utils import openai_req_generator, save_output

def interactive_flight_filter(file_name):
    # Modified version of existing code
    query_count = 1
    
    # Load the flights data from analyzed_data directory
    with open(f'output/{file_name}', 'r', encoding='utf-8') as f:
        initial_flights_data = f.read()
    
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
        
        system_prompt = system_prompt.replace('{flights_data}', initial_flights_data)
        
        # Get filtered results from LLM
        response = openai_req_generator(
            system_prompt=system_prompt,
            user_prompt=user_input,
            json_output=True,  # Changed to True to get JSON response
            model_name="gpt-4o"
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

            os.makedirs('output/step4_interactive_filter', exist_ok=True)
            excel_filename = f'output/step4_interactive_filter/filtered_flights_query_{query_count}.xlsx'
            df.to_excel(excel_filename, index=False)
            print(f"\nFiltered flights have been saved to {excel_filename}")
            
            # Also display the results in a nice format
            save_output(
                flights_data,
                f'filtered_flights_query_{query_count}.json',
                'step4_interactive_filter'
            ) 
        else:
            print("\nNo flights found matching your criteria.")
        
        query_count += 1