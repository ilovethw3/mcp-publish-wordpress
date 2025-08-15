/**
 * Articles API Route Handler (Direct Database Access)
 * 
 * This route handles article management operations using direct database access
 * instead of proxying to the MCP server, following the dual-service architecture.
 */

import { NextRequest, NextResponse } from 'next/server';
import { getArticles, approveArticle, rejectArticle, getArticleStats } from '@/lib/database/articles';

// GET: Retrieve articles with filtering
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    
    const filters = {
      status: searchParams.get('status') || undefined,
      search: searchParams.get('search') || undefined,
      agent_id: searchParams.get('agent_id') || undefined,
      target_site: searchParams.get('target_site') || undefined,
      limit: searchParams.get('limit') ? parseInt(searchParams.get('limit')!) : undefined,
      offset: searchParams.get('offset') ? parseInt(searchParams.get('offset')!) : undefined,
    };

    // Remove undefined values
    const cleanFilters = Object.fromEntries(
      Object.entries(filters).filter(([_, v]) => v !== undefined)
    );

    const result = await getArticles(cleanFilters);
    
    return NextResponse.json({
      success: true,
      data: result
    });
  } catch (error) {
    console.error('GET /api/articles error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : 'Failed to retrieve articles' 
      },
      { status: 500 }
    );
  }
}

// POST: Handle article actions (approve, reject)
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, article_id, reviewer_notes, rejection_reason } = body;

    if (!action || !article_id) {
      return NextResponse.json(
        { success: false, error: 'Missing required fields: action and article_id' },
        { status: 400 }
      );
    }

    const id = parseInt(article_id);
    if (isNaN(id)) {
      return NextResponse.json(
        { success: false, error: 'Invalid article_id: must be a number' },
        { status: 400 }
      );
    }

    let result;
    
    switch (action) {
      case 'approve':
        result = await approveArticle(id, reviewer_notes);
        return NextResponse.json({
          success: true,
          data: {
            article_id: id,
            status: result.status,
            message: 'Article approved successfully',
            updated_article: result,
          }
        });

      case 'reject':
        if (!rejection_reason || !rejection_reason.trim()) {
          return NextResponse.json(
            { success: false, error: 'Rejection reason is required' },
            { status: 400 }
          );
        }
        
        result = await rejectArticle(id, rejection_reason);
        return NextResponse.json({
          success: true,
          data: {
            article_id: id,
            status: result.status,
            rejection_reason: result.rejection_reason,
            message: 'Article rejected successfully',
            updated_article: result,
          }
        });

      default:
        return NextResponse.json(
          { success: false, error: `Unknown action: ${action}. Supported actions: approve, reject` },
          { status: 400 }
        );
    }
  } catch (error) {
    console.error('POST /api/articles error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : 'Failed to process article action' 
      },
      { status: 500 }
    );
  }
}