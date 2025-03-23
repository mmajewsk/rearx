#!/usr/bin/env python3
import os
import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from dotenv import load_dotenv

load_dotenv()

class ArxivDatabase:
    def __init__(self, clear_db=False):
        self.mongodb_user = os.getenv('MONGODB_USER')
        self.mongodb_password = os.getenv('MONGODB_PASSWORD')
        
        connection_string = f"mongodb://{self.mongodb_user}:{self.mongodb_password}@localhost:27017/?authSource=admin"
        self.client = MongoClient(connection_string)
        
        try:
            self.client.admin.command('ismaster')
            print("MongoDB connection successful")
        except ConnectionFailure as e:
            print(f"MongoDB connection failed: {e}")
            raise
        
        self.db = self.client['arxivdump']
        self.papers = self.db['papers']
        self.papers.create_index("arxiv_id", unique=True)
        
        if clear_db:
            self.papers.delete_many({})
            print("Database cleared")
    
    def insert_papers(self, papers_list):
        count = 0
        for paper in papers_list:
            if self.insert_paper(paper):
                count += 1
        return count
    
    def insert_paper(self, paper):
        if not paper.get('arxiv_id'):
            print(f"Skipping paper with no arXiv ID: {paper.get('title', 'Unknown')}")
            return False
        
        paper['db_updated'] = datetime.datetime.now()
        existing = self.papers.find_one({"arxiv_id": paper['arxiv_id']})
        
        if existing:
            if existing.get('db_updated'):
                update_cutoff = datetime.datetime.now() - datetime.timedelta(days=7)
                if existing['db_updated'] > update_cutoff:
                    if existing.get('citations') is not None:
                        paper['citations'] = existing['citations']
                    if existing.get('tweets') is not None:
                        paper['tweets'] = existing['tweets']
            
            self.papers.replace_one({"arxiv_id": paper['arxiv_id']}, paper)
            print(f"Updated paper: {paper['arxiv_id']} - {paper['title']}")
        else:
            try:
                self.papers.insert_one(paper)
                print(f"Added new paper: {paper['arxiv_id']} - {paper['title']}")
            except DuplicateKeyError:
                self.papers.replace_one({"arxiv_id": paper['arxiv_id']}, paper)
                print(f"Race condition: Updated paper: {paper['arxiv_id']} - {paper['title']}")
        
        return True
    
    def get_all_papers(self):
        return list(self.papers.find())
    
    def get_top_by_citations(self, limit=10):
        return list(self.papers.find({"citations": {"$ne": None}}).sort("citations", -1).limit(limit))
    
    def get_top_by_tweets(self, limit=10):
        return list(self.papers.find({"tweets": {"$ne": None}}).sort("tweets", -1).limit(limit))
    
    def count_papers(self):
        return self.papers.count_documents({})
    
    def search_by_keyword(self, keyword, fields=None):
        if fields is None:
            fields = ['title', 'abstract', 'authors']
        
        query = {"$or": []}
        for field in fields:
            if field == 'authors':
                query["$or"].append({"authors": {"$regex": keyword, "$options": "i"}})
            else:
                query["$or"].append({field: {"$regex": keyword, "$options": "i"}})
        
        return list(self.papers.find(query))
    
    def get_papers_by_date_range(self, start_date, end_date):
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
        self.client.close()

if __name__ == "__main__":
    db = ArxivDatabase(clear_db=False)
    print(f"Database contains {db.count_papers()} papers")
    db.close()