import { NextRequest, NextResponse } from 'next/server';
import { applyRoleToAgent } from '@/lib/database/role-templates';

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json();
    const { agent_ids, permissions_override } = body;

    if (!agent_ids || !Array.isArray(agent_ids) || agent_ids.length === 0) {
      return NextResponse.json(
        { success: false, error: 'Missing required field: agent_ids (array)' },
        { status: 400 }
      );
    }

    const results = [];
    for (const agent_id of agent_ids) {
      try {
        await applyRoleToAgent(
          agent_id,
          params.id,
          permissions_override || {}
        );
        results.push({ agent_id, success: true });
      } catch (error) {
        results.push({ agent_id, success: false, error: error.message });
      }
    }

    const successful = results.filter(r => r.success).length;
    const failed = results.filter(r => !r.success).length;

    return NextResponse.json({ 
      success: true, 
      data: { 
        results,
        summary: {
          total: agent_ids.length,
          successful,
          failed
        }
      },
      message: `Role applied to ${successful} agent(s). ${failed} failed.`
    });
  } catch (error) {
    console.error('Failed to apply role template:', error);
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}