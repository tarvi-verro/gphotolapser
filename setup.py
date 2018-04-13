from setuptools import setup, find_packages

setup(
        name = 'gphotolapser',
        version = '0.8',
        description = 'Record a timelapse with a DSLR',
        packages = [ 'gphotolapser' ],
        install_requires = ['numpy', 'future', 'pillow'],
        entry_points = {'console_scripts': [ 'gphotolapser = gphotolapser.trigger:main']},
)

