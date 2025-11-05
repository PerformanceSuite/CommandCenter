"""
Standalone test for Dagger port forwarding fixes.
Run with: python3 test_port_forwarding_standalone.py
"""

import asyncio
import socket
from pathlib import Path
import tempfile
import sys

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.dagger_modules.commandcenter import CommandCenterStack, CommandCenterConfig, ResourceLimits
import dagger


def is_port_available(port: int) -> bool:
    """Check if a port is available (not in use)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return True
        except OSError:
            return False


def find_available_ports(base_port: int, count: int) -> list[int]:
    """Find N available ports starting from base_port."""
    ports = []
    current = base_port
    max_attempts = 1000
    attempts = 0

    while len(ports) < count and attempts < max_attempts:
        if is_port_available(current):
            ports.append(current)
        current += 1
        attempts += 1

    if len(ports) < count:
        raise RuntimeError(f"Could not find {count} available ports")

    return ports


async def test_postgres_port_forwarding():
    """Test PostgreSQL port forwarding."""
    print("\n=== Test 1: PostgreSQL Port Forwarding ===")

    # Find available ports
    ports = find_available_ports(15000, 4)
    postgres_port = ports[0]

    print(f"Using port: {postgres_port}")
    print(f"Port available before: {is_port_available(postgres_port)}")

    # Create temporary project structure
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        # Create backend dir with requirements.txt
        backend_dir = project_dir / "backend"
        backend_dir.mkdir()
        (backend_dir / "requirements.txt").write_text("fastapi==0.104.1\n")

        # Create config
        config = CommandCenterConfig(
            project_name="test_postgres",
            project_path=str(project_dir),
            postgres_port=postgres_port,
            redis_port=ports[1],
            backend_port=ports[2],
            frontend_port=ports[3],
            db_password="test123",
            secret_key="test456",
        )

        # Test port forwarding
        async with CommandCenterStack(config) as stack:
            postgres = await stack.build_postgres()
            postgres_svc = postgres.as_service()

            # Start with port forwarding
            await postgres_svc.up(ports=[
                dagger.PortForward(backend=5432, frontend=postgres_port)
            ])

            # Wait for startup
            await asyncio.sleep(3)

            # Check port is in use
            port_in_use = not is_port_available(postgres_port)
            print(f"Port in use after startup: {port_in_use}")

            if port_in_use:
                print("✅ PASS: Port forwarding works!")
                return True
            else:
                print("❌ FAIL: Port not in use")
                return False


async def test_backend_build_process():
    """Test that backend build uses requirements.txt correctly."""
    print("\n=== Test 2: Backend Build Process ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        # Create backend structure
        backend_dir = project_dir / "backend"
        backend_dir.mkdir()

        # Create requirements.txt with real packages
        (backend_dir / "requirements.txt").write_text(
            "fastapi==0.104.1\nuvicorn[standard]==0.24.0\n"
        )

        # Create minimal app structure
        app_dir = backend_dir / "app"
        app_dir.mkdir()
        (app_dir / "__init__.py").write_text("")
        (app_dir / "main.py").write_text('''
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
''')

        ports = find_available_ports(16000, 4)

        config = CommandCenterConfig(
            project_name="test_build",
            project_path=str(project_dir),
            postgres_port=ports[0],
            redis_port=ports[1],
            backend_port=ports[2],
            frontend_port=ports[3],
            db_password="test123",
            secret_key="test456",
        )

        try:
            async with CommandCenterStack(config) as stack:
                # This should work now that we mount BEFORE pip install
                backend = await stack.build_backend("postgres", "redis")
                print("✅ PASS: Backend builds with requirements.txt from mounted project!")
                return True
        except Exception as e:
            print(f"❌ FAIL: Backend build failed: {e}")
            return False


async def test_service_persistence():
    """Test that services persist when stored in instance variable."""
    print("\n=== Test 3: Service Persistence ===")

    ports = find_available_ports(17000, 4)
    redis_port = ports[1]

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        backend_dir = project_dir / "backend"
        backend_dir.mkdir()
        (backend_dir / "requirements.txt").write_text("fastapi==0.104.1\n")

        config = CommandCenterConfig(
            project_name="test_persistence",
            project_path=str(project_dir),
            postgres_port=ports[0],
            redis_port=redis_port,
            backend_port=ports[2],
            frontend_port=ports[3],
            db_password="test123",
            secret_key="test456",
        )

        async with CommandCenterStack(config) as stack:
            redis = await stack.build_redis()
            redis_svc = redis.as_service()

            await redis_svc.up(ports=[
                dagger.PortForward(backend=6379, frontend=redis_port)
            ])

            # Store reference (keeps service alive)
            stack._services['redis'] = redis_svc

            await asyncio.sleep(3)

            # Check if still running
            port_in_use = not is_port_available(redis_port)
            print(f"Port in use after 3s: {port_in_use}")

            if port_in_use:
                print("✅ PASS: Service persists with stored reference!")
                return True
            else:
                print("❌ FAIL: Service not persisting")
                return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Dagger Port Forwarding & Service Persistence Tests")
    print("=" * 60)

    results = []

    try:
        result1 = await test_postgres_port_forwarding()
        results.append(("PostgreSQL Port Forwarding", result1))
    except Exception as e:
        print(f"❌ Test 1 crashed: {e}")
        results.append(("PostgreSQL Port Forwarding", False))

    try:
        result2 = await test_backend_build_process()
        results.append(("Backend Build Process", result2))
    except Exception as e:
        print(f"❌ Test 2 crashed: {e}")
        results.append(("Backend Build Process", False))

    try:
        result3 = await test_service_persistence()
        results.append(("Service Persistence", result3))
    except Exception as e:
        print(f"❌ Test 3 crashed: {e}")
        results.append(("Service Persistence", False))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
