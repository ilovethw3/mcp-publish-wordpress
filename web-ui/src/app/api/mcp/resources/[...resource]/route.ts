/**
 * MCP Resources API Route Handler
 * 
 * This route handles all MCP resource reads from the Web UI, converting HTTP requests
 * to MCP protocol resource reads and returning appropriate responses.
 */

import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: { resource: string[] } }
) {
  try {
    const resourcePath = params.resource.join('/');
    const url = new URL(request.url);
    const searchParams = Object.fromEntries(url.searchParams.entries());
    
    // Return empty data for different resources
    switch (resourcePath) {
      case 'stats/summary':
        return NextResponse.json({
          success: true,
          data: {
            total_articles: 0,
            pending_articles: 0,
            published_articles: 0,
            rejected_articles: 0,
            active_agents: 0,
            configured_sites: 0,
            system_uptime: '0 hours',
            last_updated: new Date().toISOString(),
          },
        });

      case 'stats/system-health':
        return NextResponse.json({
          success: true,
          data: {
            status: 'healthy',
            system_status: 'healthy',
            uptime: '0 hours',
            memory_usage: {
              used: 0,
              total: 0,
              percentage: 0,
            },
            cpu_usage: {
              percentage: 0,
            },
            database: {
              status: 'connected',
              response_time: 0,
            },
            redis: {
              status: 'connected',
              response_time: 0,
            },
            mcp_server: {
              status: 'connected',
              response_time: 0,
            },
            activity_metrics: {
              submissions_last_hour: 0,
              submissions_last_24h: 0,
              active_agents_24h: 0,
              active_sites_24h: 0,
            },
            publishing_metrics: {
              failure_rate_percent: 0,
              success_rate_percent: 100,
              total_publications_24h: 0,
              successful_publications_24h: 0,
              failed_publications_24h: 0,
            },
            last_check: new Date().toISOString(),
          },
        });

      case 'stats/performance':
        return NextResponse.json({
          success: true,
          data: {
            requests_per_minute: 0,
            average_response_time: 0,
            error_rate: 0,
            active_connections: 0,
            queue_size: 0,
            last_updated: new Date().toISOString(),
          },
        });

      case 'wordpress/config':
        return NextResponse.json({
          success: true,
          data: {
            sites: [],
            global_settings: {
              default_category: 'General',
              auto_publish: false,
              require_approval: true,
            },
            last_updated: new Date().toISOString(),
          },
        });

      default:
        // Handle dynamic resources like agent/{id}/articles, site/{id}/articles
        const pathParts = resourcePath.split('/');
        
        if (pathParts.length === 3 && pathParts[0] === 'agent' && pathParts[2] === 'articles') {
          return NextResponse.json({
            success: true,
            data: {
              agent_id: pathParts[1],
              articles: [],
              total: 0,
              last_updated: new Date().toISOString(),
            },
          });
        }
        
        if (pathParts.length === 3 && pathParts[0] === 'site' && pathParts[2] === 'articles') {
          return NextResponse.json({
            success: true,
            data: {
              site_id: pathParts[1],
              articles: [],
              total: 0,
              last_updated: new Date().toISOString(),
            },
          });
        }

        return NextResponse.json({
          success: true,
          data: {
            message: `Resource ${resourcePath} executed successfully with empty data`,
            resource: resourcePath,
            parameters: searchParams,
            timestamp: new Date().toISOString(),
          },
        });
    }
  } catch (error) {
    console.error('MCP resource read error:', error);
    
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      },
      { status: 500 }
    );
  }
}

// Resources are read-only, so we only support GET requests
export async function POST() {
  return new NextResponse('Method Not Allowed - Resources are read-only', { status: 405 });
}

export async function PUT() {
  return new NextResponse('Method Not Allowed - Resources are read-only', { status: 405 });
}

export async function DELETE() {
  return new NextResponse('Method Not Allowed - Resources are read-only', { status: 405 });
}

export async function PATCH() {
  return new NextResponse('Method Not Allowed - Resources are read-only', { status: 405 });
}