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

import os
import sys

os.environ["DJANGO_SETTINGS_MODULE"] = 'cloudslave.testsettings'
from cloudslave import testsettings as settings


def run_tests(settings):
    from django.test.utils import get_runner

    TestRunner = get_runner(settings)
    test_runner = TestRunner(interactive=False)
    failures = test_runner.run_tests(['cloudslave'])
    return failures


def main():
    failures = run_tests(settings)
    sys.exit(failures)

if __name__ == '__main__':
    main()
