import os
from setuptools import setup, find_packages

setup(
    name='freeradius_exporter',
    version='1.0',
    requires=['pyrad', 'prometheus_client'],
    author='Semaphor',
    author_email='info@semaphor.dk',
    description='Prometheus exporter for FreeRADIUS statistics',
    license='ISC',
    keywords='prometheus freeradius radius',
    url='https://github.com/semaphor-dk/freeradius_exporter',
    packages=find_packages(),
    include_package_data=True,
    long_description=open('README.md').read(),
    classifiers=[
        'License :: OSI Approved :: ISC license'
    ],
    scripts=['freeradius_exporter/freeradius_exporter.py'],
    data_files=[
        ('/usr/local/share/freeradius_exporter',['dictionary.freeradius.pyrad']),
        ('/lib/systemd/system/', ['freeradius_exporter.service']),
    ]
)
