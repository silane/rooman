from setuptools import setup, find_packages


setup(
    name='rooman',
    version='1.0.0',
    description='Very simple room automation framework with web API',
    author='silane',
    author_email='silane@silane8.net',
    packages=find_packages(),
    install_requires=['threading-utils'],
)
