from django.shortcuts import render
from django.conf import settings
import requests
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_squared_error
from datetime import datetime,timedelta
import pytz
import os

# Load historical data once at module level for performance
def load_historical_features():
    """Load historical weather features from CSV"""
    # Try multiple possible paths
    possible_paths = [
        r'c:\Users\ROG\Documents\MLearning\HCMWeatherDaily_Cleaned.csv',
        os.path.join(settings.BASE_DIR, '..', 'HCMWeatherDaily_Cleaned.csv'),
        r'c:\Users\ROG\Documents\MLearning\weatherProject\HCMWeatherDaily_Cleaned.csv',
    ]
    
    csv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_path = path
            break
    
    if not csv_path:
        print(f"CSV not found in any of these paths: {possible_paths}")
        return None
    
    try:
        df = pd.read_csv(csv_path)
        # Ensure datetime column is parsed
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
        print(f"Successfully loaded CSV from {csv_path}")
        return df
    except Exception as e:
        print(f"Error loading CSV from {csv_path}: {e}")
        return None

# Cache the historical data
_historical_data = load_historical_features()

def get_recent_features(days_back=30):
    """Get recent historical features for context and latest weather data"""
    global _historical_data
    if _historical_data is None:
        return None
    
    # Get last N days of data
    recent_data = _historical_data.tail(days_back)
    latest_record = _historical_data.iloc[-1] if len(_historical_data) > 0 else None
    
    # Extract key statistics
    features = {
        'avg_temp': recent_data['temp'].mean() if 'temp' in recent_data else None,
        'avg_humidity': recent_data['humidity'].mean() if 'humidity' in recent_data else None,
        'avg_windspeed': recent_data['windspeed'].mean() if 'windspeed' in recent_data else None,
        'avg_precip': recent_data['precip'].mean() if 'precip' in recent_data else None,
        'max_temp': recent_data['tempmax'].max() if 'tempmax' in recent_data else None,
        'min_temp': recent_data['tempmin'].min() if 'tempmin' in recent_data else None,
        'avg_cloudcover': recent_data['cloudcover'].mean() if 'cloudcover' in recent_data else None,
        'latest_record': latest_record,  # Add the latest record for weather_data
    }
    
    # Add all engineered features from the latest record
    if latest_record is not None:
        engineered_features = {}
        for col in latest_record.index:
            try:
                engineered_features[col] = round(float(latest_record[col]), 2) if pd.notna(latest_record[col]) else None
            except:
                engineered_features[col] = latest_record[col]
        
        features['engineered'] = engineered_features
    
    return features

def get_icon_class(description):
    """Map weather condition descriptions to Bootstrap Icons"""
    description = str(description).lower()
    
    # Map CSV condition values to Bootstrap Icons
    if "clear" in description and "cloud" not in description:
        return "bi-sun-fill"
    elif "rain" in description and "overcast" in description:
        return "bi-cloud-rain-fill"
    elif "rain" in description and "partial" in description:
        return "bi-cloud-rain"
    elif "rain" in description:
        return "bi-cloud-rain-fill"
    elif "partial" in description or "partly" in description:
        return "bi-cloud-sun"
    elif "overcast" in description or "cloudy" in description:
        return "bi-cloud-fill"
    elif "thunder" in description or "thunderstorm" in description:
        return "bi-cloud-lightning"
    elif "snow" in description:
        return "bi-snow"
    elif "fog" in description or "mist" in description or "haze" in description:
        return "bi-cloud-fog"
    else:
        return "bi-cloud"

def get_css_class_from_condition(description):
    """Convert weather condition to CSS class slug for background images"""
    description = str(description).lower().strip()
    
    # Replace spaces and commas with hyphens for CSS class compatibility
    css_class = description.replace(", ", "-").replace(" ", "-")
    
    # Direct mapping to CSS classes we defined
    if "clear" in description:
        return "clear"
    elif "rain" in description and "overcast" in description:
        return "rain-overcast"
    elif "rain" in description and "partial" in description:
        return "rain-partially-cloudy"
    elif "partial" in description or "partly" in description:
        return "partially-cloudy"
    elif "overcast" in description:
        return "overcast"
    else:
        return css_class

