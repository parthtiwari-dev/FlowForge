from setuptools import setup, find_packages

setup(
    name='workflow-engine',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A workflow engine for managing and executing tasks in a directed acyclic graph.',
    packages=find_packages(),
    install_requires=[
        # List your project dependencies here
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)