from staticmap import StaticMap, CircleMarker
from PIL import Image
import requests
from io import BytesIO
import math
import os
import dotenv

dotenv.load_dotenv(".secrets")

# CONFIGURATION
latitude, longitude = 37.4971, -77.7305  # Midlothian, VA
# latitude, longitude = 38.2527, -85.7585  # Louisville, KY
zoom = 5
width, height = 800, 600
owm_api_key = os.getenv("OPENWEATHERMAP_API_KEY")

# Weather Maps API 1.0 layers (FREE with basic API key)
weather_layers = {
    "clouds_new": "Clouds",
    "precipitation_new": "Precipitation", 
    "pressure_new": "Sea level pressure",
    "wind_new": "Wind speed",
    "temp_new": "Temperature"
}

# CONVERT LAT/LON TO TILE X/Y
def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    x = int((lon_deg + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return x, y

# DOWNLOAD TILE FROM OWM Weather Maps API 1.0 (FREE)
def download_weather_tile(x, y, zoom, layer, api_key):
    url = f"https://tile.openweathermap.org/map/{layer}/{zoom}/{x}/{y}.png?appid={api_key}"
    print(f"Weather tile URL: {url}")
    try:
        resp = requests.get(url, timeout=10)
        print(f"Status: {resp.status_code}, Content-Type: {resp.headers.get('content-type')}")
        
        if resp.status_code == 401:
            print("❌ 401 Unauthorized - Check your API key or subscription")
            return Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        elif resp.status_code == 429:
            print("❌ 429 Rate Limited - Too many requests")
            return Image.new("RGBA", (256, 256), (0, 0, 0, 0))
            
        resp.raise_for_status()
        
        tile = Image.open(BytesIO(resp.content)).convert("RGBA")
        print(f"Tile size: {tile.size}, mode: {tile.mode}")
        
        # Check transparency
        pixels = list(tile.getdata())
        transparent_pixels = sum(1 for p in pixels if p[3] == 0)
        print(f"Transparent pixels: {transparent_pixels}/{len(pixels)} ({transparent_pixels/len(pixels)*100:.1f}%)")
        
        return tile
    except Exception as e:
        print(f"Error downloading weather tile: {e}")
        return Image.new("RGBA", (256, 256), (0, 0, 0, 0))

# First, test if your API key works with the basic weather API
def test_basic_api(api_key):
    # Use coordinates instead of city name to avoid city lookup issues
    test_url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={api_key}"
    try:
        resp = requests.get(test_url)
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Basic API works! Current weather: {data['weather'][0]['description']}")
            print(f"Cloud coverage: {data.get('clouds', {}).get('all', 0)}%")
            print(f"Location: {data.get('name', 'Unknown')}")
            return True
        elif resp.status_code == 401:
            print(f"❌ API key invalid: {resp.text}")
            return False
        else:
            print(f"❌ Basic API failed: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Basic API test error: {e}")
        return False

print("Testing basic API first...")
if not test_basic_api(owm_api_key):
    print("Fix your API key before proceeding with weather tiles")
    # Don't exit, let's try the weather tiles anyway
    print("Continuing with weather tile tests...")

# Test different weather layers with the FREE API
print(f"\nTesting weather layers at zoom {zoom}...")
x_tile, y_tile = deg2num(longitude, latitude, zoom)
print(f"Tile coordinates: x={x_tile}, y={y_tile}")

for layer_code, layer_name in weather_layers.items():
    print(f"\n--- Testing {layer_name} ({layer_code}) ---")
    
    # 1. Base map
    m = StaticMap(width, height, url_template='https://tile.openstreetmap.org/{z}/{x}/{y}.png')
    m.add_marker(CircleMarker((longitude, latitude), 'red', 12))
    base_image = m.render(zoom=zoom).convert("RGBA")
    
    # 2. Weather overlay
    weather_tile = download_weather_tile(x_tile, y_tile, zoom, layer_code, owm_api_key)
    weather_resized = weather_tile.resize((width, height))
    
    # 3. Composite
    combined = Image.alpha_composite(base_image, weather_resized)
    
    # Save files
    base_image.save(f"basic_weather_{layer_code}_{zoom}.png")
    weather_tile.save(f"debug_weather_{layer_code}.png")
    combined.save(f"weather_map_{layer_code}.png")
    print(f"Saved weather_map_{layer_code}.png")

print("\n🎯 Try also testing with different zoom levels (3-8) for better weather coverage")

# Test multiple zoom levels for clouds
print(f"\n--- Testing clouds at different zoom levels ---")
for test_zoom in [3, 4, 5, 6, 7, 8]:
    x, y = deg2num(latitude, longitude, test_zoom)
    weather_tile = download_weather_tile(x, y, test_zoom, "clouds_new", owm_api_key)
    weather_tile.save(f"clouds_zoom_{test_zoom}.png")
    print(f"Saved clouds_zoom_{test_zoom}.png")