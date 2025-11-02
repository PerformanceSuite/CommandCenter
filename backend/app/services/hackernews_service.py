"""
HackerNews Monitoring Service

Fetches technology news, trending topics, and relevant discussions from HackerNews.
Used for automated monitoring of technologies in the Technology Radar.

API Documentation: https://github.com/HackerNews/API
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class HackerNewsService:
    """
    Service for fetching and analyzing HackerNews content

    Features:
    - Fetch top stories, best stories, new stories
    - Search by keywords (technology names)
    - Filter by relevance score
    - Track trending topics
    """

    BASE_URL = "https://hacker-news.firebaseio.com/v0"
    ALGOLIA_SEARCH_URL = "https://hn.algolia.com/api/v1/search"

    def __init__(self):
        """Initialize HackerNews service"""
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _fetch_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch a single HackerNews item by ID

        Args:
            item_id: HackerNews item ID

        Returns:
            Item dict with 'id', 'type', 'title', 'url', 'score', 'time', etc.
        """
        try:
            response = await self.client.get(f"{self.BASE_URL}/item/{item_id}.json")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch HN item {item_id}: {e}")
            return None

    async def get_top_stories(self, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Fetch top stories from HackerNews

        Args:
            limit: Maximum number of stories to fetch (default 30)

        Returns:
            List of story dicts
        """
        try:
            # Fetch top story IDs
            response = await self.client.get(f"{self.BASE_URL}/topstories.json")
            response.raise_for_status()
            story_ids = response.json()[:limit]

            # Fetch story details
            stories = []
            for story_id in story_ids:
                story = await self._fetch_item(story_id)
                if story and story.get("type") == "story":
                    stories.append(self._normalize_story(story))

            logger.info(f"✅ Fetched {len(stories)} top HN stories")
            return stories

        except Exception as e:
            logger.error(f"Failed to fetch top stories: {e}")
            return []

    async def get_best_stories(self, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Fetch best (highest scored) stories from HackerNews

        Args:
            limit: Maximum number of stories to fetch

        Returns:
            List of story dicts
        """
        try:
            response = await self.client.get(f"{self.BASE_URL}/beststories.json")
            response.raise_for_status()
            story_ids = response.json()[:limit]

            stories = []
            for story_id in story_ids:
                story = await self._fetch_item(story_id)
                if story and story.get("type") == "story":
                    stories.append(self._normalize_story(story))

            logger.info(f"✅ Fetched {len(stories)} best HN stories")
            return stories

        except Exception as e:
            logger.error(f"Failed to fetch best stories: {e}")
            return []

    async def search_by_keywords(
        self,
        keywords: List[str],
        since_hours: int = 168,  # Last week
        min_score: int = 10,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search HackerNews for stories matching keywords

        Args:
            keywords: List of search terms (e.g., ['rust', 'webassembly'])
            since_hours: Only include stories from last N hours (default 168 = 1 week)
            min_score: Minimum story score (default 10)
            limit: Maximum results (default 50)

        Returns:
            List of matching stories
        """
        try:
            # Calculate timestamp for date filter
            since_timestamp = int((datetime.utcnow() - timedelta(hours=since_hours)).timestamp())

            # Build search query (OR logic for multiple keywords)
            query = " OR ".join(keywords)

            # Search using Algolia HN Search API
            params = {
                "query": query,
                "tags": "story",
                "numericFilters": f"created_at_i>{since_timestamp},points>{min_score}",
                "hitsPerPage": limit,
            }

            response = await self.client.get(self.ALGOLIA_SEARCH_URL, params=params)
            response.raise_for_status()
            data = response.json()

            stories = [self._normalize_algolia_hit(hit) for hit in data.get("hits", [])]
            logger.info(f"✅ Found {len(stories)} HN stories matching keywords: {keywords}")
            return stories

        except Exception as e:
            logger.error(f"Failed to search HN for keywords {keywords}: {e}")
            return []

    async def monitor_technologies(
        self, technology_names: List[str], since_hours: int = 168, min_score: int = 20
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Monitor HackerNews for mentions of specific technologies

        Args:
            technology_names: List of technology names to monitor
            since_hours: Time window (default 168h = 1 week)
            min_score: Minimum story score (default 20)

        Returns:
            Dict mapping technology name to list of relevant stories
        """
        results = {}

        for tech_name in technology_names:
            stories = await self.search_by_keywords(
                keywords=[tech_name],
                since_hours=since_hours,
                min_score=min_score,
                limit=20,
            )
            results[tech_name] = stories

        return results

    def _normalize_story(self, story: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize HN API story to consistent format

        Returns:
            Dict with 'id', 'title', 'url', 'score', 'author', 'time', 'comments_count'
        """
        return {
            "id": story.get("id"),
            "title": story.get("title", ""),
            "url": story.get("url", f"https://news.ycombinator.com/item?id={story.get('id')}"),
            "score": story.get("score", 0),
            "author": story.get("by", "unknown"),
            "time": datetime.fromtimestamp(story.get("time", 0)).isoformat(),
            "comments_count": len(story.get("kids", [])),
            "hn_url": f"https://news.ycombinator.com/item?id={story.get('id')}",
            "source": "hackernews",
        }

    def _normalize_algolia_hit(self, hit: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Algolia search hit to consistent format

        Returns:
            Same format as _normalize_story()
        """
        return {
            "id": hit.get("objectID"),
            "title": hit.get("title", ""),
            "url": hit.get("url", f"https://news.ycombinator.com/item?id={hit.get('objectID')}"),
            "score": hit.get("points", 0),
            "author": hit.get("author", "unknown"),
            "time": hit.get("created_at", ""),
            "comments_count": hit.get("num_comments", 0),
            "hn_url": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
            "source": "hackernews",
        }

    async def calculate_relevance_score(
        self, story_title: str, technology_keywords: List[str]
    ) -> float:
        """
        Calculate relevance score for a story based on technology keywords

        Args:
            story_title: Story title to analyze
            technology_keywords: Keywords to match against

        Returns:
            Relevance score (0.0 - 1.0)
        """
        title_lower = story_title.lower()
        matches = sum(1 for keyword in technology_keywords if keyword.lower() in title_lower)
        return min(1.0, matches / max(1, len(technology_keywords)))


# Global service instance
hackernews_service = HackerNewsService()
