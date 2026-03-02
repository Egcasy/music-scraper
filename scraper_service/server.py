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
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            stream_url = info.get('url')
            ext = info.get('ext')
            print(f"Extracted URL ({ext}): {stream_url}")
            return stream_url
        except Exception as e:
            print(f"yt-dlp error: {e}")
            return None

@app.route('/get_stream_url', methods=['GET'])
def get_stream_url():
    video_id = request.args.get('videoId')
    if not video_id:
        return jsonify({'error': 'Missing videoId parameter'}), 400
        
    try:
        logging.info(f"Received request for videoId: {video_id}")
        stream_url = get_best_audio_url(video_id)
        if stream_url:
            logging.info(f"Successfully extracted URL for {video_id}")
            return jsonify({'url': stream_url})
        else:
            logging.error(f"Failed to extract stream URL for {video_id}")
            return jsonify({'error': 'Failed to extract stream URL'}), 500
    except Exception as e:
        logging.error(f"Exception during extraction for {video_id}: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import os
    # Support dynamic PORT for cloud hosting (Render/Railway)
    port = int(os.environ.get('PORT', 5001))
    # Run on 0.0.0.0 so it can be accessed from Android emulator (10.0.2.2)
    app.run(host='0.0.0.0', port=port, debug=False)
