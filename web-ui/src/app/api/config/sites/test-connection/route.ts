/**
 * Site Connection Testing API Route (Direct Database Access)
 * 
 * Tests WordPress connection without storing the site configuration
 */

import { NextRequest, NextResponse } from 'next/server';
import { testWordPressConnection, validateSiteData } from '@/lib/database/sites';

// POST: Test WordPress connection
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Validate the wordpress_config part
    const errors = validateSiteData({ wordpress_config: body.wordpress_config });
    if (errors.length > 0) {
      return NextResponse.json(
        { success: false, error: 'Validation failed', details: errors },
        { status: 400 }
      );
    }

    // Test the connection
    const result = await testWordPressConnection(body.wordpress_config);

    return NextResponse.json({
      success: result.success,
      message: result.message,
      details: result.details
    });

  } catch (error) {
    console.error('POST /api/config/sites/test-connection error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : 'Failed to test connection' 
      },
      { status: 500 }
    );
  }
}