"""
Configuration Service for MCP WordPress Publisher v2.1

This module provides database-based configuration management for agents and sites,
replacing the previous YAML file-based approach.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlmodel import select, and_
from sqlalchemy.exc import IntegrityError
import hashlib
import secrets

from mcp_wordpress.core.database import get_session
from mcp_wordpress.models.agent import Agent
from mcp_wordpress.models.site import Site
from mcp_wordpress.core.errors import (
    ValidationError,
    AgentNotFoundError,
    SiteNotFoundError,
    MCPError,
    MCPErrorCodes
)


class ConfigService:
    """Service for managing agent and site configurations in database"""
    
    @staticmethod
    def _hash_api_key(api_key: str) -> str:
        """Hash API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def _generate_api_key() -> str:
        """Generate a secure random API key"""
        return secrets.token_urlsafe(32)
    
    # Agent Management Methods
    
    async def create_agent(
        self,
        agent_id: str,
        name: str,
        description: str = "",
        api_key: Optional[str] = None,
        rate_limit: Optional[Dict] = None,
        permissions: Optional[Dict] = None,
        notifications: Optional[Dict] = None,
        status: str = "active"
    ) -> Agent:
        """Create a new agent in the database"""
        
        # Generate API key if not provided
        if not api_key:
            api_key = self._generate_api_key()
        
        # Set defaults for configuration
        if not rate_limit:
            rate_limit = {
                "requests_per_minute": 10,
                "requests_per_hour": 100,
                "requests_per_day": 500
            }
        
        if not permissions:
            permissions = {
                "can_submit_articles": True,
                "can_edit_own_articles": True,
                "can_delete_own_articles": False,
                "can_view_statistics": True,
                "allowed_categories": [],
                "allowed_tags": []
            }
        
        if not notifications:
            notifications = {
                "on_approval": False,
                "on_rejection": True,
                "on_publish_success": True,
                "on_publish_failure": True
            }
        
        # Create agent object
        agent = Agent(
            id=agent_id,
            name=name,
            description=description,
            api_key_hash=self._hash_api_key(api_key),
            status=status,
            rate_limit=rate_limit,
            permissions=permissions,
            notifications=notifications
        )
        
        async with get_session() as session:
            try:
                session.add(agent)
                await session.commit()
                await session.refresh(agent)
                return agent
            except IntegrityError:
                await session.rollback()
                raise ValidationError(f"Agent with ID '{agent_id}' already exists")
    
    async def get_agent(self, agent_id: str) -> Agent:
        """Get agent by ID"""
        async with get_session() as session:
            result = await session.execute(select(Agent).where(Agent.id == agent_id))
            agent = result.scalars().first()
            if not agent:
                raise AgentNotFoundError(f"Agent '{agent_id}' not found")
            return agent
    
    async def get_all_agents(self, active_only: bool = False) -> List[Agent]:
        """Get all agents, optionally filtering by active status"""
        async with get_session() as session:
            query = select(Agent)
            if active_only:
                query = query.where(Agent.status == "active")
            result = await session.execute(query)
            return result.scalars().all()
    
    async def update_agent(
        self,
        agent_id: str,
        **updates: Any
    ) -> Agent:
        """Update agent configuration"""
        async with get_session() as session:
            result = await session.execute(select(Agent).where(Agent.id == agent_id))
            agent = result.scalars().first()
            if not agent:
                raise AgentNotFoundError(f"Agent '{agent_id}' not found")
            
            # Update fields
            for field, value in updates.items():
                if field == "api_key":
                    # Hash the new API key
                    value = self._hash_api_key(value)
                    field = "api_key_hash"
                
                if hasattr(agent, field):
                    setattr(agent, field, value)
            
            agent.updated_at = datetime.now(timezone.utc)
            
            try:
                await session.commit()
                await session.refresh(agent)
                return agent
            except IntegrityError:
                await session.rollback()
                raise ValidationError(f"Failed to update agent '{agent_id}'")
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        async with get_session() as session:
            result = await session.execute(select(Agent).where(Agent.id == agent_id))
            agent = result.scalars().first()
            if not agent:
                raise AgentNotFoundError(f"Agent '{agent_id}' not found")
            
            await session.delete(agent)
            await session.commit()
            return True
    
    async def validate_api_key(self, api_key: str) -> Optional[str]:
        """Validate API key and return agent ID if valid"""
        hashed_key = self._hash_api_key(api_key)
        
        async with get_session() as session:
            result = await session.execute(
                select(Agent).where(
                    and_(
                        Agent.api_key_hash == hashed_key,
                        Agent.status == "active"
                    )
                )
            )
            agent = result.scalars().first()
            return agent.id if agent else None
    
    # Site Management Methods
    
    async def create_site(
        self,
        site_id: str,
        name: str,
        description: str = "",
        wordpress_config: Optional[Dict] = None,
        publishing_rules: Optional[Dict] = None,
        rate_limit: Optional[Dict] = None,
        notifications: Optional[Dict] = None,
        status: str = "active"
    ) -> Site:
        """Create a new site in the database"""
        
        # Set defaults for configuration
        if not wordpress_config:
            wordpress_config = {
                "api_url": "",
                "username": "",
                "app_password_hash": "",
                "default_status": "publish",
                "default_comment_status": "open",
                "default_ping_status": "open",
                "category_mapping": {},
                "tag_auto_create": True
            }
        
        if not publishing_rules:
            publishing_rules = {
                "allowed_agents": [],
                "allowed_categories": [],
                "min_word_count": 100,
                "max_word_count": 5000,
                "require_featured_image": False,
                "auto_approve": False,
                "auto_publish_approved": True
            }
        
        if not rate_limit:
            rate_limit = {
                "max_posts_per_hour": 10,
                "max_posts_per_day": 50,
                "max_concurrent_publishes": 2
            }
        
        if not notifications:
            notifications = {
                "on_publish_success": True,
                "on_publish_failure": True,
                "on_connection_error": True
            }
        
        # Create site object
        site = Site(
            id=site_id,
            name=name,
            description=description,
            status=status,
            wordpress_config=wordpress_config,
            publishing_rules=publishing_rules,
            rate_limit=rate_limit,
            notifications=notifications
        )
        
        async with get_session() as session:
            try:
                session.add(site)
                await session.commit()
                await session.refresh(site)
                return site
            except IntegrityError:
                await session.rollback()
                raise ValidationError(f"Site with ID '{site_id}' already exists")
    
    async def get_site(self, site_id: str) -> Site:
        """Get site by ID"""
        async with get_session() as session:
            result = await session.execute(select(Site).where(Site.id == site_id))
            site = result.scalars().first()
            if not site:
                raise SiteNotFoundError(f"Site '{site_id}' not found")
            return site
    
    async def get_all_sites(self, active_only: bool = False) -> List[Site]:
        """Get all sites, optionally filtering by active status"""
        async with get_session() as session:
            query = select(Site)
            if active_only:
                query = query.where(Site.status == "active")
            result = await session.execute(query)
            return result.scalars().all()
    
    async def update_site(
        self,
        site_id: str,
        **updates: Any
    ) -> Site:
        """Update site configuration"""
        async with get_session() as session:
            result = await session.execute(select(Site).where(Site.id == site_id))
            site = result.scalars().first()
            if not site:
                raise SiteNotFoundError(f"Site '{site_id}' not found")
            
            # Update fields
            for field, value in updates.items():
                if hasattr(site, field):
                    setattr(site, field, value)
            
            site.updated_at = datetime.now(timezone.utc)
            
            try:
                await session.commit()
                await session.refresh(site)
                return site
            except IntegrityError:
                await session.rollback()
                raise ValidationError(f"Failed to update site '{site_id}'")
    
    async def delete_site(self, site_id: str) -> bool:
        """Delete a site"""
        async with get_session() as session:
            result = await session.execute(select(Site).where(Site.id == site_id))
            site = result.scalars().first()
            if not site:
                raise SiteNotFoundError(f"Site '{site_id}' not found")
            
            await session.delete(site)
            await session.commit()
            return True
    
    # Statistics and Monitoring Methods
    
    async def get_agent_statistics(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for an agent"""
        agent = await self.get_agent(agent_id)
        
        return {
            "agent_id": agent.id,
            "name": agent.name,
            "status": agent.status,
            "total_articles_submitted": agent.total_articles_submitted,
            "total_articles_published": agent.total_articles_published,
            "total_articles_rejected": agent.total_articles_rejected,
            "success_rate": agent.success_rate,
            "first_submission": agent.first_submission,
            "last_submission": agent.last_submission,
            "last_seen": agent.last_seen,
            "created_at": agent.created_at,
            "updated_at": agent.updated_at
        }
    
    async def get_site_statistics(self, site_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a site"""
        site = await self.get_site(site_id)
        
        return {
            "site_id": site.id,
            "name": site.name,
            "status": site.status,
            "health_status": site.health_status,
            "total_posts_published": site.total_posts_published,
            "total_posts_failed": site.total_posts_failed,
            "success_rate": site.success_rate,
            "last_publish": site.last_publish,
            "last_health_check": site.last_health_check,
            "created_at": site.created_at,
            "updated_at": site.updated_at
        }
    
    async def get_system_overview(self) -> Dict[str, Any]:
        """Get system-wide configuration overview"""
        agents = await self.get_all_agents()
        sites = await self.get_all_sites()
        
        active_agents = [a for a in agents if a.status == "active"]
        active_sites = [s for s in sites if s.status == "active"]
        
        return {
            "agents": {
                "total": len(agents),
                "active": len(active_agents),
                "inactive": len(agents) - len(active_agents)
            },
            "sites": {
                "total": len(sites),
                "active": len(active_sites),
                "inactive": len(sites) - len(active_sites)
            },
            "system_health": {
                "healthy_sites": len([s for s in active_sites if s.health_status == "healthy"]),
                "total_articles_submitted": sum(a.total_articles_submitted for a in agents),
                "total_articles_published": sum(a.total_articles_published for a in agents),
                "overall_success_rate": (
                    sum(a.total_articles_published for a in agents) / 
                    max(sum(a.total_articles_submitted for a in agents), 1)
                ) * 100
            }
        }


# Global instance
config_service = ConfigService()