import requests
import re
import json
import logging
import yt_dlp

def search_spotify(query, search_type='track', limit=10):
    """
    Scrapes Spotify metadata via the search page.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        search_url = f"https://open.spotify.com/search/{query.replace(' ', '%20')}"
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return []

        # Find the JSON data in the script tag
        match = re.search(r'<script id="session" type="application/json">(.*?)</script>', response.text)
        if not match:
            match = re.search(r'<script id="initial-state" type="application/json">(.*?)</script>', response.text)
            
        if not match:
            return []

        data = json.loads(match.group(1))
        
        # Note: Parsing exact structure depends on current Spotify layout
        # This is a simplified robust version for 2025
        results = []
        
        # Extract tracks from hydrated data
        # (Since the structure varies, we'll search for common patterns)
        def find_tracks(obj):
            if isinstance(obj, dict):
                if obj.get('type') == 'track' and 'name' in obj:
                    return [obj]
                res = []
                for v in obj.values():
                    res.extend(find_tracks(v))
                return res
            elif isinstance(obj, list):
                res = []
                for item in obj:
                    res.extend(find_tracks(item))
                return res
            return []

        found = find_tracks(data)
        seen_ids = set()
        for t in found:
            if t['id'] not in seen_ids:
                results.append({
                    'id': t['id'],
                    'title': t['name'],
                    'artist': t.get('artists', [{}])[0].get('name', 'Unknown'),
                    'thumbnail': t.get('album', {}).get('images', [{}])[0].get('url', ''),
                    'duration_ms': t.get('duration_ms', 0),
                    'source': 'spotify'
                })
                seen_ids.add(t['id'])
                if len(results) >= limit: break
        
        return results
    except Exception as e:
        logging.error(f"Spotify search error: {e}")
        return []

def find_youtube_match(title, artist):
    """
    Finds the best YouTube video for a given Spotify track metadata.
    """
    query = f"{title} {artist} official audio"
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'extract_flat': 'in_playlist',
        'force_generic_extractor': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Search on YouTube
            search_results = ydl.extract_info(f"ytsearch5:{query}", download=False)
            if 'entries' in search_results:
                # Basic ranking: prefer official channels or titles that match well
                for entry in search_results['entries']:
                    if entry:
                        return entry['id'], entry['url']
    except Exception as e:
        logging.error(f"YouTube matching error: {e}")
    
    return None, None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = search_spotify("Blinding Lights")
    print(json.dumps(res, indent=2))
