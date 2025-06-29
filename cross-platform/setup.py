#!/usr/bin/env python3
"""
Setup script for Modern Serial Communication
"""

from setuptools import setup
import pathlib

# プロジェクトルートディレクトリ
HERE = pathlib.Path(__file__).parent

# README.mdの内容を読み込み（親ディレクトリから）
README = (HERE.parent / "README.md").read_text(encoding='utf-8')

setup(
    name="modern-serial-communication",
    version="1.0.0",
    description="A modern, open-source alternative to commercial serial monitoring tools",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/superdoccimo/modern-serial-communication.git",
    author="Your Name",
    author_email="github@minokamo.xyz",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Manufacturing",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications",
        "Topic :: System :: Hardware",
        "Topic :: System :: Monitoring",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Embedded Systems",
        "Environment :: Console",
        "Environment :: Console :: Curses",
    ],
    keywords="serial communication monitoring hardware embedded iot dashboard",
    py_modules=[
        "async_serial_debug",
        "compact_dual_port_dashboard",
        "dual_pipe_linux",
        "dual_pipe_windows",
        "dual_port_dashboard",
        "h_checker",
        "hybrid_network_dashboard",
        "linux_port_checker",
        "modern_serial_comm",
        "pipe_access",
        "port_checker",
        "quick_fix_test",
        "remote_client_dashboard",
        "serial_dashboard",
        "simple_dashboard",
        "test_data_sender",
        "test_data_sender_linux",
        "ultra_compact_dashboard",
        "vmware_serial_checker",
        "vmware_tcp_bridge",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyserial>=3.5",
        "pyserial-asyncio>=0.6",
        "textual>=0.41.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "mqtt": ["asyncio-mqtt>=0.11.1"],
        "web": ["fastapi>=0.68.0", "uvicorn>=0.15.0", "websockets>=10.0"],
        "dev": ["pytest>=6.0", "black>=21.0", "flake8>=3.8"],
    },
    entry_points={
        "console_scripts": [
            "serial-dashboard=serial_dashboard:main",
            "serial-checker=port_checker:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/modern-serial-communication/issues",
        "Source": "https://github.com/yourusername/modern-serial-communication",
        "Documentation": "https://github.com/yourusername/modern-serial-communication#readme",
    },
    include_package_data=True,
    zip_safe=False,
)
