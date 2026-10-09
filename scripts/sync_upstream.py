#!/usr/bin/env python3
"""Refresh the full upstream config and apply the repository's AI rules."""

from pathlib import Path
import re
import tempfile
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_URL = (
    "https://johnshall.github.io/Shadowrocket-ADBlock-Rules-Forever/"
    "sr_top500_whitelist_ad.conf"
)
OUTPUT = ROOT / "shadowrocket-apple-ai.conf"
PATCH = ROOT / "rules/apple-ai-chatgpt.list"
BYPASS_REMOVALS = {"*.ls.apple.com", "seed-sequoia.siri.apple.com"}
NOTICE = (
    "# Derived from Johnshall/Shadowrocket-ADBlock-Rules-Forever (Moshel and Johnshall).\n"
    "# License: CC BY-SA 4.0; https://creativecommons.org/licenses/by-sa/4.0/\n"
    "# Local changes: prepend AI proxy rules and remove Siri/location proxy bypasses.\n"
    "# Source: " + UPSTREAM_URL + "\n\n"
)


def merge_config(source: str, patch: str) -> str:
    source = source.replace("\r\n", "\n")
    sections = re.findall(r"^\[([^\]]+)\]\s*$", source, re.MULTILINE)
    if sections.count("General") != 1 or sections.count("Rule") != 1:
        raise ValueError("Upstream must contain exactly one General and one Rule section")
    if sections.index("General") > sections.index("Rule"):
        raise ValueError("Unexpected upstream section order")
    rule_match = re.search(r"^\[Rule\][ \t]*\n", source, re.MULTILINE)
    if rule_match is None:
        raise ValueError("Missing Rule section header")
    rule_end = re.search(r"^\[", source[rule_match.end():], re.MULTILINE)
    rule_body = source[rule_match.end():]
    if rule_end:
        rule_body = rule_body[:rule_end.start()]
    if not re.search(r"^FINAL\s*,\s*PROXY\s*$", rule_body, re.MULTILINE | re.IGNORECASE):
        raise ValueError("Upstream is missing its final proxy rule")
    ad_rules = re.findall(
        r"^DOMAIN(?:-SUFFIX)?,[^,\n]+,REJECT\s*$",
        rule_body, re.MULTILINE | re.IGNORECASE,
    )
    if len(ad_rules) < 100:
        raise ValueError("Upstream has too few advertising rules; refusing to replace config")

    patch = patch.replace("\r\n", "\n").strip()
    active_patch = [line.strip() for line in patch.splitlines()
                    if line.strip() and not line.lstrip().startswith("#")]
    if not active_patch:
        raise ValueError("AI patch is empty")
    for line in active_patch:
        if not re.fullmatch(r"DOMAIN(?:-SUFFIX|-KEYWORD)?,[a-z0-9.-]+,PROXY", line):
            raise ValueError("AI patch must contain only domain rules with PROXY policy")

    # Only change skip-proxy in General. Preserve every other upstream line.
    general_start = re.search(r"^\[General\][ \t]*\n", source, re.MULTILINE)
    if general_start is None:
        raise ValueError("Missing General section header")
    general_end_match = re.search(r"^\[", source[general_start.end():], re.MULTILINE)
    general_end = (general_start.end() + general_end_match.start()
                   if general_end_match else len(source))
    general = source[general_start.end():general_end]
    skip_matches = list(re.finditer(r"^skip-proxy\s*=([^\n]*)$", general, re.MULTILINE))
    if len(skip_matches) != 1:
        raise ValueError("Expected exactly one skip-proxy setting in General")
    skip = skip_matches[0]
    # Reject ambiguous inline comments instead of silently changing their meaning.
    if "#" in skip.group(1):
        raise ValueError("Unexpected inline comment in skip-proxy")
    kept = [item.strip() for item in skip.group(1).split(",")
            if item.strip() and item.strip().lower() not in BYPASS_REMOVALS]
    replacement = "skip-proxy = " + ", ".join(kept)
    general = general[:skip.start()] + replacement + general[skip.end():]
    merged = source[:general_start.end()] + general + source[general_end:]
    merged = re.sub(
        r"(^\[Rule\][ \t]*\n)",
        lambda match: match.group(1) + "# Local AI rules: priority over upstream ad/direct rules.\n"
        + patch + "\n\n",
        merged, count=1, flags=re.MULTILINE,
    )
    return NOTICE + merged.rstrip("\n") + "\n"


def main() -> None:
    request = Request(UPSTREAM_URL, headers={"User-Agent": "shadowrocket-apple-ai-rule-sync"})
    # HTTPS certificate verification uses Python's default trusted SSL context.
    with urlopen(request, timeout=60) as response:
        if not response.url.startswith("https://"):
            raise ValueError("Upstream redirected away from HTTPS")
        source = response.read(16 * 1024 * 1024 + 1)
    if len(source) > 16 * 1024 * 1024:
        raise ValueError("Upstream exceeds the expected size limit")
    merged = merge_config(source.decode("utf-8-sig"), PATCH.read_text(encoding="utf-8"))
    if OUTPUT.exists() and OUTPUT.read_text(encoding="utf-8") == merged:
        print("No upstream or AI rule changes")
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=ROOT, prefix=".sync-", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(merged)
        temporary.replace(OUTPUT)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(f"Updated {OUTPUT.name}: {len(merged.splitlines())} lines")


if __name__ == "__main__":
    main()
