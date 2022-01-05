from setuptools import setup, find_packages

PACKAGE_NAME = "dropy"

setup(
    name=PACKAGE_NAME,
    version='0.1.0',
    packages=find_packages("dropy"),
    install_requires=[
        "dropbox",
        "pyaml",
    ],
    entry_points={
        'console_scripts': [
            'dropy=dropy.dropy:main',
        ]
    },
    setup_requires=['flake8'],
    package_data={'dropy': ['data/config.yaml']},
    description='Handy Dropbox executables based on the Dropbox Python API',
    author='Antonio Ortega Jimenez',
    author_email='ntoniohu@gmail.com',
)