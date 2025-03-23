#!/usr/bin/env python3
import os
import time
from dotenv import load_dotenv
from twitter.search import Search

class TwitterSearch:
    def __init__(self):
        load_dotenv()
        self.auth_token = os.environ.get("TWITTER_AUTH_TOKEN")
        self.ct0_token = os.environ.get("TWITTER_CT0_TOKEN")
        self.api_client = None
        if self.auth_token and self.ct0_token:
            self.api_client = Search(cookies={"auth_token": self.auth_token, "ct0": self.ct0_token})
        
    def get_tweet_count(self, arxiv_id, delay=5.0):
        if not self.api_client:
            return 0
            
        try:
            # Always wait 5 seconds before making a request to avoid rate limits
            time.sleep(5)
            
            results = self.api_client.run(
                limit=100,
                retries=2,
                queries=[{'category': 'Top', 'query': arxiv_id}],
                save=False
            )
            tweet_count = 0
            if results and isinstance(results, list) and len(results) > 0:
                for category_results in results:
                    for tweet_data in category_results:
                        if 'entryId' in tweet_data and tweet_data['entryId'].startswith('tweet-'):
                            tweet_count += 1
            return tweet_count
        except Exception as e:
            print(f"Error searching Twitter: {e}")
            return 0

if __name__ == "__main__":
    import sys
    arxiv_id = sys.argv[1] if len(sys.argv) > 1 else "2307.15043"
    twitter = TwitterSearch()
    if twitter.api_client:
        count = twitter.get_tweet_count(arxiv_id)
        print(f"Found {count} tweets mentioning arXiv:{arxiv_id}")
    else:
        print("Twitter API tokens not found in .env file")
        print("Add TWITTER_AUTH_TOKEN and TWITTER_CT0_TOKEN to your .env file")