from __future__ import annotations

import os
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class NormalizationResult:
    raw: str
    normalized: str


_DEFAULT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bchat\s*gpt\b", re.I), "chatgpt"),
    (re.compile(r"\bchad\s*gpt\b", re.I), "chatgpt"),
    (re.compile(r"\bpanchayat\s*gpt\b", re.I), "chatgpt"),
    (re.compile(r"\bgoogle\s*crome\b", re.I), "google chrome"),
    # Replace bare "chrome" but avoid turning "google chrome" into "google google chrome"
    (re.compile(r"(?<!google\s)\bchrome\b", re.I), "google chrome"),
    (re.compile(r"\bfile\s*explorer\b", re.I), "file explorer"),
    (re.compile(r"\bthis\s*pc\b", re.I), "this pc"),
    (re.compile(r"\bdevice\s*manager\b", re.I), "device manager"),
    (re.compile(r"\btask\s*manager\b", re.I), "task manager"),
]


def normalize_transcript(text: str) -> NormalizationResult:
    raw = (text or "").strip()
    out = raw

    # Apply default corrections
    for pat, repl in _DEFAULT_RULES:
        out = pat.sub(repl, out)

    # Optional custom rules via env: "from=>to;from2=>to2"
    custom = os.getenv("VORTEX_NORMALIZER_RULES", "").strip()
    if custom:
        parts = [p.strip() for p in custom.split(";") if p.strip()]
        for p in parts:
            if "=>" not in p:
                continue
            src, dst = p.split("=>", 1)
            src = src.strip()
            dst = dst.strip()
            if not src:
                continue
            out = re.sub(rf"\b{re.escape(src)}\b", dst, out, flags=re.I)

    out = re.sub(r"\s+", " ", out).strip()
    return NormalizationResult(raw=raw, normalized=out)


__all__ = ["normalize_transcript", "NormalizationResult"]

