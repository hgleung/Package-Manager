from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pypm",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A fast package manager with SAT-based dependency resolution",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pypm",
    packages=find_packages(),
    package_data={"pypm": ["py.typed"]},
    python_requires=">=3.8",
    install_requires=[
        "python-sat>=0.1.8.dev6",
        "networkx>=3.0",
        "click>=8.1.3",
        "rich>=13.4.2",
        "orjson>=3.9.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "pypm=pypm.cli:cli",
        ],
    },
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
    ],
)
