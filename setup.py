from setuptools import setup, find_packages

with open("requirements.txt", "r", encoding="utf-8") as fh:
	requirements = fh.read().splitlines()

setup(
    name="live-logs-handler",
    version="0.1.0",
    author="Dev Gala",
    author_email="dgala@singlestore.com",
    description="Thread-Safe Structured Logging SDK for Jupyter Notebooks",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/dgalas2/live-logs-handler",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
)
