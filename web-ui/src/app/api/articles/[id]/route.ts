/**
 * Single Article API Route Handler
 * 
 * This route handles operations for individual articles.
 */

import { NextRequest, NextResponse } from 'next/server';
import { getArticleById, updateArticle, ArticleUpdateData } from '@/lib/database/articles';

// GET: Retrieve a single article by ID
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const id = parseInt(params.id);
    
    if (isNaN(id)) {
      return NextResponse.json(
        { success: false, error: 'Invalid article ID: must be a number' },
        { status: 400 }
      );
    }

    const article = await getArticleById(id);
    
    if (!article) {
      return NextResponse.json(
        { success: false, error: `Article with ID ${id} not found` },
        { status: 404 }
      );
    }

    return NextResponse.json({
      success: true,
      data: article
    });
  } catch (error) {
    console.error(`GET /api/articles/${params.id} error:`, error);
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : 'Failed to retrieve article' 
      },
      { status: 500 }
    );
  }
}

// PUT: Update an article
export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const id = parseInt(params.id);
    
    if (isNaN(id)) {
      return NextResponse.json(
        { success: false, error: 'Invalid article ID: must be a number' },
        { status: 400 }
      );
    }

    const body = await request.json();
    
    // Validate request body
    const allowedFields = ['title', 'content_markdown', 'tags', 'category', 'reviewer_notes'];
    const updateData: ArticleUpdateData = {};
    
    for (const field of allowedFields) {
      if (body[field] !== undefined) {
        updateData[field as keyof ArticleUpdateData] = body[field];
      }
    }

    if (Object.keys(updateData).length === 0) {
      return NextResponse.json(
        { success: false, error: 'No valid fields provided for update' },
        { status: 400 }
      );
    }

    const updatedArticle = await updateArticle(id, updateData);
    
    return NextResponse.json({
      success: true,
      data: updatedArticle,
      message: 'Article updated successfully'
    });
  } catch (error) {
    console.error(`PUT /api/articles/${params.id} error:`, error);
    
    // Handle specific error types
    if (error instanceof Error) {
      if (error.message.includes('not found')) {
        return NextResponse.json(
          { success: false, error: error.message },
          { status: 404 }
        );
      }
      if (error.message.includes('can only edit') || error.message.includes('status is')) {
        return NextResponse.json(
          { success: false, error: error.message },
          { status: 409 } // Conflict
        );
      }
      if (error.message.includes('cannot be empty') || error.message.includes('cannot exceed')) {
        return NextResponse.json(
          { success: false, error: error.message },
          { status: 400 }
        );
      }
    }
    
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : 'Failed to update article' 
      },
      { status: 500 }
    );
  }
}