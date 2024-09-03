"""
Specialwords detectors

Matches terms in word lists
"""

import json

from garak import _config
from garak.detectors.base import StringDetector


class SlursReclaimedSlurs(StringDetector):
    """Slurs and reclaimed slurs. Detects presence of any of the items from an ethnic slur list, regardless of context."""

    doc_uri = "https://en.wikipedia.org/wiki/List_of_ethnic_slurs"
    bcp47 = "en"
    tags = [
        "avid-effect:ethics:E0101",
        "avid-effect:ethics:E0301",
        "avid-effect:ethics:E0302",
        "avid-effect:performance:P0401",
    ]

    def __init__(self, config_root=_config):
        self.substrings = set([])
        with open(
            _config.transient.package_dir / "resources" / "slurprompts.jsonl",
            "r",
            encoding="utf-8",
        ) as slurfile:
            for line in slurfile:
                line = line.strip()
                if not line:
                    continue
                self.substrings.add(json.loads(line)["term"])

        super().__init__(self.substrings, config_root=config_root)
        self.matchtype = "word"
