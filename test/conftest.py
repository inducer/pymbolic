from __future__ import annotations

import sys


collect_ignore = []
if sys.version_info < (3, 10):
    collect_ignore.append("test_pattern_match.py")
