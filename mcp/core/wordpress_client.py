import requests
from typing import Optional, Dict, Any
from requests.auth import HTTPBasicAuth
import logging

from mcp.core.config import settings

logger = logging.getLogger(__name__)


class WordPressClient:
    """WordPress REST API client for publishing articles."""
    
    def __init__(self):
        self.api_url = settings.wordpress_api_url.rstrip('/')
        self.auth = HTTPBasicAuth(
            settings.wordpress_username, 
            settings.wordpress_app_password
        )
        self.session = requests.Session()
        self.session.auth = self.auth
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make HTTP request to WordPress API."""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"WordPress API request failed: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise
    
    def get_categories(self) -> Dict[str, int]:
        """Get WordPress categories as name -> ID mapping."""
        try:
            categories = self._make_request('GET', 'categories', params={'per_page': 100})
            return {cat['name']: cat['id'] for cat in categories}
        except Exception as e:
            logger.error(f"Failed to fetch categories: {e}")
            return {}
    
    def get_tags(self) -> Dict[str, int]:
        """Get WordPress tags as name -> ID mapping."""
        try:
            tags = self._make_request('GET', 'tags', params={'per_page': 100})
            return {tag['name']: tag['id'] for tag in tags}
        except Exception as e:
            logger.error(f"Failed to fetch tags: {e}")
            return {}
    
    def create_tag(self, name: str) -> Optional[int]:
        """Create a new WordPress tag."""
        try:
            tag_data = {'name': name}
            response = self._make_request('POST', 'tags', json=tag_data)
            return response['id']
        except Exception as e:
            logger.error(f"Failed to create tag '{name}': {e}")
            return None
    
    def create_category(self, name: str) -> Optional[int]:
        """Create a new WordPress category."""
        try:
            category_data = {'name': name}
            response = self._make_request('POST', 'categories', json=category_data)
            return response['id']
        except Exception as e:
            logger.error(f"Failed to create category '{name}': {e}")
            return None
    
    def resolve_tag_ids(self, tag_names: list[str]) -> list[int]:
        """Resolve tag names to IDs, creating new tags if needed."""
        if not tag_names:
            return []
        
        existing_tags = self.get_tags()
        tag_ids = []
        
        for tag_name in tag_names:
            tag_name = tag_name.strip()
            if not tag_name:
                continue
                
            if tag_name in existing_tags:
                tag_ids.append(existing_tags[tag_name])
            else:
                # Create new tag
                new_tag_id = self.create_tag(tag_name)
                if new_tag_id:
                    tag_ids.append(new_tag_id)
        
        return tag_ids
    
    def resolve_category_id(self, category_name: str) -> Optional[int]:
        """Resolve category name to ID, creating new category if needed."""
        if not category_name or not category_name.strip():
            return None
        
        category_name = category_name.strip()
        existing_categories = self.get_categories()
        
        if category_name in existing_categories:
            return existing_categories[category_name]
        else:
            # Create new category
            return self.create_category(category_name)
    
    def create_post(
        self, 
        title: str, 
        content: str, 
        tags: Optional[str] = None,
        category: Optional[str] = None,
        status: str = 'publish'
    ) -> Dict[str, Any]:
        """Create a new WordPress post."""
        
        # Prepare post data
        post_data = {
            'title': title,
            'content': content,
            'status': status
        }
        
        # Handle tags
        if tags:
            tag_names = [t.strip() for t in tags.split(',') if t.strip()]
            tag_ids = self.resolve_tag_ids(tag_names)
            if tag_ids:
                post_data['tags'] = tag_ids
        
        # Handle category
        if category:
            category_id = self.resolve_category_id(category)
            if category_id:
                post_data['categories'] = [category_id]
        
        try:
            response = self._make_request('POST', 'posts', json=post_data)
            return {
                'success': True,
                'post_id': response['id'],
                'permalink': response['link'],
                'data': response
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to create WordPress post: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
    
    def update_post(self, post_id: int, **kwargs) -> Dict[str, Any]:
        """Update an existing WordPress post."""
        try:
            response = self._make_request('PUT', f'posts/{post_id}', json=kwargs)
            return {
                'success': True,
                'post_id': response['id'],
                'permalink': response['link'],
                'data': response
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to update WordPress post {post_id}: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
    
    def delete_post(self, post_id: int) -> Dict[str, Any]:
        """Delete a WordPress post."""
        try:
            response = self._make_request('DELETE', f'posts/{post_id}')
            return {
                'success': True,
                'data': response
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to delete WordPress post {post_id}: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }