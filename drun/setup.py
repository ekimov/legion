from setuptools import setup
import os

PACKAGE_ROOT_PATH = os.path.dirname(os.path.abspath(__file__))


def extract_requirements(filename):
    """
    Extracts requirements from a pip formatted requirements file.
    """
    with open(filename, 'r') as requirements_file:
        return requirements_file.read().splitlines()


setup(name='drun',
      version='0.5',
      description='Legion server',
      url='http://github.com/akharlamov/drun-root',
      author='Alexey Kharlamov',
      author_email='alexey@kharlamov.biz',
      license='Apache v2',
      packages=['drun'],
      include_package_data=True,
      scripts=['bin/legion'],
      install_requires=extract_requirements(os.path.join(PACKAGE_ROOT_PATH, 'requirements', 'base.txt')),
      test_suite='nose.collector',
      tests_require=extract_requirements(os.path.join(PACKAGE_ROOT_PATH, 'requirements', 'test.txt')),
      zip_safe=False)