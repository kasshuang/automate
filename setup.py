from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="automatelib",
    version="0.1.0",
    author="kasshuang",
    author_email="kasshuang@example.com",
    description="AI驱动的PC自动化工具 - 用自然语言控制电脑完成自动化任务",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kasshuang/automate",
    license="MIT",
    packages=find_packages(exclude=["tests*", "docs*", "tasks*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyautogui>=0.9.54",
        "mss>=9.0.1",
        "Pillow>=10.0.0",
        "pywin32>=305",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "agent": [
            "openai>=1.0.0",
        ],
        "browser": [
            "selenium>=4.0.0",
            "playwright>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "automate=automate:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="automation pc-control agent ai pyautogui windows desktop gui",
    project_urls={
        "Bug Reports": "https://github.com/kasshuang/automate/issues",
        "Source": "https://github.com/kasshuang/automate",
        "Documentation": "https://github.com/kasshuang/automate#readme",
    },
)
