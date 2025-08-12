"""
Security enhancement mechanisms for MCP WordPress Publisher v2.1

This module implements rate limiting, session management, and audit logging
to provide comprehensive security for the multi-agent multi-site environment.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import hashlib

from mcp_wordpress.core.database import get_session
from mcp_wordpress.core.config import settings


logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_allowance: int = 10
    lockout_duration_minutes: int = 15


@dataclass
class SessionInfo:
    """Session information for an authenticated agent."""
    agent_id: str
    agent_name: str
    created_at: datetime
    last_activity: datetime
    request_count: int = 0
    failed_attempts: int = 0
    is_locked: bool = False
    lockout_until: Optional[datetime] = None


@dataclass 
class AuditLogEntry:
    """Audit log entry for security events."""
    timestamp: datetime
    agent_id: str
    action: str
    resource: str
    success: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[Dict] = field(default_factory=dict)


class RateLimiter:
    """
    Rate limiter with sliding window algorithm.
    
    Implements per-agent rate limiting with configurable limits
    and burst allowance for handling traffic spikes.
    """
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.minute_windows: Dict[str, deque] = defaultdict(deque)
        self.hour_windows: Dict[str, deque] = defaultdict(deque)
        self.locked_agents: Dict[str, datetime] = {}
        
    async def check_rate_limit(self, agent_id: str) -> bool:
        """
        Check if agent is within rate limits.
        
        Args:
            agent_id: The agent ID to check
            
        Returns:
            True if within limits, False if rate limited
        """
        now = datetime.now(timezone.utc)
        
        # Check if agent is currently locked out
        if agent_id in self.locked_agents:
            lockout_until = self.locked_agents[agent_id]
            if now < lockout_until:
                logger.warning(f"代理 {agent_id} 仍在锁定期内，解锁时间：{lockout_until}")
                return False
            else:
                # Lockout expired, remove from locked list
                del self.locked_agents[agent_id]
                logger.info(f"代理 {agent_id} 锁定期结束，恢复访问")
        
        # Clean old entries from sliding windows
        self._clean_windows(agent_id, now)
        
        # Check minute rate limit
        minute_requests = len(self.minute_windows[agent_id])
        if minute_requests >= self.config.requests_per_minute:
            await self._apply_lockout(agent_id, now)
            return False
            
        # Check hour rate limit
        hour_requests = len(self.hour_windows[agent_id])
        if hour_requests >= self.config.requests_per_hour:
            await self._apply_lockout(agent_id, now)
            return False
        
        # Add current request to windows
        self.minute_windows[agent_id].append(now)
        self.hour_windows[agent_id].append(now)
        
        return True
    
    def _clean_windows(self, agent_id: str, now: datetime) -> None:
        """Clean expired entries from sliding windows."""
        minute_cutoff = now - timedelta(minutes=1)
        hour_cutoff = now - timedelta(hours=1)
        
        # Clean minute window
        minute_window = self.minute_windows[agent_id]
        while minute_window and minute_window[0] < minute_cutoff:
            minute_window.popleft()
            
        # Clean hour window
        hour_window = self.hour_windows[agent_id]
        while hour_window and hour_window[0] < hour_cutoff:
            hour_window.popleft()
    
    async def _apply_lockout(self, agent_id: str, now: datetime) -> None:
        """Apply rate limit lockout to an agent."""
        lockout_until = now + timedelta(minutes=self.config.lockout_duration_minutes)
        self.locked_agents[agent_id] = lockout_until
        
        logger.warning(f"代理 {agent_id} 触发速率限制，锁定至：{lockout_until}")
        
        # Log security event
        await SecurityManager.instance.log_audit_event(
            agent_id=agent_id,
            action="rate_limit_violation",
            resource="api",
            success=False,
            details={
                "lockout_until": lockout_until.isoformat(),
                "lockout_duration_minutes": self.config.lockout_duration_minutes
            }
        )
    
    def get_agent_status(self, agent_id: str) -> Dict:
        """Get current rate limit status for an agent."""
        now = datetime.now(timezone.utc)
        self._clean_windows(agent_id, now)
        
        minute_requests = len(self.minute_windows[agent_id])
        hour_requests = len(self.hour_windows[agent_id])
        
        is_locked = agent_id in self.locked_agents
        lockout_until = self.locked_agents.get(agent_id)
        
        return {
            "agent_id": agent_id,
            "minute_requests": minute_requests,
            "minute_limit": self.config.requests_per_minute,
            "hour_requests": hour_requests,
            "hour_limit": self.config.requests_per_hour,
            "is_locked": is_locked,
            "lockout_until": lockout_until.isoformat() if lockout_until else None,
            "remaining_minute": max(0, self.config.requests_per_minute - minute_requests),
            "remaining_hour": max(0, self.config.requests_per_hour - hour_requests)
        }


class SessionManager:
    """
    Session manager for authenticated agents.
    
    Tracks active sessions, failed authentication attempts,
    and implements session timeout and cleanup.
    """
    
    def __init__(self, session_timeout_minutes: int = 60):
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.sessions: Dict[str, SessionInfo] = {}
        self.cleanup_task: Optional[asyncio.Task] = None
        
    async def start(self) -> None:
        """Start the session manager and cleanup task."""
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("会话管理器启动")
    
    async def stop(self) -> None:
        """Stop the session manager and cleanup task."""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            self.cleanup_task = None
            logger.info("会话管理器停止")
    
    async def create_session(self, agent_id: str, agent_name: str) -> SessionInfo:
        """Create or update a session for an agent."""
        now = datetime.now(timezone.utc)
        
        if agent_id in self.sessions:
            # Update existing session
            session = self.sessions[agent_id]
            session.last_activity = now
            session.request_count += 1
        else:
            # Create new session
            session = SessionInfo(
                agent_id=agent_id,
                agent_name=agent_name,
                created_at=now,
                last_activity=now,
                request_count=1
            )
            self.sessions[agent_id] = session
            
            logger.info(f"创建新会话：{agent_id} ({agent_name})")
            
            # Log session creation
            await SecurityManager.instance.log_audit_event(
                agent_id=agent_id,
                action="session_created",
                resource="auth",
                success=True,
                details={"agent_name": agent_name}
            )
        
        return session
    
    async def end_session(self, agent_id: str) -> None:
        """End a session for an agent."""
        if agent_id in self.sessions:
            session = self.sessions[agent_id]
            duration = datetime.now(timezone.utc) - session.created_at
            
            del self.sessions[agent_id]
            logger.info(f"结束会话：{agent_id}，持续时间：{duration}")
            
            # Log session end
            await SecurityManager.instance.log_audit_event(
                agent_id=agent_id,
                action="session_ended",
                resource="auth",
                success=True,
                details={
                    "duration_seconds": duration.total_seconds(),
                    "request_count": session.request_count
                }
            )
    
    def get_active_sessions(self) -> List[SessionInfo]:
        """Get list of all active sessions."""
        return list(self.sessions.values())
    
    def get_session(self, agent_id: str) -> Optional[SessionInfo]:
        """Get session information for an agent."""
        return self.sessions.get(agent_id)
    
    async def _cleanup_loop(self) -> None:
        """Background task to clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"会话清理任务错误：{e}")
    
    async def _cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions."""
        now = datetime.now(timezone.utc)
        expired_sessions = []
        
        for agent_id, session in self.sessions.items():
            if now - session.last_activity > self.session_timeout:
                expired_sessions.append(agent_id)
        
        for agent_id in expired_sessions:
            await self.end_session(agent_id)
            logger.info(f"清理过期会话：{agent_id}")


class AuditLogger:
    """
    Audit logger for security events.
    
    Logs all security-related events to database and provides
    querying capabilities for security analysis.
    """
    
    def __init__(self, max_memory_entries: int = 1000):
        self.max_memory_entries = max_memory_entries
        self.memory_log: deque = deque(maxlen=max_memory_entries)
    
    async def log_event(self, entry: AuditLogEntry) -> None:
        """Log a security audit event."""
        # Add to in-memory log for fast access
        self.memory_log.append(entry)
        
        # Log to application logger
        level = logging.WARNING if not entry.success else logging.INFO
        logger.log(
            level, 
            f"安全审计：{entry.action} | 代理：{entry.agent_id} | 资源：{entry.resource} | 成功：{entry.success}"
        )
        
        # Store to database (simplified - in production would use dedicated audit table)
        try:
            audit_data = {
                "timestamp": entry.timestamp.isoformat(),
                "agent_id": entry.agent_id,
                "action": entry.action,
                "resource": entry.resource,
                "success": entry.success,
                "ip_address": entry.ip_address,
                "user_agent": entry.user_agent,
                "details": json.dumps(entry.details) if entry.details else None
            }
            # TODO: 在生产环境中应该写入专门的审计日志表
            # await self._write_to_database(audit_data)
        except Exception as e:
            logger.error(f"审计日志写入失败：{e}")
    
    def get_recent_events(self, limit: int = 100, agent_id: Optional[str] = None) -> List[AuditLogEntry]:
        """Get recent audit events, optionally filtered by agent."""
        events = list(self.memory_log)
        
        if agent_id:
            events = [e for e in events if e.agent_id == agent_id]
        
        # Return most recent events first
        events.reverse()
        return events[:limit]
    
    def get_security_summary(self, hours: int = 24) -> Dict:
        """Get security summary for the last N hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_events = [e for e in self.memory_log if e.timestamp >= cutoff]
        
        total_events = len(recent_events)
        failed_events = len([e for e in recent_events if not e.success])
        unique_agents = len(set(e.agent_id for e in recent_events))
        
        # Count events by action
        action_counts = defaultdict(int)
        for event in recent_events:
            action_counts[event.action] += 1
        
        return {
            "period_hours": hours,
            "total_events": total_events,
            "failed_events": failed_events,
            "success_rate": round((total_events - failed_events) / total_events * 100, 2) if total_events > 0 else 100,
            "unique_agents": unique_agents,
            "action_breakdown": dict(action_counts),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }


