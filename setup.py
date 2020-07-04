from setuptools import setup, find_packages

setup(
    name="jgns",
    version="1.0.0",
    packages=find_packages(),
    entry_points={"console_scripts": ["jgns=jgns.main:wrapper"]},
    author="Jacob Glueck",
    author_email="swimgiraffe435@gmail.com",
    description="Utility scripts",
)
