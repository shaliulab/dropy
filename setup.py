from setuptools import setup, find_packages

PACKAGE_NAME = "dropy"

packages=find_packages()
print(packages)

setup(
    name=PACKAGE_NAME,
    version='0.1.0',
    packages=packages,
    install_requires=[
        "dropbox",
        "pyaml",
    ],
    entry_points={
        'console_scripts': [
            'dropy-legacy=dropy.bin.dropy_legacy:main',
            'dropy-batch=dropy.bin.dropy_batch:main',
            'dropy-init=dropy.bin.dropy_init:main',
            'dropy=dropy.bin.dropy:main',
        ]
    },
    setup_requires=['flake8'],
    package_data={'dropy': ['data/config.yaml']},
    description='Handy Dropbox executables based on the Dropbox Python API',
    author='Antonio Ortega Jimenez',
    author_email='ntoniohu@gmail.com',
)
