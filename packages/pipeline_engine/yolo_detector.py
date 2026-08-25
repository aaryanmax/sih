from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Set

from PIL import Image

logger = logging.getLogger(__name__)


def _get_default_yolo_model() -> str:
    env_model = os.getenv("YOLO_MODEL")
    if env_model:
        return env_model
    candidates = [
        Path(__file__).resolve().parents[2] / "data" / "models" / "yolov8n.pt",
        Path("data/models/yolov8n.pt"),
        Path("yolov8n.pt"),
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return "yolov8n.pt"


DEFAULT_MODEL = _get_default_yolo_model()  # Fast nano default model


class YoloDetector:
    def __init__(self, model_name: str = DEFAULT_MODEL, confidence: float = 0.35):
        """
        Args:
            model_name: ultralytics checkpoint. yolov8n (nano) / yolo26n is the right
                        default for a latency-sensitive pre-filter step.
            confidence: minimum detection confidence to keep a label.
        """
        self.model_name = model_name
        self.confidence = confidence
        self._model = None
        logger.info("YoloDetector configured: model=%s conf=%.2f", model_name, confidence)

    def _ensure_loaded(self):
        if self._model is not None:
            return
        try:
            from ultralytics import YOLO

            logger.info("Loading YOLO model '%s'...", self.model_name)
            self._model = YOLO(self.model_name)
        except Exception as e:
            logger.warning("Could not load YOLO model '%s' (%s). YOLO detections will be skipped.", self.model_name, e)
            self._model = None

    def detect_labels(self, image: Image.Image) -> Set[str]:
        """
        Run detection on a single frame, return the set of distinct object
        class names found above the confidence threshold.
        """
        self._ensure_loaded()
        if self._model is None:
            return set()

        try:
            results = self._model.predict(image, conf=self.confidence, verbose=False)

            labels: Set[str] = set()
            for result in results:
                if result.boxes is None:
                    continue

                names_map = (
                    result.names if hasattr(result, "names") and result.names else getattr(self._model, "names", {})
                )
                for cls_id in result.boxes.cls.tolist():
                    idx = int(cls_id)
                    if names_map and idx in names_map:
                        labels.add(str(names_map[idx]).lower())
            return labels
        except Exception as e:
            logger.warning("YOLO detection failed: %s", e)
            return set()

    def detect_labels_batch(self, images: List[Image.Image]) -> List[Set[str]]:
        return [self.detect_labels(img) for img in images]


# ---------------------------------------------------------------------------
# Query -> object keyword extraction
# ---------------------------------------------------------------------------

# COCO's 80 classes — the set YOLO's default checkpoint detects. Matching
# query words against this vocabulary is what lets us know a query is
# "object-bearing" and which object to filter/boost on.
COCO_CLASSES = {
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "airplane",
    "bus",
    "train",
    "truck",
    "boat",
    "traffic light",
    "fire hydrant",
    "stop sign",
    "parking meter",
    "bench",
    "bird",
    "cat",
    "dog",
    "horse",
    "sheep",
    "cow",
    "elephant",
    "bear",
    "zebra",
    "giraffe",
    "backpack",
    "umbrella",
    "handbag",
    "tie",
    "suitcase",
    "frisbee",
    "skis",
    "snowboard",
    "sports ball",
    "kite",
    "baseball bat",
    "baseball glove",
    "skateboard",
    "surfboard",
    "tennis racket",
    "bottle",
    "wine glass",
    "cup",
    "fork",
    "knife",
    "spoon",
    "bowl",
    "banana",
    "apple",
    "sandwich",
    "orange",
    "broccoli",
    "carrot",
    "hot dog",
    "pizza",
    "donut",
    "cake",
    "chair",
    "couch",
    "potted plant",
    "bed",
    "dining table",
    "toilet",
    "tv",
    "laptop",
    "mouse",
    "remote",
    "keyboard",
    "cell phone",
    "microwave",
    "oven",
    "toaster",
    "sink",
    "refrigerator",
    "book",
    "clock",
    "vase",
    "scissors",
    "teddy bear",
    "hair drier",
    "toothbrush",
}


def extract_object_keywords(query_text: str) -> Set[str]:
    """
    Extract any COCO-class object mentions from a natural-language query.
    Simple substring/word match against the known vocabulary — good enough
    for pre-filtering since we only need to know "is this object in the
    frame at all", not full NLP parsing.

    e.g. "a red car turning left" -> {"car"}
         "person walking a dog"   -> {"person", "dog"}
         "sunset over the ocean"  -> set()  (no COCO object mentioned)
    """
    query_lower = re.sub(r"[^\w\s]", " ", query_text.lower())
    words = set(query_lower.split())

    found = set()
    for cls in COCO_CLASSES:
        if " " in cls:  # multi-word classes like "traffic light"
            if cls in query_lower:
                found.add(cls)
        elif cls in words:
            found.add(cls)
    return found


# ---------------------------------------------------------------------------
# Filtering / boosting helpers — used by the pipeline
# ---------------------------------------------------------------------------


def prefilter_frames_by_object(
    query_text: str,
    frame_labels: Dict[str, Set[str]],
) -> List[str]:
    """
    Given a query and a {frame_id: detected_labels} map (built at index
    time), return only the frame_ids that contain every object keyword
    mentioned in the query. If the query has no object keywords, returns
    all frame_ids unfiltered (nothing to filter on).
    """
    keywords = extract_object_keywords(query_text)
    if not keywords:
        return list(frame_labels.keys())

    matched = [frame_id for frame_id, labels in frame_labels.items() if keywords.issubset(labels)]
    logger.info(
        "Object pre-filter: query keywords=%s -> %d/%d frames match",
        keywords,
        len(matched),
        len(frame_labels),
    )
    return matched


def object_boost_score(query_text: str, frame_labels: Set[str], boost: float = 0.5) -> float:
    """
    Additive score bonus: +boost for each query object keyword that is
    present in this frame's detected labels. Use this instead of hard
    pre-filtering when you want to bias ranking rather than exclude frames
    entirely (safer when YOLO might have missed a detection).
    """
    keywords = extract_object_keywords(query_text)
    if not keywords:
        return 0.0
    matched = keywords.intersection(frame_labels)
    return boost * len(matched)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test keyword extraction (no model download needed)
    print("Keywords in 'a red car turning left':", extract_object_keywords("a red car turning left at an intersection"))
    print("Keywords in 'person walking a dog':", extract_object_keywords("person walking a dog in the park"))
    print("Keywords in 'sunset over the ocean':", extract_object_keywords("sunset over the ocean"))

    # Test prefilter/boost logic with fake labels (no model needed)
    fake_labels = {
        "frame_1": {"car", "person"},
        "frame_2": {"dog", "person"},
        "frame_3": {"tree"},  # not a COCO class, ignored
    }
    print("Prefiltered frames for 'a car on the road':", prefilter_frames_by_object("a car on the road", fake_labels))
    print("Object boost score:", object_boost_score("a car on the road", {"car", "person"}))
