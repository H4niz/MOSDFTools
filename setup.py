"""
Setup configuration for macOS Forensics Artifacts Analyzer (mFAA)
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="mfaa",
    version="1.0.0",
    author="Digital Forensics Team",
    author_email="forensics@example.com",
    description="macOS Forensics Artifacts Analyzer - Live acquisition and analysis tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mfaa",
    packages=find_packages(exclude=["tests", "tests.*", "docs", "examples"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Legal Industry",
        "Topic :: Security",
        "Topic :: System :: Forensics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: MacOS :: MacOS X",
    ],
    python_requires=">=3.9",
    install_requires=[
        "click>=8.1.0",
        "pyyaml>=6.0",
        "jinja2>=3.1.0",
        "xattr>=0.10.0",
        "colorama>=0.4.6",
        "tqdm>=4.65.0",
        "tabulate>=0.9.0",
        "plotly>=5.18.0",
        "pandas>=2.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
            "isort>=5.12.0",
            "sphinx>=7.1.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mfaa=mfaa.cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "mfaa": [
            "reporter/templates/*.html",
            "reporter/templates/*.j2",
        ],
    },
    zip_safe=False,
)
