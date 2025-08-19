import { NextRequest, NextResponse } from 'next/server';
import { toggleRoleTemplateStatus } from '@/lib/database/role-templates';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { role_id, is_active, updated_by } = body;

    if (!role_id || typeof is_active !== 'boolean') {
      return NextResponse.json(
        { success: false, error: 'Missing required fields: role_id, is_active' },
        { status: 400 }
      );
    }

    await toggleRoleTemplateStatus(
      role_id,
      is_active,
      updated_by || 'webui'
    );

    return NextResponse.json({ 
      success: true, 
      message: `Role template ${is_active ? 'activated' : 'deactivated'} successfully` 
    });
  } catch (error) {
    console.error('Failed to toggle role template status:', error);
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}