/**
 * MCP Proxy: Approve Article
 * 
 * 代理Web UI前端对MCP服务器approve_article工具的调用
 * 使用服务端API密钥进行认证
 */

import { NextRequest, NextResponse } from 'next/server';
import { getMCPClient } from '@/lib/mcp-client';

interface ApproveArticleRequest {
  article_id: number;
  reviewer_notes?: string;
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    console.log('[WEB-UI] 🔐 收到MCP审批文章代理请求');
    
    // 检查API密钥配置
    const apiKey = process.env.WEB_UI_AGENT_API_KEY;
    if (!apiKey) {
      console.error('[WEB-UI] ❌ 环境变量中未配置 WEB_UI_AGENT_API_KEY');
      return NextResponse.json({
        success: false,
        error: '服务端API密钥未配置'
      }, { status: 500 });
    }
    
    // 解析请求体
    const body: ApproveArticleRequest = await request.json();
    const { article_id, reviewer_notes = '' } = body;
    
    if (!article_id) {
      console.error('[WEB-UI] ❌ 请求参数错误: 缺少必要参数');
      return NextResponse.json({
        success: false,
        error: '缺少必要参数: article_id'
      }, { status: 400 });
    }
    
    console.log(`[WEB-UI] 🔐 代理调用 MCP approve_article，文章ID: ${article_id}`);
    console.log(`[WEB-UI] 📝 审批备注: ${reviewer_notes || '(无)'}`);
    
    // 使用 MCP 客户端调用 approve_article 工具
    const mcpClient = getMCPClient({ apiKey });
    const result = await mcpClient.approveArticle(article_id, reviewer_notes);
    
    if (!result.success) {
      console.error(`[WEB-UI] ❌ MCP审批工具调用失败: ${result.error}`);
      return NextResponse.json({
        success: false,
        error: `MCP工具调用失败: ${result.error}`
      }, { status: 500 });
    }
    
    console.log('[WEB-UI] ✅ MCP审批工具调用成功');
    console.log(`[WEB-UI] 🎯 审批结果: ${JSON.stringify(result.data)}`);
    
    return NextResponse.json({
      success: true,
      data: result.data
    });
    
  } catch (error) {
    console.error('[WEB-UI] ❌ MCP代理调用发生错误:', error);
    
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : '代理调用失败'
    }, { status: 500 });
  }
}