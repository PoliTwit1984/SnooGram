# All database operations are now handled through cosmos_db.py
# No database models or connections needed

def get_all_configs():
    """
    This function is kept for backwards compatibility.
    All database operations should now use cosmos_db.py directly.
    """
    from cosmos_db import cosmos_db
    return cosmos_db.get_all_subreddit_configs()

def is_duplicate_post(post_id):
    """
    This function is kept for backwards compatibility.
    All database operations should now use cosmos_db.py directly.
    """
    from cosmos_db import cosmos_db
    return cosmos_db.is_duplicate_post(post_id)
