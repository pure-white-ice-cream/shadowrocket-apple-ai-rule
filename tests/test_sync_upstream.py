from ipaddress import ip_address, ip_network
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sync_upstream import merge_config

PATCH = (ROOT / "rules/apple-ai-chatgpt.list").read_text(encoding="utf-8")
SERVICES = (ROOT / "rules/service-groups.list").read_text(encoding="utf-8")


def upstream():
    advertising = "\n".join(f"DOMAIN-SUFFIX,ad{i}.example,Reject" for i in range(120))
    return (
        "# Upstream attribution\n[General]\nipv6 = false\n"
        "skip-proxy = localhost, *.ls.apple.com, seed-sequoia.siri.apple.com, "
        "*.local, captive.apple.com, sequoia.apple.com\n"
        "dns-server = system\n[Rule]\n" + advertising + "\n"
        "DOMAIN-SUFFIX,ads.apple.com,Reject\n"
        "DOMAIN-SUFFIX,ads.microsoft.com,Reject\n"
        "DOMAIN,guzzoni.apple.com,Reject\n"
        "DOMAIN-SUFFIX,apple.com,Direct\n"
        "DOMAIN-SUFFIX,ls.apple.com,Direct\n"
        "DOMAIN-SUFFIX,mzstatic.com,Direct\n"
        "DOMAIN-SUFFIX,cl2.apple.com.edgekey.net.globalredir.akadns.net,Direct\n"
        "DOMAIN-SUFFIX,cn.bing.com,Direct\n"
        "DOMAIN-SUFFIX,copilot.microsoft.com,Proxy\n"
        "DOMAIN-SUFFIX,microsoft.com,Direct\n"
        "DOMAIN-SUFFIX,live.com,Direct\n"
        "DOMAIN-SUFFIX,office.com,Direct\n"
        "DOMAIN-SUFFIX,outlook.com,Direct\n"
        "DOMAIN-SUFFIX,example.cn,Direct\n"
        "DOMAIN-SUFFIX,cn,DIRECT\nGEOIP,CN,DIRECT\n"
        "IP-CIDR,192.168.0.0/16,DIRECT\nFINAL,PROXY\n"
        "[URL Rewrite]\n^https?://example.cn https://example.com 302\n"
        "[MITM]\nhostname = *.example.cn\n"
    )


