from setuptools import setup
from pathlib import Path

if __name__ == "__main__":
    requirements_path = Path(__file__).parent / "requirements.txt"
    requirements_lines = requirements_path.read_text().strip().splitlines()

    readme_path = Path(__file__).parent / "README.md"
    long_description = readme_path.read_text()

    setup(
        name="pydranticntic",
        version="0.0.2",
        packages=["pydranticntic"],
        author="Jordan Juravsky and Sabri Eyuboglu",
        url="https://github.com/seyuboglu/pydranticntic",
        description="A flexible configuration library in pure Python",
        install_requires=requirements_lines,
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
        license="Apache License 2.0",
        include_package_data=True,
    )
