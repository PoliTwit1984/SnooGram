from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class SubredditConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subreddit_name = db.Column(db.String(100), nullable=False)
    filter_type = db.Column(db.String(20), nullable=False)  # top_day, top_week, top_month, top_year
    frequency = db.Column(db.Integer, nullable=False)  # frequency in minutes
    last_check = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'subreddit_name': self.subreddit_name,
            'filter_type': self.filter_type,
            'frequency': self.frequency,
            'is_active': self.is_active,
            'last_check': self.last_check.isoformat() if self.last_check else None
        }

class SentPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.String(20), nullable=False, index=True)  # Reddit post ID
    subreddit_name = db.Column(db.String(100), nullable=False)
    sent_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @staticmethod
    def is_duplicate(post_id):
        """Check if a post has been sent before"""
        return SentPost.query.filter_by(post_id=post_id).first() is not None
