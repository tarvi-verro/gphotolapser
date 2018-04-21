from setuptools import setup, find_packages

setup(
        name = 'gphotolapser',
        version = '0.11.1',
        description = 'Record a timelapse with a DSLR',
        packages = [ 'gphotolapser' ],
        install_requires = ['numpy', 'future', 'pillow'],
        scripts = [ 'bin/gphotolapser' ]
)

