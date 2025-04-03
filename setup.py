from setuptools import setup, find_packages
import os

# Read the content of README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rustcord",
    version="0.1.2",
    author="ghulq",
    author_email="ghulq@mcbehub.de",
    description="A high-performance Discord API library with Rust core",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ghulq/rustcord",
    project_urls={
        "Bug Tracker": "https://github.com/ghulq/rustcord/issues",
        "Documentation": "https://github.com/ghulq/rustcord#readme",
        "Source Code": "https://github.com/ghulq/rustcord",
    },
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "rustcord": ["*.so", "*.dll", "*.dylib"],
    },
    install_requires=[
        "asyncio>=3.4.3",
        "aiohttp>=3.8.0",
        "websockets>=10.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Rust",
        "Operating System :: OS Independent",
    ],
    keywords="discord, bot, api, rust, async, websocket, gateway",
)