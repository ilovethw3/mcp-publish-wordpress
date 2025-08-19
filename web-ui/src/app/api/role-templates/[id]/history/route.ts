import { NextRequest, NextResponse } from 'next/server';
import { getRoleTemplateHistory } from '@/lib/database/role-templates';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const history = await getRoleTemplateHistory(params.id);
    
    return NextResponse.json({ 
      success: true, 
      data: { history } 
    });
  } catch (error) {
    console.error('Failed to get role template history:', error);
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}