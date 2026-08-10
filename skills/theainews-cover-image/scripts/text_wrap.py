"""Pure text-wrapping helpers (no third-party imports; unit-testable)."""

from __future__ import annotations

from typing import Callable


# Break AFTER these characters when a line must wrap.
SOFT_BREAK_AFTER = set("，。、；：？！）】》」』”…—·,;:!?)]}%")
# Prefer NOT to start a line with these characters.
SOFT_BREAK_BEFORE = set("（【《「『“‘")
HARD_SPLIT = set(" \t/｜|")


def wrap_title(text: str, measure: Callable[[str], float], max_width: float) -> list[str]:
    """Greedy character wrap that prefers breaking after CJK punctuation.

    `measure(s)` must return the pixel width of string `s`.
    """
    if not text:
        return [""]

    lines: list[str] = []
    cur = ""
    break_idx: int | None = None  # best position (within `cur`) to break later

    for ch in text:
        if cur and measure(cur + ch) > max_width:
            # Overflow: break at the last good point if we have one.
            if break_idx is not None and 0 < break_idx < len(cur):
                lines.append(cur[:break_idx])
                cur = cur[break_idx:]
            else:
                lines.append(cur)
                cur = ""
            break_idx = None

        cur += ch
        if ch in SOFT_BREAK_AFTER or ch in HARD_SPLIT:
            break_idx = len(cur)
        elif ch in SOFT_BREAK_BEFORE and len(cur) > 1:
            # Keep opening quotes/brackets attached to the previous line.
            break_idx = len(cur) - 1

    if cur:
        lines.append(cur)
    return lines
