"""Two adapter contracts; dry-run only, no image API calls."""
import copy
import importlib.util
import json
import subprocess
import sys
import unittest

import helpers as fixtures


class AdapterContractTests(fixtures.FixtureCase):
    def request(self):
        return {"prompt": "Synthetic character prompt", "references": [{
                    "id": "identity", "path": self.primary("standard"),
                    "roles": ["identity"], "instruction": "Identity only"}],
                "aspect_ratio": "1:1", "resolution": {"mode": "provider-native", "width": None, "height": None},
                "output": {"format": "png", "alpha": False}}

    def test_provider_output_capabilities_are_explicit(self):
        providers = (("openai", "generate-openai.py"),
                     ("nano-banana", "generate-nanobanana.py"),
                     ("seedream", "generate-seedream.py"))
        for provider, script in providers:
            for mode in ("native", "exact", "alpha"):
                with self.subTest(provider=provider, mode=mode):
                    request = self.request()
                    if mode == "exact":
                        request["aspect_ratio"] = "3:2" if provider == "openai" else "1:1"
                        request["resolution"] = {"mode": "exact", "width": 1536,
                                                 "height": 1024 if provider == "openai" else 1536}
                    elif mode == "alpha":
                        request["output"]["alpha"] = True
                    path = self.root / "request.json"
                    path.write_text(json.dumps(request), encoding="utf-8")
                    output = self.root / "candidate.png"
                    result = subprocess.run([sys.executable, "-B", str(fixtures.SKILL_ROOT / "scripts" / script),
                        "--request", str(path), "--output", str(output), "--dry-run"], capture_output=True, text=True)
                    supported = mode == "native" or provider == "openai"
                    self.assertEqual(result.returncode, 0 if supported else 2, result.stderr)
                    if supported:
                        summary = json.loads(result.stdout)
                        self.assertEqual(summary["reference_count"], 1)
                        self.assertEqual(summary["reference_roles"], [["identity"]])
                        self.assertEqual(summary["output_alpha"], mode == "alpha")
                        size_field = "image_size" if provider == "nano-banana" else "size"
                        expected_size = "1K" if provider == "nano-banana" else "1536x1024" if mode == "exact" else "1024x1024"
                        self.assertEqual(summary[size_field], expected_size)
                    else:
                        error = json.loads(result.stderr)
                        self.assertEqual(error["category"], "capability")
                        if mode == "exact":
                            self.assertRegex(error["error"], "exact (pixel )?resolution")
                    self.assertFalse(output.exists())

        # The Codex adapter: precise auth markers and a three-state usable verdict.
        codex = importlib.util.module_from_spec(importlib.util.spec_from_file_location(
            "character_codex", fixtures.SKILL_ROOT / "scripts/generate-codex.py"))
        codex.__spec__.loader.exec_module(codex)
        self.assertEqual(codex.classify_text("Error: not logged in to Codex"), "authentication")
        self.assertEqual(codex.classify_text("HTTP 401 Unauthorized"), "authentication")
        self.assertEqual(codex.classify_text("upstream failed while rendering the login page"), "service")
        self.assertEqual(codex.classify_text("usage limit reached"), "quota")
        self.assertIs(codex.usable_verdict(True, 2, 2), True)
        self.assertIs(codex.usable_verdict(None, 2, 2), None)
        self.assertIs(codex.usable_verdict(True, None, 2), None)
        self.assertIs(codex.usable_verdict(False, None, 2), False)
        self.assertIs(codex.usable_verdict(True, 1, 2), False)

    def test_typed_references_preserve_roles_and_reject_invalid_inputs(self):
        for script in ("generate-openai.py", "generate-nanobanana.py", "generate-seedream.py"):
            spec = importlib.util.spec_from_file_location(script, fixtures.SKILL_ROOT / "scripts" / script)
            adapter = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(adapter)
            path = self.root / "request.json"
            valid = self.request()
            path.write_text(json.dumps(valid), encoding="utf-8")
            normalized = adapter.load_request(path)
            self.assertEqual(normalized["references"][0]["roles"], ["identity"])
            for defect in ("empty", "role", "hash"):
                request = copy.deepcopy(valid)
                if defect == "empty":
                    request["references"] = []
                elif defect == "role":
                    request["references"][0]["roles"] = ["unknown"]
                else:
                    request["references"][0]["sha256"] = "0" * 64
                path.write_text(json.dumps(request), encoding="utf-8")
                expected = {"empty": "at least 1 reference", "role": "role", "hash": "sha256 does not match"}[defect]
                with self.subTest(script=script, defect=defect), self.assertRaisesRegex(adapter.AdapterError, expected):
                    adapter.load_request(path)


if __name__ == "__main__":
    unittest.main()
