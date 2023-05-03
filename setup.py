from setuptools import setup, find_packages

setup(
    name='ark',
    version='1.0',
    description='Ark Biotech Take Home Project',
    packages=find_packages(include=["my_ark", "my_ark.*"]),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'run-app=my_ark.app:main'
        ]
    }
)
