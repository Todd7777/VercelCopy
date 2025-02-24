# County Health Data API

A robust REST API that provides access to county health data based on ZIP codes and health measures. The API is designed to work with any CSV file structure and includes comprehensive error handling and data validation.

## Features

- Dynamic handling of CSV files with automatic type detection
- Robust error handling and input validation
- Automatic index creation for commonly queried columns
- Support for batch processing of large datasets
- RESTful API endpoints with JSON responses
- Comprehensive logging and error reporting

## Setup

1. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Convert CSV data to SQLite:
```bash
python3 csv_to_sqlite.py county_health.db county_health_rankings.csv
python3 csv_to_sqlite.py county_health.db zip_county.csv
```

4. Run the API:
```bash
python3 app.py
```

## API Endpoints

### 1. POST /county_data

Retrieve county health data for a specific ZIP code and measure.

**Headers:**
- Content-Type: application/json

**Request Body:**
```json
{
    "zip": "02138",
    "measure_name": "Adult obesity"
}
```

**Success Response (200):**
```json
[
    {
        "confidence_interval_lower_bound": "0.22",
        "confidence_interval_upper_bound": "0.24",
        "county": "Middlesex County",
        "county_code": "17",
        "data_release_year": "2012",
        "denominator": "263078",
        "fipscode": "25017",
        "measure_id": "11",
        "measure_name": "Adult obesity",
        "numerator": "60771.02",
        "raw_value": "0.23",
        "state": "MA",
        "state_code": "25",
        "year_span": "2009"
    }
]
```

### 2. GET /measures

Get a list of all available health measures.

**Success Response (200):**
```json
{
    "measures": [
        "Adult obesity",
        "Children in poverty",
        "Diabetic screening",
        ...
    ]
}
```

### 3. GET /tables

Get information about database tables and their structure.

**Success Response (200):**
```json
{
    "county_health_rankings": {
        "columns": ["state", "county", "measure_name", ...],
        "types": {
            "state": "TEXT",
            "county": "TEXT",
            "measure_name": "TEXT",
            ...
        }
    },
    "zip_county": {
        "columns": ["zip", "county", "state_abbreviation", ...],
        "types": {
            "zip": "INTEGER",
            "county": "TEXT",
            "state_abbreviation": "TEXT",
            ...
        }
    }
}
```

## Error Codes

- 400: Bad Request (missing or invalid parameters)
- 404: Not Found (no data found or endpoint doesn't exist)
- 418: I'm a teapot (when coffee=teapot is included in request)
- 500: Internal Server Error

## CSV File Requirements

The API is designed to work with any CSV file structure, but it expects:

1. For county health data:
   - Must contain columns for county, state, and measure_name
   - Should include measurement values and metadata

2. For ZIP code mapping:
   - Must contain columns for zip, county, and state information
   - Can include additional metadata columns

The system will automatically:
- Detect column types (TEXT, INTEGER, REAL)
- Create appropriate database indices
- Handle missing or malformed data
- Convert data types as needed

## Development and Testing

The API includes:
- Comprehensive error handling
- Input validation
- Automatic type conversion
- Database connection management
- Logging for debugging

## Deployment

The API can be deployed to various platforms:
- Vercel (configuration included)
- Heroku
- AWS
- Google Cloud Platform

Update the `link.txt` file with your deployment URL after deploying.
