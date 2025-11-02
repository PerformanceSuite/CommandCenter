"""
Tests for dependency parsers
"""
import pytest

from app.schemas.project_analysis import DependencyType
from app.services.parsers.cargo_toml_parser import CargoTomlParser
from app.services.parsers.go_mod_parser import GoModParser
from app.services.parsers.package_json_parser import PackageJsonParser
from app.services.parsers.requirements_parser import RequirementsParser


@pytest.mark.asyncio
async def test_package_json_parser(sample_package_json):
    """Test Node.js package.json parser"""
    parser = PackageJsonParser()

    # Check can_parse
    assert parser.can_parse(sample_package_json)

    # Parse dependencies
    dependencies = await parser.parse(sample_package_json)

    # Verify counts
    assert len(dependencies) == 5  # 3 runtime + 2 dev

    # Check specific dependencies
    react_dep = next(d for d in dependencies if d.name == "react")
    assert react_dep.version == "18.2.0"
    assert react_dep.type == DependencyType.RUNTIME
    assert react_dep.language == "javascript"
    assert react_dep.confidence == 1.0

    jest_dep = next(d for d in dependencies if d.name == "jest")
    assert jest_dep.version == "29.0.0"
    assert jest_dep.type == DependencyType.DEV


@pytest.mark.asyncio
async def test_package_json_parser_version_cleaning():
    """Test version cleaning logic"""
    parser = PackageJsonParser()

    # Test various semver operators
    assert parser._clean_version("^18.2.0") == "18.2.0"
    assert parser._clean_version("~1.4.0") == "1.4.0"
    assert parser._clean_version(">=29.0.0") == "29.0.0"
    assert parser._clean_version("^8.0.0") == "8.0.0"


@pytest.mark.asyncio
async def test_requirements_parser(sample_requirements_txt):
    """Test Python requirements.txt parser"""
    parser = RequirementsParser()

    # Check can_parse
    assert parser.can_parse(sample_requirements_txt)

    # Parse dependencies
    dependencies = await parser.parse(sample_requirements_txt)

    # Verify counts (should find fastapi, uvicorn, sqlalchemy, pydantic, pytest)
    assert len(dependencies) >= 5

    # Check specific dependencies
    fastapi_dep = next(d for d in dependencies if d.name == "fastapi")
    assert fastapi_dep.version == "0.109.0"
    assert fastapi_dep.type == DependencyType.RUNTIME
    assert fastapi_dep.language == "python"

    pytest_dep = next(d for d in dependencies if d.name == "pytest")
    assert pytest_dep.version == "7.4.0"
    assert pytest_dep.type == DependencyType.RUNTIME  # from requirements.txt


@pytest.mark.asyncio
async def test_go_mod_parser(sample_go_mod):
    """Test Go modules parser"""
    parser = GoModParser()

    # Check can_parse
    assert parser.can_parse(sample_go_mod)

    # Parse dependencies
    dependencies = await parser.parse(sample_go_mod)

    # Verify counts
    assert len(dependencies) == 3

    # Check specific dependencies
    gin_dep = next(d for d in dependencies if "gin-gonic/gin" in d.name)
    assert gin_dep.version == "1.9.1"
    assert gin_dep.type == DependencyType.RUNTIME
    assert gin_dep.language == "go"


@pytest.mark.asyncio
async def test_cargo_toml_parser(sample_cargo_toml):
    """Test Rust Cargo.toml parser"""
    parser = CargoTomlParser()

    # Check can_parse
    assert parser.can_parse(sample_cargo_toml)

    # Parse dependencies
    dependencies = await parser.parse(sample_cargo_toml)

    # Verify counts (3 runtime + 1 dev)
    assert len(dependencies) == 4

    # Check specific dependencies
    tokio_dep = next(d for d in dependencies if d.name == "tokio")
    assert tokio_dep.version == "1.32.0"
    assert tokio_dep.type == DependencyType.RUNTIME
    assert tokio_dep.language == "rust"

    criterion_dep = next(d for d in dependencies if d.name == "criterion")
    assert criterion_dep.type == DependencyType.DEV


@pytest.mark.asyncio
async def test_parser_cannot_parse_wrong_files(tmp_path):
    """Test that parsers correctly identify when they can't parse"""
    # Create a project with only Python files
    (tmp_path / "requirements.txt").write_text("fastapi==0.109.0")

    npm_parser = PackageJsonParser()
    go_parser = GoModParser()

    # npm parser should not be able to parse this project
    assert not npm_parser.can_parse(tmp_path)
    assert not go_parser.can_parse(tmp_path)

    # Python parser should be able to parse
    python_parser = RequirementsParser()
    assert python_parser.can_parse(tmp_path)


@pytest.mark.asyncio
async def test_parser_handles_malformed_files(tmp_path):
    """Test parser error handling with malformed files"""
    # Create malformed package.json
    malformed = tmp_path / "package.json"
    malformed.write_text("{ invalid json")

    parser = PackageJsonParser()

    # Should raise JSONDecodeError
    with pytest.raises(Exception):
        await parser.parse(tmp_path)
