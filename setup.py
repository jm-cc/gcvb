import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gcvb",
    version="0.0.1",
    author="Airbus SAS",
    author_email="jean-marie.couteyen-carpaye@airbus.com",
    description="A package which goal is to simplify non-regression testing for simulation code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    #url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=["PyYAML"]
)