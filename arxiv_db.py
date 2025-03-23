#\!/usr/bin/env python3
"""
ArXiv Database Module - MongoDB wrapper for managing arXiv paper data

This module provides a database class for storing and retrieving arXiv papers
with citation counts and social metrics.
"""

import os
import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ArxivDatabase:
    """MongoDB wrapper for storing and retrieving arXiv papers"""
    
    def __init__(self, clear_db=False):
        """
        Initialize the MongoDB connection.
        Parameters:
        - clear_db: If True, clear the database on initialization
        """
        # Get MongoDB credentials from environment variables
        self.mongodb_user = os.getenv('MONGODB_USER')
        self.mongodb_password = os.getenv('MONGODB_PASSWORD')
        
        # Connect to MongoDB with the correct connection string and auth source
        connection_string = f"mongodb://{self.mongodb_user}:{self.mongodb_password}@localhost:27017/?authSource=admin"
        self.client = MongoClient(connection_string)
        
        # Check if connection was successful
        try:
            # The ismaster command is cheap and does not require auth
            self.client.admin.command('ismaster')
            print("MongoDB connection successful")
        except ConnectionFailure as e:
            print(f"MongoDB connection failed: {e}")
            raise
        
        # Get database and collection
        self.db = self.client['arxivdump']
        self.papers = self.db['papers']
        
        # Create index on arxiv_id for faster lookups if it doesn't exist
        self.papers.create_index("arxiv_id", unique=True)
        
        # Optionally clear the database
        if clear_db:
            self.papers.delete_many({})
            print("Database cleared")
    
    def insert_papers(self, papers_list):
        """Insert multiple papers into the database"""
        count = 0
        for paper in papers_list:
            if self.insert_paper(paper):
                count += 1
        return count
    
    def insert_paper(self, paper):
        """Insert or update a single paper"""
        if not paper.get('arxiv_id'):
            print(f"Skipping paper with no arXiv ID: {paper.get('title', 'Unknown')}")
            return False
        
        # Add timestamp for when this was added to the database
        paper['db_updated'] = datetime.datetime.now()
        
        # Check if paper needs citation/twitter update
        existing = self.papers.find_one({"arxiv_id": paper['arxiv_id']})
        
        if existing:
            # Check if metrics need updating (older than 7 days)
            if existing.get('db_updated'):
                update_cutoff = datetime.datetime.now() - datetime.timedelta(days=7)
                if existing['db_updated'] > update_cutoff:
                    # Use existing metrics data if it's recent
                    if existing.get('citations') is not None:
                        paper['citations'] = existing['citations']
                    if existing.get('tweets') is not None:
                        paper['tweets'] = existing['tweets']
            
            # Update paper in database
            self.papers.replace_one({"arxiv_id": paper['arxiv_id']}, paper)
            print(f"Updated paper: {paper['arxiv_id']} - {paper['title']}")
        else:
            # Insert new paper
            try:
                self.papers.insert_one(paper)
                print(f"Added new paper: {paper['arxiv_id']} - {paper['title']}")
            except DuplicateKeyError:
                # Handle race condition
                self.papers.replace_one({"arxiv_id": paper['arxiv_id']}, paper)
                print(f"Race condition: Updated paper: {paper['arxiv_id']} - {paper['title']}")
        
        return True
    
    def get_all_papers(self):
        """Retrieve all papers"""
        return list(self.papers.find())
    
    def get_top_by_citations(self, limit=10):
        """Get top papers by citations"""
        return list(self.papers.find({"citations": {"$ne": None}}).sort("citations", -1).limit(limit))
    
    def get_top_by_tweets(self, limit=10):
        """Get top papers by Twitter mentions"""
        return list(self.papers.find({"tweets": {"$ne": None}}).sort("tweets", -1).limit(limit))
    
    def count_papers(self):
        """Count total papers"""
        return self.papers.count_documents({})
    
    def search_by_keyword(self, keyword, fields=None):
        """Search papers by keyword across specified fields"""
        if fields is None:
            fields = ['title', 'abstract', 'authors']
        
        # Build MongoDB text search query
        query = {"$or": []}
        for field in fields:
            if field == 'authors':
                # Special handling for array field
                query["$or"].append({"authors": {"$regex": keyword, "$options": "i"}})
            else:
                query["$or"].append({field: {"$regex": keyword, "$options": "i"}})
        
        return list(self.papers.find(query))
    
    def get_papers_by_date_range(self, start_date, end_date):
        """Get papers published within a date range"""
        # Convert string dates to datetime if needed
        if isinstance(start_date, str):
            start_date = datetime.datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.datetime.fromisoformat(end_date)
            
        query = {
            "published": {
                "$gte": start_date.isoformat(),
                "$lte": end_date.isoformat()
            }
        }
        
        return list(self.papers.find(query).sort("published", -1))
    
    def get_papers_needing_metrics_update(self, days_threshold=7):
        """Get papers that need citation and social metrics updates"""
        update_cutoff = datetime.datetime.now() - datetime.timedelta(days=days_threshold)
        
        query = {
            "$or": [
                {"db_updated": {"$lt": update_cutoff}},
                {"db_updated": {"$exists": False}},
                {"citations": {"$exists": False}},
                {"tweets": {"$exists": False}}
            ]
        }
        
        return list(self.papers.find(query))
    
    def close(self):
        """Close database connection"""
        self.client.close()

if __name__ == "__main__":
    # Example usage
    db = ArxivDatabase(clear_db=False)
    print(f"Database contains {db.count_papers()} papers")
    
    # Close connection
    db.close()
