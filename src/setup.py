"""Setup environment for Celery task server."""
from setuptools import setup, find_packages  # noqa

install_requires = [
    "celery >= 4.3.0rc2",
    "redis == 3.2.0",
    "docopt >= 0.6.2",
    "PyYAML >= 3.12",
    "schedule >= 0.4.2",
    "requests >= 2.21.0",
    "xmljson >= 0.2.0",
    "cryptography >= 2.4.2",
    "dnspython",
    "python-dateutil >= 2.7.5",
    "mongoengine == 0.16.3",
    "tqdm >= 4.30.0",
]

tests_require = ["pytest == 4.1.1", "mock == 2.0.0", "mongomock == 3.15.0"]

setup(
    name="admiral",
    version="0.0.1",
    author="Mark Feldhousen",
    author_email="mark.feldhousen@trio.dhs.gov",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={"console_scripts": ["admiral=admiral.celery:main"]},
    license="LICENSE.txt",
    description="The Admiral",
    # long_description=open('README.md').read(),
    install_requires=install_requires + tests_require,
    # tests_require=tests_require  # TODO get pip install -e to pickup tests_require
)
