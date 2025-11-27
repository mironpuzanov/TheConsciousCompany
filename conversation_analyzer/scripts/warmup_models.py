"""
Warm up Hugging Face models so weights are cached locally before running the pipeline.
Usage:
    python conversation_analyzer/scripts/warmup_models.py
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    pipeline,
)
from sentence_transformers import SentenceTransformer
from bertopic import BERTopic

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
LOGGER = logging.getLogger("warmup")

TEXT_MODELS: List[str] = [
    "j-hartmann/emotion-english-distilroberta-base",
    "bhadresh-savani/distilbert-base-uncased-emotion",
    "cardiffnlp/twitter-roberta-base-emotion",
    "finiteautomata/beto-emotion-analysis",
    "Hate-speech-CNERG/bert-base-uncased-hatexplain",
    "valhalla/distilbart-mnli-12-1",
    "dslim/bert-base-NER",
]

TEXT_MODEL_KWARGS = {}
TEXT_MODEL_FRAMEWORK = {}

EMBEDDING_MODELS: List[str] = [
    "sentence-transformers/all-MiniLM-L6-v2",
    "sentence-transformers/all-mpnet-base-v2",
    "hkunlp/instructor-xl",
]

SUMMARIZERS: List[str] = [
    "facebook/bart-large-cnn",
    "t5-base",
]


def get_device() -> int:
    if torch.backends.mps.is_available():
        return 0
    if torch.cuda.is_available():
        return 0
    return -1


def safe_run(description: str, func) -> None:
    try:
        func()
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Skipping %s due to error: %s", description, exc)


def warmup_text_classifiers() -> None:
    device = get_device()
    for model_name in TEXT_MODELS:
        LOGGER.info("Warming up text classifier %s", model_name)
        framework = TEXT_MODEL_FRAMEWORK.get(model_name)
        model_device = device if framework != "tf" else -1
        safe_run(
            f"text classifier {model_name}",
            lambda mn=model_name: pipeline(
                "text-classification",
                model=mn,
                device=model_device,
                model_kwargs=TEXT_MODEL_KWARGS.get(mn, {}),
                framework=framework,
            )("Test sentence for warmup."),
        )


def warmup_zero_shot() -> None:
    model_name = "valhalla/distilbart-mnli-12-1"
    LOGGER.info("Warming up zero-shot model %s", model_name)
    safe_run(
        "zero-shot",
        lambda: pipeline("zero-shot-classification", model=model_name, device=get_device())(
            "Test statement", candidate_labels=["avoidance", "self-criticism"]
        ),
    )


def warmup_ner() -> None:
    model_name = "dslim/bert-base-NER"
    LOGGER.info("Warming up NER model %s", model_name)
    safe_run(
        "ner",
        lambda: pipeline("ner", model=model_name, aggregation_strategy="simple", device=get_device())(
            "Alice met Bob in Paris."
        ),
    )


def warmup_embeddings() -> None:
    for model_name in EMBEDDING_MODELS:
        LOGGER.info("Warming up embedding model %s", model_name)
        safe_run(
            f"embedding {model_name}",
            lambda mn=model_name: SentenceTransformer(mn).encode("Sample text", normalize_embeddings=True),
        )


def warmup_summarizers() -> None:
    for model_name in SUMMARIZERS:
        LOGGER.info("Warming up summarizer %s", model_name)
        safe_run(
            f"summarizer {model_name}",
            lambda mn=model_name: pipeline("summarization", model=mn, device=get_device())(
                "Short text to summarize."
            ),
        )


def warmup_topic_model() -> None:
    LOGGER.info("Warming up BERTopic with MiniLM embeddings")
    safe_run(
        "bertopic",
        lambda: BERTopic(embedding_model="sentence-transformers/all-MiniLM-L6-v2").fit_transform(
            ["Short text for topic model warmup"]
        ),
    )


def main() -> None:
    cache_dir = Path.home() / ".cache" / "huggingface"
    LOGGER.info("Using HF cache at %s", cache_dir)
    warmup_text_classifiers()
    warmup_zero_shot()
    warmup_ner()
    warmup_embeddings()
    warmup_summarizers()
    warmup_topic_model()
    LOGGER.info("Warmup complete")


if __name__ == "__main__":
    main()

