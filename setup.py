from setuptools import setup, find_packages

setup(
        name = 'gphotolapser',
        version = '0.13.0',
        description = 'Record a timelapse with a DSLR',
        packages = [ 'gphotolapser' ],
        install_requires = ['numpy', 'future', 'pillow'],
        scripts = [ 'bin/gphotolapser' ]
)

