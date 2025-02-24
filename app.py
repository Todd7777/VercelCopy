from flask import Flask, request, jsonify
import sqlite3
import os
from functools import wraps
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

VALID_MEASURES = {
    'Violent crime rate',
    'Unemployment',
    'Children in poverty',
    'Diabetic screening',
    'Mammography screening',
    'Preventable hospital stays',
    'Uninsured',
    'Sexually transmitted infections',
    'Physical inactivity',
    'Adult obesity',
    'Premature Death',
    'Daily fine particulate matter'
}

def get_db():
    """Get database connection with row factory"""
    try:
        # Use data.db instead of county_health.db
        db = sqlite3.connect('data.db')
        db.row_factory = sqlite3.Row
        return db
    except sqlite3.Error as e:
        app.logger.error(f"Database connection error: {e}")
        return None

def get_table_info():
    """Get information about tables and their columns"""
    try:
        db = get_db()
        if not db:
            return None
        
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        table_info = {}
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            table_info[table_name] = {
                'columns': [col[1] for col in columns],
                'types': {col[1]: col[2] for col in columns}
            }
        
        return table_info
    except sqlite3.Error as e:
        app.logger.error(f"Error getting table info: {e}")
        return None
    finally:
        if db:
            db.close()

def get_valid_measures():
    """Get list of valid measure names from the database"""
    try:
        db = get_db()
        if not db:
            return None
        
        cursor = db.cursor()
        cursor.execute("""
            SELECT DISTINCT measure_name 
            FROM county_health_rankings 
            WHERE measure_name IS NOT NULL
            AND measure_name != ''
            ORDER BY measure_name
        """)
        measures = [row[0] for row in cursor.fetchall()]
        return measures
    except sqlite3.Error as e:
        app.logger.error(f"Error getting measures: {e}")
        return None
    finally:
        if db:
            db.close()

def validate_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        
        # Check for teapot easter egg
        if data.get('coffee') == 'teapot':
            return '', 418
        
        # Validate required fields
        if 'zip' not in data:
            return jsonify({"error": "zip is required"}), 400
        
        zip_code = data['zip']
        if not (isinstance(zip_code, str) and zip_code.isdigit() and len(zip_code) == 5):
            return jsonify({"error": "zip must be a 5-digit string"}), 400
        
        if 'measure_name' not in data:
            return jsonify({"error": "measure_name is required"}), 400
        
        measure_name = data['measure_name']
        if measure_name not in VALID_MEASURES:
            return jsonify({
                "error": "Invalid measure_name",
                "valid_measures": sorted(list(VALID_MEASURES))
            }), 400
        
        return f(*args, **kwargs)
    return decorated_function

def get_county_data(zip_code, measure_name):
    """Get county health data for a given ZIP code and measure"""
    try:
        db = get_db()
        if not db:
            return None
        
        cursor = db.cursor()
        
        # Get county information for the ZIP code
        cursor.execute("""
            SELECT DISTINCT zc.county, zc.state_abbreviation, zc.county_code
            FROM zip_county zc
            WHERE zc.zip = ?
        """, (zip_code,))
        
        county_results = cursor.fetchall()
        if not county_results:
            return []
        
        # Get health data for each matching county
        results = []
        for county_row in county_results:
            county, state_abbr, county_code = county_row
            
            cursor.execute("""
                SELECT 
                    confidence_interval_lower_bound,
                    confidence_interval_upper_bound,
                    county,
                    county_code,
                    data_release_year,
                    denominator,
                    fipscode,
                    measure_id,
                    measure_name,
                    numerator,
                    raw_value,
                    state,
                    state_code,
                    year_span
                FROM county_health_rankings
                WHERE county = ? 
                AND (state = ? OR state_code = ?)
                AND measure_name = ?
                ORDER BY year_span DESC
            """, (county, state_abbr, county_code[:2], measure_name))
            
            columns = [column[0].lower() for column in cursor.description]
            rows = cursor.fetchall()
            
            for row in rows:
                result = dict(zip(columns, [str(val) if val is not None else "" for val in row]))
                results.append(result)
        
        return results
    except sqlite3.Error as e:
        app.logger.error(f"Database error in get_county_data: {e}")
        return None
    finally:
        if db:
            db.close()

@app.route('/county_data', methods=['POST'])
@validate_request
def county_data():
    """Handle POST requests to /county_data endpoint"""
    data = request.get_json()
    zip_code = data['zip']
    measure_name = data['measure_name']
    
    # Get the data
    results = get_county_data(zip_code, measure_name)
    
    if results is None:
        return jsonify({"error": "Database error occurred"}), 500
    
    if len(results) == 0:
        return jsonify({"error": "No data found for the given parameters"}), 404
    
    return jsonify(results)

@app.route('/measures', methods=['GET'])
def get_measures():
    """Get all available measure names"""
    return jsonify({"measures": sorted(list(VALID_MEASURES))})

@app.route('/tables', methods=['GET'])
def get_tables():
    """Get information about database tables and their structure"""
    table_info = get_table_info()
    if table_info is None:
        return jsonify({"error": "Database error occurred"}), 500
    return jsonify(table_info)

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad request"}), 400

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Check database connection on startup
    db = get_db()
    if not db:
        app.logger.error("Failed to connect to database on startup")
        exit(1)
    db.close()
    
    # Start server
    app.run(host='0.0.0.0', port=8080)
