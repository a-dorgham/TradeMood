from setuptools import setup, find_packages

setup(
    name='trademood',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy',
        'python-dateutil',
        'requests',
        'beautifulsoup4',
        'vader-sentiment',
        'transformers',
        'torch',
        'apscheduler',
        'fastapi',
        'uvicorn',
        'streamlit',
        'yfinance',
        'plotly',
        'streamlit-autorefresh',
        'exchange-calendars',
        'pytest',
    ],
    python_requires='>=3.0',
    author='Abdel Dorgham',
    author_email='a.k.y.dorgham@gmail.com',
    description='A Streamlit-based dashboard for financial market sentiment analysis and trade management.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/a-dorgham/TradeMood',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    entry_points={
        'console_scripts': [
            'trademood=trademood.scripts.run_dashboard:run_dashboard',
        ],
    },
)