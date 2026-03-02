import requests

try:
    print('Testing local python scraper with a public video...')
    # Rick Astley - Never Gonna Give You Up
    res = requests.get('http://127.0.0.1:5001/get_stream_url?videoId=dQw4w9WgXcQ')
    print(res.status_code)
    print(res.json())
except Exception as e:
    print(f"Error: {e}")
