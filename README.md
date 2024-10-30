# Reddit to Telegram Bot

This application allows users to configure and manage automatic posting of images from selected subreddits to a Telegram channel. Users can specify which subreddits to monitor, how to filter posts (top by day/week/month/year), and how frequently to check for new content.

## Setup Instructions

### Prerequisites
- Python 3.7+
- Node.js and npm
- Reddit API credentials
- Telegram Bot Token and Channel

### Backend Setup

1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Create .env file in the backend directory:
```bash
cp backend/.env.example backend/.env
```

4. Edit the .env file with your credentials:
- REDDIT_CLIENT_ID: Your Reddit API client ID
- REDDIT_CLIENT_SECRET: Your Reddit API client secret
- TELEGRAM_BOT_TOKEN: Your Telegram bot token
- TELEGRAM_CHANNEL: Your Telegram channel name (e.g., @your_channel)

5. Run the Flask backend:
```bash
cd backend
python app.py
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm start
```

The application will be available at http://localhost:3000

## Usage

1. Access the web interface at http://localhost:3000
2. Add new subreddit configurations:
   - Enter the subreddit name
   - Select the filtering option (top by day/week/month/year)
   - Set the checking frequency in minutes
3. Manage existing configurations:
   - Toggle configurations on/off
   - Delete unwanted configurations
4. The bot will automatically fetch images and post them to your Telegram channel based on the configured settings

## Features

- Web interface for managing subreddit configurations
- Multiple subreddit monitoring
- Configurable post filtering (top by day/week/month/year)
- Adjustable checking frequency
- Automatic posting to Telegram channel
- Active/Inactive status toggle for each configuration
