from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sync_upstream import merge_config


def upstream():
    advertising = "\n".join(f"DOMAIN-SUFFIX,ad{i}.example,Reject" for i in range(120))
    return (
        "# Upstream attribution\n[General]\nipv6 = false\n"
        "skip-proxy = localhost, *.ls.apple.com, seed-sequoia.siri.apple.com, *.local\n"
        "dns-server = system\n[Rule]\n" + advertising + "\n"
        "DOMAIN-SUFFIX,apple.com,Direct\n"
        "DOMAIN-SUFFIX,ls.apple.com,Direct\n"
        "DOMAIN-SUFFIX,mzstatic.com,Direct\n"
        "DOMAIN-SUFFIX,example.cn,Direct\nFINAL,PROXY\n"
        "[URL Rewrite]\n^https?://example.cn https://example.com 302\n"
        "[MITM]\nhostname = *.example.cn\n"
    )


PATCH = "\n".join([
    "DOMAIN,guzzoni.apple.com,PROXY",
    "DOMAIN-SUFFIX,ls.apple.com,PROXY",
    "DOMAIN-SUFFIX,apps.mzstatic.com,PROXY",
    "DOMAIN-SUFFIX,chatgpt.com,PROXY",
])


class SyncTests(unittest.TestCase):
    def test_ai_precedes_advertising_and_apple_direct(self):
        merged = merge_config(upstream(), PATCH)
        rules = merged.split("[Rule]\n", 1)[1].split("[URL Rewrite]", 1)[0]
        active = [line for line in rules.splitlines() if line and not line.startswith("#")]
        self.assertEqual(active[:4], PATCH.splitlines())
        self.assertIn("DOMAIN-SUFFIX,ad0.example,Reject", active)
        self.assertIn("DOMAIN-SUFFIX,ad119.example,Reject", active)
        self.assertIn("DOMAIN-SUFFIX,example.cn,Direct", active)
        self.assertEqual(active[-1], "FINAL,PROXY")

    def test_removes_only_targeted_proxy_bypasses(self):
        merged = merge_config(upstream(), PATCH)
        self.assertIn("skip-proxy = localhost, *.local\n", merged)
        self.assertNotIn("seed-sequoia.siri.apple.com", merged)
        self.assertNotIn("*.ls.apple.com", merged)
        self.assertIn("ipv6 = false\n", merged)
        self.assertIn("dns-server = system\n", merged)

    def test_preserves_upstream_rules_and_trailing_sections(self):
        source = upstream()
        merged = merge_config(source, PATCH)
        # After the inserted patch, all upstream Rule/Rewrite/MITM text survives.
        self.assertIn(source.split("[Rule]\n", 1)[1], merged)
        self.assertIn("# Upstream attribution", merged)

    def test_repeatable_and_refreshes_changes(self):
        source = upstream()
        self.assertEqual(merge_config(source, PATCH), merge_config(source, PATCH))
        updated = source.replace("ad119.example", "new-ad.example")
        self.assertIn("new-ad.example,Reject", merge_config(updated, PATCH))
        self.assertNotIn("ad119.example", merge_config(updated, PATCH))

    def test_rejects_incomplete_or_unexpected_upstream(self):
        for source in ["<html>error</html>", upstream().replace("FINAL,PROXY", ""),
                       upstream().replace("Reject", "Direct"), upstream() + "[Rule]\n",
                       upstream().replace("skip-proxy =", "# skip-proxy =")]:
            with self.subTest(source=source[:30]):
                with self.assertRaises(ValueError):
                    merge_config(source, PATCH)

    def test_rejects_bad_patch_and_supports_crlf(self):
        for patch in ["", "# empty", "[Rule]", "FINAL,DIRECT", "DOMAIN,apple.com,DIRECT"]:
            with self.subTest(patch=patch):
                with self.assertRaises(ValueError):
                    merge_config(upstream(), patch)
        self.assertEqual(merge_config(upstream(), PATCH),
                         merge_config(upstream().replace("\n", "\r\n"), PATCH))


if __name__ == "__main__":
    unittest.main()
