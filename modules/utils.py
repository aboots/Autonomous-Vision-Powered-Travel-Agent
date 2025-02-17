import os
from openai import OpenAI
from dotenv import load_dotenv
import json
from pydantic import BaseModel
from typing import List  # Add this import at the top
import base64


load_dotenv()

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
)

class Flight(BaseModel):
    source_airport: str
    destination_airport: str
    start_date: str
    return_date: str
    number_of_passengers: int
    # other_data: dict

class FlightSearch(BaseModel):
    flights: List[Flight]


def openai_req_list_flights(system_prompt, user_prompt, temperature=0.1):
    response_format = FlightSearch
    chat_completion = client.beta.chat.completions.parse(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="gpt-4o-mini",
            response_format=response_format,
            temperature=temperature,
    )
    flights = chat_completion.choices[0].message.parsed.flights
    output_json = []
    for flight in flights:
        output_json.append(flight.model_dump())
    return output_json

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def openai_req_generator(system_prompt, user_prompt, files=None, json_output=False, temperature=0.1, model_name="gpt-4o-mini"):
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    
    if files:
        content_parts = []
        for file_path in files:
            base64_image = encode_image(file_path)
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                "detail": "high"
            })
        messages.append({"role": "user", "content": content_parts})
    else:
        messages.append({"role": "user", "content": user_prompt})

    if json_output:
        response_format = {"type": "json_object"}
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model_name,
            response_format=response_format,
            temperature=temperature,
            max_tokens=4096,
        )
    else:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model_name,
            temperature=temperature,
            max_tokens=4096,
        )
    return chat_completion.choices[0].message.content

def upload_file_to_gpt_api(file_data):
    # OpenAI's file upload endpoint expects a file object and a purpose
    response = client.files.create(
        file=file_data,
        purpose='assistants'  # Set the purpose according to your use case
    )
    print("uploaded file")
    # Access id as an attribute instead of dictionary key
    return response.id, response

def save_output(data, filename, output_type=None):
    """
    Save output data to the appropriate folder
    output_type: One of 'flight_info', 'augmented_searches', 'crawled_data', 
                'analyzed_data', 'filtered_results'
    """
    if output_type is None:
        output_dir = "output"
    else:   
        output_dir = f"output/{output_type}"
    
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, filename)
    
    # Handle different file types
    if filename.endswith('.json'):
        if isinstance(data, str):
            data = json.loads(data)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(data) 