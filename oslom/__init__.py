# An OSLOM (community finding) runner for Python
# Copyright 2014 Hugo Hromic
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# OSLOM -- the community finding algorithm -- is described in:
# Lancichinetti, Andrea, et al. "Finding Statistically Significant
# Communities in Networks." PloS one 6.4 (2011): e18961.

"""An OSLOM Runner for Python."""

from oslom.runner import run
from oslom.runner import run_in_memory

# import defaults
from oslom.runner import (
    DEF_MIN_CLUSTER_SIZE,
    DEF_OSLOM_EXEC,
    DEF_OSLOM_ARGS,
)
