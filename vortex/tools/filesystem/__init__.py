import asyncio
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def _normalize_scope(scope: Optional[str]) -> Optional[Path]:
    if not scope:
        return None
    s = scope.strip().strip('"')
    low = s.lower()
    user = os.getenv("USERPROFILE") or ""
    if low in {"desktop"} and user:
        return Path(user) / "Desktop"
    if low in {"documents", "docs"} and user:
        return Path(user) / "Documents"
    if low in {"downloads"} and user:
        return Path(user) / "Downloads"
    if re.fullmatch(r"[a-zA-Z]:", s):
        return Path(s + "\\")
    if re.fullmatch(r"[a-zA-Z]:\\", s):
        return Path(s)
    return Path(s)


def _iter_paths(root: Path, max_results: int) -> Iterable[Path]:
    count = 0
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dn_low = dirpath.lower()
        if "\\windows\\winsxs" in dn_low or "\\windows\\installer" in dn_low:
            dirnames[:] = []
            continue
        for name in filenames:
            yield Path(dirpath) / name
            count += 1
            if count >= max_results:
                return
        for name in dirnames:
            yield Path(dirpath) / name
            count += 1
            if count >= max_results:
                return


def _fuzzy_contains(name: str, q: str) -> bool:
    n = re.sub(r"[^a-z0-9]", "", name.lower())
    qq = re.sub(r"[^a-z0-9]", "", q.lower())
    return qq in n or n in qq


def _token_overlap_score(name: str, query: str) -> int:
    name_tokens = set(re.findall(r"[a-z0-9]+", (name or "").lower()))
    query_tokens = set(re.findall(r"[a-z0-9]+", (query or "").lower()))
    if not name_tokens or not query_tokens:
        return 0
    return len(name_tokens.intersection(query_tokens))


def _approx_size_match(bytes_size: int, target_bytes: int, tolerance: float) -> bool:
    if target_bytes <= 0:
        return True
    lo = int(target_bytes * (1.0 - tolerance))
    hi = int(target_bytes * (1.0 + tolerance))
    return lo <= bytes_size <= hi


def _parse_size_to_bytes(size: str) -> Optional[int]:
    if not size:
        return None
    s = size.strip().lower().replace(" ", "")
    m = re.match(r"^(\d+(\.\d+)?)([a-z]+)?$", s)
    if not m:
        return None
    val = float(m.group(1))
    unit = (m.group(3) or "b").lower()
    mul = 1
    if unit in {"b", "bytes"}:
        mul = 1
    elif unit in {"k", "kb", "kib"}:
        mul = 1024
    elif unit in {"m", "mb", "mib"}:
        mul = 1024**2
    elif unit in {"g", "gb", "gib"}:
        mul = 1024**3
    elif unit in {"t", "tb", "tib"}:
        mul = 1024**4
    return int(val * mul)


async def vortex_open_drive(drive: str) -> Dict[str, Any]:
    d = (drive or "").strip()
    if not d:
        return {"ok": False, "error": "No drive specified."}
    if re.fullmatch(r"[a-zA-Z]", d):
        d = d + ":\\"
    if re.fullmatch(r"[a-zA-Z]:", d):
        d = d + "\\"
    p = Path(d)
    if not p.exists():
        return {"ok": False, "error": f"Drive '{drive}' not found."}
    try:
        os.startfile(str(p))
        return {"ok": True, "message": f"Opened {p}."}
    except Exception as e:
        return {"ok": False, "error": f"Failed to open drive: {e}"}


async def vortex_open_folder(path: str) -> Dict[str, Any]:
    p = _normalize_scope(path)
    if not p:
        return {"ok": False, "error": "No folder specified."}
    if not p.exists():
        return {"ok": False, "error": f"Folder not found: {p}"}
    try:
        os.startfile(str(p))
        return {"ok": True, "message": f"Opened {p}."}
    except Exception as e:
        return {"ok": False, "error": f"Failed to open folder: {e}"}


