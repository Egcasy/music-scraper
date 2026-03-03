from flask import Flask, request, jsonify
import yt_dlp
import traceback
import logging

logging.basicConfig(
    filename='server.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

app = Flask(__name__)

from spotify_search import search_spotify, find_youtube_match

@app.route('/search/spotify', methods=['GET'])
def spotify_search_route():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Missing query parameter'}), 400
    
    results = search_spotify(query)
    return jsonify(results)

@app.route('/get_spotify_stream', methods=['GET'])
def get_spotify_stream():
    title = request.args.get('title')
    artist = request.args.get('artist')
    
    if not title or not artist:
        return jsonify({'error': 'Missing title or artist'}), 400
        
    logging.info(f"Bridging Spotify track to YouTube: {title} by {artist}")
    video_id, _ = find_youtube_match(title, artist)
    
    if not video_id:
        return jsonify({'error': 'Could not find a YouTube match'}), 404
        
    stream_url, error = get_best_audio_url(video_id)
    if stream_url:
        return jsonify({'url': stream_url, 'videoId': video_id})
    else:
        return jsonify({'error': 'Failed to extract stream URL from matched YouTube video', 'details': error}), 500

def get_best_audio_url(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Sequence of clients to try. 
    # TV and Android often hit Error 152 (bot/age/region block).
    # MWeb and Web Embedded are better fallbacks but prone to "Sign in" bot check.
    configs = [
        # 1. Android (often the fastest if not blocked)
        {'name': 'android', 'player_client': ['android'], 'player_skip': ['web', 'ios']},
        # 2. TV (previously worked well, now prone to 152)
        {'name': 'tv', 'player_client': ['tv'], 'player_skip': ['web', 'ios', 'android']},
        # 3. Mobile Web (Standard browser bypass)
        {'name': 'mweb', 'player_client': ['mweb'], 'player_skip': ['web', 'ios', 'android', 'tv']},
        # 4. Web Embedded (requires Referer)
        {'name': 'web_embedded', 'player_client': ['web_embedded'], 'player_skip': ['web', 'ios', 'android', 'tv', 'mediaconnect', 'mweb']},
    ]
    
    last_error = "Unknown error"
    
    import os
    cookies_path = 'cookies.txt'
    has_cookies = os.path.exists(cookies_path)
    if has_cookies:
        logging.info("Using cookies.txt for extraction")

    for config in configs:
        logging.info(f"Attempting extraction with client: {config['name']}")
        
        referer = 'https://www.youtube.com/'
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        
        if config['name'] == 'mweb':
             user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'

        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'extractor_args': {
                'youtube': {
                    'player_client': config['player_client'],
                    'player_skip': config['player_skip'],
                }
            },
            'http_headers': {
                'User-Agent': user_agent,
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': referer,
                'Origin': 'https://www.youtube.com',
            },
        }
        
        if has_cookies:
            ydl_opts['cookiefile'] = cookies_path

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info and info.get('url'):
                    logging.info(f"✅ Success with client: {config['name']}")
                    return info.get('url'), None
                last_error = "No URL in info"
        except Exception as e:
            last_error = str(e)
            # If we hit 152, it's a specific "Video Unavailable" client-side block.
            # We must try the next client.
            if "152" in last_error or "Sign in to confirm" in last_error:
                logging.warning(f"❌ Client {config['name']} blocked: {last_error}")
            else:
                logging.error(f"⚠️ Error with {config['name']}: {last_error}")
            continue
            
    return None, last_error

@app.route('/get_stream_url', methods=['GET'])
def get_stream_url():
    video_id = request.args.get('videoId')
    if not video_id:
        return jsonify({'error': 'Missing videoId parameter'}), 400
        
    try:
        logging.info(f"Received request for videoId: {video_id}")
        stream_url, error = get_best_audio_url(video_id)
        if stream_url:
            logging.info(f"Successfully extracted URL for {video_id}")
            return jsonify({'url': stream_url})
        else:
            logging.error(f"Failed to extract stream URL for {video_id}: {error}")
            return jsonify({'error': 'Failed to extract stream URL', 'details': error}), 500
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Exception during extraction for {video_id}: {error_msg}")
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    import os
    # Support dynamic PORT for cloud hosting (Render/Railway)
    port = int(os.environ.get('PORT', 5001))
    # Run on 0.0.0.0 so it can be accessed from Android emulator (10.0.2.2)
    app.run(host='0.0.0.0', port=port, debug=False)
