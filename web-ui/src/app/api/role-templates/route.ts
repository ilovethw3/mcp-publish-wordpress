import { NextRequest, NextResponse } from 'next/server';
import { getAllRoleTemplates, createRoleTemplate, validateRoleTemplateData } from '@/lib/database/role-templates';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const includeInactive = searchParams.get('includeInactive') === 'true';
    
    const roles = await getAllRoleTemplates(includeInactive);
    return NextResponse.json({ 
      success: true, 
      data: { roles } 
    });
  } catch (error) {
    console.error('Failed to list role templates:', error);
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { role_id, name, description, permissions, quota_limits, created_by } = body;

    // Validate input
    const errors = validateRoleTemplateData(body);
    if (errors.length > 0) {
      return NextResponse.json(
        { success: false, error: 'Validation failed', details: errors },
        { status: 400 }
      );
    }

    if (!name || !permissions) {
      return NextResponse.json(
        { success: false, error: 'Missing required fields: name, permissions' },
        { status: 400 }
      );
    }

    const role = await createRoleTemplate({
      role_id,
      name,
      description: description || '',
      permissions,
      quota_limits: quota_limits || {},
      created_by: created_by || 'webui'
    });

    return NextResponse.json({ 
      success: true, 
      data: { role },
      message: 'Role template created successfully'
    });
  } catch (error) {
    console.error('Failed to create role template:', error);
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}