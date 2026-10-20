"""nomo-pvad/ERes2NetV2 adapter. Imports, formats and model files stay in this module."""

import hashlib
import json
import math
import sys
from pathlib import Path

from ports.result import ErrorCode, Failure, Result, Success


class NomoAdapter:
    def __init__(self, root: Path, manifest_path: Path):
        manifest = json.loads(manifest_path.read_text())
        for artifact in manifest["artifacts"]:
            path = root / artifact["path"]
            if not path.is_file() or path.stat().st_size != artifact["bytes"]:
                raise ValueError("model_artifact_missing")
            with path.open("rb") as content:
                if hashlib.file_digest(content, "sha256").hexdigest() != artifact["sha256"]:
                    raise ValueError("model_artifact_integrity_failed")
        # Existing, verified files prevent upstream's network fallback.
        sys.path.insert(0, str(root / "nomo"))
        import numpy as np
        import torch
        from nomo_pvad import NomoPVAD, NomoPVADSession

        torch.set_num_threads(2)
        torch.set_num_interop_threads(1)
        self.np = np
        self.model = NomoPVAD(str(root / "nomo/weights/nomo_pvad.pt"), str(root / "eres"), device="cpu")
        self.session = NomoPVADSession(self.model)

    def _decode(self, pcm: bytes):
        values = self.np.frombuffer(pcm, dtype="<f4").copy()
        if not self.np.isfinite(values).all():
            raise ValueError("invalid_pcm")
        return values

    def _call(self, pcm: bytes, size: int, operation, validate) -> Result:
        if len(pcm) != size * 4:
            return Failure(ErrorCode.INVALID_INPUT)
        try:
            values = self._decode(pcm)
        except ValueError:
            return Failure(ErrorCode.INVALID_INPUT)
        try:
            value = operation(values)
        except TimeoutError:
            return Failure(ErrorCode.TIMEOUT)
        except RuntimeError, ValueError, OSError:
            return Failure(ErrorCode.INFERENCE_FAILED)
        if not validate(value):
            return Failure(ErrorCode.INVALID_RESPONSE)
        return Success(value)

    def set_embedding(self, pcm: bytes) -> Result[None]:
        return self._call(pcm, 192, self.session.set_enrollment_emb, lambda value: value is None)

    def enroll(self, pcm: bytes) -> Result[list[float]]:
        return self._call(
            pcm,
            160000,
            lambda values: self.model.extract_emb(values).cpu().numpy().reshape(-1).tolist(),
            lambda value: (
                isinstance(value, list)
                and len(value) == 192
                and all(isinstance(x, (float, int)) and math.isfinite(x) for x in value)
            ),
        )

    def probability(self, pcm: bytes) -> Result[float]:
        return self._call(
            pcm,
            2560,
            self.session.process_chunk,
            lambda value: isinstance(value, (float, int)) and math.isfinite(value) and 0 <= value <= 1,
        )

    @classmethod
    def create(cls, root: Path, manifest_path: Path) -> Result:
        try:
            return Success(cls(root, manifest_path))
        except ImportError, OSError, RuntimeError, ValueError:
            return Failure(ErrorCode.UNAVAILABLE)
