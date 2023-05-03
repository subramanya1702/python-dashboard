from setuptools import setup, find_packages

setup(
    name='ark',
    version='1.0',
    description='Python-Dash Dashboard',
    packages=find_packages(include=["my_dashboard", "my_dashboard.*"]),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'run-app=my_dashboard.app:main'
        ]
    }
)
