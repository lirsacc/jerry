from setuptools import setup, find_packages

if __name__ == '__main__':
    setup(
        name='oyez',
        version="0.0.1",
        description='',
        entry_points={
            'console_scripts': []
        },
        packages=find_packages(exclude=['tests']),
        install_requires=[
            'Flask==0.10.1',
            'requests==2.9.1',
            'rethinkdb==2.3.0.post1',
        ],
        cmdclass={}
    )
