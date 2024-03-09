from setuptools import setup, find_packages

setup(
    name='populate-synapse-nb',
    version='1.43',
    packages=find_packages(),
    install_requires=[
        'pathlib',
    ],
    author='Andre Pretorius',
    author_email='pretorius.dre+github@gmail.com',
    description='A package to populate Azure Synapse Analytics Notebooks (json format) with code from Python source files.',
    url='https://github.com/pretoriusdre/populate-synapse-nb',
)