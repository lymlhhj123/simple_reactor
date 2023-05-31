# coding: utf-8

import sys

from setuptools import setup, find_packages

py_version = (3, 8, 5)

if sys.version_info < py_version:
    print("[ERROR] python version must be >= {}".format(py_version))
    sys.exit(1)


install_requires = [
    "bitarray >= 2.7.4",
    "mmh3 >= 4.0.0",
]


def get_version():
    """

    :return:
    """
    return open("version").readline().strip()


setup(
    zip_safe=False,
    include_package_data=True,
    name="libreactor",
    description="io notify based on reactor mode",
    version=get_version(),
    author="Jun Hu",
    author_email="524964426@qq.com",
    packages=find_packages(exclude=["example"]),
    install_requires=install_requires,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Console",
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)
