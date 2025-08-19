import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    // For JWT tokens, logout is typically handled on the client side
    // by removing the token from storage. No server-side action needed.
    
    return NextResponse.json({
      success: true,
      message: '退出登录成功'
    });
  } catch (error) {
    console.error('Logout API error:', error);
    return NextResponse.json({
      success: false,
      error: '服务器内部错误'
    }, { status: 500 });
  }
}