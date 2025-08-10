"""WordPress REST API client for content publishing."""

import aiohttp
import markdown
from typing import Dict, Any, Optional
from mcp_wordpress.core.config import settings


class WordPressClient:
    """Async WordPress REST API client with connection management."""
    
    def __init__(self, api_url: str = None, username: str = None, app_password: str = None):
        self.api_url = api_url or settings.wordpress_api_url
        self.username = username or settings.wordpress_username
        self.app_password = app_password or settings.wordpress_app_password
        self.auth = aiohttp.BasicAuth(self.username, self.app_password)
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with connection reuse."""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(
                auth=self.auth,
                connector=connector,
                timeout=timeout
            )
        return self._session
        
    async def close(self):
        """Close HTTP session and cleanup resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def create_post(
        self,
        title: str,
        content_markdown: str,
        tags: Optional[str] = None,
        category: Optional[str] = None,
        status: str = "publish"
    ) -> Dict[str, Any]:
        """Create a new WordPress post."""
        
        # Convert markdown to HTML
        content_html = markdown.markdown(content_markdown)
        
        post_data = {
            "title": title,
            "content": content_html,
            "status": status
        }
        
        # Add tags if provided
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            post_data["tags"] = await self._get_or_create_tags(tag_list)
        
        # Add category if provided
        if category:
            category_id = await self._get_or_create_category(category)
            if category_id:
                post_data["categories"] = [category_id]
        
        session = await self._get_session()
        async with session.post(f"{self.api_url}/posts", json=post_data) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"WordPress API error: {response.status} - {error_text}")
    
    async def _get_or_create_tags(self, tag_names: list[str]) -> list[int]:
        """Get or create tags and return their IDs."""
        tag_ids = []
        
        session = await self._get_session()
        for tag_name in tag_names:
            # Check if tag exists
            async with session.get(f"{self.api_url}/tags", params={"search": tag_name}) as response:
                    if response.status == 200:
                        tags = await response.json()
                        existing_tag = next((tag for tag in tags if tag["name"].lower() == tag_name.lower()), None)
                        
                        if existing_tag:
                            tag_ids.append(existing_tag["id"])
                        else:
                            # Create new tag
                            async with session.post(f"{self.api_url}/tags", json={"name": tag_name}) as create_response:
                                if create_response.status == 201:
                                    new_tag = await create_response.json()
                                    tag_ids.append(new_tag["id"])
        
        return tag_ids
    
    async def _get_or_create_category(self, category_name: str) -> Optional[int]:
        """Get or create category and return its ID."""
        
        session = await self._get_session()
        # Check if category exists
        async with session.get(f"{self.api_url}/categories", params={"search": category_name}) as response:
            if response.status == 200:
                    categories = await response.json()
                    existing_category = next(
                        (cat for cat in categories if cat["name"].lower() == category_name.lower()), 
                        None
                    )
                    
                    if existing_category:
                        return existing_category["id"]
                    else:
                        # Create new category
                        async with session.post(f"{self.api_url}/categories", json={"name": category_name}) as create_response:
                            if create_response.status == 201:
                                new_category = await create_response.json()
                                return new_category["id"]
        
        return None
    
    async def get_post(self, post_id: int) -> Dict[str, Any]:
        """Get a WordPress post by ID."""
        session = await self._get_session()
        async with session.get(f"{self.api_url}/posts/{post_id}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"WordPress API error: {response.status} - {error_text}")
    
    async def test_connection(self) -> bool:
        """Test WordPress API connection."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.api_url}/posts", params={"per_page": 1}) as response:
                    return response.status == 200
        except Exception:
            return False