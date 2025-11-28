"""
MongoDB connection utility for Qtratic project.
"""
from pymongo import MongoClient
from django.conf import settings


def get_mongo_client():
    """
    Get MongoDB client connection.
    Returns a MongoClient instance connected to the local MongoDB.
    """
    return MongoClient(
        host=settings.MONGO_HOST,
        port=settings.MONGO_PORT
    )


def get_mongo_db(db_name=None):
    """
    Get MongoDB database instance.
    
    Args:
        db_name: Database name (defaults to MONGO_DB_NAME from settings)
    
    Returns:
        Database instance
    """
    if db_name is None:
        db_name = settings.MONGO_DB_NAME
    
    client = get_mongo_client()
    return client[db_name]


def get_mongo_collection(collection_name, db_name=None):
    """
    Get MongoDB collection instance.
    
    Args:
        collection_name: Name of the collection
        db_name: Database name (defaults to MONGO_DB_NAME from settings)
    
    Returns:
        Collection instance
    """
    db = get_mongo_db(db_name)
    return db[collection_name]

