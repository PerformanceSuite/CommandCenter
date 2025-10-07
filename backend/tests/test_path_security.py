"""
Tests for Path Security Utilities

Tests for path traversal prevention
"""

import pytest
from pathlib import Path
import tempfile
import os

from app.utils.path_security import PathValidator


class TestPathValidation:
    """Test suite for path validation"""

    def test_valid_relative_path(self):
        """Test valid relative path validation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            safe_subdir = base / "safe"
            safe_subdir.mkdir()

            result = PathValidator.validate_path("safe", base)
            assert result == safe_subdir

    def test_valid_absolute_path_within_base(self):
        """Test valid absolute path within base directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            safe_file = base / "file.txt"
            safe_file.touch()

            result = PathValidator.validate_path(str(safe_file), base, must_exist=True)
            assert result == safe_file

    def test_prevent_parent_traversal(self):
        """Test prevention of parent directory traversal"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            with pytest.raises(ValueError, match="Path traversal blocked"):
                PathValidator.validate_path("../etc/passwd", base)

    def test_prevent_absolute_path_outside_base(self):
        """Test prevention of absolute path outside base"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            with pytest.raises(ValueError, match="Path traversal blocked"):
                PathValidator.validate_path("/etc/passwd", base)

    def test_prevent_complex_traversal(self):
        """Test prevention of complex traversal attempts"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            traversal_attempts = [
                "subdir/../../etc/passwd",
                "./../../etc/passwd",
                "safe/../../../etc/passwd",
                "a/b/c/../../../../../../../etc/passwd",
            ]

            for attempt in traversal_attempts:
                with pytest.raises(ValueError, match="Path traversal blocked"):
                    PathValidator.validate_path(attempt, base)

    def test_symlink_traversal_prevention(self):
        """Test prevention of symlink-based traversal"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            # Create symlink pointing outside base
            link = base / "malicious_link"
            try:
                link.symlink_to("/etc/passwd")

                # Should detect that resolved path is outside base
                with pytest.raises(ValueError, match="Path traversal blocked"):
                    PathValidator.validate_path("malicious_link", base)
            except OSError:
                # Skip if symlinks not supported
                pytest.skip("Symlinks not supported on this system")

    def test_empty_path(self):
        """Test empty path rejection"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="Path cannot be empty"):
                PathValidator.validate_path("", tmpdir)

    def test_empty_base_dir(self):
        """Test empty base directory rejection"""
        with pytest.raises(ValueError, match="Base directory cannot be empty"):
            PathValidator.validate_path("file.txt", "")

    def test_nonexistent_base_dir(self):
        """Test nonexistent base directory rejection"""
        with pytest.raises(ValueError, match="Base directory does not exist"):
            PathValidator.validate_path("file.txt", "/nonexistent/directory")

    def test_must_exist_enforcement(self):
        """Test must_exist parameter enforcement"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            # Should pass when must_exist=False
            result = PathValidator.validate_path("nonexistent.txt", base, must_exist=False)
            assert result == base / "nonexistent.txt"

            # Should fail when must_exist=True
            with pytest.raises(ValueError, match="Path does not exist"):
                PathValidator.validate_path("nonexistent.txt", base, must_exist=True)


class TestMultiplePathValidation:
    """Test suite for validating multiple paths"""

    def test_validate_multiple_paths(self):
        """Test validation of multiple paths"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            # Create test files
            (base / "file1.txt").touch()
            (base / "file2.txt").touch()

            paths = ["file1.txt", "file2.txt"]
            results = PathValidator.validate_paths(paths, base, must_exist=True)

            assert len(results) == 2
            assert results[0] == base / "file1.txt"
            assert results[1] == base / "file2.txt"

    def test_empty_path_list(self):
        """Test empty path list returns empty result"""
        with tempfile.TemporaryDirectory() as tmpdir:
            results = PathValidator.validate_paths([], tmpdir)
            assert results == []

    def test_multiple_paths_one_invalid(self):
        """Test that one invalid path fails entire validation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            paths = ["safe.txt", "../etc/passwd"]

            with pytest.raises(ValueError, match="Path traversal blocked"):
                PathValidator.validate_paths(paths, base)


