/**
 * Individual Agent Configuration API Routes (Direct Database Access)
 * 
 * Handles GET/PUT/DELETE operations for specific agents
 * using direct database access instead of proxying to MCP server.
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  getAgentById,
  updateAgent,
  deleteAgent,
  validateAgentData,
  type AgentFormData
} from '@/lib/database/agents';

// GET: Retrieve specific agent
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;
    const agent = await getAgentById(id);

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
      { success: false, error: error instanceof Error ? error.message : 'Failed to retrieve agent' },
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
    const errors = validateAgentData(body);
    if (errors.length > 0) {
      return NextResponse.json(
        { success: false, error: 'Validation failed', details: errors },
        { status: 400 }
      );
    }
    
    // Update agent in database
    const updatedAgent = await updateAgent(id, body);

    return NextResponse.json({
      success: true,
      data: updatedAgent,
      message: 'Agent updated successfully'
    });

  } catch (error) {
    console.error(`PUT /api/config/agents/${params.id} error:`, error);
    
    if (error instanceof Error && error.message === 'Agent not found') {
      return NextResponse.json(
        { success: false, error: 'Agent not found' },
        { status: 404 }
      );
    }
    
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : 'Failed to update agent' },
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
    const success = await deleteAgent(id);

    if (!success) {
      return NextResponse.json(
        { success: false, error: 'Agent not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({
      success: true,
      message: 'Agent deleted successfully'
    });

  } catch (error) {
    console.error(`DELETE /api/config/agents/${params.id} error:`, error);
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : 'Failed to delete agent' },
      { status: 500 }
    );
  }
}