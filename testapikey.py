def test_api_key(api_key):
    test_url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={api_key}"
    try:
        resp = requests.get(test_url)
        print(f"API key test: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Current weather in Louisville: {data.get('weather', [{}])[0].get('description', 'N/A')}")
            print(f"Cloud coverage: {data.get('clouds', {}).get('all', 'N/A')}%")
        else:
            print(f"API key error: {resp.text}")
    except Exception as e:
        print(f"API key test error: {e}")

test_api_key(owm_api_key)