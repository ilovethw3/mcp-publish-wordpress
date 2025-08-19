import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  is_reviewer?: boolean;
}

export async function GET(request: NextRequest) {
  try {
    // Get query parameters
    const { searchParams } = new URL(request.url);
    const skip = parseInt(searchParams.get('skip') || '0');
    const limit = parseInt(searchParams.get('limit') || '100');
    const search = searchParams.get('search') || '';
    const is_active = searchParams.get('is_active');

    // Call Python service to get users
    const result = await getUsers(skip, limit, search, is_active);
    
    if (result.success) {
      return NextResponse.json({
        success: true,
        data: result.data
      });
    } else {
      return NextResponse.json({
        success: false,
        error: result.error || '获取用户列表失败'
      }, { status: 500 });
    }
  } catch (error) {
    console.error('Get users API error:', error);
    return NextResponse.json({
      success: false,
      error: '服务器内部错误'
    }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body: CreateUserRequest = await request.json();
    
    if (!body.username || !body.email || !body.password) {
      return NextResponse.json({
        success: false,
        error: '用户名、邮箱和密码不能为空'
      }, { status: 400 });
    }

    // Call Python service to create user
    const result = await createUser(body);
    
    if (result.success) {
      return NextResponse.json({
        success: true,
        data: result.user
      });
    } else {
      return NextResponse.json({
        success: false,
        error: result.error || '创建用户失败'
      }, { status: 400 });
    }
  } catch (error) {
    console.error('Create user API error:', error);
    return NextResponse.json({
      success: false,
      error: '服务器内部错误'
    }, { status: 500 });
  }
}

async function getUsers(
  skip: number,
  limit: number,
  search: string,
  is_active: string | null
): Promise<{
  success: boolean;
  data?: any;
  error?: string;
}> {
  return new Promise((resolve) => {
    const scriptPath = path.join(process.cwd(), '..', 'scripts', 'get_users.py');
    const args = [skip.toString(), limit.toString(), search];
    if (is_active !== null) {
      args.push(is_active);
    }
    
    const pythonPath = path.join(process.cwd(), '..', 'venv_mcp_publish_wordpress', 'bin', 'python');
    const pythonProcess = spawn(pythonPath, [scriptPath, ...args], {
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
          error: '获取用户列表失败'
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

async function createUser(userData: CreateUserRequest): Promise<{
  success: boolean;
  user?: any;
  error?: string;
}> {
  return new Promise((resolve) => {
    const scriptPath = path.join(process.cwd(), '..', 'scripts', 'create_user.py');
    const pythonPath = path.join(process.cwd(), '..', 'venv_mcp_publish_wordpress', 'bin', 'python');
    const pythonProcess = spawn(pythonPath, [
      scriptPath,
      userData.username,
      userData.email,
      userData.password,
      userData.is_reviewer ? 'true' : 'false'
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
          error: '创建用户失败'
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