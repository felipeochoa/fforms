from os import path
from setuptools import setup

README = path.join(path.dirname(path.abspath(__file__)), "README.rst")

setup(
    name="fforms",
    version="1.1.1",
    description=("Standalone HTML form validation library"),
    long_description=open(README).read(),
    author="Felipe Ochoa",
    author_email="felipeochoa@find-me-on-github.com",
    url="https://github.com/felipeochoa/fforms",
    license="MIT",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'License :: OSI Approved :: MIT License',
    ],
    keywords="forms form html",
    packages=["fforms"],
    test_suite="tests",
)
