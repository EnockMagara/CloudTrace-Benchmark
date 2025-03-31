from setuptools import setup, find_packages
import os

# Get the absolute path to the directory containing setup.py
HERE = os.path.abspath(os.path.dirname(__file__))

# Read requirements from the requirements.txt file
with open(os.path.join(HERE, 'requirements.txt'), 'r') as f:
    requirements = [line.strip() for line in f if line.strip()]

setup(
    name="cloudtrace-benchmark",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "cloudtrace=main:main",
        ],
    },
    author="Enock Mecheo",
    description="A tool to benchmark cloud provider network performance",
    python_requires=">=3.10",
)
