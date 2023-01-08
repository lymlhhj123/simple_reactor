# coding: utf-8

from setuptools import setup


setup(
    zip_safe=False,
    include_package_data=True,
    name="libreactor",
    description="io notify based on reactor mode",
    version="1.0.0",
    author="Jun Hu",
    author_email="",
    packages=["libreactor"],
    install_requires=[],
    python_requires=">= 3.8.5",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Console",
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.8',
    ],
)
