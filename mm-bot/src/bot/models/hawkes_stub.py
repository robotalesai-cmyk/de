"""Placeholder for Hawkes process intensity model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HawkesParams:
    baseline: float
    excitation: float
    decay: float


class HawkesStub:
    """A minimal stub returning constant intensity."""

    def __init__(self, params: HawkesParams) -> None:
        self.params = params

    def intensity(self) -> float:
        return max(self.params.baseline, 1e-6)
