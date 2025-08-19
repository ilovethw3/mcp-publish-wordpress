/**
 * Agent Configuration API Routes (Direct Database Access)
 * 
 * This module handles CRUD operations for agent configuration
 * using direct database access instead of proxying to MCP server.
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  getAllAgents,
  createAgent,
  validateAgentData,
  type Agent,
  type AgentFormData
} from '@/lib/database/agents';

// GET: Retrieve all agents
export async function GET() {
  try {
    const agents = await getAllAgents();
    
    return NextResponse.json({
      success: true,
      data: {
        agents: agents || [],
        total: agents?.length || 0
      }
    });
  } catch (error) {
    console.error('GET /api/config/agents error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : 'Failed to retrieve agents' 
      },
      { status: 500 }
    );
  }
}

// POST: Create a new agent
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Validate input
    const errors = validateAgentData(body);
    if (errors.length > 0) {
      return NextResponse.json(
        { success: false, error: 'Validation failed', details: errors },
        { status: 400 }
      );
    }

    // Prepare agent data with defaults
    const agentData: AgentFormData = {
      id: body.id || `agent-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      name: body.name.trim(),
      description: body.description.trim(),
      api_key: body.api_key, // Will be generated in createAgent if not provided
      status: body.status || 'active',
      rate_limit: {
        requests_per_minute: body.rate_limit?.requests_per_minute || 10,
        requests_per_hour: body.rate_limit?.requests_per_hour || 100,
        requests_per_day: body.rate_limit?.requests_per_day || 500,
      },
      permissions: {
        can_submit_articles: body.permissions?.can_submit_articles ?? true,
        can_edit_own_articles: body.permissions?.can_edit_own_articles ?? true,
        can_edit_others_articles: body.permissions?.can_edit_others_articles ?? false,
        can_approve_articles: body.permissions?.can_approve_articles ?? false,
        can_publish_articles: body.permissions?.can_publish_articles ?? false,
        can_view_statistics: body.permissions?.can_view_statistics ?? true,
        can_review_agents: body.permissions?.can_review_agents || [],
        allowed_categories: body.permissions?.allowed_categories || [],
        allowed_tags: body.permissions?.allowed_tags || [],
      },
      notifications: {
        on_approval: body.notifications?.on_approval ?? false,
        on_rejection: body.notifications?.on_rejection ?? true,
        on_publish_success: body.notifications?.on_publish_success ?? true,
        on_publish_failure: body.notifications?.on_publish_failure ?? true,
      },
    };

    // Create agent in database
    const agent = await createAgent(agentData);

    return NextResponse.json({
      success: true,
      data: agent,
      message: 'Agent created successfully'
    });

  } catch (error) {
    console.error('POST /api/config/agents error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : 'Failed to create agent' 
      },
      { status: 500 }
    );
  }
}