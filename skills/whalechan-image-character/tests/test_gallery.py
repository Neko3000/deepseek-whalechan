"""Gallery fixtures are synthetic records, never approvals or real image QA."""
import hashlib
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("gallery", ROOT / "scripts/export-gallery.py")
gallery = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gallery)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def make_run(root, name="example", composite=False):
    """Small complete/partial records for export tests and explicitly labelled demos."""
    run = root / name
    for folder in ("source", "candidates", "prompts", "qa", "final"):
        (run / folder).mkdir(parents=True)
    subprocess.run(["magick", "-size", "80x100", "xc:#b6cfc9", str(run / "candidates/one.png")], check=True)
    subprocess.run(["magick", "-size", "100x80", "xc:#e8c5b0", str(run / "candidates/two.png")], check=True)
    shutil.copyfile(run / "candidates/one.png", run / "source/original-01.png")
    shutil.copyfile(run / "candidates/two.png", run / "source/original-02.png")
    records = []
    for index, filename in enumerate(("one.png", "two.png"), 1):
        prompt = f"Synthetic prompt {index}\n中文 ' & </script><script>alert(1)</script>"
        write_json(run / f"qa/{index}.json", {"verdict": "PASS", "overall": "PASS", "defects": []})
        (run / f"prompts/{index}.txt").write_text(prompt, encoding="utf-8")
        record = {"candidate_sha256": gallery.digest(run / "candidates" / filename),
                  "provider": "codex", "model": "synthetic-test-only", "verdict": "PASS",
                  "created_at": "2026-01-01T00:00:00Z", "consumes_candidate_budget": True}
        if gallery.COMIC:
            record.update(attempt_id=f"attempt-{index:02d}", role="component" if composite else "candidate",
                          candidate=str(run / "candidates" / filename), prompt=str(run / f"prompts/{index}.txt"),
                          automatic_qa=str(run / f"qa/{index}.json"), visual_qa=str(run / f"qa/{index}.json"))
        else:
            record.update(candidate_attempt=index, candidate_path=f"candidates/{filename}", prompt=prompt,
                          automatic_qa={"overall": "PASS"}, visual_qa={"verdict": "PASS", "defects": []})
        records.append(record)
    shutil.copyfile(run / "candidates/one.png", run / "final/01_same.png")
    state = {"status": "passed", "attempts": records, "derived": [],
             "final_path": str(run / "final/01_same.png"), "final_sha256": records[0]["candidate_sha256"],
             "provider_errors": [{"provider": "codex", "model": "synthetic", "category": "quota", "details": "Synthetic error; no image"}]}
    if composite:
        state["derived"] = [{"derived_id": "composite-01", "role": "composite", "verdict": "PASS",
                             "candidate": str(run / "final/01_same.png"), "candidate_sha256": state["final_sha256"],
                             "source_attempts": [item["attempt_id"] for item in records],
                             "automatic_qa": str(run / "qa/1.json"), "visual_qa": str(run / "qa/1.json"),
                             "consumes_candidate_budget": False}]
    assignment = {"schema_version": 11 if gallery.COMIC else 5, "run_name": name, "run_dir": str(run),
                  "input": {"type": "screenshot", "content": ["lost-1.png", "lost-2.png"]},
                  "proposal": {"options": [{"choice": key, "idea_id": f"idea_{key}", "title": f"方案 {key}",
                                            "scene": "Synthetic demonstration, not an actual generation."} for key in "AB"]},
                  "selection": {"choices": [{"choice": "A", "count": 1}]},
                  "images": [{"id": "01_same", "name": "same", "idea_id": "idea_A", "proposal_choice": "A", "references": []}]}
    write_json(run / "assignment.json", assignment)
    manifest = {"schema_version": 1 if gallery.COMIC else 3, "status": "complete",
                "assignment_sha256": gallery.digest(run / "assignment.json"), "images": {"01_same": state}}
    write_json(run / "manifest.json", manifest)
    return run


def payload(path):
    html = Path(path).read_text(encoding="utf-8")
    return json.loads(html.split('<script id="gallery-data" type="application/json">', 1)[1].split("</script>", 1)[0])


class GalleryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.run = make_run(self.root)

    def export(self, *runs, **kwargs):
        result = gallery.export_gallery(runs or [self.run], **kwargs)
        return result, payload(result["gallery"])

    def test_originals_proposals_attempts_and_exact_final_origin(self):
        result, data = self.export()
        group = data["groups"][0]
        self.assertEqual(len(group["originals"]), 2)
        self.assertEqual(group["calls"], 2)
        self.assertEqual(group["errors"], 1)
        self.assertFalse(group["proposals"][1]["selected"])
        image = group["proposals"][0]["images"][0]
        self.assertIn("Synthetic prompt 1", image["origin"]["prompt"])
        self.assertNotEqual(image["origin"]["sha256"], image["attempts"][-1]["sha256"])
        exported = Path(result["gallery"]).parent / image["final"]["src"]
        self.assertEqual(exported.read_bytes(), (self.run / "final/01_same.png").read_bytes())
        self.assertEqual(len(list(exported.parent.iterdir())), 2)

    @unittest.skipUnless(gallery.COMIC, "Flat browsing is the comic layout")
    def test_failed_attempts_are_flat_cards_and_final_copy_is_not_duplicated(self):
        manifest = gallery.read_json(self.run / "manifest.json")
        manifest["images"]["01_same"]["attempts"][1]["verdict"] = "FAIL"
        write_json(self.run / "qa/2.json", {"verdict": "FAIL", "overall": "PASS", "defects": ["Synthetic defect"]})
        write_json(self.run / "manifest.json", manifest)
        _, data = self.export()
        group = data["groups"][0]
        cards = group["gallery_images"]
        self.assertEqual(len(cards), 2)
        self.assertEqual([c["attempt_index"] for c in cards], [0, 1])
        self.assertEqual([c["is_final"] for c in cards], [True, False])
        self.assertEqual(group["proposals"][0]["images"][0]["attempts"][1]["verdict"], "FAIL")
        self.assertEqual(group["calls"], 2)
        self.assertEqual(group["errors"], 1)

    @unittest.skipUnless(gallery.COMIC, "Flat browsing is the comic layout")
    def test_flat_order_crosses_proposals_and_normalizes_timezones(self):
        assignment = gallery.read_json(self.run / "assignment.json")
        assignment["selection"]["choices"].append({"choice": "B", "count": 1})
        assignment["images"].append({"id": "02_other", "idea_id": "idea_B", "proposal_choice": "B", "references": []})
        write_json(self.run / "assignment.json", assignment)
        manifest = gallery.read_json(self.run / "manifest.json")
        state = manifest["images"]["01_same"]
        state["attempts"][0]["created_at"] = "2026-01-01T01:00:00+01:00"
        state["attempts"][1]["created_at"] = None
        second = copy.deepcopy(state)
        second["attempts"] = second["attempts"][:1]
        second["attempts"][0]["created_at"] = "2025-12-31T23:30:00Z"
        manifest["images"]["02_other"] = second
        manifest["assignment_sha256"] = gallery.digest(self.run / "assignment.json")
        write_json(self.run / "manifest.json", manifest)
        _, data = self.export()
        cards = data["groups"][0]["gallery_images"]
        self.assertEqual([(c["image_id"], c["attempt_index"]) for c in cards],
                         [("02_other", 0), ("01_same", 0), ("01_same", 1)])

    @unittest.skipUnless(gallery.COMIC, "Flat browsing is the comic layout")
    def test_final_with_missing_attempt_records_is_displayed_without_an_invented_prompt(self):
        manifest = gallery.read_json(self.run / "manifest.json")
        manifest["images"]["01_same"]["attempts"] = []
        write_json(self.run / "manifest.json", manifest)
        _, data = self.export()
        group = data["groups"][0]
        self.assertEqual(len(group["gallery_images"]), 1)
        self.assertTrue(group["gallery_images"][0]["is_final"])
        self.assertIsNone(group["gallery_images"][0]["attempt_index"])
        self.assertEqual(group["calls"], 0)
        self.assertTrue(group["warnings"])

    def test_batch_namespaces_and_no_overwrite(self):
        second = make_run(self.root, "second")
        output = self.root / "batch with spaces"
        result, data = self.export(self.run, second, output=output)
        self.assertEqual([g["title"] for g in data["groups"]], ["example", "second"])
        again, _ = self.export(self.run, second, output=output)
        self.assertNotEqual(result["gallery"], again["gallery"])
        with self.assertRaisesRegex(gallery.GalleryError, "requires --output"):
            gallery.export_gallery([self.run, second])

    def test_identical_candidates_do_not_invent_final_prompt_ownership(self):
        manifest = gallery.read_json(self.run / "manifest.json")
        records = manifest["images"]["01_same"]["attempts"]
        shutil.copyfile(self.run / "candidates/one.png", self.run / "candidates/two.png")
        records[1]["candidate_sha256"] = records[0]["candidate_sha256"]
        write_json(self.run / "manifest.json", manifest)
        _, data = self.export()
        group = data["groups"][0]
        self.assertIsNone(group["proposals"][0]["images"][0]["origin"])
        self.assertTrue(any("无法唯一确定" in message for message in group["warnings"]))
        if gallery.COMIC:
            self.assertEqual(len(group["gallery_images"]), 2)
            self.assertTrue(all(c["matches_final"] and not c["is_final"] for c in group["gallery_images"]))

    def test_export_and_moved_run_are_portable(self):
        moved = self.root / "moved 输入"
        shutil.move(self.run, moved)
        result, data = self.export(moved)
        self.assertFalse(data["groups"][0]["warnings"])
        target = self.root / "share"
        shutil.move(Path(result["gallery"]).parent, target)
        shutil.rmtree(moved)
        group = data["groups"][0]
        for picture in group["originals"] + [group["proposals"][0]["images"][0]["final"]]:
            self.assertTrue((target / picture["src"]).is_file())
        self.assertNotIn(str(self.run), (target / "index.html").read_text())

    def test_missing_records_are_explicit_not_fabricated(self):
        (self.run / "source/original-02.png").unlink()
        _, data = self.export()
        group = data["groups"][0]
        self.assertIsNone(group["originals"][1]["src"])
        self.assertTrue(group["warnings"])
        self.assertEqual(group["request"], "")

    def test_untrusted_text_is_data_not_html(self):
        result, data = self.export()
        html = Path(result["gallery"]).read_text()
        self.assertNotIn("</script><script>alert", html)
        self.assertIn("</script><script>alert", data["groups"][0]["proposals"][0]["images"][0]["origin"]["prompt"])
        self.assertNotIn("fetch(", html)

    def test_active_runs_and_tampered_assignment_are_rejected(self):
        manifest = gallery.read_json(self.run / "manifest.json")
        manifest["status"] = "in_progress"
        write_json(self.run / "manifest.json", manifest)
        with self.assertRaisesRegex(gallery.GalleryError, "Finalize"):
            self.export()
        self.assertFalse((self.run / "gallery").exists())
        manifest["status"] = "complete"
        manifest["assignment_sha256"] = "0" * 64
        write_json(self.run / "manifest.json", manifest)
        with self.assertRaisesRegex(gallery.GalleryError, "hash mismatch"):
            self.export()

    def test_corrupted_images_are_rejected(self):
        subprocess.run(["magick", "-size", "20x20", "xc:red", str(self.run / "final/01_same.png")], check=True)
        with self.assertRaisesRegex(gallery.GalleryError, "hash mismatch"):
            self.export()
        self.assertFalse((self.run / "gallery").exists())

    def test_partial_results_do_not_promote_failed_candidates(self):
        manifest = gallery.read_json(self.run / "manifest.json")
        manifest["status"] = "partial" if gallery.COMIC else "complete_with_failures"
        state = manifest["images"]["01_same"]
        state["status"] = "pending"
        state["final_path"] = None
        state["final_sha256"] = None
        state["attempts"][0]["verdict"] = "FAIL"
        write_json(self.run / "manifest.json", manifest)
        _, data = self.export()
        group = data["groups"][0]
        self.assertEqual(group["passed"], 0)
        self.assertIsNone(group["proposals"][0]["images"][0]["final"])

    @unittest.skipUnless(gallery.COMIC, "Only comics have local composites")
    def test_composite_has_component_prompts_and_no_extra_call(self):
        run = make_run(self.root, "composite", composite=True)
        _, data = self.export(run)
        image = data["groups"][0]["proposals"][0]["images"][0]
        self.assertEqual(image["calls"], 2)
        self.assertEqual(image["origin"]["role"], "composite")
        self.assertEqual(image["origin"]["prompt"], "")
        self.assertEqual(image["origin"]["sources"], ["attempt-01", "attempt-02"])
        cards = data["groups"][0]["gallery_images"]
        self.assertEqual(len(cards), 3)
        self.assertEqual(sum(c["is_final"] for c in cards), 1)

    def test_installed_skill_is_self_contained(self):
        installed = self.root / "installation" / ROOT.name
        (installed / "scripts").mkdir(parents=True)
        shutil.copyfile(ROOT / "scripts/export-gallery.py", installed / "scripts/export-gallery.py")
        shutil.copytree(ROOT / "assets/gallery", installed / "assets/gallery")
        result = subprocess.run([sys.executable, str(installed / "scripts/export-gallery.py"),
                                 "--run-dir", str(self.run)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(Path(json.loads(result.stdout)["gallery"]).exists())

    def test_bundled_gallery_files_match_when_sibling_is_available(self):
        sibling = ROOT.parent / ("whalechan-image-character" if gallery.COMIC else "whalechan-image-comic")
        if not sibling.exists():
            self.skipTest("Standalone installation")
        for file in ["scripts/export-gallery.py", "assets/gallery/index.html", "assets/gallery/gallery.css", "assets/gallery/gallery.js"]:
            self.assertEqual((ROOT / file).read_bytes(), (sibling / file).read_bytes(), file)


if __name__ == "__main__":
    unittest.main()
