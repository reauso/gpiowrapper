import re
import sys
from pathlib import Path

from setuptools import setup, find_packages

if sys.version_info < (3, 11):
    print(f'requires at least Python 3.11 to run, got version info:\n {sys.version_info}')
    sys.exit(1)

with open(Path('gpiowrapper', '__init__.py'), encoding='utf-8') as f:
    version = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read(), re.M).group(1)

if version is None:
    raise RuntimeError('Cannot find version information.')

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()


def data_files():
    files = []
    return files


def install_requires():
    requires = []
    return requires


def install_extras_require():
    extra_requires = {
        'raspi': ['RPi.GPIO~=0.7.1'],
        'testing': ['pytest', 'parameterized'],
    }

    all_extra_deps = []
    for value in extra_requires.values():
        all_extra_deps.extend(value)
    extra_requires['all'] = all_extra_deps

    return extra_requires


setup(
    name='gpiowrapper',
    version=version,
    description="A gpio wrapper library",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Rene Ebertowski',
    author_email='r.ebertowski@gmx.de',
    url='https://github.com/reauso/gpiowrapper',
    license='MIT',
    keywords="gpio raspberry raspi",
    python_requires=">=3.11",
    install_requires=install_requires(),
    extras_require=install_extras_require(),
    packages=find_packages(),
    include_package_data=True,
    data_files=data_files(),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Education',
        'Topic :: Home Automation',
        'Topic :: Other/Nonlisted Topic',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Emulators',
        'Topic :: System :: Hardware',
        'Topic :: Utilities',
    ],
)
