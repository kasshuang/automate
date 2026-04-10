from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="automatelib",
    version="0.1.0",
    author="Your Name",
    author_email="your@email.com",
    description="AI驱动的PC自动化工具 - 用自然语言控制电脑",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourname/automate",
    packages=find_packages(exclude=["tests*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Office/Business",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
        "Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyautogui>=0.9.54",
        "mss>=9.0.1",
        "Pillow>=10.0.0",
        "pywin32>=305",
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
    },
    entry_points={
        "console_scripts": [
            "automate=automate:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
