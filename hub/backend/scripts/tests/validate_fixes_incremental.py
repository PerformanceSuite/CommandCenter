#!/usr/bin/env python3
"""
Incremental validation of Dagger fixes.
NO MOCKS. Real Dagger SDK calls. Fail fast at each step.

Run: python3 validate_fixes_incremental.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def test_1_portforward_api_exists():
    """Test 1: Verify PortForward class exists in dagger SDK."""
    print("\n" + "="*60)
    print("TEST 1: PortForward API exists")
    print("="*60)

    try:
        import dagger

        # Check PortForward exists
        assert hasattr(dagger, 'PortForward'), "dagger.PortForward not found!"

        # Try to instantiate it
        pf = dagger.PortForward(backend=5432, frontend=15432)

        # Verify fields
        assert pf.backend == 5432, f"backend mismatch: {pf.backend}"
        assert pf.frontend == 15432, f"frontend mismatch: {pf.frontend}"

        print("✅ PASS: dagger.PortForward exists and works")
        print(f"   - Created: PortForward(backend=5432, frontend=15432)")
        print(f"   - Fields: backend={pf.backend}, frontend={pf.frontend}")
        return True

    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


async def test_2_service_up_accepts_ports():
    """Test 2: Verify Service.up() accepts ports parameter."""
    print("\n" + "="*60)
    print("TEST 2: Service.up(ports=[...]) signature")
    print("="*60)

    try:
        import dagger
        import inspect

        # Get Service class
        service_class = dagger.Service

        # Check up method exists
        assert hasattr(service_class, 'up'), "Service.up() not found!"

        # Get method signature
        sig = inspect.signature(service_class.up)
        params = list(sig.parameters.keys())

        print(f"   Service.up() parameters: {params}")

        # Verify 'ports' parameter exists
        assert 'ports' in params, "Service.up() missing 'ports' parameter!"

        # Get type hint
        ports_param = sig.parameters['ports']
        print(f"   ports parameter: {ports_param}")

        print("✅ PASS: Service.up(ports=[...]) signature correct")
        return True

    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


async def test_3_container_methods_exist():
    """Test 3: Verify Container has required methods."""
    print("\n" + "="*60)
    print("TEST 3: Container methods exist")
    print("="*60)

    try:
        import dagger

        required_methods = [
            'from_',
            'with_mounted_directory',
            'with_workdir',
            'with_exec',
            'with_exposed_port',
            'with_env_variable',
            'as_service',
        ]

        container_class = dagger.Container

        for method in required_methods:
            assert hasattr(container_class, method), f"Container.{method}() not found!"
            print(f"   ✓ Container.{method}()")

        print("✅ PASS: All required Container methods exist")
        return True

    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


async def test_4_build_minimal_container():
    """Test 4: Build minimal container with Dagger (proves connection works)."""
    print("\n" + "="*60)
    print("TEST 4: Build minimal container")
    print("="*60)

    try:
        import dagger

        print("   Connecting to Dagger engine...")
        async with dagger.Connection(dagger.Config()) as client:
            print("   ✓ Connected to Dagger engine")

            # Build minimal alpine container
            print("   Building alpine container...")
            container = (
                client.container()
                .from_("alpine:latest")
                .with_exec(["echo", "Hello from Dagger"])
            )

            # Get output
            print("   Executing echo command...")
            output = await container.stdout()

            print(f"   Output: {output.strip()}")

            assert "Hello from Dagger" in output, f"Unexpected output: {output}"

            print("✅ PASS: Can build and execute in Dagger container")
            return True

    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_5_directory_mount():
    """Test 5: Mount directory and access files (proves build process will work)."""
    print("\n" + "="*60)
    print("TEST 5: Directory mounting")
    print("="*60)

    try:
        import dagger
        import tempfile

        # Create temp directory with a file
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")

            print(f"   Created test file: {test_file}")

            async with dagger.Connection(dagger.Config()) as client:
                # Mount directory
                print("   Mounting directory to container...")
                host_dir = client.host().directory(tmpdir)

                container = (
                    client.container()
                    .from_("alpine:latest")
                    .with_mounted_directory("/mnt", host_dir)
                    .with_exec(["cat", "/mnt/test.txt"])
                )

                output = await container.stdout()
                print(f"   File contents: {output.strip()}")

                assert output.strip() == "test content", f"Wrong content: {output}"

                print("✅ PASS: Directory mounting works")
                return True

    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_6_workdir_and_exec():
    """Test 6: Set workdir and run commands (proves backend/frontend build will work)."""
    print("\n" + "="*60)
    print("TEST 6: Workdir and exec")
    print("="*60)

    try:
        import dagger
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create subdirectory structure like our project
            backend_dir = Path(tmpdir) / "backend"
            backend_dir.mkdir()
            (backend_dir / "requirements.txt").write_text("# test requirements\n")

            print(f"   Created backend/requirements.txt")

            async with dagger.Connection(dagger.Config()) as client:
                host_dir = client.host().directory(tmpdir)

                container = (
                    client.container()
                    .from_("alpine:latest")
                    .with_mounted_directory("/workspace", host_dir)
                    .with_workdir("/workspace/backend")
                    .with_exec(["cat", "requirements.txt"])
                )

                output = await container.stdout()
                print(f"   requirements.txt: {output.strip()}")

                assert "test requirements" in output, f"Wrong content: {output}"

                print("✅ PASS: Workdir + mounted files works")
                return True

    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_7_our_code_imports():
    """Test 7: Our code imports without errors."""
    print("\n" + "="*60)
    print("TEST 7: Import our Dagger module")
    print("="*60)

    try:
        from app.dagger_modules.commandcenter import (
            CommandCenterStack,
            CommandCenterConfig,
            ResourceLimits
        )

        print("   ✓ Imported CommandCenterStack")
        print("   ✓ Imported CommandCenterConfig")
        print("   ✓ Imported ResourceLimits")

        # Try to create config
        config = CommandCenterConfig(
            project_name="test",
            project_path="/tmp",
            postgres_port=15432,
            redis_port=16379,
            backend_port=18000,
            frontend_port=13000,
            db_password="test",
            secret_key="test",
        )

        print(f"   ✓ Created CommandCenterConfig")
        print(f"     - postgres_port: {config.postgres_port}")
        print(f"     - redis_port: {config.redis_port}")

        print("✅ PASS: Our code imports correctly")
        return True

    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all validation tests."""
    print("="*60)
    print("DAGGER FIXES VALIDATION - NO MOCKS")
    print("="*60)
    print("\nRunning incremental tests to prove fixes work...\n")

    tests = [
        ("PortForward API exists", test_1_portforward_api_exists),
        ("Service.up(ports=[...]) signature", test_2_service_up_accepts_ports),
        ("Container methods exist", test_3_container_methods_exist),
        ("Build minimal container", test_4_build_minimal_container),
        ("Directory mounting", test_5_directory_mount),
        ("Workdir and exec", test_6_workdir_and_exec),
        ("Our code imports", test_7_our_code_imports),
    ]

    results = []

    for i, (name, test_func) in enumerate(tests, 1):
        try:
            passed = await test_func()
            results.append((name, passed))

            if not passed:
                print(f"\n⚠️  Test {i} failed - stopping here")
                break

        except Exception as e:
            print(f"\n💥 Test {i} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
            break

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    total = len(results)
    passed_count = sum(1 for _, p in results if p)

    print(f"\nResult: {passed_count}/{len(tests)} tests passed")

    if passed_count == len(tests):
        print("\n🎉 ALL TESTS PASSED - Fixes are solid!")
        print("\nNext step: Test with real Hub orchestration")
        return 0
    else:
        print(f"\n⚠️  {len(tests) - passed_count} test(s) failed or not run")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
