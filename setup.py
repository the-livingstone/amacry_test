from setuptools import setup

setup(
    name='amacry_test',
    version='1.0',
    description='test assignment',
    author='Alexey Serikov',
    author_email='serikov.alexey42@gmail.com',
    packages=['app'],
    install_requires=[
       'dash',
       'dash_daq',
       'pandas',
       'plotly'
    ],
)