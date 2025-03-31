from setuptools import setup, find_packages
import os

# Get the absolute path to the directory containing setup.py
HERE = os.path.abspath(os.path.dirname(__file__))

# Default requirements if file isn't available
default_requirements = [
    "requests>=2.28.0",
    "pandas==2.2.1",
    "python-dotenv==1.0.1",
    "pytest>=7.0.0",
    "matplotlib>=3.5.0",
    "plotly==5.19.0",
    "flask==3.0.2",
    "dash>=2.9.0",
    "geopy>=2.3.0"
]

# Try to read requirements from the requirements.txt file
try:
    with open(os.path.join(HERE, 'requirements.txt'), 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
except FileNotFoundError:
    print("requirements.txt not found, using default requirements")
    requirements = default_requirements

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
    include_package_data=True,
)
