"""
This is the setup module for the example project.

Based on:

- https://packaging.python.org/distributing/
- https://github.com/pypa/sampleproject/blob/master/setup.py
- https://blog.ionelmc.ro/2014/05/25/python-packaging/#the-structure
"""

from glob import glob
from os.path import splitext, basename

from setuptools import setup, find_packages


def readme():
    """Read in and return the contents of the project's README.md file."""
    with open("README.md", encoding="utf-8") as f:
        return f.read()


def package_vars(version_file):
    """Read in and return the variables defined by the version_file."""
    pkg_vars = {}
    with open(version_file) as f:
        exec(f.read(), pkg_vars)  # nosec
    return pkg_vars


setup(
    name="admiral",
    # Versions should comply with PEP440
    version=package_vars("src/admiral/_version.py")["__version__"],
    description="Admiral",
    long_description=readme(),
    long_description_content_type="text/markdown",
    # NCATS "homepage"
    url="https://www.us-cert.gov/resources/ncats",
    # The project's main homepage
    download_url="https://github.com/cisagov/admiral",
    # Author details
    author="Cyber and Infrastructure Security Agency",
    author_email="ncats@hq.dhs.gov",
    license="License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 3 - Alpha",
        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        # Pick your license as you wish (should match "license" above)
        "License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    # What does your project relate to?
    keywords="skeleton",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    install_requires=[
        "celery >= 4.3.0rc2",
        "cryptography >= 2.4.2",
        "defusedxml",
        "dnspython",
        "docopt",
        "docker-compose",
        "mongoengine == 0.16.3",
        "python-dateutil >= 2.7.5",
        "PyYAML >= 3.12",
        "redis == 3.2.0",
        "requests >= 2.21.0",
        "schedule >= 0.4.2",
        "setuptools",
        "tqdm >= 4.30.0",
        "xmljson >= 0.2.0",
    ],
    extras_require={
        "test": ["pre-commit", "pytest", "pytest-cov", "coveralls", "mock", "mongomock"]
    },
    # Conveniently allows one to run the CLI tool as `admiral`
    entry_points={"console_scripts": ["admiral=admiral.celery:main"]},
)
