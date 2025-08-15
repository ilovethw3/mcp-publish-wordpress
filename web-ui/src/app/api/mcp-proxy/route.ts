/**
 * MCP HTTP Proxy for Web UI
 * 
 * This route acts as a proxy between the Web UI and the MCP server,
 * handling the MCP protocol communication and providing a simple HTTP API.
 */

import { NextRequest, NextResponse } from 'next/server';
import { getMCPClient } from '@/lib/mcp-client';

// MCP server configuration
const MCP_SERVER_URL = process.env.NEXT_PUBLIC_MCP_SERVER_URL || 'http://localhost:8000';
const MCP_SSE_PATH = process.env.NEXT_PUBLIC_MCP_SSE_PATH || '/sse';

/**
 * Test Web UI Agent authentication with MCP server using real MCP client
 */
async function testMCPAuth(): Promise<{
  valid: boolean;
  agent_id?: string;
  error?: string;
  details?: any;
}> {
  try {
    console.log('[WEB-UI] 🔐 测试 Web UI Agent MCP 认证...');
    
    const apiKey = process.env.WEB_UI_AGENT_API_KEY;
    if (!apiKey) {
      console.error('[WEB-UI] ❌ 环境变量中未配置 WEB_UI_AGENT_API_KEY');
      return {
        valid: false,
        error: 'API密钥未配置',
        details: { env_key_status: '未配置' }
      };
    }
    
    console.log(`[WEB-UI] 🔍 使用API密钥: ${apiKey.substring(0, 10)}...`);
    
    // 使用 MCP 客户端调用 list_agents 工具测试认证
    const mcpClient = getMCPClient({ apiKey });
    const result = await mcpClient.listAgents(false);
    
    if (!result.success) {
      console.error(`[WEB-UI] ❌ MCP认证失败: ${result.error}`);
      return {
        valid: false,
        error: `MCP认证失败: ${result.error}`,
        details: { 
          api_key_prefix: apiKey.substring(0, 10) + '...',
          mcp_error: result.error
        }
      };
    }
    
    console.log('[WEB-UI] ✅ Web UI Agent MCP认证成功');
    console.log(`[WEB-UI] 🎯 认证代理: web-ui-internal`);
    
    return {
      valid: true,
      agent_id: 'web-ui-internal',
      details: {
        api_key_prefix: apiKey.substring(0, 10) + '...',
        tools_response: result.data
      }
    };
    
  } catch (error) {
    console.error('[WEB-UI] ❌ MCP认证测试过程发生错误:', error);
    
    return {
      valid: false,
      error: error instanceof Error ? error.message : 'Unknown auth error',
      details: { error: 'exception' }
    };
  }
}

/**
 * Test MCP server connectivity and Web UI Agent authentication
 */
async function testMCPConnection(): Promise<{
  isConnected: boolean;
  message: string;
  details?: any;
  auth_status?: any;
}> {
  const sseUrl = `${MCP_SERVER_URL}${MCP_SSE_PATH}`;
  
  try {
    // Test health endpoint directly (no authentication required)
    const healthUrl = `${MCP_SERVER_URL}/health`;
    const healthResponse = await fetch(healthUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      signal: AbortSignal.timeout(5000), // 5 second timeout
    });

    if (!healthResponse.ok) {
      return {
        isConnected: false,
        message: `MCP health endpoint error: ${healthResponse.status} ${healthResponse.statusText}`,
        details: { healthStatus: healthResponse.status, url: healthUrl }
      };
    }

    // Parse health response to check server status
    let healthData;
    try {
      healthData = await healthResponse.json();
    } catch (e) {
      return {
        isConnected: false,
        message: 'Invalid health endpoint response - not JSON',
        details: { url: healthUrl }
      };
    }

    // Check if server reports healthy status
    if (healthData.status !== 'healthy') {
      return {
        isConnected: false,
        message: `MCP server reports unhealthy status: ${healthData.status}`,
        details: { healthData, url: healthUrl }
      };
    }

    // If health check passed, also test Web UI Agent authentication
    const authResult = await testMCPAuth();
    
    return {
      isConnected: true,
      message: authResult.valid 
        ? 'MCP server健康且Web UI认证成功' 
        : `MCP server健康但Web UI认证失败: ${authResult.error}`,
      details: { 
        healthStatus: healthResponse.status,
        healthData,
        baseUrl: MCP_SERVER_URL,
        healthUrl,
        sseUrl
      },
      auth_status: authResult
    };

  } catch (error) {
    // Handle different types of connection errors
    if (error instanceof Error) {
      if (error.name === 'TimeoutError') {
        return {
          isConnected: false,
          message: 'MCP server connection timeout (5s)',
          details: { error: 'timeout', url: MCP_SERVER_URL }
        };
      }
      
      if (error.message.includes('ECONNREFUSED')) {
        return {
          isConnected: false,
          message: 'MCP server connection refused - server may be down',
          details: { error: 'connection_refused', url: MCP_SERVER_URL }
        };
      }
      
      if (error.message.includes('ENOTFOUND')) {
        return {
          isConnected: false,
          message: 'MCP server host not found',
          details: { error: 'host_not_found', url: MCP_SERVER_URL }
        };
      }
    }

    return {
      isConnected: false,
      message: `MCP server connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      details: { 
        error: error instanceof Error ? error.message : 'Unknown error',
        url: MCP_SERVER_URL 
      }
    };
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { method, params } = body;

    if (!method) {
      return NextResponse.json(
        { success: false, error: 'Method is required' },
        { status: 400 }
      );
    }

    // Implement real MCP server ping
    if (method === 'ping') {
      const connectionTest = await testMCPConnection();
      
      if (connectionTest.isConnected) {
        return NextResponse.json({
          success: true,
          data: {
            status: 'ok',
            message: connectionTest.message,
            timestamp: new Date().toISOString(),
            connection_details: connectionTest.details,
            auth_status: connectionTest.auth_status, // 包含认证状态
          },
        });
      } else {
        return NextResponse.json({
          success: false,
          error: connectionTest.message,
          details: connectionTest.details,
          auth_status: connectionTest.auth_status, // 即使连接失败也返回认证状态
        });
      }
    }

    // For other methods, return not implemented for now
    return NextResponse.json(
      { success: false, error: `Method ${method} not implemented yet` },
      { status: 501 }
    );
  } catch (error) {
    console.error('MCP proxy error:', error);
    
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json({ 
    message: 'MCP Proxy is running',
    timestamp: new Date().toISOString(),
  });
}