import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

interface ChangePasswordRequest {
  new_password: string;
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const userId = parseInt(id);
    const body: ChangePasswordRequest = await request.json();

    if (isNaN(userId)) {
      return NextResponse.json({
        success: false,
        error: '无效的用户ID'
      }, { status: 400 });
    }

    if (!body.new_password) {
      return NextResponse.json({
        success: false,
        error: '新密码不能为空'
      }, { status: 400 });
    }

    // Call Python service to change password
    const result = await changePassword(userId, body.new_password);
    
    if (result.success) {
      return NextResponse.json({
        success: true,
        message: '密码修改成功'
      });
    } else {
      return NextResponse.json({
        success: false,
        error: result.error || '密码修改失败'
      }, { status: 400 });
    }
  } catch (error) {
    console.error('Change password API error:', error);
    return NextResponse.json({
      success: false,
      error: '服务器内部错误'
    }, { status: 500 });
  }
}

async function changePassword(userId: number, newPassword: string): Promise<{
  success: boolean;
  error?: string;
}> {
  return new Promise((resolve) => {
    const scriptPath = path.join(process.cwd(), '..', 'scripts', 'change_password.py');
    const pythonPath = path.join(process.cwd(), '..', 'venv_mcp_publish_wordpress', 'bin', 'python');
    const pythonProcess = spawn(pythonPath, [
      scriptPath,
      userId.toString(),
      newPassword
    ], {
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
          error: '密码修改失败'
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