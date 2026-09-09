"""Backend-neutral prediction contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence


@dataclass(frozen=True)
class MetricPrediction:
    score: float
    diagnostics: Mapping[str, Any] = field(default_factory=dict)


class MetricBackend(Protocol):
    alias: str
    batch_size: int

    def prepare(self) -> None: ...
    def predict_batch(self, pairs: Sequence[tuple[str, str]]) -> list[MetricPrediction]: ...
    def provenance(self) -> Mapping[str, Any]: ...
    def close(self) -> None: ...

