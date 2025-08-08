#!/usr/bin/env python3
"""
MCP WordPress 发布平台测试运行器

提供不同类型和级别的测试执行选项。

使用方法:
    python run_tests.py --help
    python run_tests.py --unit          # 只运行单元测试
    python run_tests.py --integration   # 只运行集成测试
    python run_tests.py --coverage      # 运行测试并生成覆盖率报告
    python run_tests.py --all           # 运行所有测试
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description=""):
    """运行命令并处理输出"""
    if description:
        print(f"\n🔄 {description}")
        print("=" * 50)
    
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=True)
        print(result.stdout)
        if result.stderr:
            print(f"警告: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 错误: {e}")
        print(f"标准输出: {e.stdout}")
        print(f"错误输出: {e.stderr}")
        return False


def check_dependencies():
    """检查测试依赖是否已安装"""
    print("🔍 检查测试环境依赖...")
    
    # 检查基础测试包
    test_packages_ok = check_test_packages()
    
    # 检查核心项目依赖
    core_packages_ok = check_core_dependencies()
    
    # 特别检查jose包问题
    jose_ok = diagnose_jose_issue()
    
    all_ok = test_packages_ok and core_packages_ok and jose_ok
    
    if all_ok:
        print("✅ 所有依赖检查通过")
    else:
        print("\n❌ 发现依赖问题，请按照上述建议解决")
    
    return all_ok


def check_test_packages():
    """检查测试相关包"""
    required_packages = [
        "pytest",
        "pytest-cov", 
        "pytest-mock",
        "pytest-asyncio",
        "httpx"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 缺少以下测试依赖:")
        for package in missing_packages:
            print(f"   - {package}")
        print(f"\n💡 修复命令: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ 测试框架依赖正常")
    return True


def check_core_dependencies():
    """检查核心项目依赖"""
    core_packages = {
        "fastapi": "FastAPI web框架",
        "sqlmodel": "SQLModel ORM", 
        "passlib": "密码哈希库",
        "requests": "HTTP客户端",
        "pydantic_settings": "配置管理",
        "markdown": "Markdown处理"
    }
    
    missing_packages = []
    
    for package, description in core_packages.items():
        try:
            __import__(package)
        except ImportError:
            missing_packages.append((package, description))
    
    if missing_packages:
        print("❌ 缺少以下核心依赖:")
        for package, desc in missing_packages:
            print(f"   - {package} ({desc})")
        
        print(f"\n💡 修复命令: pip install -r requirements.txt")
        return False
    
    print("✅ 核心项目依赖正常")
    return True


def diagnose_jose_issue():
    """诊断jose包问题"""
    print("🔍 检查JWT处理库...")
    
    try:
        # 尝试导入python-jose
        from jose import jwt
        print("✅ python-jose导入正常")
        
        # 测试基本JWT功能
        try:
            test_payload = {"test": "data"}
            test_secret = "test-secret"
            token = jwt.encode(test_payload, test_secret, algorithm="HS256")
            decoded = jwt.decode(token, test_secret, algorithms=["HS256"])
            if decoded["test"] == "data":
                print("✅ JWT功能测试正常")
                return True
            else:
                print("❌ JWT功能测试失败")
                return False
        except Exception as e:
            print(f"❌ JWT功能测试失败: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ 无法导入python-jose: {e}")
        print("\n🔧 可能的问题:")
        print("1. 安装了错误的jose包（应该是python-jose）")
        print("2. python-jose版本与Python 3.13不兼容")
        print("3. 缺少cryptography依赖")
        
        print("\n💡 修复建议:")
        print("1. 卸载错误包: pip uninstall jose python-jose -y")
        print("2. 重新安装: pip install python-jose[cryptography]==3.3.0")
        print("3. 如仍有问题，尝试PyJWT: pip install PyJWT[crypto]==2.8.0")
        
        return False
    except Exception as e:
        print(f"❌ jose包检查时发生错误: {e}")
        return False


def run_unit_tests():
    """运行单元测试"""
    cmd = [
        "python", "-m", "pytest", 
        "mcp/tests/",
        "-m", "unit",
        "-v",
        "--tb=short"
    ]
    return run_command(cmd, "运行单元测试")


def run_integration_tests():
    """运行集成测试"""
    cmd = [
        "python", "-m", "pytest",
        "mcp/tests/",
        "-m", "integration", 
        "-v",
        "--tb=short"
    ]
    return run_command(cmd, "运行集成测试")


def run_all_tests():
    """运行所有测试"""
    cmd = [
        "python", "-m", "pytest",
        "mcp/tests/",
        "-v"
    ]
    return run_command(cmd, "运行所有测试")


def run_coverage_tests():
    """运行测试并生成覆盖率报告"""
    cmd = [
        "python", "-m", "pytest",
        "mcp/tests/",
        "--cov=mcp",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--cov-report=term-missing",
        "--cov-fail-under=80",
        "-v"
    ]
    success = run_command(cmd, "运行覆盖率测试")
    
    if success:
        print("\n📊 覆盖率报告已生成:")
        print("   - HTML报告: htmlcov/index.html")
        print("   - XML报告: coverage.xml")
    
    return success


def run_specific_test(test_path):
    """运行特定测试文件或测试函数"""
    cmd = [
        "python", "-m", "pytest",
        test_path,
        "-v",
        "--tb=short"
    ]
    return run_command(cmd, f"运行特定测试: {test_path}")


def run_performance_tests():
    """运行性能测试"""
    cmd = [
        "python", "-m", "pytest",
        "mcp/tests/",
        "-m", "slow",
        "-v",
        "--tb=short"
    ]
    return run_command(cmd, "运行性能测试")


def run_security_tests():
    """运行安全测试"""
    cmd = [
        "python", "-m", "pytest",
        "mcp/tests/test_quality_assurance.py::TestSecurityValidation",
        "-v"
    ]
    return run_command(cmd, "运行安全测试")


def main():
    parser = argparse.ArgumentParser(
        description="MCP WordPress 发布平台测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python run_tests.py --unit                    # 运行单元测试
    python run_tests.py --integration             # 运行集成测试
    python run_tests.py --coverage               # 运行覆盖率测试
    python run_tests.py --all                    # 运行所有测试
    python run_tests.py --file test_auth.py      # 运行特定文件
    python run_tests.py --performance            # 运行性能测试
    python run_tests.py --security               # 运行安全测试
        """
    )
    
    parser.add_argument("--unit", action="store_true", help="运行单元测试")
    parser.add_argument("--integration", action="store_true", help="运行集成测试")
    parser.add_argument("--coverage", action="store_true", help="运行覆盖率测试")
    parser.add_argument("--all", action="store_true", help="运行所有测试")
    parser.add_argument("--performance", action="store_true", help="运行性能测试")
    parser.add_argument("--security", action="store_true", help="运行安全测试")
    parser.add_argument("--file", help="运行特定测试文件")
    parser.add_argument("--check-deps", action="store_true", help="检查测试依赖")
    
    args = parser.parse_args()
    
    # 如果没有提供参数，显示帮助
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    print("🧪 MCP WordPress 发布平台测试运行器")
    print("=" * 50)
    
    # 处理依赖检查
    if args.check_deps:
        # 只检查依赖，显示真实结果，不运行测试
        deps_ok = check_dependencies()
        sys.exit(0 if deps_ok else 1)
    
    # 对于其他命令，在运行测试前检查依赖
    if not check_dependencies():
        sys.exit(1)  # 依赖检查失败，退出
    
    success = True
    
    try:
        if args.unit:
            success &= run_unit_tests()
        
        elif args.integration:
            success &= run_integration_tests()
        
        elif args.coverage:
            success &= run_coverage_tests()
        
        elif args.all:
            success &= run_all_tests()
        
        elif args.performance:
            success &= run_performance_tests()
        
        elif args.security:
            success &= run_security_tests()
        
        elif args.file:
            test_path = f"mcp/tests/{args.file}" if not args.file.startswith("mcp/tests/") else args.file
            success &= run_specific_test(test_path)
        
        # 输出结果摘要
        print("\n" + "=" * 50)
        if success:
            print("✅ 所有测试都通过了！")
            sys.exit(0)
        else:
            print("❌ 一些测试失败了。")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 运行测试时发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()