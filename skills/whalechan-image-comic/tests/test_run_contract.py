"""Core QA barriers; fixtures do not represent real visual reviews."""
import argparse
import copy
import json
import unittest
from pathlib import Path

import test_manage_run as fixtures

manage = fixtures.manage


class QAProtocolTests(unittest.TestCase):
    setUp = fixtures.RunStateTests.setUp
    initialize = fixtures.RunStateTests.initialize
    files = fixtures.RunStateTests.files

    def qa(self, args):
        return manage.read_json(Path(args.visual_json))

    def validate(self, args, value, component=False, spec=None):
        manage.write_json(Path(args.visual_json), value)
        return manage.validate_qa(Path(args.visual_json), manage.sha256(Path(args.candidate)),
                                  component=component, image_spec=spec or self.image_spec)

    def test_unreviewed_candidates_components_and_composites_are_rejected(self):
        frozen = manage.read_json(self.run_dir / "assignment.json")
        self.image_spec = frozen["images"][1]
        self.image = self.image_spec["id"]
        args = self.files(1, "PASS")
        pending = self.qa(args)
        pending["review_status"] = "pending"
        manage.write_json(Path(args.visual_json), pending)
        for component in (False, True):
            with self.subTest(component=component), self.assertRaisesRegex(manage.RunError, "review_status"):
                manage.record_image(args, component=component)
        self.assertEqual(manage.load_run(str(self.run_dir))[2]["images"][self.image]["attempts"], [])
        sources = []
        for panel in (1, 2):
            component = self.files(panel + 1, "PASS")
            qa = self.qa(component)
            qa["gates"] = {key: "PASS" for key in manage.COMPONENT_GATES}
            qa["observation"]["panels"] = [{"panel": panel, "observed_scene": "Synthetic panel"}]
            qa["observation"]["text_transcription"] = [self.image_spec["core_text"][panel - 1]]
            qa.pop("evidence")
            manage.write_json(Path(component.visual_json), qa)
            sources.append(manage.record_image(component, component=True)["attempt_id"])
        args.source_attempt = sources
        with self.assertRaisesRegex(manage.RunError, "review_status"):
            manage.cmd_record_composite(args)
        self.assertEqual(manage.load_run(str(self.run_dir))[2]["images"][self.image]["derived"], [])

    def test_promotion_rechecks_both_reviews_and_candidate_hash(self):
        args = self.files(1, "PASS")
        audit = Path(self.temporary.name) / "candidate.png.codex.json"
        manage.write_json(audit, {"provider": "codex", "transport": "cli", "usable": None,
                                  "output_sha256": manage.sha256(Path(args.candidate))})
        for transport, audit_path, provider, message in (
            (None, None, "codex", "--transport cli or --transport builtin"),
            ("cli", None, "codex", "require --provider-audit"),
            ("builtin", str(audit), "codex", "no provider audit"),
        ):
            trial = argparse.Namespace(**{**vars(args), "transport": transport, "provider_audit": audit_path, "provider": provider})
            with self.subTest(transport=transport, provider=provider), self.assertRaisesRegex(manage.RunError, message):
                manage.record_image(trial, component=False)
        args.transport, args.provider_audit = "cli", str(audit)
        record = manage.record_image(args, component=False)
        attempt = manage.load_run(str(self.run_dir))[2]["images"][self.image]["attempts"][-1]
        self.assertEqual((attempt["verdict"], attempt["transport"], attempt["provider_audit"]["verified"]), ("PASS", "cli", False))
        promote = argparse.Namespace(run_dir=str(self.run_dir), image=self.image)
        for key, field, wrong in (("visual_qa", "review_status", "pending"),
                                  ("automatic_qa", "overall", "FAIL")):
            path = Path(record[key])
            original = manage.read_json(path)
            changed = {**original, field: wrong}
            manage.write_json(path, changed)
            with self.subTest(review=key), self.assertRaises(manage.RunError):
                manage.cmd_promote(promote)
            manage.write_json(path, original)
        Path(record["candidate"]).write_bytes(b"changed test candidate")
        with self.assertRaisesRegex(manage.RunError, "SHA-256 mismatch"):
            manage.cmd_promote(promote)
        self.assertFalse((self.run_dir / "final" / f"{self.image}.png").exists())

    def test_both_historical_v12_contracts_resume_without_rewriting_consent(self):
        original = manage.read_json(self.run_dir / "assignment.json")
        original_manifest = manage.read_json(self.run_dir / "manifest.json")
        # These hashes were produced independently by the two pre-merge implementations:
        # 9d905a9 (tournament) and codex/auto-subagents (two user gates).
        cases = (("tournament", "c365367f8429e4b202f51f666aee180d13fa006f5bc458cbd71ed9b9acf78498"),
                 ("selection", "c18bfdaff5a0f10714f72e8f6d3a0aca201c9be11f16ac1bde921e6f5567eff5"))
        for kind, historical_hash in cases:
            frozen = copy.deepcopy(original)
            frozen["schema_version"] = 12
            if kind == "tournament":
                frozen["execution"].pop("subagent_count")
                frozen["execution"]["max_parallelism"] = 5
            else:
                legacy = fixtures.legacy_assignment()
                for field in ("creative_pool", "duels", "ranked_ideas", "proposal", "selection", "confirmation"):
                    frozen[field] = copy.deepcopy(legacy[field])
                for image, legacy_image in zip(frozen["images"], legacy["images"]):
                    for field in ("idea_id", "premise", "source_rank", "execution", "core_text"):
                        image[field] = copy.deepcopy(legacy_image[field])
                frozen.pop("worker_plan")
                frozen["execution"] = {**legacy["execution"], "max_parallelism": 10, "subagent_count": 0}
            frozen["confirmation"]["summary_sha256"] = historical_hash
            frozen_path = self.run_dir / "assignment.json"
            manage.write_json(frozen_path, frozen)
            manifest = copy.deepcopy(original_manifest)
            manifest["assignment_sha256"] = manage.sha256(frozen_path)
            manifest["execution"] = {**frozen["execution"],
                                     "effective_parallelism": frozen["execution"]["requested_parallelism"]}
            if kind == "selection":
                manifest["execution"]["effective_subagent_count"] = 0
            manage.write_json(self.run_dir / "manifest.json", manifest)
            original_bytes = frozen_path.read_bytes()
            with self.subTest(kind=kind):
                self.assertEqual(manage.selection_summary(frozen)["summary_sha256"], historical_hash)
                resumed = manage.load_run(str(self.run_dir))[1]
                self.assertEqual(resumed["confirmation"]["summary_sha256"], historical_hash)
                self.assertEqual(frozen_path.read_bytes(), original_bytes)
                if kind == "selection":
                    manifest["execution"]["effective_subagent_count"] = 1
                    manage.write_json(self.run_dir / "manifest.json", manifest)
                    with self.assertRaisesRegex(manage.RunError, "confirmed limit"):
                        manage.load_run(str(self.run_dir))
                with self.assertRaisesRegex(manage.RunError, "schema_version"):
                    manage.cmd_init(argparse.Namespace(assignment=str(frozen_path),
                                                      root=self.temporary.name, effective_parallelism=None))

    def test_old_or_incomplete_contracts_are_rejected(self):
        path = Path(self.temporary.name) / "old-assignment.json"
        value = fixtures.assignment()
        value["schema_version"] = 9
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(manage.RunError, "schema_version"):
            manage.validate_assignment(path)
        value["schema_version"] = manage.ASSIGNMENT_SCHEMA_VERSION
        value["input"].update(type="screenshot", content="A chat screenshot where the comma is missing")
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(manage.RunError, "existing source file paths"):
            manage.validate_assignment(path)
        value["input"]["content"] = str(fixtures.SKILL_ROOT / "assets/supporting-character-references/abstract-user-pose-sheet.webp")
        path.write_text(json.dumps(fixtures.confirm_fixture_plan(value)))
        self.assertEqual(manage.validate_assignment(path)["input"]["type"], "screenshot")
        value["schema_version"] = 10
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(manage.RunError, f"schema_version must be {manage.ASSIGNMENT_SCHEMA_VERSION}"):
            manage.validate_assignment(path)
        frozen_path = self.run_dir / "assignment.json"
        original = manage.read_json(frozen_path)
        # Reconstruct the legacy approval contract around genuine frozen image assets.
        legacy = fixtures.legacy_assignment()
        for version, resumable in ((10, True), (11, True), (9, False)):
            frozen = copy.deepcopy(original)
            for field in ("creative_pool", "duels", "ranked_ideas", "proposal", "selection", "confirmation"):
                frozen[field] = copy.deepcopy(legacy[field])
            for image, legacy_image in zip(frozen["images"], legacy["images"]):
                for field in ("idea_id", "premise", "source_rank", "execution", "core_text"):
                    image[field] = copy.deepcopy(legacy_image[field])
            frozen["execution"] = copy.deepcopy(legacy["execution"])
            frozen.pop("worker_plan", None)
            frozen["schema_version"] = version
            # v10's summary hash predates direction metadata; derive its own legacy hash.
            if resumable:
                frozen["confirmation"]["summary_sha256"] = manage.selection_summary(frozen)["summary_sha256"]
            manage.write_json(frozen_path, frozen)
            manifest = manage.read_json(self.run_dir / "manifest.json")
            manifest["assignment_sha256"] = manage.sha256(frozen_path)
            manage.write_json(self.run_dir / "manifest.json", manifest)
            with self.subTest(version=version):
                if resumable:
                    self.assertEqual(manage.load_run(str(self.run_dir))[1]["schema_version"], version)
                else:
                    with self.assertRaisesRegex(manage.RunError, "schema_version"):
                        manage.load_run(str(self.run_dir))
        args = self.files(1, "PASS")
        spec = copy.deepcopy(self.image_spec)
        spec.pop("dialogue_plan")
        with self.assertRaisesRegex(manage.RunError, "dialogue_plan"):
            self.validate(args, self.qa(args), spec=spec)


if __name__ == "__main__":
    unittest.main()
