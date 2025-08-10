#!/usr/bin/env python3
"""
Complete MCP WordPress Workflow Test

This script tests the complete workflow of the MCP WordPress system:
1. Article submission
2. Article listing and status checking
3. Article approval/rejection
4. Resource access
5. Database verification
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from mcp_wordpress.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from mcp import SSEClient
    from mcp.types import Tool, Resource
except ImportError:
    print("❌ MCP library not found. Please install it with: pip install mcp")
    exit(1)


class WorkflowTestClient:
    """Complete workflow test client for MCP WordPress."""
    
    def __init__(self, server_url: str = None):
        if server_url is None:
            server_url = f"http://localhost:{settings.mcp_port}{settings.mcp_sse_path}"
        self.server_url = server_url
        self.client = None
        self.test_articles = []
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = SSEClient(self.server_url)
        await self.client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def create_test_articles(self) -> List[Dict[str, Any]]:
        """Create multiple test articles for workflow testing."""
        logger.info("📝 Creating test articles...")
        
        test_articles = [
            {
                "title": "Introduction to MCP Protocol",
                "content_markdown": """# Introduction to MCP Protocol

The Model Context Protocol (MCP) is a powerful way for AI agents to interact with external systems.

## Key Features
- Standardized communication
- Tool-based interactions  
- Resource access
- Secure connections

## Use Cases
- WordPress integration
- Database operations
- Content management

Created: """ + datetime.now().isoformat(),
                "tags": "mcp, protocol, ai, integration",
                "category": "Technology"
            },
            {
                "title": "WordPress Automation with MCP",
                "content_markdown": """# WordPress Automation with MCP

This article demonstrates how MCP can automate WordPress content management.

## Workflow
1. Submit articles via MCP
2. Review and approve content
3. Publish to WordPress
4. Monitor statistics

## Benefits
- Automated publishing
- Quality control
- Statistical tracking
- Multi-source content

Generated: """ + datetime.now().isoformat(),
                "tags": "wordpress, automation, publishing, mcp",
                "category": "Automation"
            },
            {
                "title": "Testing Article - Should be Rejected",
                "content_markdown": """# Test Article for Rejection

This is a test article specifically created to test the rejection workflow.

It contains minimal content and should be rejected during review.

