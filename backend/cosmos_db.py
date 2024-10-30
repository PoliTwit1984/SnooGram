from azure.cosmos import CosmosClient, PartitionKey
from datetime import datetime
import logging
import traceback
from functools import wraps
from config import Config
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def singleton(cls):
    _instances = {}
    def get_instance(*args, **kwargs):
        if cls not in _instances:
            _instances[cls] = cls(*args, **kwargs)
        return _instances[cls]
    return get_instance

@singleton
class CosmosDB:
    def __init__(self):
        self._initialize()

    def _initialize(self):
        self.client = None
        self.database = None
        self.subreddit_config_container = None
        self.sent_posts_container = None
        self.is_initialized = False

        try:
            endpoint = Config.COSMOS_ENDPOINT
            key = Config.COSMOS_KEY
            database_name = Config.COSMOS_DATABASE

            logger.info("\nCosmos DB Configuration:")
            logger.info(f"Endpoint: {endpoint}")
            logger.info(f"Key length: {len(key) if key else 0}")
            logger.info(f"Database name: {database_name}")

            if endpoint and key and database_name:
                logger.info("\nInitializing Cosmos DB client...")
                try:
                    self.client = CosmosClient(url=endpoint, credential=key)
                    logger.info("Successfully created Cosmos DB client")
                except Exception as e:
                    logger.error(f"Error creating Cosmos DB client: {str(e)}")
                    logger.error(traceback.format_exc())
                    return
                
                logger.info("Creating/getting database...")
                try:
                    self.database = self.client.create_database_if_not_exists(
                        id=database_name
                    )
                    logger.info(f"Successfully got database: {database_name}")
                except Exception as e:
                    logger.error(f"Error creating/getting database: {str(e)}")
                    logger.error(traceback.format_exc())
                    return
                
                logger.info("Creating/getting subreddit_configs container...")
                try:
                    self.subreddit_config_container = self.database.create_container_if_not_exists(
                        id='subreddit_configs',
                        partition_key=PartitionKey(path='/subreddit_name'),
                        offer_throughput=400
                    )
                    logger.info("Successfully created subreddit_configs container")
                except Exception as e:
                    logger.error(f"Error creating subreddit_configs container: {str(e)}")
                    logger.error(traceback.format_exc())
                    return
                
                logger.info("Creating/getting sent_posts container...")
                try:
                    self.sent_posts_container = self.database.create_container_if_not_exists(
                        id='sent_posts',
                        partition_key=PartitionKey(path='/subreddit_name'),
                        offer_throughput=400
                    )
                    logger.info("Successfully created sent_posts container")
                except Exception as e:
                    logger.error(f"Error creating sent_posts container: {str(e)}")
                    logger.error(traceback.format_exc())
                    return
                
                self.is_initialized = True
                logger.info("Cosmos DB initialized successfully")
            else:
                missing = []
                if not endpoint:
                    missing.append("COSMOS_ENDPOINT")
                if not key:
                    missing.append("COSMOS_KEY")
                if not database_name:
                    missing.append("COSMOS_DATABASE")
                logger.error(f"Cosmos DB initialization failed. Missing environment variables: {', '.join(missing)}")
        except Exception as e:
            logger.error(f"Error initializing Cosmos DB: {str(e)}")
            logger.error(traceback.format_exc())

    def create_subreddit_config(self, config_data):
        """Create a new subreddit configuration"""
        if not self.is_initialized:
            self._initialize()
            if not self.is_initialized:
                logger.error("Cosmos DB not initialized, skipping create_subreddit_config")
                return None
            
        try:
            # Generate a new UUID for the config
            config_data['id'] = str(uuid.uuid4())
            config_data['created_at'] = datetime.utcnow().isoformat()
            config_data['last_check'] = datetime.utcnow().isoformat()
            config_data['is_active'] = True
            logger.info(f"Creating subreddit config in Cosmos DB: {config_data}")
            result = self.subreddit_config_container.create_item(body=config_data)
            logger.info(f"Successfully created config in Cosmos DB: {result}")
            return result
        except Exception as e:
            logger.error(f"Error creating subreddit config in Cosmos DB: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    def get_subreddit_config(self, subreddit_name):
        """Get subreddit configuration by name"""
        if not self.is_initialized:
            self._initialize()
            if not self.is_initialized:
                logger.error("Cosmos DB not initialized, skipping get_subreddit_config")
                return None
            
        try:
            query = "SELECT * FROM c WHERE c.subreddit_name = @subreddit_name"
            params = [{"name": "@subreddit_name", "value": subreddit_name}]
            results = list(self.subreddit_config_container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=True
            ))
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error getting subreddit config from Cosmos DB: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    def get_all_subreddit_configs(self):
        """Get all subreddit configurations"""
        if not self.is_initialized:
            self._initialize()
            if not self.is_initialized:
                logger.error("Cosmos DB not initialized, skipping get_all_subreddit_configs")
                return []
            
        try:
            query = "SELECT * FROM c"
            logger.info("Querying all subreddit configs from Cosmos DB...")
            results = list(self.subreddit_config_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            logger.info(f"Found {len(results)} configs in Cosmos DB")
            return results
        except Exception as e:
            logger.error(f"Error getting all subreddit configs from Cosmos DB: {str(e)}")
            logger.error(traceback.format_exc())
            return []

    def update_subreddit_config(self, config_data):
        """Update an existing subreddit configuration"""
        if not self.is_initialized:
            self._initialize()
            if not self.is_initialized:
                logger.error("Cosmos DB not initialized, skipping update_subreddit_config")
                return None
            
        try:
            config_data['id'] = str(config_data['id'])
            return self.subreddit_config_container.upsert_item(body=config_data)
        except Exception as e:
            logger.error(f"Error updating subreddit config in Cosmos DB: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    def delete_subreddit_config(self, config_id, subreddit_name):
        """Delete a subreddit configuration"""
        if not self.is_initialized:
            self._initialize()
            if not self.is_initialized:
                logger.error("Cosmos DB not initialized, skipping delete_subreddit_config")
                return
            
        try:
            self.subreddit_config_container.delete_item(
                item=str(config_id),
                partition_key=subreddit_name
            )
        except Exception as e:
            logger.error(f"Error deleting subreddit config from Cosmos DB: {str(e)}")
            logger.error(traceback.format_exc())

    def create_sent_post(self, post_data):
        """Record a sent post"""
        if not self.is_initialized:
            self._initialize()
            if not self.is_initialized:
                logger.error("Cosmos DB not initialized, skipping create_sent_post")
                return None
            
        try:
            post_data['id'] = str(uuid.uuid4())
            post_data['sent_at'] = datetime.utcnow().isoformat()
            logger.info(f"Creating sent post in Cosmos DB: {post_data}")
            result = self.sent_posts_container.create_item(body=post_data)
            logger.info(f"Successfully created sent post in Cosmos DB: {result}")
            return result
        except Exception as e:
            logger.error(f"Error creating sent post in Cosmos DB: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    def is_duplicate_post(self, post_id):
        """Check if a post has been sent before"""
        if not self.is_initialized:
            self._initialize()
            if not self.is_initialized:
                logger.error("Cosmos DB not initialized, skipping is_duplicate_post check")
                return False
            
        try:
            query = "SELECT * FROM c WHERE c.post_id = @post_id"
            params = [{"name": "@post_id", "value": post_id}]
            results = list(self.sent_posts_container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=True
            ))
            return len(results) > 0
        except Exception as e:
            logger.error(f"Error checking duplicate post in Cosmos DB: {str(e)}")
            logger.error(traceback.format_exc())
            return False

# Create a singleton instance
cosmos_db = CosmosDB()
