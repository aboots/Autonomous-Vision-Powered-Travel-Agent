import json
from .utils import openai_req_list_flights, save_output, openai_req_generator

def augment_search_options(flight_info):
    # Read the system prompt for augmentation
    with open('prompts/augment_search.md', 'r', encoding='utf-8') as file:
        system_prompt = file.read()
    
    # Convert flight_info to string if it's a dict
    if isinstance(flight_info, dict):
        flight_info = json.dumps(flight_info)
    # print(flight_info)
    
    # Get augmented search options from LLM
    response = openai_req_generator(
        system_prompt=system_prompt,
        user_prompt=flight_info,
        json_output=True,
    )
    
    response = json.loads(response)
    response = response['flights']
    # Save output
    save_output(
        response,
        'step2_augmented_searches.json',
    )
    
    return response 