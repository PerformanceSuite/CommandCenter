#!/usr/bin/env python3.12
"""
Test script to start CommandCenter via Dagger orchestration
"""
import asyncio
import sys
sys.path.insert(0, 'hub/backend')

from app.dagger_modules.commandcenter import CommandCenterConfig, CommandCenterStack


async def main():
    """Start CommandCenter stack with Dagger"""
    print("=" * 60)
    print("DAGGER ORCHESTRATION TEST")
    print("=" * 60)

    # Create configuration
    config = CommandCenterConfig(
        project_name="commandcenter-test",
        project_path="/Users/danielconnolly/Projects/CommandCenter",
        backend_port=8010,
        frontend_port=3010,
        postgres_port=5442,
        redis_port=6389,
        db_password="test_password_123",
        secret_key="test_secret_key_32_chars_long!"
    )

    print(f"\n📋 Configuration:")
    print(f"   Project: {config.project_name}")
    print(f"   Path: {config.project_path}")
    print(f"   Ports: Backend={config.backend_port}, Frontend={config.frontend_port}")
    print(f"          Postgres={config.postgres_port}, Redis={config.redis_port}")

    # Create stack
    print(f"\n🔧 Creating Dagger stack...")
    async with CommandCenterStack(config) as stack:
        print(f"   ✅ Dagger client initialized")

        # Start services
        print(f"\n🚀 Starting services...")
        result = await stack.start()

        print(f"\n✅ Services started successfully!")
        print(f"\n📊 Result:")
        for key, value in result.items():
            print(f"   {key}: {value}")

        print(f"\n🔍 Checking if ports are bound...")
        import subprocess
        for port in [config.backend_port, config.frontend_port, config.postgres_port, config.redis_port]:
            try:
                output = subprocess.check_output(["lsof", "-i", f":{port}"], stderr=subprocess.STDOUT, text=True)
                print(f"   ✅ Port {port}: LISTENING")
            except subprocess.CalledProcessError:
                print(f"   ❌ Port {port}: NOT BOUND")

        print(f"\n⏳ Services running. Press Ctrl+C to stop...")
        try:
            # Keep running until interrupted
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print(f"\n\n🛑 Stopping services...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