def weather_view(request):
    # Load historical features from CSV
    recent_features = get_recent_features(days_back=30)
    
    # Build weather_data from latest CSV record
    weather_data = {
        'date': '2023-07-13',
        'city': 'Ho Chi Minh City',
        'country': 'VN',
        'description': 'clear',
    }
    
    # If we have CSV data, populate weather_data from it
    if recent_features and recent_features.get('latest_record') is not None:
        latest = recent_features['latest_record']
        
        # Map CSV columns to weather_data keys
        weather_data.update({
            'date': str(latest.get('datetime', '2023-07-13'))[:10] if 'datetime' in latest else '2023-07-13',
            'current_temp': int(latest.get('temp', 29)) if pd.notna(latest.get('temp')) else 29,
            'feels_like': int(latest.get('feelslike', 31)) if pd.notna(latest.get('feelslike')) else 31,
            'humidity': int(latest.get('humidity', 78)) if pd.notna(latest.get('humidity')) else 78,
            'clouds': int(latest.get('cloudcover', 90)) if pd.notna(latest.get('cloudcover')) else 90,
            'pressure': int(latest.get('sealevelpressure', 1008)) if pd.notna(latest.get('sealevelpressure')) else 1008,
            'wind': int(latest.get('windspeed', 5)) if pd.notna(latest.get('windspeed')) else 5,
            'visibility': int(latest.get('visibility', 8000)) if pd.notna(latest.get('visibility')) else 8000,
            'MaxTemp': int(latest.get('tempmax', 32)) if pd.notna(latest.get('tempmax')) else 32,
            'Mintemp': int(latest.get('tempmin', 25)) if pd.notna(latest.get('tempmin')) else 25,
            'description': latest.get('conditions', 'clear') if pd.notna(latest.get('conditions')) else 'clear',
        })
        
        # Add 7-day forecast (using rolling window from CSV if available, else simulate)
        df = _historical_data
        if df is not None and len(df) >= 7:
            # Use last 7 days from CSV as forecast (real data simulation)
            forecast_subset = df.tail(7).reset_index(drop=True)
            for i in range(1, 8):
                if i <= len(forecast_subset):
                    row = forecast_subset.iloc[i-1]
                    weather_data[f'time{i}'] = pd.to_datetime(row.get('datetime', datetime.now())).strftime('%A %d %b')
                    weather_data[f'temp{i}'] = int(row.get('temp', 29)) if pd.notna(row.get('temp')) else 29
                    weather_data[f'hum{i}'] = int(row.get('humidity', 78)) if pd.notna(row.get('humidity')) else 78
                else:
                    # Fallback if not enough data
                    forecast_date = datetime.now() + timedelta(days=i)
                    weather_data[f'time{i}'] = forecast_date.strftime('%A %d %b')
                    weather_data[f'temp{i}'] = weather_data['current_temp'] + (i % 3)
                    weather_data[f'hum{i}'] = weather_data['humidity'] + (i % 5)
        else:
            # Fallback: generate forecast based on current temp
            for i in range(1, 8):
                forecast_date = datetime.now() + timedelta(days=i)
                weather_data[f'time{i}'] = forecast_date.strftime('%A %d %b')
                weather_data[f'temp{i}'] = weather_data['current_temp'] + (i % 3)
                weather_data[f'hum{i}'] = weather_data['humidity'] + (i % 5)
    
    # Add historical context features
    if recent_features:
        weather_data['historical_features'] = {
            'avg_temp_30d': round(recent_features['avg_temp'], 2) if recent_features['avg_temp'] else 'N/A',
            'avg_humidity_30d': round(recent_features['avg_humidity'], 2) if recent_features['avg_humidity'] else 'N/A',
            'avg_windspeed_30d': round(recent_features['avg_windspeed'], 2) if recent_features['avg_windspeed'] else 'N/A',
            'avg_precip_30d': round(recent_features['avg_precip'], 2) if recent_features['avg_precip'] else 'N/A',
            'max_temp_30d': round(recent_features['max_temp'], 2) if recent_features['max_temp'] else 'N/A',
            'min_temp_30d': round(recent_features['min_temp'], 2) if recent_features['min_temp'] else 'N/A',
            'avg_cloudcover_30d': round(recent_features['avg_cloudcover'], 2) if recent_features['avg_cloudcover'] else 'N/A',
        }
        
        # Add all engineered features from CSV
        if 'engineered' in recent_features:
            weather_data['engineered_features'] = recent_features['engineered']
        
        # Add comparison context
        weather_data['temp_vs_avg'] = weather_data['current_temp'] - recent_features['avg_temp'] if recent_features['avg_temp'] else 0
        weather_data['humidity_vs_avg'] = weather_data['humidity'] - recent_features['avg_humidity'] if recent_features['avg_humidity'] else 0
    
    # Get icon class for description
    icon_class = get_icon_class(weather_data['description'])
    
    # Get CSS class for background image
    css_background_class = get_css_class_from_condition(weather_data['description'])
    
    # Add both to context
    weather_data['icon_class'] = icon_class
    weather_data['css_background_class'] = css_background_class
    
    # Prepare week series for template/JS (times, temps, hums)
    import json
    week_times = [weather_data[f'time{i}'] for i in range(1,8)]
    week_temps = [weather_data[f'temp{i}'] for i in range(1,8)]
    week_hums = [weather_data[f'hum{i}'] for i in range(1,8)]
    weather_data['week_times'] = json.dumps(week_times)
    weather_data['week_temps'] = json.dumps(week_temps)
    weather_data['week_hums'] = json.dumps(week_hums)
    
    return render(request, 'weather.html', weather_data)
