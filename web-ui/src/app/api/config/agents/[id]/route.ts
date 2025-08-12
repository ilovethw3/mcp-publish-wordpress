/**
 * Individual Agent Configuration API Routes
 * Handles GET/PUT/DELETE operations for specific agents
 */

import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import { join } from 'path';
import yaml from 'js-yaml';

// Types (same as in route.ts)
interface Agent {
  id: string;
  name: string;
  description: string;
  api_key: string;
  rate_limit: {
    requests_per_minute: number;
    requests_per_hour: number;
    requests_per_day: number;
  };
  permissions: {
    can_submit_articles: boolean;
    can_edit_own_articles: boolean;
    can_delete_own_articles: boolean;
    can_view_statistics: boolean;
    allowed_categories: string[];
    allowed_tags: string[];
  };
  notifications: {
    on_approval: boolean;
    on_rejection: boolean;
    on_publish_success: boolean;
    on_publish_failure: boolean;
  };
  created_at: string;
  status: 'active' | 'inactive';
}

interface AgentConfig {
  global_settings: any;
  agents: Agent[];
  agent_groups: Record<string, string[]>;
  monitoring: any;
  audit: any;
}

const CONFIG_PATH = join(process.cwd(), '..', 'config', 'agents.yml');

// Utility functions
async function readConfig(): Promise<AgentConfig> {
  try {
    const fileContent = await fs.readFile(CONFIG_PATH, 'utf8');
    return yaml.load(fileContent) as AgentConfig;
  } catch (error) {
    console.error('Error reading agent config:', error);
    throw new Error('Failed to read agent configuration');
  }
}

async function writeConfig(config: AgentConfig): Promise<void> {
  try {
    // Create backup
    const backupPath = CONFIG_PATH + '.backup.' + Date.now();
    try {
      await fs.copyFile(CONFIG_PATH, backupPath);
    } catch (error) {
      console.warn('Could not create backup:', error);
    }

    // Write new config
    const yamlString = yaml.dump(config, {
      indent: 2,
      lineWidth: 120,
      noRefs: true
    });
    
    await fs.writeFile(CONFIG_PATH, yamlString, 'utf8');
  } catch (error) {
    console.error('Error writing agent config:', error);
    throw new Error('Failed to write agent configuration');
  }
}

function validateAgent(agent: Partial<Agent>): string[] {
  const errors: string[] = [];

  if (!agent.name || agent.name.trim().length === 0) {
    errors.push('Agent name is required');
  }

  if (!agent.description || agent.description.trim().length === 0) {
    errors.push('Agent description is required');
  }

  if (agent.rate_limit) {
    if (agent.rate_limit.requests_per_minute <= 0) {
      errors.push('Requests per minute must be greater than 0');
    }
    if (agent.rate_limit.requests_per_hour <= 0) {
      errors.push('Requests per hour must be greater than 0');
    }
    if (agent.rate_limit.requests_per_day <= 0) {
      errors.push('Requests per day must be greater than 0');
    }
  }

  return errors;
}

// GET: Retrieve specific agent
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const config = await readConfig();
    
    const agent = config.agents.find(a => a.id === id);
    
    if (!agent) {
      return NextResponse.json(
        { success: false, error: 'Agent not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({
      success: true,
      data: agent
    });
  } catch (error) {
    console.error(`GET /api/config/agents/${params.id} error:`, error);
    return NextResponse.json(
      { success: false, error: 'Failed to retrieve agent' },
      { status: 500 }
    );
  }
}

// PUT: Update specific agent
export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const body = await request.json();
    
    // Validate input
    const errors = validateAgent(body);
    if (errors.length > 0) {
      return NextResponse.json(
        { success: false, error: 'Validation failed', details: errors },
        { status: 400 }
      );
    }

    const config = await readConfig();
    const agentIndex = config.agents.findIndex(a => a.id === id);
    
    if (agentIndex === -1) {
      return NextResponse.json(
        { success: false, error: 'Agent not found' },
        { status: 404 }
      );
    }

    // Update agent (preserve id and created_at)
    const existingAgent = config.agents[agentIndex];
    const updatedAgent: Agent = {
      ...existingAgent,
      name: body.name?.trim() || existingAgent.name,
      description: body.description?.trim() || existingAgent.description,
      api_key: body.api_key || existingAgent.api_key,
      rate_limit: {
        requests_per_minute: body.rate_limit?.requests_per_minute ?? existingAgent.rate_limit.requests_per_minute,
        requests_per_hour: body.rate_limit?.requests_per_hour ?? existingAgent.rate_limit.requests_per_hour,
        requests_per_day: body.rate_limit?.requests_per_day ?? existingAgent.rate_limit.requests_per_day,
      },
      permissions: {
        can_submit_articles: body.permissions?.can_submit_articles ?? existingAgent.permissions.can_submit_articles,
        can_edit_own_articles: body.permissions?.can_edit_own_articles ?? existingAgent.permissions.can_edit_own_articles,
        can_delete_own_articles: body.permissions?.can_delete_own_articles ?? existingAgent.permissions.can_delete_own_articles,
        can_view_statistics: body.permissions?.can_view_statistics ?? existingAgent.permissions.can_view_statistics,
        allowed_categories: body.permissions?.allowed_categories ?? existingAgent.permissions.allowed_categories,
        allowed_tags: body.permissions?.allowed_tags ?? existingAgent.permissions.allowed_tags,
      },
      notifications: {
        on_approval: body.notifications?.on_approval ?? existingAgent.notifications.on_approval,
        on_rejection: body.notifications?.on_rejection ?? existingAgent.notifications.on_rejection,
        on_publish_success: body.notifications?.on_publish_success ?? existingAgent.notifications.on_publish_success,
        on_publish_failure: body.notifications?.on_publish_failure ?? existingAgent.notifications.on_publish_failure,
      },
      status: body.status || existingAgent.status,
    };

    config.agents[agentIndex] = updatedAgent;

    // Write config
    await writeConfig(config);

    return NextResponse.json({
      success: true,
      data: updatedAgent,
      message: 'Agent updated successfully'
    });

  } catch (error) {
    console.error(`PUT /api/config/agents/${params.id} error:`, error);
    return NextResponse.json(
      { success: false, error: 'Failed to update agent' },
      { status: 500 }
    );
  }
}

// DELETE: Remove specific agent
export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const config = await readConfig();
    
    const agentIndex = config.agents.findIndex(a => a.id === id);
    
    if (agentIndex === -1) {
      return NextResponse.json(
        { success: false, error: 'Agent not found' },
        { status: 404 }
      );
    }

    // Remove agent
    const removedAgent = config.agents.splice(agentIndex, 1)[0];

    // Remove from agent groups
    Object.keys(config.agent_groups).forEach(groupName => {
      config.agent_groups[groupName] = config.agent_groups[groupName].filter(
        agentId => agentId !== id
      );
      // Remove empty groups
      if (config.agent_groups[groupName].length === 0) {
        delete config.agent_groups[groupName];
      }
    });

    // Write config
    await writeConfig(config);

    return NextResponse.json({
      success: true,
      data: removedAgent,
      message: 'Agent deleted successfully'
    });

  } catch (error) {
    console.error(`DELETE /api/config/agents/${params.id} error:`, error);
    return NextResponse.json(
      { success: false, error: 'Failed to delete agent' },
      { status: 500 }
    );
  }
}