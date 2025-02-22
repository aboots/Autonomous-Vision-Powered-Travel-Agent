from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from modules.flight_extractor import extract_flight_info
from modules.flight_augmentor import augment_search_options
from modules.flight_crawler import crawl_flight_data_kayak
from modules.flight_analyzer import (
    json_to_md_table,
    extract_flights_listings_llm_v2,
    create_html_table,
    create_step1_table,
    create_step2_table
)
from modules.flight_filter import interactive_flight_filter, interactive_flight_filter_v2
from modules.utils import save_output
import json
import os
import pandas as pd
import shutil

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

def process_flight_search(user_query):
    results = {
        'step1': None,
        'step2': None,
        'step3': None,
        'final_table': None
    }
    
    # Step 1: Extract flight info
    flight_info = extract_flight_info(user_query)
    print("Step 1 Completed:flight info extracted")
    results['step1'] = flight_info
    
    # Step 2: Augment search options
    augmented_searches = augment_search_options(flight_info)
    print("Step 2 Completed: augmented searches done")
    results['step2'] = augmented_searches
    
    # Step 3: Crawl and process flights
    all_flights = {"flights": []}
    for i, search in enumerate(augmented_searches):
        print(f"\nProcessing search option {i+1}/{len(augmented_searches)}...")
        # Step 4: Extract and analyze flight information
        crawl_flight_data_kayak(search, i)
        
        image_files = []
        section = 1
        while True:
            image_path = f'output/step3_images/kayak_results_{i}_section_{section}.png'
            if not os.path.exists(image_path):
                break
            image_files.append(image_path)
            section += 1
            
        search_flights = extract_flights_listings_llm_v2(image_files, i)
        
        for flight in search_flights["flights"]:
            flight.update({
                'start_date': search['start_date'],
                'return_date': search['return_date'],
                'number_of_passengers': search['number_of_passengers'],
                'other_data': search['other_data']
            })
            
        if search_flights and "flights" in search_flights:
            all_flights["flights"].extend(search_flights["flights"])
    save_output(
        all_flights,
        'step3_all_crawledflights.json',
    )
    
    print(f"\nStep 3 Completed: Total flights collected: {len(all_flights['flights'])}")
    
    # Create table from merged data
    json_to_md_table(all_flights)
    df = pd.DataFrame.from_records(all_flights['flights'])
    df.to_excel('output/step3_all_crawledflights.xlsx', index=False)
    print(f"\nFiltered flights have been saved to xlsx file")    

    # Start interactive filtering with merged data
    interactive_flight_filter("step3_all_crawledflights.json")
    results['step3'] = all_flights
    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        user_query = request.form['query']
    else:
        user_query = request.args.get('query', '')
    
    # Initialize empty results
    results = {
        'step1': None,
        'step2': None,
        'step3': None,
        'step4': None
    }
    return render_template('results.html', results=results, query=user_query)

@socketio.on('start_search')
def handle_search(user_query):
    # Step 1: Extract flight info or load from file
    step1_file = 'output/step1_flight_info.json'
    if os.path.exists(step1_file):
        with open(step1_file, 'r') as f:
            flight_info = json.load(f)
        print("Step 1: Loading existing flight info from file")
    else:
        flight_info = extract_flight_info(user_query)
        print("Step 1: Extracting new flight info")
    
    # Create HTML table for step 1
    step1_table = create_step1_table(flight_info)
    step1_result = {
        'title': 'Flight Information Extraction',
        'data': flight_info,
        'table': step1_table,
        'description': 'Extracted parameters from your search query'
    }
    emit('step1_complete', step1_result)
    
    # Step 2: Augment search options or load from file
    step2_file = 'output/step2_augmented_searches.json'
    if os.path.exists(step2_file):
        with open(step2_file, 'r') as f:
            augmented_searches = json.load(f)
        print("Step 2: Loading existing augmented searches from file")
    else:
        augmented_searches = augment_search_options(flight_info)
        print("Step 2: Generating new augmented searches")
    
    # Create HTML table for step 2
    step2_table = create_step2_table(augmented_searches)
    step2_result = {
        'title': 'Search Options Generation',
        'data': augmented_searches,
        'table': step2_table,
        'description': 'Generated alternative search options to find the best flights'
    }
    emit('step2_complete', step2_result)
    
    # Step 3: Load existing flights or crawl and process new ones
    step3_file = 'output/step3_all_crawledflights.json'
    step3_table_file = 'output/step3_all_crawledflights.md'
    
    if os.path.exists(step3_file) and os.path.exists(step3_table_file):
        with open(step3_file, 'r') as f:
            all_flights = json.load(f)
        with open(step3_table_file, 'r') as f:
            table_md = f.read()
        print("Step 3: Loading existing flight results from file")
    else:
        print("Step 3: Crawling new flight data")
        all_flights = {"flights": []}
        for i, search in enumerate(augmented_searches):
            crawl_flight_data_kayak(search, i)
            
            image_files = []
            section = 1
            while True:
                image_path = f'static/results/kayak_results_{i}_section_{section}.png'
                if not os.path.exists(image_path):
                    break
                image_files.append(image_path)
                section += 1
                
            search_flights = extract_flights_listings_llm_v2(image_files, i)
            
            for flight in search_flights["flights"]:
                flight.update({
                    'start_date': search['start_date'],
                    'return_date': search['return_date'],
                    'number_of_passengers': search['number_of_passengers'],
                    'other_data': search['other_data']
                })
                
            if search_flights and "flights" in search_flights:
                all_flights["flights"].extend(search_flights["flights"])
        
        save_output(
        all_flights,
        step3_file,
        )
    
        print(f"\nStep 3 Completed: Total flights collected: {len(all_flights['flights'])}")
        # Generate and save markdown table
        table_md = json_to_md_table(all_flights)
        
        df = pd.DataFrame.from_records(all_flights['flights'])
        df.to_excel('output/step3_all_crawledflights.xlsx', index=False)
        print(f"\nFiltered flights have been saved to xlsx file")  
    
    # Create HTML table instead of markdown
    flights_table = create_html_table(all_flights['flights'])
    
    step3_result = {
        'title': 'Flight Search Results',
        'data': all_flights,
        'table': flights_table,
        'description': f'Found {len(all_flights["flights"])} flights matching your criteria'
    }
    emit('step3_complete', step3_result)

@app.route('/clear-cache', methods=['POST'])
def clear_cache():
    """Clear all cached files to force a fresh search"""
    output_dir = 'output'
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        print(f"Cleared output directory: {output_dir}")
        os.makedirs(output_dir)  # Recreate empty output directory
    
    return jsonify({'status': 'success', 'message': 'Cache cleared successfully'})

@app.route('/filter', methods=['POST'])
def filter_flights():
    query = request.json['query']
    
    # Load the original flights data
    with open('output/step3_all_crawledflights.json', 'r') as f:
        all_flights = json.load(f)
    
    # Apply filter
    filtered_flights = interactive_flight_filter_v2(all_flights, query)
    
    # Create HTML table from filtered results
    flights_table = create_html_table(filtered_flights['flights'])
    
    return jsonify({
        'table': flights_table,
        'count': len(filtered_flights['flights'])
    })

if __name__ == "__main__":
    socketio.run(app, debug=True) 