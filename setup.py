from setuptools import setup
from glob import glob


__version__ = '0.2b8'


setup(
    name='babygdcli',
    version=__version__,
    description='little PyDrive CLI',
    py_modules=[
        'babygdcli',
    ],
    scripts=glob('scripts/*'),
    install_requires=[
        'PyDrive>=1.3.1',
    ],
    url='https://github.com/cjmay/babygdcli',
    license='BSD',
)
