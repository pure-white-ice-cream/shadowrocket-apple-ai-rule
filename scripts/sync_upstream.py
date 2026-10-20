#!/usr/bin/env python3
"""Refresh upstream rules and apply persistent service policies and proxy groups."""

from ipaddress import ip_network
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
SERVICE_PATCH = ROOT / "rules/service-groups.list"
BYPASS_REMOVALS = {"*.ls.apple.com", "seed-sequoia.siri.apple.com"}
GROUP_NAMES = ("Apple AI", "ChatGPT", "苹果服务", "微软服务")
PROXY_GROUPS = (
    "# Each group defaults to the home-screen proxy; all imported nodes are selectable.\n"
    + "\n".join(
        f"{name} = select,PROXY,DIRECT,policy-regex-filter=.*,policy-select-name=PROXY"
        for name in GROUP_NAMES
    ) + "\n"
)
NOTICE = (
    "# Derived from Johnshall/Shadowrocket-ADBlock-Rules-Forever (Moshel and Johnshall).\n"
    "# License: CC BY-SA 4.0; https://creativecommons.org/licenses/by-sa/4.0/\n"
    "# Local changes: AI/service policy groups, proxy defaults, and Siri bypass fixes.\n"
    "# Source: " + UPSTREAM_URL + "\n\n"
)


def validate_patch(patch: str, policies: set[str], *, allow_ip: bool = False) -> str:
    patch = patch.replace("\r\n", "\n").strip()
    active = [line.strip() for line in patch.splitlines()
              if line.strip() and not line.lstrip().startswith("#")]
    if not active:
        raise ValueError("Local rule patch is empty")
    for line in active:
        fields = line.split(",")
        if len(fields) < 3 or fields[2] not in policies:
            raise ValueError("Local patch contains an unsupported policy")
        if fields[0] in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
            if len(fields) != 3 or not re.fullmatch(r"[a-z0-9.-]+", fields[1]):
                raise ValueError("Invalid local domain rule")
        elif allow_ip and fields[0] in {"IP-CIDR", "IP-CIDR6"}:
            if len(fields) != 4 or fields[3] != "no-resolve":
                raise ValueError("Local IP rules must use no-resolve")
            network = ip_network(fields[1], strict=True)
            if network.version != (6 if fields[0] == "IP-CIDR6" else 4):
                raise ValueError("Local IP rule has the wrong address family")
        else:
            raise ValueError("Local patch contains an unsupported rule type")
    return patch


def merge_config(source: str, patch: str, service_patch: str) -> str:
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

    patch = validate_patch(patch, {"PROXY", "Apple AI", "ChatGPT"})
    service_patch = validate_patch(service_patch, {"苹果服务", "微软服务"}, allow_ip=True)

    # Leave the upstream advertising block ahead of ordinary service routing.
    # Insert before its first non-reject rule, including broad domain/GEOIP rules.
    service_offset = 0
    for line in rule_body.splitlines(keepends=True):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            fields = [field.strip() for field in stripped.split(",")]
            policy = fields[1] if fields[0].upper() == "FINAL" else (
                fields[2] if len(fields) >= 3 else ""
            )
            if not policy.upper().startswith("REJECT"):
                break
        service_offset += len(line)
    else:
        raise ValueError("Cannot find the upstream service rule boundary")
    insertion = rule_match.end() + service_offset
    source = (source[:insertion]
              + "# Local service policies: override upstream direct/proxy defaults below.\n"
              + service_patch + "\n\n" + source[insertion:])

    # Only change skip-proxy in General. Keep LAN and captive-portal bypasses.
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

    # Preserve any unrelated upstream groups and avoid silently shadowing names.
    group_matches = list(re.finditer(r"^\[Proxy Group\][ \t]*\n", merged, re.MULTILINE))
    if len(group_matches) > 1:
        raise ValueError("Upstream has duplicate Proxy Group sections")
    if group_matches:
        group_start = group_matches[0].end()
        next_section = re.search(r"^\[", merged[group_start:], re.MULTILINE)
        group_end = group_start + next_section.start() if next_section else len(merged)
        existing_names = {
            line.split("=", 1)[0].strip()
            for line in merged[group_start:group_end].splitlines()
            if "=" in line and not line.lstrip().startswith("#")
        }
        if existing_names.intersection(GROUP_NAMES):
            raise ValueError("Upstream proxy group conflicts with a local group")
        merged = merged[:group_end] + PROXY_GROUPS + "\n" + merged[group_end:]
    else:
        merged = re.sub(r"^\[Rule\][ \t]*\n",
                        lambda _: "[Proxy Group]\n" + PROXY_GROUPS + "\n[Rule]\n",
                        merged, count=1, flags=re.MULTILINE)
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
    merged = merge_config(source.decode("utf-8-sig"), PATCH.read_text(encoding="utf-8"),
                          SERVICE_PATCH.read_text(encoding="utf-8"))
    if OUTPUT.exists() and OUTPUT.read_text(encoding="utf-8") == merged:
        print("No upstream or local policy changes")
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
