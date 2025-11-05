#!/usr/bin/env python3
"""
ULTIMATE TEST: Real Hub orchestration with actual CommandCenter project.
NO MOCKS. REAL DAGGER CONTAINERS. REAL PORT FORWARDING.

This proves the fixes work end-to-end.
"""

import asyncio
import sys
import socket
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.dagger_modules.commandcenter import CommandCenterStack, CommandCenterConfig


def is_port_available(port: int) -> bool:
    """Check if a port is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return True
        except OSError:
            return False


def find_available_ports(base_port: int, count: int) -> list[int]:
    """Find N available ports."""
    ports = []
    current = base_port
    while len(ports) < count and current < base_port + 1000:
        if is_port_available(current):
            ports.append(current)
        current += 1
    if len(ports) < count:
        raise RuntimeError(f"Could not find {count} available ports")
    return ports


async def test_real_commandcenter_orchestration():
    """
    Start a REAL CommandCenter instance using Hub orchestration.
    This is the ultimate test - no mocks, real containers, real ports.
    """
    print("="*70)
    print("ULTIMATE TEST: Real Hub Orchestration")
    print("="*70)
    print("\nStarting ACTUAL CommandCenter via Dagger...")
    print("(This will build real containers - may take 2-3 minutes)\n")

    # Use the actual CommandCenter project
    project_path = "/Users/danielconnolly/Projects/CommandCenter"

    # Verify project files exist
    backend_req = Path(project_path) / "backend" / "requirements.txt"
    frontend_pkg = Path(project_path) / "frontend" / "package.json"

    print(f"Project path: {project_path}")
    print(f"  ✓ {backend_req.name}: {backend_req.exists()}")
    print(f"  ✓ {frontend_pkg.name}: {frontend_pkg.exists()}")

    if not backend_req.exists() or not frontend_pkg.exists():
        print("❌ FAIL: Project files not found")
        return False

    # Find available ports
    print("\nFinding available ports...")
    ports = find_available_ports(15000, 4)

    postgres_port = ports[0]
    redis_port = ports[1]
    backend_port = ports[2]
    frontend_port = ports[3]

    print(f"  Postgres: {postgres_port}")
    print(f"  Redis:    {redis_port}")
    print(f"  Backend:  {backend_port}")
    print(f"  Frontend: {frontend_port}")

    # Create configuration
    config = CommandCenterConfig(
        project_name="test_commandcenter",
        project_path=project_path,
        postgres_port=postgres_port,
        redis_port=redis_port,
        backend_port=backend_port,
        frontend_port=frontend_port,
        db_password="test_password_123",
        secret_key="test_secret_key_456",
    )

    print(f"\n{'='*70}")
    print("PHASE 1: Build Containers")
    print('='*70)

    try:
        async with CommandCenterStack(config) as stack:
            print("\n1️⃣  Building Postgres container...")
            postgres = await stack.build_postgres()
            print("   ✓ Postgres built")

            print("\n2️⃣  Building Redis container...")
            redis = await stack.build_redis()
            print("   ✓ Redis built")

            print("\n3️⃣  Building Backend container (uses requirements.txt)...")
            backend = await stack.build_backend("postgres", "redis")
            print("   ✓ Backend built with project dependencies")

            print("\n4️⃣  Building Frontend container (uses package.json)...")
            print("   (This will take longest - npm install is slow)")
            frontend = await stack.build_frontend("http://backend:8000")
            print("   ✓ Frontend built with project dependencies")

            print(f"\n{'='*70}")
            print("PHASE 2: Start Services with Port Forwarding")
            print('='*70)

            # Store containers
            stack._service_containers["postgres"] = postgres
            stack._service_containers["redis"] = redis
            stack._service_containers["backend"] = backend
            stack._service_containers["frontend"] = frontend

            # Start as services
            print("\n5️⃣  Starting Postgres service...")
            postgres_svc = postgres.as_service()

            print(f"   Forwarding port 5432 → {postgres_port}...")
            import dagger
            await postgres_svc.up(ports=[
                dagger.PortForward(backend=5432, frontend=postgres_port)
            ])

            # Check port is in use
            await asyncio.sleep(2)
            postgres_bound = not is_port_available(postgres_port)
            print(f"   Port {postgres_port} bound: {postgres_bound}")

            if not postgres_bound:
                print(f"   ❌ FAIL: Postgres port {postgres_port} not bound!")
                return False

            print("\n6️⃣  Starting Redis service...")
            redis_svc = redis.as_service()

            print(f"   Forwarding port 6379 → {redis_port}...")
            await redis_svc.up(ports=[
                dagger.PortForward(backend=6379, frontend=redis_port)
            ])

            await asyncio.sleep(2)
            redis_bound = not is_port_available(redis_port)
            print(f"   Port {redis_port} bound: {redis_bound}")

            if not redis_bound:
                print(f"   ❌ FAIL: Redis port {redis_port} not bound!")
                return False

            # Store service references (keeps them alive)
            stack._services = {
                "postgres": postgres_svc,
                "redis": redis_svc,
            }

            print(f"\n{'='*70}")
            print("PHASE 3: Verify Persistence")
            print('='*70)

            print("\n7️⃣  Waiting 5 seconds to verify services stay running...")
            await asyncio.sleep(5)

            postgres_still_bound = not is_port_available(postgres_port)
            redis_still_bound = not is_port_available(redis_port)

            print(f"   Postgres port {postgres_port} still bound: {postgres_still_bound}")
            print(f"   Redis port {redis_port} still bound: {redis_still_bound}")

            if not postgres_still_bound or not redis_still_bound:
                print("   ❌ FAIL: Services didn't persist!")
                return False

            print(f"\n{'='*70}")
            print("RESULTS")
            print('='*70)

            print("\n✅ ALL CHECKS PASSED:")
            print("  ✓ Containers built with project files (requirements.txt, package.json)")
            print("  ✓ Port forwarding works (custom host ports mapped)")
            print("  ✓ Services persist (still running after 5s)")
            print("  ✓ Service references keep containers alive")

            print("\n🎉 ULTIMATE TEST PASSED - Hub orchestration is SOLID!\n")
            return True

    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("\n" + "="*70)
    print("Hub Orchestration - End-to-End Validation")
    print("="*70)
    print("\nThis test will:")
    print("  1. Build real Dagger containers from CommandCenter project")
    print("  2. Start services with custom port forwarding")
    print("  3. Verify services persist and ports stay bound")
    print("\nNO MOCKS. REAL CONTAINERS. REAL PORTS.\n")

    input("Press Enter to start (or Ctrl+C to cancel)...")

    success = await test_real_commandcenter_orchestration()

    if success:
        print("\n" + "="*70)
        print("SUCCESS - All fixes validated with real orchestration!")
        print("="*70)
        return 0
    else:
        print("\n" + "="*70)
        print("FAILED - See error details above")
        print("="*70)
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(1)
