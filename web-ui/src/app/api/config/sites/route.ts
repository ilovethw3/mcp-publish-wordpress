/**
 * Site Configuration API Routes
 * Handles CRUD operations for site configuration
 */

import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import { join } from 'path';
import yaml from 'js-yaml';
import { v4 as uuidv4 } from 'uuid';

// Types
interface Site {
  id: string;
  name: string;
  description: string;
  wordpress_config: {
    api_url: string;
    username: string;
    app_password: string;
    default_status: string;
    default_comment_status: string;
    default_ping_status: string;
    category_mapping: Record<string, number>;
    tag_auto_create: boolean;
  };
  publishing_rules: {
    allowed_agents: string[];
    allowed_categories: string[];
    min_word_count: number;
    max_word_count: number;
    require_featured_image: boolean;
    auto_approve: boolean;
    auto_publish_approved: boolean;
  };
  rate_limit: {
    max_posts_per_hour: number;
    max_posts_per_day: number;
    max_concurrent_publishes: number;
  };
  notifications: {
    on_publish_success: boolean;
    on_publish_failure: boolean;
    on_connection_failure: boolean;
    email_notifications: string[];
  };
  created_at: string;
  status: 'active' | 'inactive';
  priority: number;
}

interface SiteConfig {
  global_settings: any;
  sites: Site[];
  site_groups: Record<string, string[]>;
  load_balancing: any;
  monitoring: any;
  backup: any;
  synchronization: any;
}

const CONFIG_PATH = join(process.cwd(), '..', 'config', 'sites.yml');

// Utility functions
async function readConfig(): Promise<SiteConfig> {
  try {
    const fileContent = await fs.readFile(CONFIG_PATH, 'utf8');
    return yaml.load(fileContent) as SiteConfig;
  } catch (error) {
    console.error('Error reading site config:', error);
    throw new Error('Failed to read site configuration');
  }
}

async function writeConfig(config: SiteConfig): Promise<void> {
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
    console.error('Error writing site config:', error);
    throw new Error('Failed to write site configuration');
  }
}

function validateSite(site: Partial<Site>): string[] {
  const errors: string[] = [];

  if (!site.name || site.name.trim().length === 0) {
    errors.push('Site name is required');
  }

  if (!site.description || site.description.trim().length === 0) {
    errors.push('Site description is required');
  }

  if (site.id && !/^[a-zA-Z0-9-_]+$/.test(site.id)) {
    errors.push('Site ID must contain only alphanumeric characters, hyphens, and underscores');
  }

  if (site.wordpress_config) {
    if (!site.wordpress_config.api_url || !site.wordpress_config.api_url.startsWith('http')) {
      errors.push('Valid WordPress API URL is required');
    }

    if (!site.wordpress_config.username || site.wordpress_config.username.trim().length === 0) {
      errors.push('WordPress username is required');
    }

    if (!site.wordpress_config.app_password || site.wordpress_config.app_password.trim().length === 0) {
      errors.push('WordPress application password is required');
    }
  }

  if (site.publishing_rules) {
    if (site.publishing_rules.min_word_count < 0) {
      errors.push('Minimum word count cannot be negative');
    }
    if (site.publishing_rules.max_word_count < site.publishing_rules.min_word_count) {
      errors.push('Maximum word count cannot be less than minimum word count');
    }
  }

  if (site.rate_limit) {
    if (site.rate_limit.max_posts_per_hour <= 0) {
      errors.push('Max posts per hour must be greater than 0');
    }
    if (site.rate_limit.max_posts_per_day <= 0) {
      errors.push('Max posts per day must be greater than 0');
    }
  }

  return errors;
}

// Test WordPress connection
async function testWordPressConnection(apiUrl: string, username: string, appPassword: string): Promise<boolean> {
  try {
    const auth = Buffer.from(`${username}:${appPassword}`).toString('base64');
    const response = await fetch(`${apiUrl}/users/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Basic ${auth}`,
        'Content-Type': 'application/json',
      },
    });
    return response.ok;
  } catch (error) {
    console.error('WordPress connection test failed:', error);
    return false;
  }
}

