# Weather Forecasting Project

A Django-based weather forecasting application that displays current weather conditions and a 7-day forecast using historical weather data from Ho Chi Minh City.

## Features

✨ **Core Features:**
- 🌤️ Current weather display with real-time data
- 📊 Interactive 7-day weather forecast with Chart.js visualization
- 📅 Historical date picker to view past weather and forecasts
- 🎨 Dynamic background images based on weather conditions
- 📱 Responsive design optimized for all devices
- 🔄 Smooth animations and transitions
- 💨 Floating icon animation for weather conditions

## Screenshots

[Your weather app with floating animation and 7-day forecast]

## Tech Stack

- **Backend:** Django 5.2.7
- **Frontend:** HTML5, CSS3, JavaScript
- **Data Processing:** Pandas, NumPy, Scikit-learn
- **Visualization:** Chart.js
- **Icons:** Bootstrap Icons
- **Styling:** Custom CSS with glassmorphism effects

## Installation

### Prerequisites
- Python 3.13+
- pip

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/weather-forecasting-project.git
   cd weather-forecasting-project
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv myenv
   myenv\Scripts\activate  # Windows
   source myenv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

6. **Open in browser:**
   ```
   http://127.0.0.1:8000
   ```

## Usage

### Viewing Weather

1. Visit the homepage to see current weather
2. Use the date picker to select a historical date
3. View the 7-day forecast from that date
4. Check the interactive chart for temperature and humidity trends

### Data

The project uses historical weather data from:
- **Location:** Ho Chi Minh City, Vietnam
- **Data Source:** `HCMWeatherDaily_Cleaned.csv`
- **Period:** 2015-10-08
- **Updates:** Manual CSV updates required

## Project Structure

```
weather-forecasting-project/
├── forecast/                    # Main Django app
│   ├── migrations/
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css       # Main styling
│   │   ├── js/
│   │   │   └── chartSetup.js    # Chart visualization
│   │   └── img/                 # Weather background images
│   ├── templates/
│   │   └── weather.html         # Main template
│   ├── views.py                 # View logic & data processing
│   ├── urls.py
│   ├── models.py
│   └── apps.py
├── weatherProject/              # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── data/
│   └── HCMWeatherDaily_Cleaned.csv
├── manage.py
├── requirements.txt
├── .gitignore
├── .env.example
└── README.md
```

## Key Features Explained

### Date Picker
- Select any date from the historical data
- Forecast automatically updates to show next 7 days from selected date
- Available dates displayed in dropdown (last 14 days)

### Weather Icons
- Dynamic Bootstrap Icons matching weather conditions
- Floating animation that loops continuously
- Smooth transitions between states

### Interactive Chart
- Displays temperature (left axis) and humidity (right axis)
- Responsive design adapts to screen size
- Smooth animations on data updates

### Dynamic Backgrounds
- 12+ weather condition backgrounds
- CSS-based background selection
- Glassmorphism overlay for readability

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
DEBUG=True
SECRET_KEY=your-django-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
CSV_PATH=./data/HCMWeatherDaily_Cleaned.csv
```

### Django Settings

Update `weatherProject/settings.py` for production:
- Set `DEBUG=False`
- Configure `ALLOWED_HOSTS`
- Set secure `SECRET_KEY`
- Configure static files

## Development

### Adding Weather Conditions

Edit `forecast/views.py` to add more weather condition mappings:

```python
def get_icon_class(description):
    # Add your condition mappings here
```

### Customizing Styles

Modify `forecast/static/css/styles.css` to change:
- Colors and gradients
- Background images
- Font sizes and spacing
- Animations

## Performance Optimization

- CSV data is loaded once at module startup
- Historical data cached in memory
- Static files served efficiently
- Chart.js optimized with responsive settings

## Future Enhancements

- [ ] Real-time weather API integration
- [ ] Weather alerts and notifications
- [ ] User accounts and saved preferences
- [ ] Weather trends and analytics
- [ ] Mobile app version
- [ ] Database integration for real-time updates
- [ ] Weather comparison between cities
- [ ] Historical data analysis

## Troubleshooting

### Chart Not Displaying Correct Dates
- Ensure `selected_date` is calculated from selected date, not current date
- Check that forecast data generation uses correct base date

### CSV File Not Found
- Verify `HCMWeatherDaily_Cleaned.csv` is in `data/` folder
- Check path configuration in `views.py`

### Static Files Not Loading
- Run `python manage.py collectstatic`
- Verify `STATIC_ROOT` in settings.py

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Author

**Your Name**
- GitHub: [@YOUR_USERNAME](https://github.com/YOUR_USERNAME)
- Email: your.email@example.com

## Acknowledgments

- Django Documentation
- Chart.js Library
- Bootstrap Icons
- Pandas and Scikit-learn communities

---

**Last Updated:** November 17, 2025
