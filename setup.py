#!/usr/bin/python3
import os
import sys

from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

if os.environ.get("BROWNIE_LIB", "0") == "1":
    if sys.platform == "win32":
        requirements_filename = "requirements-windows.in"
    else:
        requirements_filename = "requirements.in"
else:
    if sys.platform == "win32":
        requirements_filename = "requirements-windows.txt"
    else:
        requirements_filename = "requirements.txt"


def read_requirements(filename):
    requirements = []
    with open(filename, "r") as f:
        for line in f:
            requirement = line.strip()
            if not requirement or requirement.startswith("#"):
                continue
            if requirement.startswith("-r "):
                requirements.extend(read_requirements(requirement[3:].strip()))
                continue
            if "#egg=" in requirement:
                requirement = requirement.split("#egg=", 1)[1]
            elif requirement.startswith("-e"):
                continue
            requirements.append(requirement)
    return requirements


requirements = read_requirements(requirements_filename)

setup(
    name="eth-brownie",
    packages=find_packages(),
    version="1.16.2",  # don't change this manually, use bumpversion instead
    license="MIT",
    description="A Python framework for Ethereum smart contract deployment, testing and interaction.",  # noqa: E501
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Ben Hauser",
    author_email="ben@hauser.id",
    url="https://github.com/eth-brownie/brownie",
    keywords=["brownie"],
    install_requires=requirements,
    entry_points={
        "console_scripts": ["brownie=brownie._cli.__main__:main"],
        "pytest11": ["pytest-brownie=brownie.test.plugin"],
    },
    include_package_data=True,
    python_requires=">=3.6,<4",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
