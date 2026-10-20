"""nomo-pvad/ERes2NetV2 adapter. Imports, formats and model files stay in this module."""

import hashlib
import json
import sys
from pathlib import Path


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

    def set_embedding(self, pcm: bytes) -> None:
        self.session.set_enrollment_emb(self._decode(pcm))

    def enroll(self, pcm: bytes) -> list[float]:
        return self.model.extract_emb(self._decode(pcm)).cpu().numpy().reshape(-1).tolist()

    def probability(self, pcm: bytes) -> float:
        return self.session.process_chunk(self._decode(pcm))
