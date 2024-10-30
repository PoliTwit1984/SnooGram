import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, SubredditConfig, SentPost
from datetime import datetime
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import praw
from telegram.ext import Application
import logging
from logging.handlers import RotatingFileHandler
import re
import requests
from urllib.parse import urlparse
import hashlib

# Set up logging with rotation
log_handler = RotatingFileHandler(
    'app.log',
    maxBytes=1024 * 1024,  # 1MB
    backupCount=3  # Keep 3 backup files
)
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[log_handler]
)

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reddit_bot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Initialize Reddit client
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent='RedditTelegramBot/1.0'
)
reddit.read_only = True

# Initialize Telegram bot
telegram_app = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

# Redgifs API configuration
REDGIFS_TOKEN = None
REDGIFS_TOKEN_EXPIRES = 0

def get_redgifs_token():
    """Get a new access token for Redgifs API"""
    global REDGIFS_TOKEN, REDGIFS_TOKEN_EXPIRES
    
    current_time = datetime.now().timestamp()
    if REDGIFS_TOKEN and current_time < REDGIFS_TOKEN_EXPIRES:
        return REDGIFS_TOKEN
        
    try:
        response = requests.get('https://api.redgifs.com/v2/auth/temporary')
        if response.status_code == 200:
            data = response.json()
            REDGIFS_TOKEN = data.get('token')
            # Token expires in 1 hour, we'll refresh 5 minutes early
            REDGIFS_TOKEN_EXPIRES = current_time + 3300  # 55 minutes
            return REDGIFS_TOKEN
    except Exception as e:
        logging.error(f"Error getting Redgifs token: {str(e)}")
    return None

def is_image_url(url):
    """Check if URL is an image."""
    # Direct image URLs
    if url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
        return True
    # Reddit hosted images
    if 'i.redd.it' in url:
        return True
    # Imgur direct images or albums
    if 'imgur.com' in url:
        return True
    return False

def is_video_url(url, post):
    """Check if URL is a video."""
    # Reddit hosted videos
    if hasattr(post, 'is_video') and post.is_video:
        return True
    # Direct video URLs
    if url.endswith(('.mp4', '.webm')):
        return True
    # Redgifs URLs
    if 'redgifs.com' in url:
        return True
    # Reddit video URLs
    if 'v.redd.it' in url:
        return True
    return False

def get_video_url(post):
    """Extract actual video URL from post."""
    try:
        if hasattr(post, 'is_video') and post.is_video and hasattr(post, 'media'):
            return post.media['reddit_video']['fallback_url']
        elif 'redgifs.com' in post.url:
            # Extract video ID from URL
            if '/watch/' in post.url:
                video_id = post.url.split('/watch/')[-1]
            else:
                video_id = post.url.split('/')[-1]
            
            # Get token and make API request
            token = get_redgifs_token()
            if not token:
                logging.error("Failed to get Redgifs token")
                return None
                
            headers = {'Authorization': f'Bearer {token}'}
            api_url = f'https://api.redgifs.com/v2/gifs/{video_id}'
            
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                # Get HD URL if available, otherwise SD
                urls = data.get('gif', {}).get('urls', {})
                return urls.get('hd') or urls.get('sd')
            else:
                logging.error(f"Failed to get Redgifs video URL: {response.status_code}")
                return None
        return post.url
    except Exception as e:
        logging.error(f"Error getting video URL: {str(e)}")
        return None

def download_media(url, post_id, is_video=False):
    """Download media file and return local path"""
    try:
        # Create a unique filename using post_id and timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        
        # Get file extension from URL
        parsed_url = urlparse(url)
        ext = os.path.splitext(parsed_url.path)[1]
        if not ext:
            ext = '.mp4' if is_video else '.jpg'
        
        # Create filename and determine directory
        filename = f"{post_id}_{timestamp}_{file_hash}{ext}"
        base_dir = 'downloads/videos' if is_video else 'downloads/pics'
        filepath = os.path.join(base_dir, filename)
        
        # Download the file
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logging.info(f"Successfully downloaded media to {filepath}")
        return filepath
    except Exception as e:
        logging.error(f"Error downloading media: {str(e)}")
        return None

async def send_telegram_photo(chat_id, photo_path, caption):
    """Helper function to send photo to telegram"""
    logging.info(f"Attempting to send photo to Telegram - Path: {photo_path}")
    try:
        async with telegram_app:
            with open(photo_path, 'rb') as photo:
                await telegram_app.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=caption
                )
        logging.info("Successfully sent photo to Telegram")
    except Exception as e:
        logging.error(f"Failed to send photo to Telegram: {str(e)}")
        raise

