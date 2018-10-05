from setuptools import setup, find_packages
import giant_time_series

setup(
    name='giant_time_series',
    version=giant_time_series.__version__,
    long_description=giant_time_series.__description__,
    url=giant_time_series.__url__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "pytest", "scripttest", "mock", "flake8", "pylint",
        "pytest-cov"
    ]
)