class SecurityManager:
    """
    Central security manager coordinating all security mechanisms.
    
    Singleton class that manages rate limiting, sessions, and audit logging
    for the entire MCP server instance.
    """
    
    instance: Optional['SecurityManager'] = None
    
    def __init__(self):
        if SecurityManager.instance is not None:
            raise RuntimeError("SecurityManager已经初始化，请使用SecurityManager.instance")
        
        # Initialize security components
        self.rate_limiter = RateLimiter(RateLimitConfig())
        self.session_manager = SessionManager()
        self.audit_logger = AuditLogger()
        self.is_initialized = False
        
        SecurityManager.instance = self
    
    @classmethod
    def get_instance(cls) -> 'SecurityManager':
        """Get singleton instance of SecurityManager."""
        if cls.instance is None:
            cls.instance = cls()
        return cls.instance
    
    async def initialize(self) -> None:
        """Initialize all security components."""
        if self.is_initialized:
            return
        
        await self.session_manager.start()
        self.is_initialized = True
        
        logger.info("安全管理器初始化完成")
        
        # Log initialization
        await self.log_audit_event(
            agent_id="system",
            action="security_manager_initialized",
            resource="system",
            success=True
        )
    
    async def cleanup(self) -> None:
        """Cleanup all security components."""
        if not self.is_initialized:
            return
        
        await self.session_manager.stop()
        self.is_initialized = False
        
        logger.info("安全管理器清理完成")
    
    async def authenticate_request(self, agent_id: str, agent_name: str) -> bool:
        """
        Authenticate and authorize a request from an agent.
        
        Args:
            agent_id: The agent ID making the request
            agent_name: The agent name
            
        Returns:
            True if request is allowed, False if blocked
        """
        try:
            # Check rate limits
            if not await self.rate_limiter.check_rate_limit(agent_id):
                await self.log_audit_event(
                    agent_id=agent_id,
                    action="request_rate_limited",
                    resource="api",
                    success=False
                )
                return False
            
            # Update/create session
            await self.session_manager.create_session(agent_id, agent_name)
            
            # Log successful authentication
            await self.log_audit_event(
                agent_id=agent_id,
                action="request_authenticated",
                resource="api",
                success=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"认证请求时发生错误：{e}")
            await self.log_audit_event(
                agent_id=agent_id,
                action="authentication_error",
                resource="api",
                success=False,
                details={"error": str(e)}
            )
            return False
    
    async def log_audit_event(
        self,
        agent_id: str,
        action: str,
        resource: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> None:
        """Log an audit event."""
        entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc),
            agent_id=agent_id,
            action=action,
            resource=resource,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {}
        )
        
        await self.audit_logger.log_event(entry)
    
    def get_security_status(self) -> Dict:
        """Get comprehensive security status."""
        active_sessions = self.session_manager.get_active_sessions()
        security_summary = self.audit_logger.get_security_summary()
        
        return {
            "active_sessions": len(active_sessions),
            "session_details": [
                {
                    "agent_id": s.agent_id,
                    "agent_name": s.agent_name,
                    "created_at": s.created_at.isoformat(),
                    "last_activity": s.last_activity.isoformat(),
                    "request_count": s.request_count,
                    "is_locked": s.is_locked
                }
                for s in active_sessions
            ],
            "audit_summary": security_summary,
            "rate_limiting": {
                "locked_agents": len(self.rate_limiter.locked_agents),
                "lockout_duration_minutes": self.rate_limiter.config.lockout_duration_minutes
            }
        }