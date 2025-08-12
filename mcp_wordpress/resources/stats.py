"""MCP Resources for system statistics and WordPress configuration."""

import json
from datetime import datetime, timezone, timedelta
from sqlmodel import select, func
from fastmcp import FastMCP

from mcp_wordpress.core.database import get_session
from mcp_wordpress.core.wordpress import WordPressClient
from mcp_wordpress.core.config import settings
from mcp_wordpress.models.article import Article, ArticleStatus


def register_stats_resources(mcp: FastMCP):
    """Register all statistics and configuration resources with the MCP server."""
    
    @mcp.resource("wordpress://config")
    async def get_wordpress_config() -> str:
        """Get WordPress site configuration information."""
        wp_client = WordPressClient()
        
        try:
            # Test connection
            is_connected = await wp_client.test_connection()
            
            return json.dumps({
                "api_base": "/".join(settings.wordpress_api_url.split("/")[:-2]),  # 只暴露主域名
                "connection_status": "connected" if is_connected else "disconnected",
                "last_checked": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            return json.dumps({
                "api_base": "/".join(settings.wordpress_api_url.split("/")[:-2]),  # 只暴露主域名
                "connection_status": "error",
                "error_message": "Connection failed",  # 不暴露具体错误信息
                "last_checked": datetime.now(timezone.utc).isoformat()
            })
    
    @mcp.resource("stats://summary")
    async def get_stats_summary() -> str:
        """Get system statistics summary."""
        async with get_session() as session:
            # Count articles by status
            stats = {}
            for status in ArticleStatus:
                result = await session.execute(
                    select(func.count(Article.id)).where(Article.status == status)
                )
                stats[status.value] = result.scalar() or 0
            
            # Get total count
            total_result = await session.execute(select(func.count(Article.id)))
            total_count = total_result.scalar() or 0
            
            # Get recent activity (last 24 hours)
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            recent_result = await session.execute(
                select(func.count(Article.id)).where(Article.created_at >= yesterday)
            )
            recent_count = recent_result.scalar() or 0
            
            return json.dumps({
                "total_articles": total_count,
                "articles_by_status": stats,
                "recent_submissions_24h": recent_count,
                "last_updated": datetime.now(timezone.utc).isoformat()
            })
    
    @mcp.resource("stats://performance")
    async def get_performance_metrics() -> str:
        """Get system performance metrics."""
        async with get_session() as session:
            # Calculate average processing time for published articles
            published_articles = await session.execute(
                select(Article).where(Article.status == ArticleStatus.PUBLISHED)
            )
            articles = published_articles.scalars().all()
            
            if articles:
                processing_times = []
                for article in articles:
                    if article.created_at and article.updated_at:
                        processing_time = (article.updated_at - article.created_at).total_seconds()
                        processing_times.append(processing_time)
                
                avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            else:
                avg_processing_time = 0
            
            # Calculate success rate
            total_attempted = await session.execute(
                select(func.count(Article.id)).where(
                    Article.status.in_([
                        ArticleStatus.PUBLISHED, 
                        ArticleStatus.PUBLISH_FAILED
                    ])
                )
            )
            total_attempted_count = total_attempted.scalar() or 0
            
            published_count = await session.execute(
                select(func.count(Article.id)).where(Article.status == ArticleStatus.PUBLISHED)
            )
            published_count_result = published_count.scalar() or 0
            
            success_rate = (published_count_result / total_attempted_count * 100) if total_attempted_count > 0 else 0
            
            return json.dumps({
                "avg_processing_time_seconds": round(avg_processing_time, 2),
                "success_rate_percent": round(success_rate, 2),
                "total_attempted_publications": total_attempted_count,
                "successful_publications": published_count_result,
                "last_calculated": datetime.now(timezone.utc).isoformat()
            })
    # ========== v2.1新增多代理和多站点统计Resources ==========
    
    @mcp.resource("stats://agents")
    async def get_agent_stats() -> str:
        """Get comprehensive agent statistics across all agents."""
        async with get_session() as session:
            # 统计所有代理的基本信息
            agent_stats_query = select(
                Article.submitting_agent_id,
                Article.submitting_agent_name,
                func.count(Article.id).label("total_submitted"),
                func.count().filter(Article.status == ArticleStatus.PUBLISHED).label("published"),
                func.count().filter(Article.status == ArticleStatus.REJECTED).label("rejected"),
                func.count().filter(Article.status == ArticleStatus.PENDING_REVIEW).label("pending"),
                func.min(Article.created_at).label("first_submission"),
                func.max(Article.created_at).label("last_submission")
            ).where(
                Article.submitting_agent_id.isnot(None)
            ).group_by(
                Article.submitting_agent_id,
                Article.submitting_agent_name
            )
            
            result = await session.execute(agent_stats_query)
            agent_stats = []
            total_agents = 0
            total_submissions = 0
            total_published = 0
            
            for row in result.all():
                agent_id, agent_name, submitted, published, rejected, pending, first_sub, last_sub = row
                success_rate = (published / submitted * 100) if submitted > 0 else 0
                total_agents += 1
                total_submissions += submitted
                total_published += published
                
                agent_stats.append({
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "statistics": {
                        "total_submitted": submitted,
                        "published": published,
                        "rejected": rejected,
                        "pending_review": pending,
                        "success_rate": round(success_rate, 2),
                        "first_submission": first_sub.isoformat() if first_sub else None,
                        "last_submission": last_sub.isoformat() if last_sub else None
                    }
                })
            
            # 计算系统整体成功率
            system_success_rate = (total_published / total_submissions * 100) if total_submissions > 0 else 0
            
            return json.dumps({
                "total_agents": total_agents,
                "system_statistics": {
                    "total_submissions": total_submissions,
                    "total_published": total_published,
                    "system_success_rate": round(system_success_rate, 2)
                },
                "agent_details": agent_stats,
                "last_updated": datetime.now(timezone.utc).isoformat()
            })
    
    @mcp.resource("stats://sites")
    async def get_site_stats() -> str:
        """Get comprehensive site statistics across all WordPress sites."""
        async with get_session() as session:
            # 统计所有站点的发布信息
            site_stats_query = select(
                Article.target_site_id,
                Article.target_site_name,
                func.count(Article.id).label("total_articles"),
                func.count().filter(Article.status == ArticleStatus.PUBLISHED).label("published"),
                func.count().filter(Article.status == ArticleStatus.PUBLISH_FAILED).label("failed"),
                func.max(Article.updated_at).filter(Article.status == ArticleStatus.PUBLISHED).label("last_success"),
                func.max(Article.updated_at).filter(Article.status == ArticleStatus.PUBLISH_FAILED).label("last_failure")
            ).where(
                Article.target_site_id.isnot(None)
            ).group_by(
                Article.target_site_id,
                Article.target_site_name
            )
            
            result = await session.execute(site_stats_query)
            site_stats = []
            total_sites = 0
            total_publications = 0
            total_failures = 0
            healthy_sites = 0
            
            for row in result.all():
                site_id, site_name, total, published, failed, last_success, last_failure = row
                total_attempts = published + failed
                success_rate = (published / total_attempts * 100) if total_attempts > 0 else 0
                
                # 确定站点健康状态
                if success_rate >= 90:
                    health_status = "healthy"
                    healthy_sites += 1
                elif success_rate >= 70:
                    health_status = "warning"
                else:
                    health_status = "error"
                
                total_sites += 1
                total_publications += published
                total_failures += failed
                
                site_stats.append({
                    "site_id": site_id,
                    "site_name": site_name,
                    "health_status": health_status,
                    "statistics": {
                        "total_articles": total,
                        "published": published,
                        "failed": failed,
                        "success_rate": round(success_rate, 2),
                        "last_successful_publish": last_success.isoformat() if last_success else None,
                        "last_failed_publish": last_failure.isoformat() if last_failure else None
                    }
                })
            
            # 计算系统整体发布成功率
            system_publish_rate = (total_publications / (total_publications + total_failures) * 100) if (total_publications + total_failures) > 0 else 0
            
            return json.dumps({
                "total_sites": total_sites,
                "healthy_sites": healthy_sites,
                "system_statistics": {
                    "total_publications": total_publications,
                    "total_failures": total_failures,
                    "system_publish_success_rate": round(system_publish_rate, 2)
                },
                "site_details": site_stats,
                "last_updated": datetime.now(timezone.utc).isoformat()
            })
    
    @mcp.resource("stats://system-health")
    async def get_system_health() -> str:
        """Get comprehensive system health metrics for v2.1 multi-agent multi-site environment."""
        async with get_session() as session:
            # 系统整体健康指标
            now = datetime.now(timezone.utc)
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)
            
            # 最近1小时活动
            recent_submissions = await session.execute(
                select(func.count(Article.id)).where(Article.created_at >= hour_ago)
            )
            submissions_1h = recent_submissions.scalar() or 0
            
            # 最近24小时活动
            daily_submissions = await session.execute(
                select(func.count(Article.id)).where(Article.created_at >= day_ago)
            )
            submissions_24h = daily_submissions.scalar() or 0
            
            # 活跃代理数量（最近24小时有提交的）
            active_agents = await session.execute(
                select(func.count(func.distinct(Article.submitting_agent_id))).where(
                    Article.created_at >= day_ago,
                    Article.submitting_agent_id.isnot(None)
                )
            )
            active_agents_24h = active_agents.scalar() or 0
            
            # 使用中的站点数量（最近24小时有发布的）
            active_sites = await session.execute(
                select(func.count(func.distinct(Article.target_site_id))).where(
                    Article.updated_at >= day_ago,
                    Article.target_site_id.isnot(None),
                    Article.status == ArticleStatus.PUBLISHED
                )
            )
            active_sites_24h = active_sites.scalar() or 0
            
            # 发布失败率（最近24小时）
            failed_publishes = await session.execute(
                select(func.count(Article.id)).where(
                    Article.updated_at >= day_ago,
                    Article.status == ArticleStatus.PUBLISH_FAILED
                )
            )
            failed_24h = failed_publishes.scalar() or 0
            
            successful_publishes = await session.execute(
                select(func.count(Article.id)).where(
                    Article.updated_at >= day_ago,
                    Article.status == ArticleStatus.PUBLISHED
                )
            )
            successful_24h = successful_publishes.scalar() or 0
            
            total_publish_attempts = failed_24h + successful_24h
            failure_rate = (failed_24h / total_publish_attempts * 100) if total_publish_attempts > 0 else 0
            
            # 确定系统健康状态
            if failure_rate <= 5 and submissions_1h > 0:
                system_status = "healthy"
            elif failure_rate <= 15:
                system_status = "warning"
            else:
                system_status = "error"
            
            return json.dumps({
                "system_status": system_status,
                "activity_metrics": {
                    "submissions_last_hour": submissions_1h,
                    "submissions_last_24h": submissions_24h,
                    "active_agents_24h": active_agents_24h,
                    "active_sites_24h": active_sites_24h
                },
                "publishing_metrics": {
                    "successful_publishes_24h": successful_24h,
                    "failed_publishes_24h": failed_24h,
                    "failure_rate_percent": round(failure_rate, 2)
                },
                "last_updated": now.isoformat()
            })
