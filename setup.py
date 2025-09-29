"""
PromptGuard: Reciprocity-based prompt evaluation for AI safety.

A radical alternative to rule-based prompt filtering, using
Multi-Neutrosophic evaluation and Ayni-based reciprocal balance.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="promptguard",
    version="0.1.0",
    author="Tony & Claude Collective",
    author_email="",
    description="Reciprocity-based prompt evaluation using Multi-Neutrosophic Ayni Method",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/promptguard",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.19.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=22.0",
            "mypy>=0.900",
        ],
    },
    keywords="AI safety, prompt injection, reciprocity, neutrosophic, ayni",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/promptguard/issues",
        "Source": "https://github.com/yourusername/promptguard",
        "Paper": "https://digitalrepository.unm.edu/nss_journal/vol84/iss1/1",
    },
)