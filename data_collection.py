import asyncio
import json
import os
from datetime import datetime
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

class DataCollector:
    def __init__(self):
        self.client = ApifyClient(os.getenv('APIFY_API_TOKEN'))
        self.output_file = 'scraped_ads.json'
    
    async def run_scraper(self):
        """Scrape ads for Dropps and Clean People using apify/facebook-ads-scraper, save all ad types"""
        start_urls = [
            {"url": "https://www.facebook.com/Dropps/"},
            {"url": "https://www.facebook.com/cleanpeople/"}
        ]
        run = self.client.actor("apify/facebook-ads-scraper").call(
            run_input={
                "startUrls": start_urls,
                "resultsLimit": 50,
                "activeStatus": "active"
            }
        )
        
        results = []
        for item in self.client.dataset(run['defaultDatasetId']).iterate_items():
            results.append(item)
        
        with open(self.output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        return results

# Usage
if __name__ == "__main__":
    collector = DataCollector()
    ads_data = asyncio.run(collector.run_scraper())
    print(f"Collected {len(ads_data)} ads (all types)") 