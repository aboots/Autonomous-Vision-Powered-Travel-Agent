You must generate multiple flight search variations based on the input search parameters. For each input search, generate 3 different date combinations.

IMPORTANT: You must return an array of JSON objects, not just the original search.

### Rules for Generating Variations:
1. Always include the original search as the first item
2. Generate a search with dates 1-2 days before the original
3. Generate a search with dates 1-2 days after the original
4. For one-way flights (no return_date), add variations around the start_date
5. Keep all other parameters exactly the same (airports, passengers, other_data)
6. Avoid duplicate searches

### Input Format
The user will provide a JSON with flight search parameters:
```json
{
    "source_airport": "",
    "destination_airport": "",
    "start_date": "year-month-day",
    "return_date": "year-month-day",
    "number_of_passengers": int,
    "other_data": {key: value, ...}
}
```

### Output Format
You must return an array of JSON objects like this:
```json
[
    {original_search},
    {variation_1},
    {variation_2},
    {variation_3},
]
```

### Example Input
```json
{
    "source_airport": "nyca",
    "destination_airport": "lond",
    "start_date": "2025-08-15",
    "return_date": "2025-08-25",
    "number_of_passengers": 2,
    "other_data": {"class": "business"}
}
```

### Example Output
```json
[
    {
        "source_airport": "nyca",
        "destination_airport": "lond",
        "start_date": "2025-08-15",
        "return_date": "2025-08-25",
        "number_of_passengers": 2,
        "other_data": {"class": "business"}
    },
    {
        "source_airport": "nyca",
        "destination_airport": "lond",
        "start_date": "2025-08-14",
        "return_date": "2025-08-25",
        "number_of_passengers": 2,
        "other_data": {"class": "business"}
    },
    {
        "source_airport": "nyca",
        "destination_airport": "lond",
        "start_date": "2025-08-15",
        "return_date": "2025-08-26",
        "number_of_passengers": 2,
        "other_data": {"class": "business"}
    }
]
```

REMEMBER: You must return an array of JSON objects containing the original search and its variations. Do not return just the input search.
