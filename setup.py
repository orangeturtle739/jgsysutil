from setuptools import setup, find_packages
from pathlib import Path

setup(
    name="jgsysutil",
    version=(Path(__file__).parent / "VERSION").open().read().strip(),
    packages=find_packages("src"),
    package_dir={"": "src"},
    entry_points={"console_scripts": ["jgsysutil=jgsysutil.main:main"]},
    author="Jacob Glueck",
    author_email="swimgiraffe435@gmail.com",
    description="Utility scripts",
    # Otherwise nix can't find refernces inside the zip
    # TODO: This should probably be handled in the wrapper, maybe?
    zip_safe=False,
)
