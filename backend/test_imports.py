"""
测试后端依赖是否已安装
"""
import sys

def test_imports():
    """测试所有必需的依赖"""

    print("=" * 50)
    print("Backend Dependency Check")
    print("=" * 50)

    dependencies = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("sqlalchemy", "SQLAlchemy"),
        ("akshare", "AKShare"),
        ("pandas", "Pandas"),
        ("numpy", "NumPy"),
        ("scipy", "SciPy"),
        ("loguru", "Loguru"),
        ("dotenv", "python-dotenv"),
    ]

    missing = []
    installed = []

    for module, name in dependencies:
        try:
            __import__(module)
            print(f"[OK] {name} - Installed")
            installed.append(name)
        except ImportError:
            print(f"[FAIL] {name} - Not Installed")
            missing.append(name)

    print("=" * 50)
    print(f"Installed: {len(installed)}/{len(dependencies)}")

    if missing:
        print(f"Missing: {', '.join(missing)}")
        print("\nPlease run: pip install -r requirements/base.txt")
        return False
    else:
        print("\n[SUCCESS] All core dependencies are installed!")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
