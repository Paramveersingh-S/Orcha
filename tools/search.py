import os
import requests
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class SearchTool:
    def __init__(self):
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not self.tavily_api_key:
            print("WARNING: TAVILY_API_KEY not found. Search may fail.")

    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Searches the web using Tavily API.
        Returns a list of dictionaries containing 'title', 'url', and 'content'.
        """
        if not self.tavily_api_key:
            return [{"title": "Error", "url": "", "content": "Tavily API key missing."}]

        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": "basic",
            "include_answer": False,
            "max_results": max_results,
        }

        try:
            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", "")
                })
            return results
        except Exception as e:
            print(f"Search failed for query '{query}': {e}")
            return []