async def send_telegram_video(chat_id, video_path, caption):
    """Helper function to send video to telegram"""
    logging.info(f"Attempting to send video to Telegram - Path: {video_path}")
    try:
        async with telegram_app:
            with open(video_path, 'rb') as video:
                await telegram_app.bot.send_video(
                    chat_id=chat_id,
                    video=video,
                    caption=caption
                )
        logging.info("Successfully sent video to Telegram")
    except Exception as e:
        logging.error(f"Failed to send video to Telegram: {str(e)}")
        raise

def send_to_telegram(subreddit_config):
    try:
        with app.app_context():  # Ensure we have application context
            logging.info(f"Processing subreddit: {subreddit_config.subreddit_name}")
            subreddit = reddit.subreddit(subreddit_config.subreddit_name)
            
            # Fetch more posts initially to ensure we have enough to work with after filtering
            if subreddit_config.filter_type == 'top_day':
                logging.info("Fetching top posts of the day")
                posts = list(subreddit.top(time_filter='day', limit=50))
            elif subreddit_config.filter_type == 'top_week':
                logging.info("Fetching top posts of the week")
                posts = list(subreddit.top(time_filter='week', limit=50))
            elif subreddit_config.filter_type == 'top_month':
                logging.info("Fetching top posts of the month")
                posts = list(subreddit.top(time_filter='month', limit=50))
            else:
                logging.info("Fetching top posts of the year")
                posts = list(subreddit.top(time_filter='year', limit=50))

            # Sort posts by upvotes (score) in descending order
            posts.sort(key=lambda x: x.score, reverse=True)
            
            content_found = False
            for post in posts:
                logging.info(f"Checking post: {post.id} - Score: {post.score} - URL: {post.url}")
                # Skip if we've sent this post before
                if SentPost.is_duplicate(post.id):
                    logging.info(f"Post {post.id} is a duplicate, skipping")
                    continue

                if hasattr(post, 'url'):
                    if is_image_url(post.url):
                        logging.info(f"Found image post: {post.id} with URL: {post.url}")
                        # Download the image
                        local_path = download_media(post.url, post.id, is_video=False)
                        if local_path:
                            try:
                                # Send the image using asyncio
                                asyncio.run(send_telegram_photo(
                                    chat_id=TELEGRAM_CHANNEL_ID,
                                    photo_path=local_path,
                                    caption=f"From r/{subreddit_config.subreddit_name}: {post.title}\nUpvotes: {post.score:,}"
                                ))
                                content_found = True
                            except Exception as e:
                                logging.error(f"Error sending image post {post.id}: {str(e)}")
                                continue
                    elif is_video_url(post.url, post):
                        logging.info(f"Found video post: {post.id}")
                        video_url = get_video_url(post)
                        if video_url:
                            # Download the video
                            local_path = download_media(video_url, post.id, is_video=True)
                            if local_path:
                                try:
                                    # Send the video using asyncio
                                    asyncio.run(send_telegram_video(
                                        chat_id=TELEGRAM_CHANNEL_ID,
                                        video_path=local_path,
                                        caption=f"From r/{subreddit_config.subreddit_name}: {post.title}\nUpvotes: {post.score:,}"
                                    ))
                                    content_found = True
                                except Exception as e:
                                    logging.error(f"Error sending video post {post.id}: {str(e)}")
                                    continue
                        else:
                            logging.error(f"Could not get video URL for post {post.id}")
                            continue
                    else:
                        logging.info(f"Post {post.id} is not an image or video post, skipping")
                        continue

                if content_found:
                    # Record that we sent this post
                    sent_post = SentPost(
                        post_id=post.id,
                        subreddit_name=subreddit_config.subreddit_name
                    )
                    db.session.add(sent_post)
                    db.session.commit()
                    logging.info(f"Successfully processed and recorded post {post.id}")
                    break
                    
            if not content_found:
                logging.warning(f"No suitable image or video posts found in r/{subreddit_config.subreddit_name}")
                    
            subreddit_config.last_check = datetime.now()
            db.session.commit()
            logging.info(f"Updated last_check for {subreddit_config.subreddit_name}")
    except Exception as e:
        logging.error(f"Error processing subreddit {subreddit_config.subreddit_name}: {str(e)}")
        raise

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

