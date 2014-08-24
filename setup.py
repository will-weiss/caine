from distutils.core import setup

setup(
    name='waltz',
    version='0.0.1',
    author='Will Weiss',
    author_email='will.weiss1230@gmail.com',
    packages=['waltz'],
    scripts=[],
    url='https://github.com/will-weiss/waltz/',
    license='http://www.apache.org/licenses/LICENSE-2.0.html',
    description='supporting actors offer concurrent inbox processing',
    long_description=open('README.md').read(),
    install_requires=[],
)
