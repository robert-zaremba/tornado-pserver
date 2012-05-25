# Copyright 2012 Robert Zaremba
# based on the original Tornado by Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

try:
    from logger import logger
except ImportError:
    import logging as logger

__author__ = "Robert Zaremba"
__version__ = version = "0.1"
__license__ = "Apache License v2"

from base import PServer
from protocols import *

