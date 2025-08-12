/**
 * WordPress Connection Test API Route
 */

import { NextRequest, NextResponse } from 'next/server';

interface WordPressConfig {
  api_url: string;
  username: string;
  app_password: string;
}

// Test WordPress connection
async function testWordPressConnection(config: WordPressConfig): Promise<boolean> {
  try {
    const auth = Buffer.from(`${config.username}:${config.app_password}`).toString('base64');
    const response = await fetch(`${config.api_url}/users/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Basic ${auth}`,
        'Content-Type': 'application/json',
      },
    });
    return response.ok;
  } catch (error) {
    console.error('WordPress connection test failed:', error);
    return false;
  }
}

// POST: Test WordPress connection
export async function POST(request: NextRequest) {
  try {
    const config = await request.json() as WordPressConfig;
    
    // Validate input
    if (!config.api_url || !config.username || !config.app_password) {
      return NextResponse.json(
        { success: false, error: 'Missing required connection parameters' },
        { status: 400 }
      );
    }

    const connectionOk = await testWordPressConnection(config);

    return NextResponse.json({
      success: connectionOk,
      data: {
        connection_status: connectionOk ? 'success' : 'failed',
        tested_at: new Date().toISOString(),
        api_url: config.api_url
      },
      message: connectionOk ? 'Connection successful' : 'Connection failed'
    });

  } catch (error) {
    console.error('POST /api/config/sites/test-connection error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to test connection' },
      { status: 500 }
    );
  }
}