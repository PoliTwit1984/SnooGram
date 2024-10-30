from models import db, SubredditConfig, SentPost
from cosmos_db import cosmos_db
from app import app
import logging
from pprint import pformat
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_migration():
    with app.app_context():
        try:
            # Check if Cosmos DB is initialized
            if not cosmos_db.is_initialized:
                cosmos_db._initialize()
                if not cosmos_db.is_initialized:
                    logger.error("Failed to initialize Cosmos DB")
                    return

            # Check subreddit configs
            logger.info("\n=== SQLite Database Contents ===")
            sqlite_configs = SubredditConfig.query.all()
            logger.info(f"SQLite Subreddit Configs ({len(sqlite_configs)}):")
            for config in sqlite_configs:
                logger.info(pformat(config.to_dict()))
            
            sqlite_posts = SentPost.query.all()
            logger.info(f"\nSQLite Sent Posts ({len(sqlite_posts)}):")
            for post in sqlite_posts:
                logger.info(pformat({
                    'id': post.id,
                    'post_id': post.post_id,
                    'subreddit_name': post.subreddit_name,
                    'sent_at': post.sent_at.isoformat() if post.sent_at else None
                }))
            
            logger.info("\n=== Cosmos DB Contents ===")
            try:
                cosmos_configs = cosmos_db.get_all_subreddit_configs()
                logger.info(f"Cosmos DB Subreddit Configs ({len(cosmos_configs)}):")
                for config in cosmos_configs:
                    logger.info(pformat(config))
            except Exception as e:
                logger.error(f"Error getting Cosmos DB configs: {str(e)}")
                logger.error(traceback.format_exc())
            
            try:
                cosmos_posts_query = "SELECT * FROM c"
                cosmos_posts = list(cosmos_db.sent_posts_container.query_items(
                    query=cosmos_posts_query,
                    enable_cross_partition_query=True
                ))
                logger.info(f"\nCosmos DB Sent Posts ({len(cosmos_posts)}):")
                for post in cosmos_posts:
                    logger.info(pformat(post))
            except Exception as e:
                logger.error(f"Error getting Cosmos DB posts: {str(e)}")
                logger.error(traceback.format_exc())

        except Exception as e:
            logger.error(f"Error during verification: {str(e)}")
            logger.error(traceback.format_exc())

if __name__ == "__main__":
    verify_migration()
