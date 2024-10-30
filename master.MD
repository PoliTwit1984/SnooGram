# Reddit to Telegram Media Bot

## Overview
This application is an automated bot that monitors specified subreddits and forwards media content (images and videos) to a Telegram channel. It features a web-based dashboard for configuration and management, allowing users to easily add, modify, and monitor subreddit tracking settings.

## Technical Architecture

### Backend (Python/Flask)
- Flask server running on port 8888
- SQLite database for configuration and post tracking
- Integration with Reddit API (PRAW)
- Integration with Telegram Bot API
- Support for various media types (images, videos, including Redgifs)
- Automated scheduling system for periodic posts

### Frontend (React)
- React-based dashboard
- Real-time configuration management
- Subreddit search functionality
- Active monitoring of configurations

## Core Features

### 1. Subreddit Monitoring
- Monitor multiple subreddits simultaneously
- Configurable monitoring frequencies
- Support for different time-based filters:
  - Top of Day
  - Top of Week
  - Top of Month
  - Top of Year

### 2. Media Handling
- Automatic detection and download of:
  - Direct images (jpg, jpeg, png, gif)
  - Reddit-hosted images
  - Imgur images
  - Reddit-hosted videos
  - Redgifs videos
- Automatic media storage in organized directories
- Duplicate post detection to prevent reposts

### 3. Configuration Management
- Add/remove subreddits
- Enable/disable monitoring
- Adjust monitoring frequency
- Modify filter types
- Manual "Send Now" trigger
- Active status tracking

## Setup Instructions

### Prerequisites
1. Python 3.x
2. Node.js and npm
3. Reddit API credentials
4. Telegram Bot Token and Channel ID

### Environment Setup

1. Create a `.env` file in the backend directory with:
```
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHANNEL_ID=your_telegram_channel_id
```

### Installation

1. Backend Setup:
```bash
# Install Python dependencies
pip install -r requirements.txt

# Initialize database
cd backend
python app.py
```

2. Frontend Setup:
```bash
# Install frontend dependencies
cd frontend
npm install

# Start frontend development server
npm start
```

## Database Schema

### SubredditConfig
- id: Primary key
- subreddit_name: Name of the subreddit to monitor
- filter_type: Type of posts to fetch (top_day, top_week, top_month, top_year)
- frequency: Monitoring frequency in minutes
- last_check: Timestamp of last check
- is_active: Current monitoring status
- created_at: Configuration creation timestamp

### SentPost
- id: Primary key
- post_id: Reddit post ID
- subreddit_name: Source subreddit
- sent_at: Timestamp when post was sent

## API Endpoints

### Subreddit Management
- GET `/api/subreddits/search?q={query}`: Search for subreddits
- GET `/api/configs`: List all configurations
- POST `/api/configs`: Add new configuration
- PUT `/api/configs/{id}`: Update configuration
- DELETE `/api/configs/{id}`: Delete configuration
- POST `/api/configs/{id}/toggle`: Toggle configuration status
- POST `/api/configs/{id}/send-now`: Trigger immediate post

## File Structure
```
/
├── backend/
│   ├── app.py           # Main Flask application
│   ├── models.py        # Database models
│   └── instance/        # SQLite database location
├── frontend/
│   ├── src/
│   │   ├── App.js      # Main React component
│   │   └── App.css     # Styles
│   └── public/         
└── downloads/
    ├── pics/           # Downloaded images
    └── videos/         # Downloaded videos
```

## Usage Instructions

1. Start both backend and frontend servers
2. Access the dashboard at `http://localhost:3000`
3. Add subreddits to monitor:
   - Search for a subreddit or enter name manually
   - Select filter type (top of day/week/month/year)
   - Set monitoring frequency in minutes
   - Click "Add Subreddit"
4. Manage configurations:
   - Enable/disable monitoring
   - Edit settings
   - Trigger immediate posts
   - Remove configurations

## Important Notes

1. Media Storage:
   - Images are stored in `downloads/pics/`
   - Videos are stored in `downloads/videos/`
   - Files are named using format: `{post_id}_{timestamp}_{hash}.{extension}`

2. Rate Limiting:
   - Respects Reddit API rate limits
   - Implements Redgifs token management
   - Handles API errors gracefully

3. Logging:
   - Rotating log files (app.log)
   - Maximum size: 1MB
   - Keeps 3 backup files

## Recovery Instructions

To recreate this application:

1. Set up the environment and install dependencies
2. Create the required directory structure
3. Configure environment variables
4. Initialize the database
5. Start both servers
6. Add desired subreddit configurations through the dashboard

The application will automatically:
- Create necessary directories
- Initialize the database
- Schedule active configurations
- Handle media downloads and posting

## Troubleshooting

1. Media Download Issues:
   - Check network connectivity
   - Verify Reddit API credentials
   - Ensure sufficient storage space

2. Posting Issues:
   - Verify Telegram bot token and channel ID
   - Check bot permissions in channel
   - Review app.log for specific errors

3. Configuration Issues:
   - Ensure database file exists
   - Check file permissions
   - Verify environment variables

## Security Considerations

1. API Access:
   - Store credentials securely in .env file
   - Never commit sensitive information
   - Use read-only Reddit access

2. Media Handling:
   - Validate file types before download
   - Implement file size limits
   - Clean up old media files periodically

3. Database:
   - Use SQLite with appropriate file permissions
   - Implement proper error handling
   - Regular backups recommended
