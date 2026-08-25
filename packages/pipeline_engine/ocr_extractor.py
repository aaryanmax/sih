from __future__ import annotations

import logging
import re
from typing import List

from PIL import Image

logger = logging.getLogger(__name__)


class OcrExtractor:
    def __init__(self, lang: str = "eng", min_confidence: int = 40):
        """
        Args:
            lang: tesseract language code.
            min_confidence: drop low-confidence word detections (0-100).
        """
        self.lang = lang
        self.min_confidence = min_confidence
        logger.info("OcrExtractor configured: lang=%s min_conf=%d", lang, min_confidence)

    def extract_text(self, image: Image.Image) -> str:
        """Return the cleaned, concatenated OCR text found in the frame."""
        try:
            import pytesseract

            data = pytesseract.image_to_data(image, lang=self.lang, output_type=pytesseract.Output.DICT)

            words = [
                word.strip()
                for word, conf in zip(data["text"], data["conf"])
                if word.strip() and int(conf) >= self.min_confidence
            ]
            return " ".join(words)
        except Exception as e:
            logger.debug("OCR extraction skipped or failed: %s", e)
            return ""

    def extract_text_parallel(self, images: List[Image.Image], max_workers: int = 4) -> List[str]:
        """Extract OCR text from multiple video frames simultaneously across CPU cores."""
        if not images:
            return []
        from concurrent.futures import ThreadPoolExecutor

        workers = min(max_workers, len(images))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            return list(executor.map(self.extract_text, images))

    def extract_text_batch(self, images: List[Image.Image], max_workers: int = 4) -> List[str]:
        return self.extract_text_parallel(images, max_workers=max_workers)


def text_match_score(query_text: str, ocr_text: str) -> float:
    """
    Simple lexical overlap score between the query and a frame's OCR text —
    fraction of query words that appear in the OCR text.
    """
    if not ocr_text or not ocr_text.strip():
        return 0.0

    # Strip punctuation before splitting so "AHEAD." and "ahead" count as
    # the same word instead of missing each other in the set overlap.
    query_words = set(re.sub(r"[^\w\s]", " ", query_text.lower()).split())
    ocr_words = set(re.sub(r"[^\w\s]", " ", ocr_text.lower()).split())
    if not query_words:
        return 0.0

    overlap = query_words.intersection(ocr_words)
    return len(overlap) / len(query_words)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Text match scoring can be tested without any image/model
    print(
        "Match 'speed limit 60' in 'SPEED LIMIT 60 AHEAD':", text_match_score("speed limit 60", "SPEED LIMIT 60 AHEAD")
    )
    print("Match 'red car' in 'SPEED LIMIT 60 AHEAD':", text_match_score("red car", "SPEED LIMIT 60 AHEAD"))
    print("Punctuation check 'ahead' in 'SPEED LIMIT 60 AHEAD.':", text_match_score("ahead", "SPEED LIMIT 60 AHEAD."))
