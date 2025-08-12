/**
 * Agent Configuration API Routes
 * Handles CRUD operations for agent configuration
 */

import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import { join } from 'path';
import yaml from 'js-yaml';
import { v4 as uuidv4 } from 'uuid';
import crypto from 'crypto';

// Types
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
function generateApiKey(): string {
  return crypto.randomBytes(32).toString('hex');
}

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

  if (agent.id && !/^[a-zA-Z0-9-_]+$/.test(agent.id)) {
    errors.push('Agent ID must contain only alphanumeric characters, hyphens, and underscores');
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

// GET: Retrieve all agents
export async function GET() {
  try {
    const config = await readConfig();
    
    return NextResponse.json({
      success: true,
      data: {
        agents: config.agents || [],
        global_settings: config.global_settings,
        total: config.agents?.length || 0
      }
    });
  } catch (error) {
    console.error('GET /api/config/agents error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to retrieve agents' },
      { status: 500 }
    );
  }
}

// POST: Create a new agent
export async function POST(request: NextRequest) {
  try {
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
    
    // Generate unique ID if not provided
    const agentId = body.id || `agent-${Date.now()}-${uuidv4().split('-')[0]}`;
    
    // Check for duplicate ID
    if (config.agents.some(agent => agent.id === agentId)) {
      return NextResponse.json(
        { success: false, error: 'Agent ID already exists' },
        { status: 400 }
      );
    }

    // Create new agent with defaults
    const newAgent: Agent = {
      id: agentId,
      name: body.name.trim(),
      description: body.description.trim(),
      api_key: body.api_key || generateApiKey(),
      rate_limit: {
        requests_per_minute: body.rate_limit?.requests_per_minute || 10,
        requests_per_hour: body.rate_limit?.requests_per_hour || 100,
        requests_per_day: body.rate_limit?.requests_per_day || 500,
      },
      permissions: {
        can_submit_articles: body.permissions?.can_submit_articles ?? true,
        can_edit_own_articles: body.permissions?.can_edit_own_articles ?? true,
        can_delete_own_articles: body.permissions?.can_delete_own_articles ?? false,
        can_view_statistics: body.permissions?.can_view_statistics ?? true,
        allowed_categories: body.permissions?.allowed_categories || [],
        allowed_tags: body.permissions?.allowed_tags || [],
      },
      notifications: {
        on_approval: body.notifications?.on_approval ?? false,
        on_rejection: body.notifications?.on_rejection ?? true,
        on_publish_success: body.notifications?.on_publish_success ?? true,
        on_publish_failure: body.notifications?.on_publish_failure ?? true,
      },
      created_at: new Date().toISOString(),
      status: body.status || 'active',
    };

    // Add to config
    config.agents = config.agents || [];
    config.agents.push(newAgent);

    // Write config
    await writeConfig(config);

    return NextResponse.json({
      success: true,
      data: newAgent,
      message: 'Agent created successfully'
    });

  } catch (error) {
    console.error('POST /api/config/agents error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to create agent' },
      { status: 500 }
    );
  }
}