/**
 * Individual Site Configuration API Routes (Direct Database Access)
 * 
 * Handles GET/PUT/DELETE operations for specific sites
 * using direct database access instead of proxying to MCP server.
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  getSiteById,
  updateSite,
  deleteSite,
  validateSiteData,
  type SiteFormData
} from '@/lib/database/sites';

// GET: Retrieve specific site
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const site = await getSiteById(id);

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
      { success: false, error: error instanceof Error ? error.message : 'Failed to retrieve site' },
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
    const errors = validateSiteData(body);
    if (errors.length > 0) {
      return NextResponse.json(
        { success: false, error: 'Validation failed', details: errors },
        { status: 400 }
      );
    }
    
    // Update site in database
    const updatedSite = await updateSite(id, body);

    return NextResponse.json({
      success: true,
      data: updatedSite,
      message: 'Site updated successfully'
    });

  } catch (error) {
    console.error(`PUT /api/config/sites/${params.id} error:`, error);
    
    if (error instanceof Error && error.message === 'Site not found') {
      return NextResponse.json(
        { success: false, error: 'Site not found' },
        { status: 404 }
      );
    }
    
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : 'Failed to update site' },
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
    const success = await deleteSite(id);

    if (!success) {
      return NextResponse.json(
        { success: false, error: 'Site not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({
      success: true,
      message: 'Site deleted successfully'
    });

  } catch (error) {
    console.error(`DELETE /api/config/sites/${params.id} error:`, error);
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : 'Failed to delete site' },
      { status: 500 }
    );
  }
}