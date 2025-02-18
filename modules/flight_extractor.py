import json
from .utils import openai_req_generator, save_output

def extract_flight_info(user_query):
    # Read the system prompt from file
    with open('prompts/extract_info.md', 'r', encoding='utf-8') as file:
        system_prompt = file.read()
    
    # Get response from LLM
    response = openai_req_generator(
        system_prompt=system_prompt,
        user_prompt=user_query,
        json_output=True,
        model_name="gpt-4o",
    )

    response = json.loads(response)
    
    # Save output
    save_output(
        response,
        'step1_flight_info.json',
    )
    
    return response 