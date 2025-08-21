"""
Setup script for Sale Tracker - Improved Version

Usage:
    python setup_improved.py py2app
"""

from setuptools import setup, find_packages

APP = ['main_improved.py']
DATA_FILES = [
    ('', ['config.py', '.env']),
]
OPTIONS = {
    'argv_emulation': True,
    'packages': ['requests', 'bs4', 'schedule', 'dotenv'],
    'includes': ['config'],
    'iconfile': None,  # Add icon file path if you have one
    'plist': {
        'CFBundleName': 'Sale Tracker',
        'CFBundleDisplayName': 'Sale Tracker',
        'CFBundleGetInfoString': 'Product price tracking and email notifications',
        'CFBundleIdentifier': 'com.saletracker.app',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2024 Sale Tracker'
    }
}

setup(
    name='Sale Tracker',
    version='2.0.0',
    description='Product price tracking and email notifications',
    author='Sale Tracker Team',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=[
        'requests==2.31.0',
        'beautifulsoup4==4.12.3',
        'python-dotenv==1.0.1',
        'schedule==1.2.1',
    ],
    entry_points={
        'console_scripts': [
            'sale-tracker=cli:main',
        ],
    },
    python_requires='>=3.8',
)