async def vortex_search(
    query: str,
    *,
    scope: Optional[str] = None,
    kind: str = "any",
    max_results: int = 25,
) -> Dict[str, Any]:
    q = (query or "").strip()
    if not q:
        return {"ok": False, "error": "No search query provided."}
    root = _normalize_scope(scope) or Path(os.getenv("USERPROFILE") or "C:\\")
    if not root.exists():
        return {"ok": False, "error": f"Scope path not found: {root}"}

    kind = (kind or "any").lower()
    max_results = max(1, min(int(max_results), 200))

    def _run() -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for p in _iter_paths(root, max_results=max_results * 30):
            try:
                if not _fuzzy_contains(p.name, q):
                    continue
                is_dir = p.is_dir()
                if kind == "file" and is_dir:
                    continue
                if kind == "folder" and not is_dir:
                    continue
                size = None
                if not is_dir:
                    try:
                        size = p.stat().st_size
                    except Exception:
                        size = None
                results.append({"path": str(p), "name": p.name, "is_dir": is_dir, "size_bytes": size})
                if len(results) >= max_results:
                    break
            except Exception:
                continue
        return results

    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(None, _run)
    if not results:
        return {"ok": False, "error": f"No matches found for '{query}' in {root}."}
    return {"ok": True, "message": f"Found {len(results)} result(s).", "results": results}


async def vortex_search_by_size(
    query: str,
    *,
    approx_size: str,
    tolerance: float = 0.15,
    scope: Optional[str] = None,
    kind: str = "file",
    max_results: int = 20,
) -> Dict[str, Any]:
    target = _parse_size_to_bytes(approx_size)
    if target is None:
        return {"ok": False, "error": f"Invalid size '{approx_size}'. Try like '9.5gb'."}

    base = await vortex_search(query, scope=scope, kind=kind, max_results=max_results * 5)
    if not base.get("ok"):
        return base

    results = base.get("results") or []
    filtered = []
    for r in results:
        sb = r.get("size_bytes")
        if isinstance(sb, int) and _approx_size_match(sb, target, float(tolerance)):
            filtered.append(r)
    if not filtered:
        return {"ok": False, "error": f"Found matches for '{query}', but none near {approx_size}."}
    return {"ok": True, "message": f"Found {len(filtered)} near {approx_size}.", "results": filtered[:max_results]}


async def vortex_open_in_explorer(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"ok": False, "error": f"Path not found: {p}"}
    try:
        if p.is_dir():
            os.startfile(str(p))
        else:
            subprocess.Popen(["explorer", "/select,", str(p)])
        return {"ok": True, "message": "Opened in File Explorer."}
    except Exception as e:
        return {"ok": False, "error": f"Failed to open in Explorer: {e}"}


async def vortex_find_and_open(
    query: str,
    *,
    scope: Optional[str] = None,
    kind: str = "file",
    max_results: int = 30,
) -> Dict[str, Any]:
    q = (query or "").strip()
    if not q:
        return {"ok": False, "error": "No file/folder name provided to open."}

    search_res = await vortex_search(q, scope=scope, kind=kind, max_results=max_results)
    if not search_res.get("ok"):
        return search_res

    results = search_res.get("results") or []
    if not results:
        return {"ok": False, "error": f"No matches found for '{q}'."}

    ranked = sorted(
        results,
        key=lambda r: (
            _token_overlap_score(str(r.get("name", "")), q),
            len(str(r.get("name", ""))),
        ),
        reverse=True,
    )
    best = ranked[0]
    best_path = str(best.get("path", "")).strip()
    if not best_path:
        return {"ok": False, "error": "Match found but path was empty."}

    try:
        os.startfile(best_path)
        return {
            "ok": True,
            "message": f"Opening {best.get('name')}.",
            "path": best_path,
            "match_count": len(results),
        }
    except Exception as e:
        return {"ok": False, "error": f"Found a match but failed to open it: {e}"}


__all__ = [
    "vortex_open_drive",
    "vortex_open_folder",
    "vortex_search",
    "vortex_search_by_size",
    "vortex_open_in_explorer",
    "vortex_find_and_open",
]