def schedule_subreddit(config):
    job_id = f"subreddit_{config.id}"
    logging.info(f"Scheduling job for subreddit: {config.subreddit_name} with frequency: {config.frequency} minutes")
    scheduler.add_job(
        send_to_telegram,
        'interval',
        minutes=config.frequency,
        id=job_id,
        replace_existing=True,
        args=[config]
    )

@app.route('/api/subreddits/search', methods=['GET'])
def search_subreddits():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    try:
        subreddits = []
        for subreddit in reddit.subreddits.search(query, limit=10):
            subreddits.append({
                'name': subreddit.display_name,
                'title': subreddit.title,
                'subscribers': subreddit.subscribers,
                'over18': subreddit.over18
            })
        return jsonify(subreddits)
    except Exception as e:
        logging.error(f"Error searching subreddits: {str(e)}")
        return jsonify([])

@app.route('/api/configs', methods=['GET'])
def get_configs():
    configs = SubredditConfig.query.all()
    return jsonify([config.to_dict() for config in configs])

@app.route('/api/configs', methods=['POST'])
def add_config():
    data = request.json
    logging.info(f"Adding new subreddit configuration: {data}")
    config = SubredditConfig(
        subreddit_name=data['subreddit_name'],
        filter_type=data['filter_type'],
        frequency=data['frequency'],
        is_active=True
    )
    db.session.add(config)
    db.session.commit()
    logging.info(f"Successfully added configuration for r/{config.subreddit_name}")
    
    try:
        # Send first image immediately
        logging.info(f"Attempting to send first image for r/{config.subreddit_name}")
        send_to_telegram(config)
        # Then set up the schedule
        schedule_subreddit(config)
        logging.info(f"Successfully set up scheduling for r/{config.subreddit_name}")
    except Exception as e:
        logging.error(f"Error in initial setup for r/{config.subreddit_name}: {str(e)}")
    
    return jsonify(config.to_dict())

@app.route('/api/configs/<int:config_id>', methods=['PUT'])
def update_config(config_id):
    config = SubredditConfig.query.get_or_404(config_id)
    data = request.json
    
    logging.info(f"Updating configuration for r/{config.subreddit_name}")
    config.filter_type = data['filter_type']
    config.frequency = data['frequency']
    db.session.commit()
    
    # Update the scheduler if config is active
    if config.is_active:
        schedule_subreddit(config)
    
    return jsonify(config.to_dict())

@app.route('/api/configs/<int:config_id>', methods=['DELETE'])
def delete_config(config_id):
    config = SubredditConfig.query.get_or_404(config_id)
    logging.info(f"Deleting configuration for r/{config.subreddit_name}")
    db.session.delete(config)
    db.session.commit()
    
    job_id = f"subreddit_{config_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logging.info(f"Removed scheduler job for r/{config.subreddit_name}")
    
    return '', 204

@app.route('/api/configs/<int:config_id>/toggle', methods=['POST'])
def toggle_config(config_id):
    config = SubredditConfig.query.get_or_404(config_id)
    config.is_active = not config.is_active
    db.session.commit()
    logging.info(f"Toggled r/{config.subreddit_name} to {'active' if config.is_active else 'inactive'}")
    
    job_id = f"subreddit_{config_id}"
    if config.is_active:
        try:
            # Send first image immediately when reactivating
            logging.info(f"Attempting to send image for reactivated r/{config.subreddit_name}")
            send_to_telegram(config)
            # Then set up the schedule
            schedule_subreddit(config)
            logging.info(f"Successfully set up scheduling for reactivated r/{config.subreddit_name}")
        except Exception as e:
            logging.error(f"Error in reactivation setup for r/{config.subreddit_name}: {str(e)}")
    else:
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            logging.info(f"Removed scheduler job for deactivated r/{config.subreddit_name}")
    
    return jsonify(config.to_dict())

@app.route('/api/configs/<int:config_id>/send-now', methods=['POST'])
def send_now(config_id):
    config = SubredditConfig.query.get_or_404(config_id)
    if not config.is_active:
        return jsonify({'error': 'Config is not active'}), 400
    
    try:
        send_to_telegram(config)
        return jsonify({'message': 'Content sent successfully'})
    except Exception as e:
        logging.error(f"Error in send-now for r/{config.subreddit_name}: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create downloads directories if they don't exist
        os.makedirs('downloads/pics', exist_ok=True)
        os.makedirs('downloads/videos', exist_ok=True)
        # Reschedule active configs on startup
        active_configs = SubredditConfig.query.filter_by(is_active=True).all()
        for config in active_configs:
            schedule_subreddit(config)
    app.run(port=8888, debug=True)
