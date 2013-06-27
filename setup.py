#
#   Copyright 2013 Cisco Systems
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from setuptools import setup, find_packages

setup(
    name='django-cloudslave',
    version='0.2.2',
    description='Create, use and destroy temporary slaves in the cloud',
    author='Soren Hansen',
    author_email='sorhanse@cisco.com',
    url='http://github.com/sorenh/python-django-cloudslave',
    packages=find_packages(),
    include_package_data=True,
    license='Apache 2.0',
    keywords='django openstack cloud',
    install_requires=[
        'django',
        'python-novaclient',
        'south'
    ],
    test_suite='tests.main',
    classifiers=[
      'Development Status :: 2 - Pre-Alpha',
      'Environment :: Web Environment',
      'Framework :: Django',
      'Intended Audience :: Developers',
      'License :: OSI Approved :: Apache Software License',
      'Operating System :: POSIX :: Linux',
      'Programming Language :: Python',
      'Topic :: Software Development',
     ]
)
