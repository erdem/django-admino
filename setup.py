import os
from setuptools import setup, find_packages

VERSION = (0, 0, 1)
__version__ = '.'.join(map(str, VERSION))

readme_rst = os.path.join(os.path.dirname(__file__), 'README.rst')

if os.path.exists(readme_rst):
    long_description = open(readme_rst).read()
else:
    long_description = "Admino is a django package that provides a REST API for admin endpoints. It allows you to customize django admin panel."

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-admino',
    version=__version__,
    description="Admino is a django package that provides a REST API for admin endpoints. It allows you to customize django admin panel.",
    long_description=long_description,
    author="Erdem Ozkol",
    author_email="info@admino.io",
    url="https://github.com/erdem/django-admino",
    license="MIT",
    platforms=["any"],
    packages=find_packages(exclude=("example", "env", "notes")),
    include_package_data=True,
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: Django",
        "Programming Language :: Python",
    ],
)

