import os
import sys
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.align import Align
from rich.text import Text
from rich import box
from alive_progress import alive_bar
from art import text2art

# Initialize Rich console
console = Console()

# Load environment variables
load_dotenv()

class WeatherDashboard:
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.geocoder = Nominatim(user_agent="weather_dashboard")
        
        if not self.api_key:
            console.print("[red]Error: API key not found. Please add your OpenWeatherMap API key to the .env file.[/red]")
            sys.exit(1)

    def show_welcome(self):
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Create ASCII art title
        title_art = text2art("Weather   Dashboard", font="small")
        console.print(Panel(title_art, style="bold blue", border_style="blue"))
        console.print("\n")

    def get_coordinates(self, city):
        with alive_bar(1, title="Finding location", bar="classic", spinner="dots") as bar:
            try:
                location = self.geocoder.geocode(city)
                bar()
                if location:
                    return location.latitude, location.longitude, location.address
                return None, None, None
            except GeocoderTimedOut:
                raise Exception("Geocoding service timed out. Please try again.")

    def get_weather_data(self, city):
        lat, lon, address = self.get_coordinates(city)
        if not lat or not lon:
            raise Exception(f"Could not find location: {city}")

        weather_data = {}
        with alive_bar(3, title="Fetching weather data", bar="classic", spinner="dots") as bar:
            # Current weather
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            current_response = requests.get(f"{self.base_url}/weather", params=params)
            current_response.raise_for_status()
            weather_data['current'] = current_response.json()
            bar()

            # Forecast
            forecast_response = requests.get(f"{self.base_url}/forecast", params=params)
            forecast_response.raise_for_status()
            weather_data['forecast'] = forecast_response.json()
            bar()

            # Air quality
            try:
                air_response = requests.get(f"{self.base_url}/air_pollution", params=params)
                air_response.raise_for_status()
                weather_data['air'] = air_response.json()
            except:
                weather_data['air'] = None
            bar()

            weather_data['address'] = address
            return weather_data

    def get_weather_icon(self, condition):
        icons = {
            'Clear': '☀️',
            'Clouds': '☁️',
            'Rain': '🌧️',
            'Snow': '❄️',
            'Thunderstorm': '⚡',
            'Drizzle': '🌦️',
            'Mist': '🌫️',
            'Smoke': '🌫️',
            'Haze': '🌫️',
            'Dust': '🌫️',
            'Fog': '🌫️',
            'Sand': '🌫️',
            'Ash': '🌫️',
            'Squall': '💨',
            'Tornado': '🌪️'
        }
        return icons.get(condition, '❓')

    def create_current_weather_panel(self, weather_data):
        current = weather_data['current']
        weather_icon = self.get_weather_icon(current['weather'][0]['main'])
        
        content = Text()
        content.append(f"\nTemperature: {current['main']['temp']}°C", style="cyan")
        content.append(f"\nFeels like: {current['main']['feels_like']}°C", style="cyan")
        content.append(f"\nHumidity: {current['main']['humidity']}%", style="green")
        content.append(f"\nWind Speed: {current['wind']['speed']} m/s", style="yellow")
        content.append(f"\nPressure: {current['main']['pressure']} hPa", style="magenta")
        content.append(f"\nConditions: {weather_icon} {current['weather'][0]['description'].capitalize()}", style="blue")
        
        return Panel(
            content,
            title="[bold]Current Weather[/bold]",
            border_style="blue",
            padding=(1, 2)
        )

    def create_forecast_panel(self, weather_data):
        table = Table(show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Date/Time")
        table.add_column("Temp")
        table.add_column("Conditions")

        for item in weather_data['forecast']['list'][:5]:
            date = datetime.fromtimestamp(item['dt'])
            weather_icon = self.get_weather_icon(item['weather'][0]['main'])
            table.add_row(
                date.strftime('%Y-%m-%d %H:%M'),
                f"{item['main']['temp']}°C",
                f"{weather_icon} {item['weather'][0]['description'].capitalize()}"
            )

        return Panel(
            table,
            title="[bold]5-Day Forecast[/bold]",
            border_style="green",
            padding=(1, 1)
        )

    def create_air_quality_panel(self, weather_data):
        if not weather_data.get('air'):
            return Panel(
                "Air quality data not available",
                title="[bold]Air Quality[/bold]",
                border_style="yellow",
                padding=(1, 2)
            )

        aqi_labels = {
            1: ("Good", "green"),
            2: ("Fair", "cyan"),
            3: ("Moderate", "yellow"),
            4: ("Poor", "red"),
            5: ("Very Poor", "red bold")
        }

        aqi = weather_data['air']['list'][0]['main']['aqi']
        aqi_label, aqi_color = aqi_labels[aqi]
        components = weather_data['air']['list'][0]['components']

        content = Text()
        content.append(f"\nOverall: ", style="white")
        content.append(f"{aqi_label}", style=aqi_color)
        content.append(f"\nPM2.5: {components['pm2_5']} μg/m³", style="cyan")
        content.append(f"\nNO2: {components['no2']} μg/m³", style="cyan")

        return Panel(
            content,
            title="[bold]Air Quality[/bold]",
            border_style="yellow",
            padding=(1, 2)
        )

    def display_weather(self, weather_data):
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Show title
        title_art = text2art("Weather   Dashboard", font="small")
        console.print(Panel(title_art, style="bold blue", border_style="blue"))

        # Create location panel
        location_text = Text(weather_data['address'], style="bold white")
        console.print(Panel(
            Align.center(location_text),
            border_style="blue",
            padding=(1, 2)
        ))

        # Create layout
        layout = Layout()
        layout.split_column(
            Layout(name="upper"),
            Layout(name="lower")
        )
        layout["upper"].split_row(
            Layout(name="current"),
            Layout(name="air")
        )

        # Add panels to layout
        layout["current"].update(self.create_current_weather_panel(weather_data))
        layout["air"].update(self.create_air_quality_panel(weather_data))
        layout["lower"].update(self.create_forecast_panel(weather_data))

        # Print layout
        console.print(layout)
        console.print("\n")

    def run(self):
        while True:
            self.show_welcome()
            city = console.input("[bold green]Enter city name (or 'quit' to exit): [/bold green]").strip()
            
            if city.lower() == 'quit':
                console.print("[bold blue]Thank you for using Weather Dashboard![/bold blue]")
                break
                
            if city:
                try:
                    weather_data = self.get_weather_data(city)
                    self.display_weather(weather_data)
                except Exception as e:
                    console.print(f"[red]Error: {str(e)}[/red]")
            else:
                console.print("[yellow]Please enter a valid city name.[/yellow]")
            
            if city.lower() != 'quit':
                console.input("\n[bold cyan]Press Enter to continue...[/bold cyan]")

def main():
    try:
        app = WeatherDashboard()
        app.run()
    except KeyboardInterrupt:
        console.print("\n[bold blue]Thank you for using Weather Dashboard![/bold blue]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
