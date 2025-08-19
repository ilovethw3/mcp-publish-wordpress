import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

interface LoginRequest {
  username: string;
  password: string;
}

export async function POST(request: NextRequest) {
  try {
    const body: LoginRequest = await request.json();
    
    if (!body.username || !body.password) {
      return NextResponse.json({
        success: false,
        error: '用户名和密码不能为空'
      }, { status: 400 });
    }

    // Call Python user service for authentication
    const result = await authenticateUser(body.username, body.password);
    
    if (result.success) {
      return NextResponse.json({
        success: true,
        data: {
          user: result.user,
          token: result.token
        }
      });
    } else {
      return NextResponse.json({
        success: false,
        error: result.error || '用户名或密码错误'
      }, { status: 401 });
    }
  } catch (error) {
    console.error('Login API error:', error);
    return NextResponse.json({
      success: false,
      error: '服务器内部错误'
    }, { status: 500 });
  }
}

async function authenticateUser(username: string, password: string): Promise<{
  success: boolean;
  user?: any;
  token?: string;
  error?: string;
}> {
  return new Promise((resolve) => {
    const scriptPath = path.join(process.cwd(), '..', 'scripts', 'auth_user.py');
    const pythonPath = path.join(process.cwd(), '..', 'venv_mcp_publish_wordpress', 'bin', 'python');
    const pythonProcess = spawn(pythonPath, [scriptPath, username, password], {
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
          error: '认证失败'
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