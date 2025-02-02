import os
from openai import OpenAI
from dotenv import load_dotenv

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

def process_input_file():
    try:
        # Read the input query from file
        with open('test.txt', 'r', encoding='utf-8') as file:
            user_query = file.read().strip()
        
        # Process the query through extract_flight_info
        result = extract_flight_info(user_query)
        
        return result
        
    except FileNotFoundError:
        print("Error: test.txt file not found")
        return None
    except Exception as e:
        print(f"Error processing input: {str(e)}")
        return None

if __name__ == "__main__":
    process_input_file()
