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

# Load predicted data once at module level for performance
def load_predicted_data():
    """Load predicted temperatures from CSV (supports multiple filenames)"""
    possible_paths = [
        os.path.join(settings.BASE_DIR, 'data', 'predict_dataset.csv'),
        os.path.join(settings.BASE_DIR, 'data', 'predicted_data.csv'),
        os.path.join(settings.BASE_DIR, 'predict_dataset.csv'),
        os.path.join(settings.BASE_DIR, 'predicted_data.csv'),
        os.path.join(settings.BASE_DIR, '..', 'data', 'predict_dataset.csv'),
        os.path.join(settings.BASE_DIR, '..', 'data', 'predicted_data.csv'),
    ]

    csv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_path = path
            print(f"✓ Found predicted CSV at: {csv_path}")
            break

    if not csv_path:
        print(f"✗ Predicted CSV not found in: {possible_paths}")
        return None

    try:
        df = pd.read_csv(csv_path)
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
        # Normalize column names for ease of access
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        print(f"✗ Error loading predicted CSV: {e}")
        return None

_predicted_data = load_predicted_data()

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
                # Ignore parsing errors; will fallback to default
                pass
        # Fallback to 2025-10-04 if no date selected
        if selected_record is None:
            try:
                default_date = pd.to_datetime('2025-10-04').date()
                matching_rows = _historical_data[_historical_data['datetime'].dt.date == default_date]
                if not matching_rows.empty:
                    selected_record = matching_rows.iloc[-1]
                    selected_date_str = '2025-10-04'  # Set the date string to default
            except Exception:
                # Final fallback to latest record
                if len(_historical_data) > 0:
                    selected_record = _historical_data.iloc[-1]

    # Build base weather_data (defaults)
    weather_data = {
        'date': selected_date_str if selected_date_str else '2025-10-04',
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
        'max_date': '2025-10-08',  # Maximum date in dataset - forecast will show available days only
    }

    # If we have a record (selected or latest), populate weather_data
    if selected_record is not None:
        record = selected_record
        
        # Get predicted temperature for today (Pred_Day 0) from predicted CSV
        predicted_temp_today = None
        if _predicted_data is not None and 'datetime' in _predicted_data.columns:
            try:
                pred_df = _predicted_data.copy()
                pred_df['date_only'] = pred_df['datetime'].dt.date
                parsed_date = pd.to_datetime(str(record.get('datetime', weather_data['date']))[:10]).date()
                matching_pred = pred_df[pred_df['date_only'] == parsed_date]
                if not matching_pred.empty:
                    pred_row = matching_pred.iloc[-1]
                    # Look for Pred_Day 0 column with flexible matching
                    import re
                    for col in pred_row.index:
                        col_lower = str(col).strip().lower()
                        # Match patterns: "pred_day 0", "pred_day0", "pred day 0", etc.
                        if 'pred' in col_lower and 'day' in col_lower:
                            match = re.search(r'day\s*(\d+)', col_lower)
                            if match and int(match.group(1)) == 0:
                                predicted_temp_today = int(pred_row[col]) if pd.notna(pred_row[col]) else None
                                break
            except Exception:
                pass
        
        # Use predicted temp if available, otherwise fallback to actual temp
        display_temp = predicted_temp_today if predicted_temp_today is not None else (int(record.get('temp', 29)) if pd.notna(record.get('temp')) else 29)
        
        # Map CSV columns to weather_data keys
        weather_data.update({
            'date': str(record.get('datetime', weather_data['date']))[:10],
            'current_temp': display_temp,  # Use predicted temperature
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

        # Determine forecast horizon from predicted columns (default 7, usually 5)
        try:
            current_date = pd.to_datetime(weather_data['date']).date()
        except Exception:
            current_date = datetime.now().date()

        horizon = 7
        if _predicted_data is not None and 'datetime' in _predicted_data.columns:
            try:
                pred_df_h = _predicted_data.copy()
                pred_df_h['date_only'] = pred_df_h['datetime'].dt.date
                row_h = pred_df_h[pred_df_h['date_only'] == current_date]
                if not row_h.empty:
                    cols = []
                    import re
                    for c in pred_df_h.columns:
                        cl = str(c).strip().lower()
                        if 'pred' in cl and 'day' in cl:
                            try:
                                match = re.search(r'day\s*(\d+)', cl)
                                if match:
                                    idx = int(match.group(1))
                                    cols.append(idx)
                            except Exception:
                                pass
                    if cols:
                        horizon = min(len(sorted([i for i in cols if i >= 0])), 7)
            except Exception:
                pass

        if horizon <= 0:
            horizon = 5  # sensible default

        # Build a forecast starting from TODAY (D+0) with dynamic horizon
        # D+0 = today (selected date), D+1 = tomorrow, etc.
        df = _historical_data
        forecast_subset = None
        actual_horizon = horizon  # Track actual available days
        if df is not None and 'datetime' in df.columns:
            try:
                # Get rows starting from current_date (inclusive) for horizon days
                from_date = df[df['datetime'].dt.date >= current_date]
                if len(from_date) >= horizon:
                    # Take horizon days starting from current_date
                    forecast_subset = from_date.head(horizon).reset_index(drop=True)
                    actual_horizon = horizon
                elif len(from_date) > 0:
                    # Only use what we actually have - no synthetic fill
                    forecast_subset = from_date.head(len(from_date)).reset_index(drop=True)
                    actual_horizon = len(from_date)
            except Exception:
                pass

        if forecast_subset is not None and len(forecast_subset) > 0:
            # Get predicted temperatures from predicted CSV for each day
            pred_temps_map = {}  # Map day index to predicted temp
            if _predicted_data is not None and 'datetime' in _predicted_data.columns:
                try:
                    pred_df = _predicted_data.copy()
                    pred_df['date_only'] = pred_df['datetime'].dt.date
                    matching_pred = pred_df[pred_df['date_only'] == current_date]
                    if not matching_pred.empty:
                        pred_row = matching_pred.iloc[-1]
                        # Extract Pred_Day 0, 1, 2, 3, 4
                        import re
                        for col in pred_row.index:
                            col_lower = str(col).strip().lower()
                            # Match patterns: "pred_day 0", "pred_day0", "pred day 0", etc.
                            if 'pred' in col_lower and 'day' in col_lower:
                                try:
                                    match = re.search(r'day\s*(\d+)', col_lower)
                                    if match:
                                        day_idx = int(match.group(1))
                                        pred_temps_map[day_idx] = int(pred_row[col]) if pd.notna(pred_row[col]) else None
                                except Exception:
                                    pass
                except Exception:
                    pass
            
            # Use predicted temps for available days (D+0 to D+actual_horizon-1)
            for i in range(0, actual_horizon):
                row = forecast_subset.iloc[i]
                # i=0 is today (time0, temp0), i=1 is tomorrow (time1, temp1), etc.
                weather_data[f'time{i}'] = pd.to_datetime(row.get('datetime', datetime.now())).strftime('%A %d %b')
                # Use predicted temp if available, otherwise fallback to actual
                weather_data[f'temp{i}'] = pred_temps_map.get(i, int(row.get('temp', 29)) if pd.notna(row.get('temp')) else 29)
                weather_data[f'hum{i}'] = int(row.get('humidity', 78)) if pd.notna(row.get('humidity')) else 78
            
            # Keep prediction horizon (5 days) for chart, use actual horizon for forecast box
            forecast_box_horizon = actual_horizon
        else:
            # No data available - don't show forecast box
            forecast_box_horizon = 0
    
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
    
    # Prepare week series for template/JS with dynamic horizon based on predictions
    week_times = [weather_data.get(f'time{i}') for i in range(0,8)]
    week_temps = [weather_data.get(f'temp{i}') for i in range(0,8)]

    # Determine base date and prediction horizon (from Pred_Day columns)
    try:
        base_date = pd.to_datetime(weather_data['date']).date()
    except Exception:
        base_date = datetime.now().date()

    # Determine prediction horizon from predicted columns (typically 5)
    pred_horizon = 5  # default
    if _predicted_data is not None and 'datetime' in _predicted_data.columns:
        try:
            pred_df_h2 = _predicted_data.copy()
            pred_df_h2['date_only'] = pred_df_h2['datetime'].dt.date
            row_h2 = pred_df_h2[pred_df_h2['date_only'] == base_date]
            if not row_h2.empty:
                cols2 = []
                import re
                for c in pred_df_h2.columns:
                    cl = str(c).strip().lower()
                    if 'pred' in cl and 'day' in cl:
                        try:
                            match = re.search(r'day\s*(\d+)', cl)
                            if match:
                                idx = int(match.group(1))
                                cols2.append(idx)
                        except Exception:
                            pass
                if cols2:
                    pred_horizon = len(sorted([i for i in cols2 if i >= 0]))
        except Exception:
            pass

    # Use prediction horizon for chart (not limited by historical data)
    horizon = pred_horizon if pred_horizon > 0 else 5

    # Create D+0..D+(horizon-1) labels (today through horizon-1 days ahead)
    forecast_dates = [base_date + timedelta(days=i) for i in range(0, horizon)]
    week_times = [d.strftime('%A %d %b') for d in forecast_dates]

    # Actual temps from historical data if available for those dates (may have gaps)
    week_actual_temps = []
    if _historical_data is not None and 'datetime' in _historical_data.columns:
        hist_by_date = _historical_data.copy()
        hist_by_date['date_only'] = hist_by_date['datetime'].dt.date
        hist_map = hist_by_date.set_index('date_only')
        for d in forecast_dates:
            if d in hist_map.index and 'temp' in hist_map.columns:
                val = hist_map.loc[d]['temp']
                # If multiple rows per date, take the latest (handle Series)
                if isinstance(val, (pd.Series, list)):
                    try:
                        v = float(val.iloc[-1])
                    except Exception:
                        v = None
                else:
                    try:
                        v = float(val)
                    except Exception:
                        v = None
                week_actual_temps.append(round(v, 2) if v is not None and pd.notna(v) else None)
            else:
                week_actual_temps.append(None)
    else:
        week_actual_temps = [None] * horizon

    # Predicted temps based on the SELECTED DATE row's Pred_Day N columns
    # Pred_Day 0 = today's prediction, Pred_Day 1 = tomorrow's prediction, etc.
    week_pred_temps = [None] * horizon
    if _predicted_data is not None and 'datetime' in _predicted_data.columns:
        try:
            pred_df = _predicted_data.copy()
            pred_df['date_only'] = pred_df['datetime'].dt.date
            base_row = pred_df[pred_df['date_only'] == base_date]
            if not base_row.empty:
                base_row = base_row.iloc[0]
                # Find columns Pred_Day 0..N and sort by index number
                pred_cols = []
                for c in pred_df.columns:
                    # Normalize column name: strip whitespace and lowercase
                    cl = str(c).strip().lower()
                    # Match patterns: "pred_day 0", "pred_day0", "pred day 0", etc.
                    if 'pred' in cl and 'day' in cl:
                        try:
                            # Extract the number after "day"
                            import re
                            match = re.search(r'day\s*(\d+)', cl)
                            if match:
                                idx = int(match.group(1))
                                pred_cols.append((idx, c))  # Store original column name
                        except Exception:
                            continue
                pred_cols.sort(key=lambda x: x[0])
                # Map D+0..D+(horizon-1) to Pred_Day 0..(horizon-1)
                for i in range(horizon):
                    try:
                        col = next((c for (idx, c) in pred_cols if idx == i), None)
                        if col is None:
                            week_pred_temps[i] = None
                        else:
                            val = base_row.get(col, None)
                            week_pred_temps[i] = round(float(val), 2) if val is not None and pd.notna(val) else None
                    except Exception:
                        week_pred_temps[i] = None
        except Exception as e:
            print(f"Pred mapping error: {e}")

    # Trim week_temps fallback to horizon for legacy parser
    weather_data['week_times'] = json.dumps(week_times)
    weather_data['week_temps'] = json.dumps(week_temps[:horizon] if week_temps else [])
    # Humidity no longer used on the chart
    weather_data['week_actual_temps'] = json.dumps(week_actual_temps)
    weather_data['week_pred_temps'] = json.dumps(week_pred_temps)

    # Build forecast items for template list (limit to actual data horizon)
    # i=0 is today, i=1 is tomorrow, etc.
    forecast_items = []
    for i in range(0, forecast_box_horizon):
        forecast_items.append({
            'day': weather_data.get(f'time{i}', week_times[i] if i < len(week_times) else ''),
            'temp': weather_data.get(f'temp{i}', None),
            'hum': weather_data.get(f'hum{i}', None)
        })
    weather_data['forecast_items'] = forecast_items
    
    return render(request, 'weather.html', weather_data)
