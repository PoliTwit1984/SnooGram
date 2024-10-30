from models import db, SubredditConfig, SentPost
from cosmos_db import cosmos_db
from app import app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_subreddit_configs():
    """Migrate subreddit configurations from SQLite to Cosmos DB"""
    with app.app_context():
        configs = SubredditConfig.query.all()
        logger.info(f"\nMigrating {len(configs)} subreddit configurations...")
        
        for config in configs:
            cosmos_data = {
                'id': str(config.id),
                'subreddit_name': config.subreddit_name,
                'filter_type': config.filter_type,
                'frequency': config.frequency,
                'is_active': config.is_active,
                'last_check': config.last_check.isoformat() if config.last_check else None,
                'created_at': config.created_at.isoformat() if config.created_at else None
            }
            try:
                cosmos_db.create_subreddit_config(cosmos_data)
                logger.info(f"✓ Migrated config for subreddit: {config.subreddit_name}")
            except Exception as e:
                logger.error(f"✗ Error migrating config {config.id}: {str(e)}")

def migrate_sent_posts():
    """Migrate sent posts from SQLite to Cosmos DB"""
    with app.app_context():
        posts = SentPost.query.all()
        logger.info(f"\nMigrating {len(posts)} sent posts...")
        
        for post in posts:
            cosmos_data = {
                'id': str(post.id),
                'post_id': post.post_id,
                'subreddit_name': post.subreddit_name,
                'sent_at': post.sent_at.isoformat() if post.sent_at else None
            }
            try:
                cosmos_db.create_sent_post(cosmos_data)
                logger.info(f"✓ Migrated sent post: {post.post_id}")
            except Exception as e:
                logger.error(f"✗ Error migrating post {post.id}: {str(e)}")

def verify_migration():
    """Verify the migration was successful"""
    with app.app_context():
        # Check subreddit configs
        sqlite_configs = SubredditConfig.query.all()
        cosmos_configs = cosmos_db.get_all_subreddit_configs()
        
        logger.info("\n=== Migration Verification ===")
        logger.info(f"Subreddit Configurations:")
        logger.info(f"SQLite count: {len(sqlite_configs)}")
        logger.info(f"Cosmos DB count: {len(cosmos_configs)}")
        
        # Check sent posts
        sqlite_posts = SentPost.query.all()
        cosmos_posts_query = "SELECT * FROM c"
        cosmos_posts = list(cosmos_db.sent_posts_container.query_items(
            query=cosmos_posts_query,
            enable_cross_partition_query=True
        ))
        
        logger.info(f"\nSent Posts:")
        logger.info(f"SQLite count: {len(sqlite_posts)}")
        logger.info(f"Cosmos DB count: {len(cosmos_posts)}")

def main():
    logger.info("Starting database migration to Cosmos DB...")
    
    # Initialize Cosmos DB
    if not cosmos_db.is_initialized:
        cosmos_db._initialize()
        if not cosmos_db.is_initialized:
            logger.error("Failed to initialize Cosmos DB. Check your connection settings.")
            return

    try:
        migrate_subreddit_configs()
        migrate_sent_posts()
        verify_migration()
        logger.info("\nMigration completed successfully!")
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")

if __name__ == "__main__":
    main()
