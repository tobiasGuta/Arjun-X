from setuptools import setup, find_packages

setup(
    name='arjun-x',
    version='0.0.1',
    description='Arjun-X HTTP Parameter Discovery Suite (fork)',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests>=2.0.0',
        'dicttoxml>=1.7.4',
        'cloudscraper>=1.2.70',
        'fake-useragent>=1.1.0',
        'ratelimit>=2.2.1'
    ],
    entry_points={
        'console_scripts': [
            'arjun=arjun.__main__:main'
        ]
    },
    python_requires='>=3.8',
)