class TestSafeFilename:
    """Test suite for safe filename validation"""

    def test_safe_filenames(self):
        """Test safe filename detection"""
        safe_filenames = [
            "file.txt",
            "document.pdf",
            "image-2023.jpg",
            "data_file.csv",
            "archive.tar.gz",
        ]

        for filename in safe_filenames:
            assert PathValidator.is_safe_filename(filename) is True

    def test_unsafe_filenames(self):
        """Test unsafe filename detection"""
        unsafe_filenames = [
            "../etc/passwd",
            "path/to/file.txt",
            "\\windows\\path",
            "..",
            ".",
            "file\x00.txt",
            "file/name.txt",
        ]

        for filename in unsafe_filenames:
            assert PathValidator.is_safe_filename(filename) is False

    def test_empty_filename(self):
        """Test empty filename detection"""
        assert PathValidator.is_safe_filename("") is False


class TestFilenameSanitization:
    """Test suite for filename sanitization"""

    def test_sanitize_basic_filename(self):
        """Test sanitization of basic filename"""
        result = PathValidator.sanitize_filename("file.txt")
        assert result == "file.txt"

    def test_sanitize_path_separators(self):
        """Test sanitization removes path separators"""
        result = PathValidator.sanitize_filename("path/to/file.txt")
        assert "/" not in result
        assert result == "path_to_file.txt"

    def test_sanitize_parent_refs(self):
        """Test sanitization removes parent directory references"""
        result = PathValidator.sanitize_filename("../file.txt")
        assert ".." not in result

    def test_sanitize_null_bytes(self):
        """Test sanitization removes null bytes"""
        result = PathValidator.sanitize_filename("file\x00.txt")
        assert "\x00" not in result

    def test_sanitize_custom_replacement(self):
        """Test sanitization with custom replacement character"""
        result = PathValidator.sanitize_filename("path/to/file.txt", replacement="-")
        assert result == "path-to-file.txt"

    def test_sanitize_empty_after_cleaning(self):
        """Test that empty result after sanitization raises error"""
        with pytest.raises(ValueError, match="empty after sanitization"):
            PathValidator.sanitize_filename("..")


class TestPathComponents:
    """Test suite for path component extraction"""

    def test_get_safe_components(self):
        """Test extraction of safe path components"""
        components = PathValidator.get_safe_path_components("dir/subdir/file.txt")
        assert components == ["dir", "subdir", "file.txt"]

    def test_unsafe_component_rejection(self):
        """Test rejection of unsafe components"""
        with pytest.raises(ValueError, match="Unsafe path component"):
            PathValidator.get_safe_path_components("dir/../etc/passwd")


class TestSafePathCreation:
    """Test suite for safe path creation"""

    def test_create_safe_path(self):
        """Test creation of safe path from components"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            result = PathValidator.create_safe_path(base, "subdir", "file.txt")
            assert result == base / "subdir" / "file.txt"

    def test_create_safe_path_rejects_traversal(self):
        """Test safe path creation rejects traversal attempts"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            with pytest.raises(ValueError, match="Unsafe path component"):
                PathValidator.create_safe_path(base, "..", "etc", "passwd")

    def test_create_safe_path_rejects_absolute(self):
        """Test safe path creation rejects absolute path components"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            with pytest.raises(ValueError, match="Unsafe path component"):
                PathValidator.create_safe_path(base, "/etc/passwd")


class TestIntegration:
    """Integration tests for path security"""

    def test_real_world_document_upload(self):
        """Test realistic document upload scenario"""
        with tempfile.TemporaryDirectory() as tmpdir:
            upload_dir = Path(tmpdir) / "uploads"
            upload_dir.mkdir()

            # Simulate user upload with sanitized filename
            user_filename = "my-document (1).pdf"
            safe_filename = PathValidator.sanitize_filename(user_filename)

            # Validate upload path
            upload_path = PathValidator.validate_path(
                safe_filename, upload_dir, must_exist=False
            )

            # Should be safe path within upload directory
            assert upload_path.is_relative_to(upload_dir)
            assert upload_path.name == safe_filename

    def test_prevent_directory_traversal_attack(self):
        """Test prevention of directory traversal attack"""
        with tempfile.TemporaryDirectory() as tmpdir:
            upload_dir = Path(tmpdir) / "uploads"
            upload_dir.mkdir()

            # Attacker tries to upload to /etc/passwd
            malicious_filename = "../../../etc/passwd"

            # Should be blocked
            with pytest.raises(ValueError, match="Path traversal blocked"):
                PathValidator.validate_path(malicious_filename, upload_dir)

    def test_multiple_security_layers(self):
        """Test multiple security validation layers"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            # Layer 1: Sanitize filename
            unsafe_name = "../../etc/passwd"
            safe_name = PathValidator.sanitize_filename(unsafe_name)

            # Layer 2: Validate path
            safe_path = PathValidator.validate_path(safe_name, base)

            # Should be safe
            assert safe_path.is_relative_to(base)
