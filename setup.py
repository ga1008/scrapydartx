import sys

try:
    from setuptools import setup
    using_setuptools = True
except ImportError:
    from distutils.core import setup
    using_setuptools = False

#
# with open('scrapydartx/VERSION') as f:
#     version = f.read().strip()

setup_args = {
    'name': 'scrapydartx',
    'version': '1.3.2',
    'url': 'https://github.com/GuardianGH/scrapydartx',
    'description': 'a extension from ScrapydArt',
    'long_description': open('README.md', encoding="utf-8").read(),
    'author': 'Scrapy developers',
    'author_email': 'zhling2012@live.com',
    'maintainer': 'Scrapy developers',
    'maintainer_email': 'info@scrapy.org',
    'long_description_content_type': "text/markdown",
    'LICENSE': 'BSD',
    'packages': ['scrapydartx'],
    'include_package_data': True,
    'zip_safe': False,
    'classifiers': [
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Environment :: No Input/Output (Daemon)',
        'Topic :: Internet :: WWW/HTTP',
    ],
}


if using_setuptools:
    setup_args['install_requires'] = [
        'attrs==19.3.0',
        'Automat==0.8.0',
        'bleach==3.1.0',
        'certifi==2019.11.28',
        'cffi==1.13.2',
        'chardet==3.0.4',
        'constantly==15.1.0',
        'cryptography==2.8',
        'cssselect==1.1.0',
        'docutils==0.15.2',
        'enum-compat==0.0.3',
        'hyperlink==19.0.0',
        'idna==2.8',
        'importlib-metadata==1.3.0',
        'incremental==17.5.0',
        'jeepney==0.4.1',
        'keyring==20.0.0',
        'lxml==4.4.2',
        'more-itertools==8.0.2',
        'numpy==1.17.4',
        'parsel==1.5.2',
        'pkginfo==1.5.0.1',
        'Protego==0.1.16',
        'psutil==5.6.7',
        'pyasn1==0.4.8',
        'pyasn1-modules==0.2.7',
        'pycparser==2.19',
        'PyDispatcher==2.0.5',
        'Pygments==2.5.2',
        'PyHamcrest==1.9.0',
        'PyMySQL==0.9.3',
        'pyOpenSSL==19.1.0',
        'queuelib==1.5.0',
        'readme-renderer==24.0',
        'requests==2.22.0',
        'requests-toolbelt==0.9.1',
        'Scrapy==1.8.0',
        'SecretStorage==3.1.1',
        'service-identity==18.1.0',
        'six==1.13.0',
        'SQLAlchemy==1.3.12',
        'tqdm==4.40.2',
        'twine==3.1.0',
        'Twisted==18.9.0',
        'urllib3==1.25.7',
        'w3lib==1.21.0',
        'webencodings==0.5.1',
        'zipp==0.6.0',
        'zope.interface==4.7.1',
    ]
    setup_args['entry_points'] = {'console_scripts': [
        'scrapydartx = scrapydartx.scripts.scrapyd_run:main'
    ]}
else:
    setup_args['scripts'] = ['scrapydartx/scripts/scrapyd_run.py']

setup(**setup_args)
