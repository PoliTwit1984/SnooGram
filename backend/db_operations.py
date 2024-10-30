from cosmos_db import cosmos_db
from datetime import datetime

class DatabaseOperations:
    @staticmethod
    def add_subreddit_config(data):
        cosmos_data = {
            'subreddit_name': data['subreddit_name'],
            'filter_type': data['filter_type'],
            'frequency': data['frequency']
        }
        return cosmos_db.create_subreddit_config(cosmos_data)

    @staticmethod
    def get_all_configs():
        return cosmos_db.get_all_subreddit_configs()

    @staticmethod
    def update_config(config_id, data):
        # First get existing config to preserve other fields
        configs = cosmos_db.get_all_subreddit_configs()
        config = next((c for c in configs if c['id'] == str(config_id)), None)
        if not config:
            raise Exception('Config not found')

        # Update with new data
        config['filter_type'] = data['filter_type']
        config['frequency'] = data['frequency']
        
        return cosmos_db.update_subreddit_config(config)

    @staticmethod
    def delete_config(config_id):
        # First get the config to get the subreddit_name for partition key
        configs = cosmos_db.get_all_subreddit_configs()
        config = next((c for c in configs if c['id'] == str(config_id)), None)
        if not config:
            raise Exception('Config not found')
            
        cosmos_db.delete_subreddit_config(str(config_id), config['subreddit_name'])

    @staticmethod
    def toggle_config(config_id):
        # First get existing config
        configs = cosmos_db.get_all_subreddit_configs()
        config = next((c for c in configs if c['id'] == str(config_id)), None)
        if not config:
            raise Exception('Config not found')

        # Toggle is_active
        config['is_active'] = not config['is_active']
        
        return cosmos_db.update_subreddit_config(config)

    @staticmethod
    def add_sent_post(post_id, subreddit_name):
        cosmos_data = {
            'post_id': post_id,
            'subreddit_name': subreddit_name
        }
        return cosmos_db.create_sent_post(cosmos_data)

    @staticmethod
    def is_duplicate_post(post_id):
        return cosmos_db.is_duplicate_post(post_id)
