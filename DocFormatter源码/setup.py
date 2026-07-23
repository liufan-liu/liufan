"""DocFormatter setup configuration."""
from setuptools import setup, find_packages

setup(
    name="DocFormatter",
    version="1.0.0",
    description="跨平台文档排版工具 — 导入多格式，统一排版，导出为精美的 Word 文档",
    author="DocFormatter Team",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "app": [
            "templates/builtin/*.yaml",
        ],
    },
    install_requires=[
        "PySide6>=6.6.0",
        "python-docx>=1.1.0",
        "markdown-it-py>=3.0.0",
        "mdit-py-plugins>=0.4.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=5.0.0",
        "PyYAML>=6.0",
        "Pillow>=10.0.0",
    ],
    entry_points={
        "console_scripts": [
            "docformatter=main:main",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Office/Business :: Office Suites",
    ],
)
