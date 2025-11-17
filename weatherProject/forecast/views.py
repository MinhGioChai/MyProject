from django.shortcuts import render
from django.conf import settings
import pandas as pd
from datetime import datetime, timedelta
import os
import json

# Load historical data once at module level for performance
def load_historical_features():
    """Load historical weather features from CSV"""
    # Try multiple possible paths (works on both local and Render)
    possible_paths = [
        os.path.join(settings.BASE_DIR, 'data', 'HCMWeatherDaily_Cleaned.csv'),
        os.path.join(settings.BASE_DIR, 'HCMWeatherDaily_Cleaned.csv'),
        os.path.join(settings.BASE_DIR, '..', 'data', 'HCMWeatherDaily_Cleaned.csv'),
        os.path.join(settings.BASE_DIR, '..', 'HCMWeatherDaily_Cleaned.csv'),
    ]
    
    csv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_path = path
            print(f"✓ Found CSV at: {csv_path}")
            break
    
    if not csv_path:
        print(f"✗ CSV not found in: {possible_paths}")
        print(f"  BASE_DIR = {settings.BASE_DIR}")
        return None
    
    try:
        df = pd.read_csv(csv_path)
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
        print(f"✓ CSV loaded successfully ({len(df)} rows)")
        return df
    except Exception as e:
        print(f"✗ Error loading CSV: {e}")
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
    # Determine if user selected a date via query parameter
    selected_date_str = request.GET.get('date')
    selected_record = None

    if _historical_data is not None and 'datetime' in _historical_data.columns:
        if selected_date_str:
            try:
                parsed_date = pd.to_datetime(selected_date_str).date()
                # Filter rows matching the selected date (date-only comparison)
                matching_rows = _historical_data[_historical_data['datetime'].dt.date == parsed_date]
                if not matching_rows.empty:
                    selected_record = matching_rows.iloc[-1]
            except Exception:
                # Ignore parsing errors; will fallback to latest
                pass
        # Fallback to latest record if no matching row
        if selected_record is None and len(_historical_data) > 0:
            selected_record = _historical_data.iloc[-1]

    # Build base weather_data (defaults)
    weather_data = {
        'date': selected_date_str if selected_date_str else '2025-10-08',
        'city': 'Ho Chi Minh City',
        'country': 'VN',
        'description': 'clear',
        # Default numeric values (used if no record is found)
        'current_temp': 29,
        'feels_like': 31,
        'humidity': 78,
        'clouds': 90,
        'pressure': 1008,
        'wind': 5,
        'visibility': 8000,
        'MaxTemp': 32,
        'Mintemp': 25,
        'max_date': '2025-10-08',  # Maximum date in dataset
    }

    # If we have a record (selected or latest), populate weather_data
    if selected_record is not None:
        record = selected_record
        # Map CSV columns to weather_data keys
        weather_data.update({
            'date': str(record.get('datetime', weather_data['date']))[:10],
            'current_temp': int(record.get('temp', 29)) if pd.notna(record.get('temp')) else 29,
            'feels_like': int(record.get('feelslike', 31)) if pd.notna(record.get('feelslike')) else 31,
            'humidity': int(record.get('humidity', 78)) if pd.notna(record.get('humidity')) else 78,
            'clouds': int(record.get('cloudcover', 90)) if pd.notna(record.get('cloudcover')) else 90,
            'pressure': int(record.get('sealevelpressure', 1008)) if pd.notna(record.get('sealevelpressure')) else 1008,
            'wind': int(record.get('windspeed', 5)) if pd.notna(record.get('windspeed')) else 5,
            'visibility': int(record.get('visibility', 8000)) if pd.notna(record.get('visibility')) else 8000,
            'MaxTemp': int(record.get('tempmax', 32)) if pd.notna(record.get('tempmax')) else 32,
            'Mintemp': int(record.get('tempmin', 25)) if pd.notna(record.get('tempmin')) else 25,
            'description': record.get('conditions', 'clear') if pd.notna(record.get('conditions')) else 'clear',
        })

        # Build a 7-day forecast AFTER the selected date
        df = _historical_data
        forecast_subset = None
        if df is not None and 'datetime' in df.columns:
            try:
                current_date = pd.to_datetime(weather_data['date']).date()
                # Get rows AFTER the selected date (next 7 days)
                after_date = df[df['datetime'].dt.date > current_date]
                if len(after_date) >= 7:
                    # Take the next 7 days after selected date
                    forecast_subset = after_date.head(7).reset_index(drop=True)
                elif len(after_date) > 0:
                    # Use whatever days we have and fill the rest synthetically
                    forecast_subset = after_date.head(len(after_date)).reset_index(drop=True)
            except Exception:
                pass

        if forecast_subset is not None and len(forecast_subset) > 0:
            # Use actual data for available days
            for i in range(1, min(8, len(forecast_subset) + 1)):
                row = forecast_subset.iloc[i-1]
                weather_data[f'time{i}'] = pd.to_datetime(row.get('datetime', datetime.now())).strftime('%A %d %b')
                weather_data[f'temp{i}'] = int(row.get('temp', 29)) if pd.notna(row.get('temp')) else 29
                weather_data[f'hum{i}'] = int(row.get('humidity', 78)) if pd.notna(row.get('humidity')) else 78
            
            # Fill remaining days with synthetic predictions if needed
            if len(forecast_subset) < 7:
                try:
                    last_available_date = pd.to_datetime(forecast_subset.iloc[-1]['datetime']).date()
                    for i in range(len(forecast_subset) + 1, 8):
                        days_ahead = i - len(forecast_subset)
                        forecast_date = last_available_date + timedelta(days=days_ahead)
                        # Simple prediction: slight variation from current temp
                        weather_data[f'time{i}'] = forecast_date.strftime('%A %d %b')
                        weather_data[f'temp{i}'] = weather_data['current_temp'] + ((i - 1) % 3 - 1)
                        weather_data[f'hum{i}'] = weather_data['humidity'] + ((i - 1) % 5 - 2)
                except Exception:
                    # Fallback to simple synthetic
                    for i in range(len(forecast_subset) + 1, 8):
                        forecast_date = datetime.now() + timedelta(days=i)
                        weather_data[f'time{i}'] = forecast_date.strftime('%A %d %b')
                        weather_data[f'temp{i}'] = weather_data['current_temp'] + ((i - 1) % 3 - 1)
                        weather_data[f'hum{i}'] = weather_data['humidity'] + ((i - 1) % 5 - 2)
        else:
            # No data available after selected date - create synthetic forecast
            try:
                base_date = pd.to_datetime(weather_data['date']).date()
            except:
                base_date = datetime.now().date()
            
            for i in range(1, 8):
                forecast_date = base_date + timedelta(days=i)
                weather_data[f'time{i}'] = forecast_date.strftime('%A %d %b')
                # Simple prediction model: slight temperature variation
                weather_data[f'temp{i}'] = weather_data['current_temp'] + ((i - 1) % 3 - 1)
                weather_data[f'hum{i}'] = weather_data['humidity'] + ((i - 1) % 5 - 2)
    
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
    week_times = [weather_data[f'time{i}'] for i in range(1,8)]
    week_temps = [weather_data[f'temp{i}'] for i in range(1,8)]
    week_hums = [weather_data[f'hum{i}'] for i in range(1,8)]
    weather_data['week_times'] = json.dumps(week_times)
    weather_data['week_temps'] = json.dumps(week_temps)
    weather_data['week_hums'] = json.dumps(week_hums)
    
    return render(request, 'weather.html', weather_data)
