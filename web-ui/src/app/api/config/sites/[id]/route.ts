/**
 * Individual Site Configuration API Routes
 * Handles GET/PUT/DELETE operations for specific sites
 */

import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import { join } from 'path';
import yaml from 'js-yaml';

// Types (same as in route.ts)
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

// GET: Retrieve specific site
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const config = await readConfig();
    
    const site = config.sites.find(s => s.id === id);
    
    if (!site) {
      return NextResponse.json(
        { success: false, error: 'Site not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({
      success: true,
      data: site
    });
  } catch (error) {
    console.error(`GET /api/config/sites/${params.id} error:`, error);
    return NextResponse.json(
      { success: false, error: 'Failed to retrieve site' },
      { status: 500 }
    );
  }
}

// PUT: Update specific site
export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
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
    const siteIndex = config.sites.findIndex(s => s.id === id);
    
    if (siteIndex === -1) {
      return NextResponse.json(
        { success: false, error: 'Site not found' },
        { status: 404 }
      );
    }

    // Test WordPress connection if requested
    if (body.test_connection && body.wordpress_config) {
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

    // Update site (preserve id and created_at)
    const existingSite = config.sites[siteIndex];
    const updatedSite: Site = {
      ...existingSite,
      name: body.name?.trim() || existingSite.name,
      description: body.description?.trim() || existingSite.description,
      wordpress_config: {
        api_url: body.wordpress_config?.api_url?.trim() || existingSite.wordpress_config.api_url,
        username: body.wordpress_config?.username?.trim() || existingSite.wordpress_config.username,
        app_password: body.wordpress_config?.app_password?.trim() || existingSite.wordpress_config.app_password,
        default_status: body.wordpress_config?.default_status || existingSite.wordpress_config.default_status,
        default_comment_status: body.wordpress_config?.default_comment_status || existingSite.wordpress_config.default_comment_status,
        default_ping_status: body.wordpress_config?.default_ping_status || existingSite.wordpress_config.default_ping_status,
        category_mapping: body.wordpress_config?.category_mapping ?? existingSite.wordpress_config.category_mapping,
        tag_auto_create: body.wordpress_config?.tag_auto_create ?? existingSite.wordpress_config.tag_auto_create,
      },
      publishing_rules: {
        allowed_agents: body.publishing_rules?.allowed_agents ?? existingSite.publishing_rules.allowed_agents,
        allowed_categories: body.publishing_rules?.allowed_categories ?? existingSite.publishing_rules.allowed_categories,
        min_word_count: body.publishing_rules?.min_word_count ?? existingSite.publishing_rules.min_word_count,
        max_word_count: body.publishing_rules?.max_word_count ?? existingSite.publishing_rules.max_word_count,
        require_featured_image: body.publishing_rules?.require_featured_image ?? existingSite.publishing_rules.require_featured_image,
        auto_approve: body.publishing_rules?.auto_approve ?? existingSite.publishing_rules.auto_approve,
        auto_publish_approved: body.publishing_rules?.auto_publish_approved ?? existingSite.publishing_rules.auto_publish_approved,
      },
      rate_limit: {
        max_posts_per_hour: body.rate_limit?.max_posts_per_hour ?? existingSite.rate_limit.max_posts_per_hour,
        max_posts_per_day: body.rate_limit?.max_posts_per_day ?? existingSite.rate_limit.max_posts_per_day,
        max_concurrent_publishes: body.rate_limit?.max_concurrent_publishes ?? existingSite.rate_limit.max_concurrent_publishes,
      },
      notifications: {
        on_publish_success: body.notifications?.on_publish_success ?? existingSite.notifications.on_publish_success,
        on_publish_failure: body.notifications?.on_publish_failure ?? existingSite.notifications.on_publish_failure,
        on_connection_failure: body.notifications?.on_connection_failure ?? existingSite.notifications.on_connection_failure,
        email_notifications: body.notifications?.email_notifications ?? existingSite.notifications.email_notifications,
      },
      status: body.status || existingSite.status,
      priority: body.priority ?? existingSite.priority,
    };

    config.sites[siteIndex] = updatedSite;

    // Write config
    await writeConfig(config);

    return NextResponse.json({
      success: true,
      data: updatedSite,
      message: 'Site updated successfully'
    });

  } catch (error) {
    console.error(`PUT /api/config/sites/${params.id} error:`, error);
    return NextResponse.json(
      { success: false, error: 'Failed to update site' },
      { status: 500 }
    );
  }
}

// DELETE: Remove specific site
export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const config = await readConfig();
    
    const siteIndex = config.sites.findIndex(s => s.id === id);
    
    if (siteIndex === -1) {
      return NextResponse.json(
        { success: false, error: 'Site not found' },
        { status: 404 }
      );
    }

    // Remove site
    const removedSite = config.sites.splice(siteIndex, 1)[0];

    // Remove from site groups
    Object.keys(config.site_groups).forEach(groupName => {
      config.site_groups[groupName] = config.site_groups[groupName].filter(
        siteId => siteId !== id
      );
      // Remove empty groups
      if (config.site_groups[groupName].length === 0) {
        delete config.site_groups[groupName];
      }
    });

    // Write config
    await writeConfig(config);

    return NextResponse.json({
      success: true,
      data: removedSite,
      message: 'Site deleted successfully'
    });

  } catch (error) {
    console.error(`DELETE /api/config/sites/${params.id} error:`, error);
    return NextResponse.json(
      { success: false, error: 'Failed to delete site' },
      { status: 500 }
    );
  }
}

// POST: Test WordPress connection for specific site
export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const config = await readConfig();
    
    const site = config.sites.find(s => s.id === id);
    
    if (!site) {
      return NextResponse.json(
        { success: false, error: 'Site not found' },
        { status: 404 }
      );
    }

    const connectionOk = await testWordPressConnection(
      site.wordpress_config.api_url,
      site.wordpress_config.username,
      site.wordpress_config.app_password
    );

    return NextResponse.json({
      success: true,
      data: {
        site_id: id,
        connection_status: connectionOk ? 'success' : 'failed',
        tested_at: new Date().toISOString()
      }
    });

  } catch (error) {
    console.error(`POST /api/config/sites/${params.id} error:`, error);
    return NextResponse.json(
      { success: false, error: 'Failed to test site connection' },
      { status: 500 }
    );
  }
}