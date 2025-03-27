from setuptools import setup, find_packages

setup(
    name="cloudtrace-benchmark",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=open("requirements.txt").readlines(),
    entry_points={
        "console_scripts": [
            "cloudtrace=main:main",
        ],
    },
    author="Enock Mecheo",
    description="A tool to benchmark cloud provider network performance",
    python_requires=">=3.10",
)
