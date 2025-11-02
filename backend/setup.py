"""
CommandCenter CLI - Setup Configuration

Production-ready setup.py for pip installation of the CommandCenter CLI tool.
"""

from pathlib import Path

from setuptools import find_packages, setup

# Read the README for long description
readme_path = Path(__file__).parent.parent / "README.md"
long_description = ""
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()

# Read requirements from requirements.txt
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, "r", encoding="utf-8") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="commandcenter-cli",
    version="0.1.0",
    description="CommandCenter CLI - R&D Management & Knowledge Base System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="CommandCenter Team",
    author_email="team@commandcenter.dev",
    url="https://github.com/yourusername/commandcenter",
    license="MIT",
    # Package discovery
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    # Python version requirement
    python_requires=">=3.11",
    # Dependencies
    install_requires=[
        "click>=8.0",
        "rich>=13.0",
        "httpx>=0.24",
        "pyyaml>=6.0",
        "keyring>=24.0",  # Secure credential storage
        "pydantic>=2.0",
        "textual>=0.40",  # For TUI search interface
    ],
    # Development dependencies
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=6.0",
            "mypy>=1.0",
        ],
    },
    # Console scripts entry point
    entry_points={
        "console_scripts": [
            "commandcenter=cli.commandcenter:cli",
        ],
    },
    # Project metadata
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Documentation",
        "Topic :: Text Processing :: Markup",
    ],
    # Keywords for PyPI
    keywords="cli research development knowledge-base rag fastapi",
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/yourusername/commandcenter/issues",
        "Source": "https://github.com/yourusername/commandcenter",
        "Documentation": "https://github.com/yourusername/commandcenter/docs",
    },
)
