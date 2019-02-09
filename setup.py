from setuptools import setup, find_packages

long_description = open('README.rst').read()

setup(
    name="census",
    version="0.8.13",
    py_modules=['census'],
    author="Jeremy Carbaugh",
    author_email='jcarbaugh@sunlightfoundation.com',
    maintainer='Forest Gregg',
    maintainer_email='fgregg@gmail.com',
    license="BSD",
    url="http://github.com/datamade/census",
    long_description=long_description,
    packages=find_packages(),
    description="A wrapper for the US Census Bureau's API",
    platforms=["any"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    install_requires=['requests>=1.1.0',
                      'future',
                      'backports.functools_lru_cache;python_version<"3.3"'],
)
