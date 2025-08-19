import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get('authorization');
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json({
        success: false,
        error: '缺少认证token'
      }, { status: 401 });
    }

    const token = authHeader.substring(7);
    
    // Call Python service to refresh token
    const result = await refreshToken(token);
    
    if (result.success) {
      return NextResponse.json({
        success: true,
        data: {
          token: result.token
        }
      });
    } else {
      return NextResponse.json({
        success: false,
        error: result.error || 'Token刷新失败'
      }, { status: 401 });
    }
  } catch (error) {
    console.error('Refresh token API error:', error);
    return NextResponse.json({
      success: false,
      error: '服务器内部错误'
    }, { status: 500 });
  }
}

async function refreshToken(token: string): Promise<{
  success: boolean;
  token?: string;
  error?: string;
}> {
  return new Promise((resolve) => {
    const scriptPath = path.join(process.cwd(), '..', 'scripts', 'refresh_token.py');
    const pythonPath = path.join(process.cwd(), '..', 'venv_mcp_publish_wordpress', 'bin', 'python');
    const pythonProcess = spawn(pythonPath, [scriptPath, token], {
      cwd: path.join(process.cwd(), '..')
    });

    let output = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code === 0) {
        try {
          // Extract JSON from mixed output (logging + JSON)
          const trimmedOutput = output.trim();
          const jsonStart = trimmedOutput.indexOf('{"success"');
          
          if (jsonStart === -1) {
            throw new Error('No JSON found in output');
          }
          
          const jsonString = trimmedOutput.substring(jsonStart);
          const result = JSON.parse(jsonString);
          resolve(result);
        } catch (error) {
          console.error('JSON parse error:', error);
          resolve({
            success: false,
            error: '解析响应失败'
          });
        }
      } else {
        console.error('Python script error:', errorOutput);
        resolve({
          success: false,
          error: 'Token刷新失败'
        });
      }
    });

    pythonProcess.on('error', (error) => {
      console.error('Failed to start Python process:', error);
      resolve({
        success: false,
        error: '服务器错误'
      });
    });
  });
}