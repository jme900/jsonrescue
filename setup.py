from setuptools import setup, find_packages

setup(
    name='JSONRescue',
    version="0.1.0",
    description="A library to parse and repair malformed JSON-like text.",
    author='Jesse English',
    author_email='jme900@gmail.com',
    url="https://github.com/jme900/jsonrescue",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "regex",
    ],
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)