#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('CHANGELOG.rst') as changelog_file:
    changelog = changelog_file.read()

install_requires = [
    'wagtail>=1.6',
    'twython>=3.0,<4.0',
    'facepy>=1.0.8',
    'wagtailfontawesome>=1.0',
    'requests>=2.0',
    'python-dateutil>=2.5',
    'enum34',
]

test_require = [
    'responses>=0.5',
    'factory-boy>=2.7,<2.8',
    'beautifulsoup4>=4',
    'coverage>=3.7.0',
    'flake8>=2.2.0',
    'isort>=4.2.0',
    'tox>=2.3.1',
    'cryptography==1.4',
    'PyYAML==3.11',
    'bumpversion==0.5.3',
    'wheel==0.29.0',
    'django-coverage-plugin==1.3.1',
]

docs_require = [
    'sphinx',
    'sphinx_rtd_theme',
]

setup(
    name='wagtailsocialfeed',
    version='0.2.0',
    description="A Wagtail module that provides pages and content blocks to show social media feeds", # NOQA
    long_description=readme + '\n\n' + changelog,
    author="Tim Leguijt",
    author_email='info@leguijtict.nl',
    url='https://github.com/LUKKIEN/wagtailsocialfeed',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    install_requires=install_requires,
    license='BSD',
    zip_safe=False,
    keywords='wagtailsocialfeed',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    extras_require={
        'testing': test_require,
        'docs': docs_require,
    },
)
