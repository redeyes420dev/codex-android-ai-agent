#!/usr/bin/env python3
"""Setup script for Codex-Android-AI-Agent."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="codex-android-ai-agent",
    version="0.1.0",
    author="CADX Team",
    author_email="dev@cadx.ai",
    description="Open source tool for Android development automation with Codex CLI and multi-agent pipelines",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/username/codex-android-ai-agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Tools",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "cadx=cli.main:main",
            "codex-android-agent=cli.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)