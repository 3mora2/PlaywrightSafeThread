from setuptools import find_packages
from setuptools import setup

long_description = open("README.md", encoding="utf-8").read()
description = "PlaywrightSafeThread"

version = "0.4.1"

setup(
    name="PlaywrightSafeThread",
    version=version,
    license="MIT License",
    author="Ammar Alkotb",
    author_email="ammar.alkotb@gmail.com",
    description=description,
    packages=find_packages(),
    url="https://github.com/3mora2/PlaywrightSafeThread",
    project_urls={"Bug Report": "https://github.com/3mora2/PlaywrightSafeThread/issues/new"},
    install_requires=[
        "playwright",
        "playwright-stealth",
        "psutil",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"": "."},
    # package_data={"PlaywrightSafeThread": ["*.md"]},
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",

    ],

)
