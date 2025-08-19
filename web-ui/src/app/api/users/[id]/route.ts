import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

interface UpdateUserRequest {
  username?: string;
  email?: string;
  is_reviewer?: boolean;
  is_active?: boolean;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const userId = parseInt(id);

    if (isNaN(userId)) {
      return NextResponse.json({
        success: false,
        error: '无效的用户ID'
      }, { status: 400 });
    }

    // Call Python service to get user
    const result = await getUser(userId);
    
    if (result.success) {
      return NextResponse.json({
        success: true,
        data: result.user
      });
    } else {
      return NextResponse.json({
        success: false,
        error: result.error || '用户不存在'
      }, { status: 404 });
    }
  } catch (error) {
    console.error('Get user API error:', error);
    return NextResponse.json({
      success: false,
      error: '服务器内部错误'
    }, { status: 500 });
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const userId = parseInt(id);
    const body: UpdateUserRequest = await request.json();

    if (isNaN(userId)) {
      return NextResponse.json({
        success: false,
        error: '无效的用户ID'
      }, { status: 400 });
    }

    // Call Python service to update user
    const result = await updateUser(userId, body);
    
    if (result.success) {
      return NextResponse.json({
        success: true,
        data: result.user
      });
    } else {
      return NextResponse.json({
        success: false,
        error: result.error || '更新用户失败'
      }, { status: 400 });
    }
  } catch (error) {
    console.error('Update user API error:', error);
    return NextResponse.json({
      success: false,
      error: '服务器内部错误'
    }, { status: 500 });
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const userId = parseInt(id);

    if (isNaN(userId)) {
      return NextResponse.json({
        success: false,
        error: '无效的用户ID'
      }, { status: 400 });
    }

    // Call Python service to delete user
    const result = await deleteUser(userId);
    
    if (result.success) {
      return NextResponse.json({
        success: true,
        message: '用户已删除'
      });
    } else {
      return NextResponse.json({
        success: false,
        error: result.error || '删除用户失败'
      }, { status: 400 });
    }
  } catch (error) {
    console.error('Delete user API error:', error);
    return NextResponse.json({
      success: false,
      error: '服务器内部错误'
    }, { status: 500 });
  }
}

async function getUser(userId: number): Promise<{
  success: boolean;
  user?: any;
  error?: string;
}> {
  return new Promise((resolve) => {
    const scriptPath = path.join(process.cwd(), '..', 'scripts', 'get_user.py');
    const pythonPath = path.join(process.cwd(), '..', 'venv_mcp_publish_wordpress', 'bin', 'python');
    const pythonProcess = spawn(pythonPath, [scriptPath, userId.toString()], {
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
          error: '获取用户失败'
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

async function updateUser(userId: number, updateData: UpdateUserRequest): Promise<{
  success: boolean;
  user?: any;
  error?: string;
}> {
  return new Promise((resolve) => {
    const scriptPath = path.join(process.cwd(), '..', 'scripts', 'update_user.py');
    const pythonPath = path.join(process.cwd(), '..', 'venv_mcp_publish_wordpress', 'bin', 'python');
    const pythonProcess = spawn(pythonPath, [
      scriptPath,
      userId.toString(),
      JSON.stringify(updateData)
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
          error: '更新用户失败'
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

async function deleteUser(userId: number): Promise<{
  success: boolean;
  error?: string;
}> {
  return new Promise((resolve) => {
    const scriptPath = path.join(process.cwd(), '..', 'scripts', 'delete_user.py');
    const pythonPath = path.join(process.cwd(), '..', 'venv_mcp_publish_wordpress', 'bin', 'python');
    const pythonProcess = spawn(pythonPath, [scriptPath, userId.toString()], {
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
          error: '删除用户失败'
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