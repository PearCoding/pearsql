from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(name='pearsql',
      version='0.1.1',
      description='Very simple sql query builder focusing on sqlite compatibility',
      long_description=readme(),
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          'Topic :: Database',
          'Topic :: Software Development :: Code Generators'
          'Topic :: Utilities'
      ],
      keywords='sql sqlite builder',
      url='http://github.com/pearcoding/pearsql',
      author='PearCoding',
      author_email='pearcoding@gmail.com',
      license='MIT',
      packages=['pearsql'],
      install_requires=[
          'six',
      ],
      zip_safe=False)
