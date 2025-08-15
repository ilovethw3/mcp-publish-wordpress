/**
 * Site Configuration API Routes (Direct Database Access)
 * 
 * This module handles CRUD operations for site configuration
 * using direct database access instead of proxying to MCP server.
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  getAllSites,
  createSite,
  validateSiteData,
  type Site,
  type SiteFormData
} from '@/lib/database/sites';

// GET: Retrieve all sites
export async function GET() {
  try {
    const sites = await getAllSites();
    
    return NextResponse.json({
      success: true,
      data: {
        sites: sites || [],
        total: sites?.length || 0
      }
    });
  } catch (error) {
    console.error('GET /api/config/sites error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : 'Failed to retrieve sites' 
      },
      { status: 500 }
    );
  }
}

// POST: Create a new site
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Validate input
    const errors = validateSiteData(body);
    if (errors.length > 0) {
      return NextResponse.json(
        { success: false, error: 'Validation failed', details: errors },
        { status: 400 }
      );
    }

    // Prepare site data with defaults
    const siteData: SiteFormData = {
      id: body.id || `site-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      name: body.name.trim(),
      description: body.description.trim(),
      status: body.status || 'active',
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
        max_word_count: body.publishing_rules?.max_word_count || 10000,
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
        on_connection_error: body.notifications?.on_connection_error ?? true,
      },
    };

    // Create site in database
    const site = await createSite(siteData);

    return NextResponse.json({
      success: true,
      data: site,
      message: 'Site created successfully'
    });

  } catch (error) {
    console.error('POST /api/config/sites error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : 'Failed to create site' 
      },
      { status: 500 }
    );
  }
}