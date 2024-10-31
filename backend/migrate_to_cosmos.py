from cosmos_db import cosmos_db
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_cosmos_db():
    """Verify Cosmos DB connection and contents"""
    logger.info("Verifying Cosmos DB...")
    
    # Initialize Cosmos DB
    if not cosmos_db.is_initialized:
        cosmos_db._initialize()
        if not cosmos_db.is_initialized:
            logger.error("Failed to initialize Cosmos DB. Check your connection settings.")
            return

    try:
        # Check subreddit configs
        cosmos_configs = cosmos_db.get_all_subreddit_configs()
        logger.info("\n=== Cosmos DB Contents ===")
        logger.info(f"Subreddit Configurations: {len(cosmos_configs)}")
        for config in cosmos_configs:
            logger.info(f"✓ Found config for subreddit: {config['subreddit_name']}")
        
        # Check sent posts
        cosmos_posts_query = "SELECT * FROM c"
        cosmos_posts = list(cosmos_db.sent_posts_container.query_items(
            query=cosmos_posts_query,
            enable_cross_partition_query=True
        ))
        
        logger.info(f"\nSent Posts: {len(cosmos_posts)}")
        logger.info("\nCosmos DB verification completed!")
    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")

def add_test_config():
    """Add a test subreddit configuration"""
    try:
        if not cosmos_db.is_initialized:
            cosmos_db._initialize()
            if not cosmos_db.is_initialized:
                logger.error("Failed to initialize Cosmos DB")
                return

        test_config = {
            'subreddit_name': 'test_subreddit',
            'filter_type': 'top_day',
            'frequency': 60,
            'is_active': True,
            'last_check': datetime.now().isoformat(),
            'created_at': datetime.now().isoformat()
        }

        logger.info(f"Adding test configuration: {test_config}")
        result = cosmos_db.create_subreddit_config(test_config)
        logger.info(f"Successfully added test configuration: {result}")

    except Exception as e:
        logger.error(f"Error adding test configuration: {str(e)}")

def add_test_sent_post():
    """Add a test sent post"""
    try:
        if not cosmos_db.is_initialized:
            cosmos_db._initialize()
            if not cosmos_db.is_initialized:
                logger.error("Failed to initialize Cosmos DB")
                return

        test_post = {
            'post_id': 'test_post_123',
            'subreddit_name': 'test_subreddit',
            'sent_at': datetime.now().isoformat()
        }

        logger.info(f"Adding test sent post: {test_post}")
        result = cosmos_db.create_sent_post(test_post)
        logger.info(f"Successfully added test sent post: {result}")

    except Exception as e:
        logger.error(f"Error adding test sent post: {str(e)}")

if __name__ == "__main__":
    verify_cosmos_db()
