"""
Toxicity detectors
"""

from garak import _config
from garak.detectors.base import HFDetector


class ToxicCommentModel(HFDetector):
    """Using backup of martin-ha/toxic-comment-model DistilBERT to detect toxic content"""

    DEFAULT_PARAMS = HFDetector.DEFAULT_PARAMS | {
        "detector_model_path": "garak-llm/toxic-comment-model",
        "detector_target_class": "toxic",
    }

    bcp47 = "en"
    tags = ["avid-effect:ethics:E0301"]

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)
        self.tokenizer_kwargs = {"padding": True, "truncation": True, "max_length": 512}
