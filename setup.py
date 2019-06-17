from setuptools import setup, find_packages


setup(name="rulai_wget",
    version="0.1.2",
    packages=find_packages(where="./src/"),
    package_dir={"":"src"},
    include_package_data=False,
    package_data={"data":[]},
    description="一个多进程下载的python3版本,改编自mwget的python2版本",
    author="miaorulai",
    author_email="miaorulai@gmail.com",
    url='',
    license="MIT",
    install_requires=[],
    entry_points = {'console_scripts': "mwget = mwget.__init__:main"}
)