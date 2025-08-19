import { NextRequest, NextResponse } from 'next/server';
import { getRoleTemplateById, updateRoleTemplate, deleteRoleTemplate } from '@/lib/database/role-templates';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const role = await getRoleTemplateById(params.id);
    
    if (!role) {
      return NextResponse.json(
        { success: false, error: 'Role template not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({ 
      success: true, 
      data: { role } 
    });
  } catch (error) {
    console.error('Failed to get role template:', error);
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json();
    const { name, description, permissions, quota_limits, updated_by } = body;

    const role = await updateRoleTemplate({
      role_id: params.id,
      name,
      description,
      permissions,
      quota_limits,
      updated_by: updated_by || 'webui'
    });

    return NextResponse.json({ 
      success: true, 
      data: { role } 
    });
  } catch (error) {
    console.error('Failed to update role template:', error);
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { searchParams } = new URL(request.url);
    const deleted_by = searchParams.get('deleted_by') || 'webui';

    await deleteRoleTemplate(params.id, deleted_by);

    return NextResponse.json({ 
      success: true, 
      message: 'Role template deleted successfully' 
    });
  } catch (error) {
    console.error('Failed to delete role template:', error);
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}