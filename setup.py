from setuptools import setup

setup(name='stratum',
      version='0.5.2',
      description='Manage layered dotfiles',
      url='https://github.com/frutiger/stratum',
      author='Masud Rahman',
      license='MIT',
      packages=['stratum'],
      entry_points={
          'console_scripts': ['stratum=stratum:main'],
      })

