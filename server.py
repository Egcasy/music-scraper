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

def get_best_audio_url(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Sequence of clients to try
    configs = [
        # 1. Android (often most permissive)
        {'player_client': ['android'], 'player_skip': ['web', 'ios']},
        # 2. TV (previously worked well)
        {'player_client': ['tv'], 'player_skip': ['web', 'ios', 'android']},
        # 3. MediaConnect (newer bypass client)
        {'player_client': ['mediaconnect'], 'player_skip': ['web', 'ios', 'android', 'tv']},
        # 4. Web Embedded (requires Referer)
        {'player_client': ['web_embedded'], 'player_skip': ['web', 'ios', 'android', 'tv', 'mediaconnect']},
    ]
    
    last_error = "Unknown error"
    
    import os
    cookies_path = 'cookies.txt'
    has_cookies = os.path.exists(cookies_path)
    if has_cookies:
        logging.info("Using cookies.txt for extraction")

    for config in configs:
        referer = 'https://www.youtube.com/' if config['player_client'][0] == 'web_embedded' else None
        
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
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
            },
        }
        
        if referer:
            ydl_opts['http_headers']['Referer'] = referer
            
        if has_cookies:
            ydl_opts['cookiefile'] = cookies_path

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info and info.get('url'):
                    return info.get('url'), None
                last_error = "No URL in info"
        except Exception as e:
            last_error = str(e)
            if "Sign in to confirm you're not a bot" not in last_error:
                # If it's a different error, maybe the client is invalid, continue to next
                logging.warning(f"Client {config['player_client']} failed: {last_error}")
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
