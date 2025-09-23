from setuptools import setup, find_packages

setup(
    name='flowforge',
    version='0.1.0',
    description='A Python workflow orchestration engine',
    author='Parth Tiwari',
    packages=find_packages(),
    install_requires=[],
    tests_require=['pytest'],
    python_requires='>=3.7',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)