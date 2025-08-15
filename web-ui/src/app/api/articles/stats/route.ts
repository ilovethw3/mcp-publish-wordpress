/**
 * Article Statistics API Route Handler
 * 
 * This route provides article statistics for the dashboard.
 */

import { NextRequest, NextResponse } from 'next/server';
import { getArticleStats } from '@/lib/database/articles';

// GET: Retrieve article statistics
export async function GET(request: NextRequest) {
  try {
    const stats = await getArticleStats();
    
    return NextResponse.json({
      success: true,
      data: stats
    });
  } catch (error) {
    console.error('GET /api/articles/stats error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : 'Failed to retrieve article statistics' 
      },
      { status: 500 }
    );
  }
}