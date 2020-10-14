import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gcvb",
    version="1.0.0",
    author="Airbus SAS",
    author_email="jean-marie.couteyen-carpaye@airbus.com",
    description="A package which goal is to simplify non-regression testing for simulation code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    #url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    package_data={'' : ["assets/*"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=["PyYAML >= 5.1"],
    entry_points = {
        'console_scripts' : ['gcvb=gcvb.command_line:main']
    }
)