// GET: Retrieve all sites
export async function GET() {
  try {
    const config = await readConfig();
    
    return NextResponse.json({
      success: true,
      data: {
        sites: config.sites || [],
        global_settings: config.global_settings,
        total: config.sites?.length || 0
      }
    });
  } catch (error) {
    console.error('GET /api/config/sites error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to retrieve sites' },
      { status: 500 }
    );
  }
}

// POST: Create a new site
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Validate input
    const errors = validateSite(body);
    if (errors.length > 0) {
      return NextResponse.json(
        { success: false, error: 'Validation failed', details: errors },
        { status: 400 }
      );
    }

    const config = await readConfig();
    
    // Generate unique ID if not provided
    const siteId = body.id || `site-${Date.now()}-${uuidv4().split('-')[0]}`;
    
    // Check for duplicate ID
    if (config.sites.some(site => site.id === siteId)) {
      return NextResponse.json(
        { success: false, error: 'Site ID already exists' },
        { status: 400 }
      );
    }

    // Test WordPress connection if requested
    if (body.test_connection) {
      const connectionOk = await testWordPressConnection(
        body.wordpress_config.api_url,
        body.wordpress_config.username,
        body.wordpress_config.app_password
      );
      
      if (!connectionOk) {
        return NextResponse.json(
          { success: false, error: 'WordPress connection test failed' },
          { status: 400 }
        );
      }
    }

    // Create new site with defaults
    const newSite: Site = {
      id: siteId,
      name: body.name.trim(),
      description: body.description.trim(),
      wordpress_config: {
        api_url: body.wordpress_config.api_url.trim(),
        username: body.wordpress_config.username.trim(),
        app_password: body.wordpress_config.app_password.trim(),
        default_status: body.wordpress_config.default_status || 'draft',
        default_comment_status: body.wordpress_config.default_comment_status || 'closed',
        default_ping_status: body.wordpress_config.default_ping_status || 'closed',
        category_mapping: body.wordpress_config.category_mapping || {},
        tag_auto_create: body.wordpress_config.tag_auto_create ?? true,
      },
      publishing_rules: {
        allowed_agents: body.publishing_rules?.allowed_agents || [],
        allowed_categories: body.publishing_rules?.allowed_categories || [],
        min_word_count: body.publishing_rules?.min_word_count || 100,
        max_word_count: body.publishing_rules?.max_word_count || 5000,
        require_featured_image: body.publishing_rules?.require_featured_image ?? false,
        auto_approve: body.publishing_rules?.auto_approve ?? false,
        auto_publish_approved: body.publishing_rules?.auto_publish_approved ?? true,
      },
      rate_limit: {
        max_posts_per_hour: body.rate_limit?.max_posts_per_hour || 10,
        max_posts_per_day: body.rate_limit?.max_posts_per_day || 50,
        max_concurrent_publishes: body.rate_limit?.max_concurrent_publishes || 3,
      },
      notifications: {
        on_publish_success: body.notifications?.on_publish_success ?? true,
        on_publish_failure: body.notifications?.on_publish_failure ?? true,
        on_connection_failure: body.notifications?.on_connection_failure ?? true,
        email_notifications: body.notifications?.email_notifications || [],
      },
      created_at: new Date().toISOString(),
      status: body.status || 'active',
      priority: body.priority || 1,
    };

    // Add to config
    config.sites = config.sites || [];
    config.sites.push(newSite);

    // Write config
    await writeConfig(config);

    return NextResponse.json({
      success: true,
      data: newSite,
      message: 'Site created successfully'
    });

  } catch (error) {
    console.error('POST /api/config/sites error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to create site' },
      { status: 500 }
    );
  }
}