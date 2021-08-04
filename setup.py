import os
import re

from setuptools import setup  # type: ignore

with open("README.md", "r") as fh:
    long_description = fh.read()


def version():
    version_pattern = r"__version__\W*=\W*\"([^\"]+)\""
    src = os.path.join(os.path.dirname(__file__), 'asparser/__init__.py')
    with open(src, 'r') as f:
        (v,) = re.findall(version_pattern, f.read())
    return v


setup(
    name='asparser',
    version=version(),
    author='Marcus LaFerrera',
    author_email='mlaferrera@splunk.com',
    description='Collect ASN information',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='Apache License 2.0',
    url='https://github.com/splunk/asparser',
    include_package_data=True,
    packages=['asparser'],
    keywords='ASN',
    python_requires='>=3.7',
    entry_points={'console_scripts': ['asparser=asparser.cli:main']},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: Utilities',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
