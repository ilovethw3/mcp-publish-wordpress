/**
 * Web UI MCP API Key Validation Endpoint
 * 
 * 验证环境变量中的API密钥是否在数据库中有效
 * 这些日志会出现在Web UI容器日志中: docker logs web-ui-container
 */

import { NextRequest, NextResponse } from 'next/server';
import { query } from '@/lib/database/connection';
import crypto from 'crypto';

interface ValidationResult {
  valid: boolean;
  agent_id?: string;
  error?: string;
  details?: {
    env_key_prefix?: string;
    database_status?: string;
  };
}

/**
 * 验证API密钥是否在数据库中存在
 */
async function validateApiKeyInDatabase(apiKey: string): Promise<{valid: boolean, agent_id?: string}> {
  try {
    // 计算API密钥的哈希值
    const keyHash = crypto.createHash('sha256').update(apiKey).digest('hex');
    
    console.log('[WEB-UI] 🔐 开始验证API密钥...');
    console.log(`[WEB-UI] 🔍 密钥前缀: ${apiKey.substring(0, 10)}...`);
    console.log(`[WEB-UI] 🔍 密钥哈希: ${keyHash.substring(0, 10)}...`);
    
    // 查询数据库中匹配的Agent
    const result = await query(`
      SELECT id, name, status 
      FROM agents 
      WHERE api_key_hash = $1 AND status = 'active'
    `, [keyHash]);
    
    if (result.rows.length > 0) {
      const agent = result.rows[0];
      console.log(`[WEB-UI] ✅ 找到匹配的Agent: ${agent.name} (${agent.id})`);
      return { valid: true, agent_id: agent.id };
    } else {
      console.error('[WEB-UI] ❌ 数据库中未找到匹配的Agent');
      console.error(`[WEB-UI] 🔍 查询哈希: ${keyHash.substring(0, 10)}...`);
      return { valid: false };
    }
  } catch (error) {
    console.error('[WEB-UI] ❌ 数据库验证过程发生错误:', error);
    return { valid: false };
  }
}

export async function GET(request: NextRequest): Promise<NextResponse<ValidationResult>> {
  try {
    console.log('[WEB-UI] 🔐 收到API密钥验证请求');
    
    // 读取环境变量中的API密钥
    const apiKey = process.env.WEB_UI_AGENT_API_KEY;
    
    if (!apiKey) {
      console.error('[WEB-UI] ❌ 环境变量中未配置 WEB_UI_AGENT_API_KEY');
      console.error('[WEB-UI] 🔧 解决方案: 运行 python init_production_db.py 生成密钥');
      
      return NextResponse.json({
        valid: false,
        error: '环境变量中未配置 WEB_UI_AGENT_API_KEY',
        details: {
          env_key_prefix: '未配置',
          database_status: '未检查'
        }
      });
    }
    
    // 验证密钥格式
    if (!apiKey.startsWith('webui_')) {
      console.error('[WEB-UI] ❌ API密钥格式错误 - 应该以 webui_ 开头');
      console.error(`[WEB-UI] 🔍 当前密钥前缀: ${apiKey.substring(0, 10)}...`);
      
      return NextResponse.json({
        valid: false,
        error: 'API密钥格式错误',
        details: {
          env_key_prefix: apiKey.substring(0, 10) + '...',
          database_status: '格式错误，未检查数据库'
        }
      });
    }
    
    // 验证数据库中是否存在该密钥
    const dbResult = await validateApiKeyInDatabase(apiKey);
    
    if (dbResult.valid) {
      console.log('[WEB-UI] ✅ API密钥验证成功');
      console.log(`[WEB-UI] 🎯 认证的Agent: ${dbResult.agent_id}`);
      
      return NextResponse.json({
        valid: true,
        agent_id: dbResult.agent_id,
        details: {
          env_key_prefix: apiKey.substring(0, 10) + '...',
          database_status: '验证成功'
        }
      });
    } else {
      console.error('[WEB-UI] ❌ API密钥验证失败 - 密钥不一致!');
      console.error(`[WEB-UI] 🔍 环境变量密钥: ${apiKey.substring(0, 10)}... (来源: .env.local)`);
      console.error('[WEB-UI] 🔍 数据库验证结果: 密钥哈希不匹配');
      console.error('[WEB-UI] ⚠️  Web UI 无法调用 MCP 工具进行文章审批');
      console.error('[WEB-UI] 🔧 修复步骤:');
      console.error('[WEB-UI]    1. 运行: python init_production_db.py');
      console.error('[WEB-UI]    2. 重启 Web UI 容器');
      
      return NextResponse.json({
        valid: false,
        error: 'API密钥不一致',
        details: {
          env_key_prefix: apiKey.substring(0, 10) + '...',
          database_status: '数据库中无匹配记录'
        }
      });
    }
    
  } catch (error) {
    console.error('[WEB-UI] ❌ API密钥验证接口发生错误:', error);
    
    return NextResponse.json({
      valid: false,
      error: '验证过程发生内部错误',
      details: {
        env_key_prefix: '错误',
        database_status: '检查失败'
      }
    }, { status: 500 });
  }
}

/**
 * 健康检查接口 - 可用于容器健康检查
 */
export async function HEAD(request: NextRequest): Promise<NextResponse> {
  try {
    const apiKey = process.env.WEB_UI_AGENT_API_KEY;
    if (!apiKey) {
      return new NextResponse(null, { status: 503 }); // Service Unavailable
    }
    
    const dbResult = await validateApiKeyInDatabase(apiKey);
    if (dbResult.valid) {
      return new NextResponse(null, { status: 200 }); // OK
    } else {
      return new NextResponse(null, { status: 503 }); // Service Unavailable
    }
  } catch (error) {
    return new NextResponse(null, { status: 500 }); // Internal Server Error
  }
}