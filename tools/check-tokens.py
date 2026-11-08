#!/usr/bin/env python3
"""Check wa.user.styl against a WhatsApp Web stylesheet.

WhatsApp ships a semantic `--WDS-*` token set; a token the theme doesn't map shows
up as a native-colored surface. Grab the current CSS URL from the page's <link> tags:

    curl -o wa.css <url> && python3 tools/check-tokens.py wa.css

Exits 1 when WhatsApp has a semantic token the theme neither maps nor excludes.
"""
import re
import sys
from pathlib import Path

# Deliberately left to WhatsApp: fixed colors on media and platform chrome.
EXCLUDED = {
    "persistent-always-black",
    "persistent-always-white",
    "systems-attachment-drawing",
    "components-platform-gesture-bar",
    "components-platform-status-bar",
    "components-profile-photo-status-ring-close-friends",
}


def semantic_tokens(css: str) -> set[str]:
    """Tokens of the base theme, which is the only block that sets the wash tokens."""
    tokens: set[str] = set()
    for body in re.findall(r"\{([^{}]*--WDS-background-wash-plain:[^{}]*)\}", css):
        tokens |= set(re.findall(r"--WDS-([\w-]+?)(?:-RGB)?\s*:", body))
    return tokens


def mapped_tokens(styl: str) -> set[str]:
    return set(re.findall(r"\bwdsa?\('([\w-]+)'", styl))


def missing(css: str, styl: str) -> list[str]:
    return sorted(semantic_tokens(css) - mapped_tokens(styl) - EXCLUDED)


def self_check() -> None:
    css = ".a{--WDS-background-wash-plain:#000;--WDS-accent:#000;--WDS-accent-RGB:0,0,0}.b{--WDS-other:#000}"
    assert semantic_tokens(css) == {"background-wash-plain", "accent"}
    assert missing(css, "wds('accent', 'ac-0')") == ["background-wash-plain"]
    assert missing(css, "wds('accent', 'ac-0')\nwdsa('background-wash-plain', 'bg-0', 1)") == []


def main() -> int:
    self_check()
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    css = Path(sys.argv[1]).read_text()
    styl = (Path(__file__).parent.parent / "wa.user.styl").read_text()
    if not semantic_tokens(css):
        print("No base theme block found: WhatsApp changed how it ships tokens.")
        return 1
    gaps = missing(css, styl)
    stale = sorted(mapped_tokens(styl) - semantic_tokens(css))
    for token in stale:
        print(f"stale   {token}")
    for token in gaps:
        print(f"missing {token}")
    print(f"{len(semantic_tokens(css))} tokens, {len(gaps)} missing, {len(stale)} stale")
    return 1 if gaps else 0


if __name__ == "__main__":
    sys.exit(main())
