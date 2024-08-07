#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import sys
from optparse import OptionParser

import eventlet.debug

from swift.common.ring import Ring
from swift.common.utils import split_path
from swift.common.storage_policy import POLICIES

from swift.container.reconciler import add_to_reconciler_queue
"""
This tool is primarily for debugging and development but can be used an example
of how an operator could enqueue objects manually if a problem is discovered -
might be particularly useful if you need to hack a fix into the reconciler
and re-run it.
"""

USAGE = """
%prog <policy_index> </a/c/o> <timestamp> [options]

This script enqueues an object to be evaluated by the reconciler.

Arguments:
policy_index: the policy the object is currently stored in.
      /a/c/o: the full path of the object - utf-8
   timestamp: the timestamp of the datafile/tombstone.

""".strip()

parser = OptionParser(USAGE)
parser.add_option('-X', '--op', default='PUT', choices=('PUT', 'DELETE'),
                  help='the method of the misplaced operation')
parser.add_option('-f', '--force', action='store_true',
                  help='force an object to be re-enqueued')


def main():
    eventlet.debug.hub_exceptions(True)
    options, args = parser.parse_args()
    try:
        policy_index, path, timestamp = args
    except ValueError:
        sys.exit(parser.print_help())
    container_ring = Ring('/etc/swift/container.ring.gz')
    policy = POLICIES.get_by_index(policy_index)
    if not policy:
        return 'ERROR: invalid storage policy index: %s' % policy
    try:
        account, container, obj = split_path(path, 3, 3, True)
    except ValueError as e:
        return 'ERROR: %s' % e
    container_name = add_to_reconciler_queue(
        container_ring, account, container, obj,
        policy.idx, timestamp, options.op, force=options.force)
    if not container_name:
        return 'ERROR: unable to enqueue!'
    print(container_name)


if __name__ == "__main__":
    sys.exit(main())
