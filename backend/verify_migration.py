from cosmos_db import cosmos_db
import logging
from pprint import pformat
import traceback
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_cosmos_db():
    """Verify Cosmos DB connection and contents"""
    try:
        # Check if Cosmos DB is initialized
        if not cosmos_db.is_initialized:
            cosmos_db._initialize()
            if not cosmos_db.is_initialized:
                logger.error("Failed to initialize Cosmos DB")
                return

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
            cosmos_posts_query = "SELECT * FROM c ORDER BY c._ts DESC"
            cosmos_posts = list(cosmos_db.sent_posts_container.query_items(
                query=cosmos_posts_query,
                enable_cross_partition_query=True
            ))
            logger.info(f"\nCosmos DB Sent Posts ({len(cosmos_posts)}):")
            for post in cosmos_posts:
                if '_ts' in post:
                    post['sent_at_readable'] = datetime.fromtimestamp(post['_ts']).isoformat()
                logger.info(pformat(post))
        except Exception as e:
            logger.error(f"Error getting Cosmos DB posts: {str(e)}")
            logger.error(traceback.format_exc())

    except Exception as e:
        logger.error(f"Error during verification: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    verify_cosmos_db()
