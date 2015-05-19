from distutils.core import setup
setup(
  name = "oslom-runner",
  packages = ["oslom"],
  version = "1.3",
  description = "An OSLOM (community finding) runner for Python",
  long_description = "An OSLOM (community finding) runner for Python",
  author = "Hugo Hromic",
  author_email = "hhromic@gmail.com",
  url = "https://github.com/hhromic/python-oslom-runner",
  download_url = "https://github.com/hhromic/python-oslom-runner/tarball/1.3",
  install_requires = ["simplejson"],
  keywords = ["oslom", "runner", "clustering", "communities"],
  classifiers = [],
  license = "MIT",
  platforms = ["all"],
  entry_points = {
    "console_scripts": [
      "oslom-runner = oslom.runner:main",
    ],
  },
)
