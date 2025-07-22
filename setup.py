from setuptools import setup
from pathlib import Path

if __name__ == "__main__":
    readme_path = Path(__file__).parent / "README.md"
    long_description = readme_path.read_text()

    REQUIREMENTS = [
        "pyyaml>=6.0,<7",
        "dill>=0.3.7,<0.4",
        "pydantic>=2.9.2",
    ]

    setup(
        name="pydrantic",
        version="0.0.3",
        packages=["pydrantic"],
        author="Sabri Eyuboglu",
        url="https://github.com/seyuboglu/pydrantic",
        description="A simple library that facilitates the use of Pydantic models for configuration",
        install_requires=REQUIREMENTS,
        long_description=long_description,
        long_description_content_type="text/markdown",
        python_requires=">=3.9",
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
        ],
        # license="Apache License 2.0",
        include_package_data=True,
    )