def active_rules(config):
    body = config.split("[Rule]\n", 1)[1].split("[URL Rewrite]", 1)[0]
    return [line.strip() for line in body.splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def first_policy(config, domain="", address=None):
    """Evaluate the domain/IP rules used in these routing regression cases."""
    for line in active_rules(config):
        fields = line.split(",")
        kind, value = fields[:2]
        if kind == "FINAL":
            return value
        matched = (
            (kind == "DOMAIN" and domain == value)
            or (kind == "DOMAIN-SUFFIX" and
                (domain == value or domain.endswith("." + value)))
            or (kind == "DOMAIN-KEYWORD" and value in domain)
            or (kind in {"IP-CIDR", "IP-CIDR6"} and address is not None
                and ip_address(address) in ip_network(value))
        )
        if matched:
            return fields[2]
    raise AssertionError("No matching rule")


class SyncTests(unittest.TestCase):
    def test_ai_precedes_advertising_and_service_rules(self):
        merged = merge_config(upstream(), PATCH, SERVICES)
        patch_rules = [line for line in PATCH.splitlines()
                       if line and not line.startswith("#")]
        self.assertEqual(active_rules(merged)[:len(patch_rules)], patch_rules)
        self.assertEqual(first_policy(merged, "guzzoni.apple.com"), "Apple AI")
        self.assertEqual(first_policy(merged, "gspe1-ssl.ls.apple.com"), "Apple AI")
        self.assertEqual(first_policy(merged, "chatgpt.com"), "ChatGPT")
        self.assertEqual(first_policy(merged, "api.openai.com"), "ChatGPT")
        self.assertEqual(first_policy(merged, "host.livekit.cloud"), "ChatGPT")

    def test_services_override_upstream_direct_and_proxy_defaults(self):
        merged = merge_config(upstream(), PATCH, SERVICES)
        cases = {
            "apple.com": "苹果服务",
            "apps.apple.com": "苹果服务",
            "www.apple.com.cn": "苹果服务",
            "a3.mzstatic.com": "苹果服务",
            "www.icloud.com": "苹果服务",
            "cl2.apple.com.edgekey.net.globalredir.akadns.net": "苹果服务",
            "store.apple.com.edgekey.net": "苹果服务",
            "cdn.origin-apple.com.akadns.net": "苹果服务",
            "microsoft.com": "微软服务",
            "cn.bing.com": "微软服务",
            "copilot.microsoft.com": "微软服务",
            "login.live.com": "微软服务",
            "login.microsoftonline.com": "微软服务",
            "outlook.office365.com": "微软服务",
            "outlook.com": "微软服务",
            "office.com": "微软服务",
            "example.sharepoint.com": "微软服务",
            "api.onedrive.com": "微软服务",
            "www.microsoft.com.cn": "微软服务",
            "example.cn": "Direct",
        }
        for domain, expected in cases.items():
            with self.subTest(domain=domain):
                self.assertEqual(first_policy(merged, domain), expected)

    def test_advertising_keeps_precedence_over_ordinary_services(self):
        merged = merge_config(upstream(), PATCH, SERVICES)
        for domain in ("ads.apple.com", "ads.microsoft.com", "ad119.example"):
            with self.subTest(domain=domain):
                self.assertEqual(first_policy(merged, domain), "Reject")

    def test_service_ip_rules_precede_geoip_without_resolving_domains(self):
        merged = merge_config(upstream(), PATCH, SERVICES)
        self.assertEqual(first_policy(merged, address="17.1.2.3"), "苹果服务")
        self.assertEqual(first_policy(merged, address="2620:149::1"), "苹果服务")
        self.assertEqual(first_policy(merged, address="192.168.1.1"), "DIRECT")
        rules = active_rules(merged)
        self.assertLess(rules.index("IP-CIDR,17.0.0.0/8,苹果服务,no-resolve"),
                        rules.index("GEOIP,CN,DIRECT"))

    def test_four_groups_default_to_proxy_and_allow_independent_nodes(self):
        merged = merge_config(upstream(), PATCH, SERVICES)
        self.assertEqual(merged.count("[Proxy Group]\n"), 1)
        groups = merged.split("[Proxy Group]\n", 1)[1].split("[Rule]\n", 1)[0]
        definitions = {}
        for line in groups.splitlines():
            if line and not line.startswith("#"):
                name, values = line.split(" = ", 1)
                definitions[name] = values.split(",")
        self.assertEqual(set(definitions), {"Apple AI", "ChatGPT", "苹果服务", "微软服务"})
        for values in definitions.values():
            self.assertEqual(values[:3], ["select", "PROXY", "DIRECT"])
            self.assertIn("policy-select-name=PROXY", values)
            self.assertIn("policy-regex-filter=.*", values)

    def test_removes_only_targeted_proxy_bypasses(self):
        merged = merge_config(upstream(), PATCH, SERVICES)
        self.assertIn("skip-proxy = localhost, *.local, captive.apple.com, sequoia.apple.com\n",
                      merged)
        self.assertNotIn("seed-sequoia.siri.apple.com", merged)
        self.assertNotIn("*.ls.apple.com", merged)
        self.assertIn("ipv6 = false\n", merged)
        self.assertIn("dns-server = system\n", merged)

    def test_preserves_upstream_rules_in_order_and_trailing_sections(self):
        source = upstream()
        merged = merge_config(source, PATCH, SERVICES)
        remaining = iter(active_rules(merged))
        self.assertTrue(all(rule in remaining for rule in active_rules(source)))
        self.assertEqual(source.split("[URL Rewrite]\n", 1)[1],
                         merged.split("[URL Rewrite]\n", 1)[1])
        self.assertIn("# Upstream attribution", merged)

    def test_shared_cdn_and_unrelated_domains_are_not_apple_services(self):
        merged = merge_config(upstream(), PATCH, SERVICES)
        for domain in ("assets.thirdparty.akadns.net", "assets.thirdparty.edgekey.net",
                       "apple.com.example.net", "microsoft.com.example.net"):
            with self.subTest(domain=domain):
                self.assertEqual(first_policy(merged, domain), "PROXY")

    def test_repeatable_and_refreshes_changes(self):
        source = upstream()
        self.assertEqual(merge_config(source, PATCH, SERVICES),
                         merge_config(source, PATCH, SERVICES))
        updated = source.replace("ad119.example", "new-ad.example")
        self.assertIn("new-ad.example,Reject", merge_config(updated, PATCH, SERVICES))
        self.assertNotIn("ad119.example", merge_config(updated, PATCH, SERVICES))

    def test_rejects_incomplete_or_unexpected_upstream(self):
        for source in ["<html>error</html>", upstream().replace("FINAL,PROXY", ""),
                       upstream().replace("Reject", "Direct"), upstream() + "[Rule]\n",
                       upstream().replace("skip-proxy =", "# skip-proxy =")]:
            with self.subTest(source=source[:30]):
                with self.assertRaises(ValueError):
                    merge_config(source, PATCH, SERVICES)

    def test_rejects_bad_patches(self):
        for patch in ["", "# empty", "[Rule]", "FINAL,DIRECT", "DOMAIN,apple.com,DIRECT",
                      "DOMAIN,apple.com,MissingGroup"]:
            with self.subTest(patch=patch):
                with self.assertRaises(ValueError):
                    merge_config(upstream(), patch, SERVICES)
        for service in ["", "DOMAIN,apple.com,MissingGroup", "FINAL,PROXY",
                        "IP-CIDR,17.0.0.0/8,苹果服务",
                        "IP-CIDR,not-an-ip,苹果服务,no-resolve",
                        "IP-CIDR6,17.0.0.0/8,苹果服务,no-resolve"]:
            with self.subTest(service=service):
                with self.assertRaises(ValueError):
                    merge_config(upstream(), PATCH, service)

    def test_supports_crlf_and_whitespace_in_section_header(self):
        expected = merge_config(upstream(), PATCH, SERVICES)
        self.assertEqual(
            expected,
            merge_config(upstream().replace("\n", "\r\n"),
                         PATCH.replace("\n", "\r\n"), SERVICES.replace("\n", "\r\n")),
        )
        self.assertEqual(expected, merge_config(upstream().replace("[Rule]\n", "[Rule] \t\n"),
                                                PATCH, SERVICES))

    def test_preserves_unrelated_upstream_groups_and_rejects_conflicts(self):
        source = upstream().replace("[Rule]\n",
                                    "[Proxy Group]\nExisting = select,PROXY\n\n[Rule]\n")
        merged = merge_config(source, PATCH, SERVICES)
        self.assertEqual(merged.count("[Proxy Group]\n"), 1)
        self.assertIn("Existing = select,PROXY\n", merged)
        for invalid in (source.replace("Existing =", "Apple AI ="),
                        source.replace("[Rule]\n", "[Proxy Group]\n[Rule]\n")):
            with self.assertRaises(ValueError):
                merge_config(invalid, PATCH, SERVICES)


if __name__ == "__main__":
    unittest.main()
