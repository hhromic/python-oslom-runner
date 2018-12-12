"""Main setup script."""

from setuptools import setup, find_packages

NAME = "oslom-runner"
VERSION = "1.5"
DESCRIPTION = "An OSLOM (community finding) runner for Python"
AUTHOR = "Hugo Hromic"
AUTHOR_EMAIL = "hhromic@gmail.com"
URL = "https://github.com/hhromic/python-oslom-runner"
DOWNLOAD_URL = URL + "/tarball/" + VERSION

def _read_file(filename):
    with open(filename) as reader:
        return reader.read()

setup(
    name=NAME, version=VERSION, description=DESCRIPTION,
    author=AUTHOR, author_email=AUTHOR_EMAIL,
    maintainer=AUTHOR, maintainer_email=AUTHOR_EMAIL,
    url=URL, download_url=DOWNLOAD_URL,
    requires=["simplejson"],
    install_requires=["simplejson"],
    provides=["oslom"],
    keywords=["oslom", "runner", "clustering", "communities"],
    classifiers=["Environment :: Console"],
    license="Apache-2.0",
    platforms=["all"],
    long_description=_read_file("README.md"),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    entry_points={"console_scripts": ["oslom-runner = oslom.runner:main"]}
)
