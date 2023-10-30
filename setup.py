import setuptools

setuptools.setup(
    name='redis_record',
    version='0.0.3',
    description='redis streams recordings',
    long_description=open('README.md').read().strip(),
    long_description_content_type='text/markdown',
    author='Bea Steers',
    author_email='bea.steers@gmail.com',
    url=f'https://github.com/beasteers/redis-record',
    packages=setuptools.find_packages(),
    entry_points={'console_scripts': ['redis-record=redis_record.cmd:cli']},
    install_requires=[
        'redis', 'mcap', 'orjson', 'tqdm', 'fire',
    ],
    extras_require={},
    license='MIT License',
    keywords='redis record streams video streaming')
