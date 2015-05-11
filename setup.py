from distutils.core import setup
setup(
  name = "oslom-runner",
  packages = ["oslom"],
  version = "1.0",
  description = "Run OSLOM over a list of edges and process the output clusters",
  long_description = "Run OSLOM over a list of edges and process the output clusters",
  author = "Hugo Hromic",
  author_email = "hhromic@gmail.com",
  url = "https://github.com/hhromic/python-oslom-runner",
  download_url = "https://github.com/hhromic/python-oslom-runner/tarball/1.0",
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