"""MCP Tools for security management and monitoring."""

import json
from datetime import datetime, timezone
from typing import Optional
from fastmcp import FastMCP

from mcp_wordpress.core.security import SecurityManager
from mcp_wordpress.core.errors import create_mcp_success, MCPError, MCPErrorCodes


def register_security_tools(mcp: FastMCP):
    """Register all security management tools with the MCP server."""
    
    @mcp.tool(
        description="Get comprehensive security status and metrics for the system"
    )
    async def get_security_status() -> str:
        """Get comprehensive security status including active sessions, rate limits, and audit logs.
        
        Returns:
            JSON string with detailed security status information
        """
        try:
            security_manager = SecurityManager.get_instance()
            
            if not security_manager.is_initialized:
                return create_mcp_success({
                    "status": "not_initialized",
                    "message": "安全管理器尚未初始化",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
            status = security_manager.get_security_status()
            
            return create_mcp_success({
                "security_status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": "安全状态获取成功"
            })
            
        except Exception as e:
            error = MCPError(MCPErrorCodes.INTERNAL_ERROR, f"获取安全状态失败: {str(e)}")
            return error.to_json()
    
    @mcp.tool(
        description="Get rate limiting status for a specific agent or all agents"
    )
    async def get_rate_limit_status(agent_id: Optional[str] = None) -> str:
        """Get rate limiting status for agents.
        
        Args:
            agent_id: Specific agent ID to check (optional, if not provided shows all)
            
        Returns:
            JSON string with rate limit status information
        """
        try:
            security_manager = SecurityManager.get_instance()
            
            if not security_manager.is_initialized:
                return create_mcp_success({
                    "status": "not_initialized",
                    "message": "安全管理器尚未初始化"
                })
            
            if agent_id:
                # Get status for specific agent
                agent_status = security_manager.rate_limiter.get_agent_status(agent_id)
                return create_mcp_success({
                    "agent_status": agent_status,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            else:
                # Get status for all agents with active sessions
                active_sessions = security_manager.session_manager.get_active_sessions()
                agent_statuses = []
                
                for session in active_sessions:
                    status = security_manager.rate_limiter.get_agent_status(session.agent_id)
                    agent_statuses.append(status)
                
                return create_mcp_success({
                    "all_agents": agent_statuses,
                    "total_agents": len(agent_statuses),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
        except Exception as e:
            error = MCPError(MCPErrorCodes.INTERNAL_ERROR, f"获取速率限制状态失败: {str(e)}")
            return error.to_json()
    
    @mcp.tool(
        description="Get recent security audit events"
    )
    async def get_audit_events(
        limit: int = 50,
        agent_id: Optional[str] = None,
        hours: int = 24
    ) -> str:
        """Get recent security audit events.
        
        Args:
            limit: Maximum number of events to return (max 200)
            agent_id: Filter events by specific agent ID (optional)
            hours: Time range in hours for security summary (default 24)
            
        Returns:
            JSON string with audit events and security summary
        """
        try:
            # Validate limit
            if limit > 200:
                limit = 200
            
            security_manager = SecurityManager.get_instance()
            
            if not security_manager.is_initialized:
                return create_mcp_success({
                    "events": [],
                    "summary": {},
                    "message": "安全管理器尚未初始化"
                })
            
            # Get recent events
            events = security_manager.audit_logger.get_recent_events(
                limit=limit,
                agent_id=agent_id
            )
            
            # Get security summary
            summary = security_manager.audit_logger.get_security_summary(hours=hours)
            
            # Convert events to serializable format
            events_data = []
            for event in events:
                events_data.append({
                    "timestamp": event.timestamp.isoformat(),
                    "agent_id": event.agent_id,
                    "action": event.action,
                    "resource": event.resource,
                    "success": event.success,
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                    "details": event.details
                })
            
            return create_mcp_success({
                "events": events_data,
                "summary": summary,
                "filter": {
                    "limit": limit,
                    "agent_id": agent_id,
                    "hours": hours
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            error = MCPError(MCPErrorCodes.INTERNAL_ERROR, f"获取审计事件失败: {str(e)}")
            return error.to_json()
    
    @mcp.tool(
        description="Get active sessions information"
    )
    async def get_active_sessions() -> str:
        """Get information about all currently active agent sessions.
        
        Returns:
            JSON string with active session details
        """
        try:
            security_manager = SecurityManager.get_instance()
            
            if not security_manager.is_initialized:
                return create_mcp_success({
                    "sessions": [],
                    "message": "安全管理器尚未初始化"
                })
            
            active_sessions = security_manager.session_manager.get_active_sessions()
            
            sessions_data = []
            for session in active_sessions:
                session_duration = datetime.now(timezone.utc) - session.created_at
                inactive_duration = datetime.now(timezone.utc) - session.last_activity
                
                sessions_data.append({
                    "agent_id": session.agent_id,
                    "agent_name": session.agent_name,
                    "created_at": session.created_at.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "request_count": session.request_count,
                    "failed_attempts": session.failed_attempts,
                    "is_locked": session.is_locked,
                    "lockout_until": session.lockout_until.isoformat() if session.lockout_until else None,
                    "session_duration_minutes": round(session_duration.total_seconds() / 60, 2),
                    "inactive_minutes": round(inactive_duration.total_seconds() / 60, 2)
                })
            
            return create_mcp_success({
                "active_sessions": sessions_data,
                "total_sessions": len(sessions_data),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            error = MCPError(MCPErrorCodes.INTERNAL_ERROR, f"获取活跃会话失败: {str(e)}")
            return error.to_json()
    
    @mcp.tool(
        description="End a specific agent session (admin function)"
    )
    async def end_agent_session(agent_id: str) -> str:
        """End a specific agent session.
        
        Args:
            agent_id: The agent ID whose session should be ended
            
        Returns:
            JSON string with operation result
        """
        try:
            security_manager = SecurityManager.get_instance()
            
            if not security_manager.is_initialized:
                return create_mcp_success({
                    "success": False,
                    "message": "安全管理器尚未初始化"
                })
            
            # Check if session exists
            session = security_manager.session_manager.get_session(agent_id)
            if not session:
                return create_mcp_success({
                    "success": False,
                    "message": f"未找到代理 {agent_id} 的活跃会话"
                })
            
            # End the session
            await security_manager.session_manager.end_session(agent_id)
            
            # Log admin action
            await security_manager.log_audit_event(
                agent_id="system",
                action="admin_end_session",
                resource="session",
                success=True,
                details={"target_agent": agent_id}
            )
            
            return create_mcp_success({
                "success": True,
                "message": f"代理 {agent_id} 的会话已成功终止",
                "ended_session": {
                    "agent_id": session.agent_id,
                    "agent_name": session.agent_name,
                    "session_duration_minutes": round(
                        (datetime.now(timezone.utc) - session.created_at).total_seconds() / 60, 2
                    )
                }
            })
            
        except Exception as e:
            error = MCPError(MCPErrorCodes.INTERNAL_ERROR, f"终止代理会话失败: {str(e)}")
            return error.to_json()
    
    @mcp.tool(
        description="Get security configuration and system health metrics"
    )
    async def get_security_config() -> str:
        """Get current security configuration and system health metrics.
        
        Returns:
            JSON string with security configuration and health metrics
        """
        try:
            security_manager = SecurityManager.get_instance()
            
            if not security_manager.is_initialized:
                return create_mcp_success({
                    "initialized": False,
                    "message": "安全管理器尚未初始化"
                })
            
            # Get rate limiter configuration
            rate_config = security_manager.rate_limiter.config
            
            # Get session manager configuration
            session_timeout_minutes = security_manager.session_manager.session_timeout.total_seconds() / 60
            
            # Get audit logger configuration
            audit_config = {
                "max_memory_entries": security_manager.audit_logger.max_memory_entries,
                "current_memory_entries": len(security_manager.audit_logger.memory_log)
            }
            
            return create_mcp_success({
                "initialized": True,
                "configuration": {
                    "rate_limiting": {
                        "requests_per_minute": rate_config.requests_per_minute,
                        "requests_per_hour": rate_config.requests_per_hour,
                        "burst_allowance": rate_config.burst_allowance,
                        "lockout_duration_minutes": rate_config.lockout_duration_minutes
                    },
                    "session_management": {
                        "session_timeout_minutes": session_timeout_minutes,
                        "cleanup_interval_minutes": 5
                    },
                    "audit_logging": audit_config
                },
                "system_health": {
                    "active_sessions": len(security_manager.session_manager.get_active_sessions()),
                    "locked_agents": len(security_manager.rate_limiter.locked_agents),
                    "audit_events_in_memory": len(security_manager.audit_logger.memory_log)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            error = MCPError(MCPErrorCodes.INTERNAL_ERROR, f"获取安全配置失败: {str(e)}")
            return error.to_json()