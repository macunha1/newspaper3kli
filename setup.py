from setuptools import setup, find_packages


def read_file(name):
    with open(name) as filedesc:
        return filedesc.read()


setup(name="newspaper3kli",
      version="0.1.1",
      author="Matheus Cunha",
      author_email="macunha@protonmail.com",
      description=("A tiny layer on top of Newspaper3k with support for "
                   "Unix-like executions and parallelism (using asyncio) to "
                   "download bulks of articles faster."),
      url="https://macunha.me",
      license="UNLICENSE",
      project_urls={
          'Source': "https://github.com/macunha1/newspaper3kli"
      },
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Environment :: Console',

          'Natural Language :: English',

          # Python versions supported
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8'
      ],
      keywords='newspaper3k cli',
      packages=find_packages(),
      python_requires='>=3, <4',
      install_requires=read_file("requirements.txt").split("\n"),

      data_files=[('', ['UNLICENSE'])],

      long_description=read_file("README.md"),
      long_description_content_type="text/markdown",

      py_modules=["newspaper3kli"],
      entry_points={
          'console_scripts': [
              'newspaper3kli = newspaper3kli:main'
          ]
      })
