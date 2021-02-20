import setuptools

version = '1.3.5'

setuptools.setup(
    name="scrapydartx",  # Replace with your own username
    version=version,
    author="ga1008",
    author_email="zhling2012@live.com",
    include_package_data=True,
    description="A extension from ScrapydArt",
    long_description='<h1>see https://github.com/GuardianGH/scrapydartx</h1>',
    long_description_content_type="text/markdown",
    url="https://github.com/GuardianGH/scrapydartx",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
    install_requires=[
        "twisted~=20.3.0",
        "six~=1.15.0",
        "setuptools~=52.0.0",
        "scrapy~=2.4.1",
        "w3lib~=1.22.0",
        "requests~=2.25.1",
        "pymysql~=1.0.2",
        "psutil~=5.8.0",
        "numpy>=1.19",
        "sqlalchemy~=1.3.23",
    ],
    entry_points={
        'console_scripts': [
            'scrapydartx = scrapydartx.scripts.scrapyd_run:main'
        ]
    }
)