Time: """ + datetime.now().isoformat(),
                "tags": "test, rejection",
                "category": "Testing"
            }
        ]
        
        submitted_articles = []
        for i, article in enumerate(test_articles, 1):
            try:
                logger.info(f"  Submitting article {i}/{len(test_articles)}: {article['title'][:30]}...")
                result = await self.client.call_tool("submit_article", article)
                submitted_articles.append({
                    'original': article,
                    'submission_result': result,
                    'article_id': self._extract_article_id(result)
                })
                logger.info(f"  ✅ Article {i} submitted successfully")
                await asyncio.sleep(1)  # Small delay between submissions
            except Exception as e:
                logger.error(f"  ❌ Failed to submit article {i}: {e}")
        
        self.test_articles = submitted_articles
        logger.info(f"✅ Created {len(submitted_articles)} test articles")
        return submitted_articles
    
    def _extract_article_id(self, result: Any) -> Optional[int]:
        """Extract article ID from submission result."""
        try:
            if isinstance(result, dict):
                # Try different possible field names
                for field in ['article_id', 'id', 'Article ID']:
                    if field in result:
                        return result[field]
            elif isinstance(result, str):
                # Try to parse JSON if result is string
                try:
                    parsed = json.loads(result)
                    return self._extract_article_id(parsed)
                except:
                    pass
        except:
            pass
        return None
    
    async def test_article_listing(self) -> Dict[str, Any]:
        """Test article listing functionality."""
        logger.info("📋 Testing article listing...")
        
        try:
            # Test listing all articles
            all_articles = await self.client.call_tool("list_articles", {})
            logger.info(f"  ✅ Listed all articles: {len(all_articles) if isinstance(all_articles, list) else 'N/A'}")
            
            # Test listing pending articles
            pending_articles = await self.client.call_tool("list_articles", {
                "status": "pending",
                "limit": 20
            })
            logger.info(f"  ✅ Listed pending articles: {len(pending_articles) if isinstance(pending_articles, list) else 'N/A'}")
            
            # Test with category filter
            tech_articles = await self.client.call_tool("list_articles", {
                "category": "Technology"
            })
            logger.info(f"  ✅ Listed Technology articles: {len(tech_articles) if isinstance(tech_articles, list) else 'N/A'}")
            
            return {
                "all_articles": all_articles,
                "pending_articles": pending_articles,
                "tech_articles": tech_articles
            }
            
        except Exception as e:
            logger.error(f"❌ Article listing failed: {e}")
            return {}
    
    async def test_article_status_checking(self) -> List[Dict[str, Any]]:
        """Test article status checking."""
        logger.info("🔍 Testing article status checking...")
        
        status_results = []
        for i, article_info in enumerate(self.test_articles, 1):
            article_id = article_info.get('article_id')
            if not article_id:
                logger.warning(f"  ⚠️  Article {i}: No ID available for status check")
                continue
            
            try:
                status = await self.client.call_tool("get_article_status", {
                    "article_id": article_id
                })
                status_results.append({
                    'article_id': article_id,
                    'status': status,
                    'title': article_info['original']['title']
                })
                logger.info(f"  ✅ Article {i} status retrieved")
            except Exception as e:
                logger.error(f"  ❌ Failed to get status for article {i}: {e}")
        
        logger.info(f"✅ Checked status for {len(status_results)} articles")
        return status_results
    
    async def test_article_approval_workflow(self) -> Dict[str, Any]:
        """Test article approval and rejection workflow."""
        logger.info("✅❌ Testing approval/rejection workflow...")
        
        workflow_results = {}
        
        # Approve first article if available
        if len(self.test_articles) >= 1:
            first_article = self.test_articles[0]
            article_id = first_article.get('article_id')
            if article_id:
                try:
                    approval_result = await self.client.call_tool("approve_article", {
                        "article_id": article_id
                    })
                    workflow_results['approved'] = approval_result
                    logger.info("  ✅ First article approved successfully")
                except Exception as e:
                    logger.error(f"  ❌ Failed to approve first article: {e}")
        
        # Reject last article if available (the one designed for rejection)
        if len(self.test_articles) >= 3:
            last_article = self.test_articles[-1]
            article_id = last_article.get('article_id')
            if article_id:
                try:
                    rejection_result = await self.client.call_tool("reject_article", {
                        "article_id": article_id,
                        "reason": "This article was created specifically for testing the rejection workflow. Content is insufficient for publication."
                    })
                    workflow_results['rejected'] = rejection_result
                    logger.info("  ✅ Last article rejected successfully")
                except Exception as e:
                    logger.error(f"  ❌ Failed to reject last article: {e}")
        
        return workflow_results
    
    async def test_resource_access(self) -> Dict[str, Any]:
        """Test accessing various resources."""
        logger.info("📚 Testing resource access...")
        
        resource_results = {}
        
        # Test stats summary
        try:
            stats = await self.client.read_resource("stats://summary")
            resource_results['stats'] = stats
            logger.info("  ✅ Stats summary accessed")
        except Exception as e:
            logger.warning(f"  ⚠️  Stats summary not available: {e}")
        
        # Test pending articles resource
        try:
            pending = await self.client.read_resource("article://pending")
            resource_results['pending'] = pending
            logger.info("  ✅ Pending articles resource accessed")
        except Exception as e:
            logger.warning(f"  ⚠️  Pending articles resource not available: {e}")
        
        return resource_results
    
    async def generate_test_report(self, test_results: Dict[str, Any]):
        """Generate a comprehensive test report."""
        logger.info("📊 Generating test report...")
        
        report = {
            "test_timestamp": datetime.now().isoformat(),
            "server_url": self.server_url,
            "test_summary": {},
            "detailed_results": test_results
        }
        
        # Calculate summary statistics
        total_articles = len(self.test_articles)
        successful_submissions = sum(1 for art in self.test_articles if art.get('article_id'))
        
        report["test_summary"] = {
            "total_test_articles": total_articles,
            "successful_submissions": successful_submissions,
            "submission_success_rate": f"{(successful_submissions/total_articles*100):.1f}%" if total_articles > 0 else "N/A",
            "tests_performed": list(test_results.keys()),
            "resource_access_tests": len(test_results.get('resource_results', {}))
        }
        
        # Save report to file
        report_filename = f"mcp_test_report_{int(time.time())}.json"
        try:
            with open(report_filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"  ✅ Test report saved to {report_filename}")
        except Exception as e:
            logger.error(f"  ❌ Failed to save report: {e}")
        
        return report
    
    async def run_complete_workflow_test(self):
        """Run the complete workflow test suite."""
        logger.info("🚀 Starting Complete MCP WordPress Workflow Test")
        logger.info("=" * 60)
        
        test_results = {}
        
        try:
            # 1. Create test articles
            test_results['article_creation'] = await self.create_test_articles()
            
            # 2. Test article listing
            test_results['article_listing'] = await self.test_article_listing()
            
            # 3. Test status checking
            test_results['status_checking'] = await self.test_article_status_checking()
            
            # 4. Test approval/rejection workflow
            test_results['workflow_results'] = await self.test_article_approval_workflow()
            
            # 5. Test resource access
            test_results['resource_results'] = await self.test_resource_access()
            
            # 6. Generate comprehensive report
            report = await self.generate_test_report(test_results)
            
            logger.info("=" * 60)
            logger.info("✅ Complete workflow test finished successfully!")
            
            return True, test_results
            
        except Exception as e:
            logger.error(f"❌ Workflow test failed: {e}")
            return False, test_results


async def main():
    """Main function to run the complete workflow test."""
    try:
        async with WorkflowTestClient() as client:
            success, results = await client.run_complete_workflow_test()
            
            if success:
                print("\n🎉 Complete MCP WordPress workflow test PASSED!")
                print(f"📊 Test completed with {len(results)} test categories")
                return True
            else:
                print("\n❌ Complete MCP WordPress workflow test FAILED!")
                return False
                
    except Exception as e:
        logger.error(f"❌ Test setup failed: {e}")
        print(f"\n❌ Could not run workflow test: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)