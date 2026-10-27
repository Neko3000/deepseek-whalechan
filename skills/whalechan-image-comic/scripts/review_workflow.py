"""Single-review candidate and contact-sheet lifecycle for QA11 assignments."""
from __future__ import annotations

import importlib.util
from pathlib import Path


class ReviewWorkflow:
    def __init__(self, manager):
        self.m = manager

    def require(self, condition, message):
        if not condition:
            raise self.m.RunError(message)

    def event(self, manifest, name, image=None, **data):
        manifest.setdefault("events", []).append({"event": name, "image": image,
                                                   "at": self.m.now(), **data})

    def load(self, args):
        run, assignment, manifest = self.m.load_run(args.run_dir)

        self.require(manifest["status"] == "in_progress", "Run is not open")
        return run, assignment, manifest

    def findings(self, values, allowed):
        self.require(isinstance(values, list), "Findings must be a list")
        for item in values:
            self.require(isinstance(item, dict) and item.get("check") in allowed,
                         "Finding must name a reviewed check")
            self.m.text(item.get("detail"), "finding.detail")

    def validate_qa(self, value, digest, image):
        self.require(value.get("review_status") == "reviewed", "Visual review_status must be reviewed")
        self.require(value.get("candidate_sha256") == digest, "Visual QA candidate_sha256 does not match")
        self.m.text(value.get("reviewer"), "reviewer")
        self.require(value.get("method") == "direct-image-inspection", "Review must inspect the actual image")
        checked = value.get("checked")
        self.require(isinstance(checked, list) and all(isinstance(k, str) for k in checked)
                     and set(checked) == self.m.CONFIGURABLE_GATES
                     and len(checked) == len(self.m.CONFIGURABLE_GATES),
                     "checked must cover all 14 visual checks exactly once")
        panels = value.get("panels")
        self.require(isinstance(panels, list) and [p.get("panel") for p in panels if isinstance(p, dict)]
                     == list(range(1, image["panel_count"] + 1)), "Observe every panel in reading order")
        for panel in panels:
            self.m.text(panel.get("observed_scene"), "observed_scene")
        transcript = value.get("text_transcription")
        self.require(isinstance(transcript, list) and all(isinstance(t, str) for t in transcript),
                     "text_transcription must contain actual visible text")
        core, minor = value.get("core_defects"), value.get("minor_issues")
        self.findings(core, self.m.CONFIGURABLE_GATES)
        self.findings(minor, self.m.CONFIGURABLE_GATES)
        passed = not core
        self.require(value.get("verdict") == ("PASS" if passed else "FAIL"),
                     "Verdict must agree with core_defects; minor issues alone pass")
        if passed:
            self.require(transcript == image["core_text"], "PASS transcription must match exact core_text")
            self.require(value.get("targeted_retry") is None, "PASS cannot request a retry")
        else:
            self.m.text(value.get("targeted_retry"), "targeted_retry")
        self.m.model_cast().validate_qa(value, image)
        form = value.get("form_evidence")
        self.require(isinstance(form, dict), "form_evidence is required")
        if image["proportion_check"] == "visible-only":
            self.require(form.get("mode") == "visible-only" and not any(
                k in form for k in ("calculated_head_ratio", "head_axis", "body_segments")),
                "Visible-only review cannot claim a measured ratio")
            self.m.text(form.get("reason"), "form_evidence.reason")
            self.m.string_list(form.get("observed_cues"), "form_evidence.observed_cues")
        elif passed:
            self.m.validate_form_evidence(form, image, digest)
        return value
    def prepare(self, args):
        run, assignment, manifest = self.load(args)
        self.require((getattr(self.m, "task_local", False)),
                     "Use image-task for single-image mutations")
        state = self.m.state_for(manifest, args.image)
        self.require(state["status"] == "pending", "Image is not ready for generation")
        self.require(len(state["attempts"]) < 3, "Per-image candidate budget is exhausted")
        self.m.provider_allowed(state, args.provider, assignment)
        spec = next(i for i in assignment["images"] if i["id"] == args.image)
        source = Path(args.candidate).resolve()
        if not source.is_file():
            state.update(status="technical_blocked", technical_error="Returned candidate file is missing")
            self.event(manifest, "technical_blocked", args.image, reason=state["technical_error"])
            self.m.save_manifest(run, manifest)
            return {"status": "technical_blocked", "next": "report-technical-block"}
        number = len(state["attempts"]) + 1
        folder = run / "candidates" / args.image / f"attempt-{number:02d}"
        folder.mkdir(parents=True, exist_ok=getattr(self.m, "task_local", False))
        candidate = folder / "candidate.png"
        self.m.copy_once(source, candidate)
        digest = self.m.sha256(candidate)
        record = {"attempt_id": f"attempt-{number:02d}", "role": "candidate",
                  "provider": args.provider, "model": args.model,
                  "candidate": str(candidate), "candidate_sha256": digest,
                  "created_at": self.m.now(), "verdict": "PENDING",
                  "consumes_candidate_budget": True, "transport": getattr(args, "transport", None),
                  "visual_qa": None, "automatic_qa": None, "provider_audit": None}
        state["attempts"].append(record)
        state["status"] = "awaiting_review"
        self.event(manifest, "image_returned", args.image, attempt=record["attempt_id"])
        # Preserve the returned image and consumed slot before any other check can fail.
        self.m.save_manifest(run, manifest)
        try:
            prompt = Path(args.prompt_file)
            self.require(prompt.is_file() and prompt.read_text().strip(), "Prompt file is missing or empty")
            self.m.copy_once(prompt, folder / "prompt.txt")
            record["prompt"] = str(folder / "prompt.txt")
            loader = importlib.util.spec_from_file_location("comic_automatic", self.m.SKILL_ROOT / "scripts/validate-image.py")
            automatic_module = importlib.util.module_from_spec(loader)
            loader.loader.exec_module(automatic_module)
            automatic = automatic_module.validate(candidate, spec["output"])
            self.m.write_json(folder / "automatic.json", automatic)
            record["automatic_qa"] = str(folder / "automatic.json")
            record["output"] = {"requested": spec["output"], "effective": automatic["expected_output"],
                                "actual": automatic["metrics"]}
            audit_arg = getattr(args, "provider_audit", None)
            audit_path = Path(audit_arg) if audit_arg else None
            self.m.resolve_transport(args, audit_path)
            if audit_path:
                audit = self.m.load_provider_audit(audit_path, args.provider, digest)
                self.m.copy_once(audit_path, folder / "provider-audit.json")
                record["provider_audit"] = {**audit, "path": str(folder / "provider-audit.json")}
                self.require(audit["usable"] is not False, "Provider audit failed; no automatic regeneration")
            self.require(automatic["overall"] == "PASS", "Automatic image checks failed; no regeneration")
        except (OSError, ValueError, RuntimeError, KeyError) as exc:
            record["verdict"] = "FAIL"
            record["technical_error"] = str(exc)
            state["status"] = "technical_blocked"
        self.event(manifest, "automatic_check_completed", args.image, status=state["status"])
        self.m.save_manifest(run, manifest)
        return {"attempt": record, "status": state["status"], "next": "single-image-review" if
                state["status"] == "awaiting_review" else "report-technical-block"}

    def record_candidate(self, args, run, assignment, manifest):
        self.require(manifest["status"] == "in_progress", "Run is not open")
        state = self.m.state_for(manifest, args.image)
        self.require(state["status"] == "awaiting_review", "Run image-task ingest first; candidate may already be reviewed")
        record = state["attempts"][-1]
        digest = self.m.sha256(Path(record["candidate"]))
        self.require(digest == record["candidate_sha256"] == self.m.sha256(Path(args.candidate)),
                     "Candidate hash mismatch")
        self.require(args.provider == record["provider"] and args.model == record["model"], "Provider/model changed after preparation")
        spec = next(i for i in assignment["images"] if i["id"] == args.image)
        self.require(bool(args.visual_json), "Visual review file is required")
        review = self.m.read_json(Path(args.visual_json))
        # These are deterministic bindings, never fabricated observations or gate results.
        review.setdefault("candidate_sha256", digest)
        visual = self.validate_qa(review, digest, spec)
        self.m.validate_automatic(Path(record["automatic_qa"]), digest, spec["output"])
        target = Path(record["candidate"]).parent / "visual.json"
        self.require(not target.exists() or (getattr(self.m, "task_local", False) and self.m.read_json(target) == visual),
                     "This candidate already has a different visual review")
        self.m.write_json(target, visual)
        record.update(visual_qa=str(target), visual_sha256=self.m.sha256(target), verdict=visual["verdict"], reviewed_at=self.m.now(),
                      minor_issues=visual["minor_issues"], defects=visual["core_defects"])
        if visual["verdict"] == "PASS":
            state["status"] = "awaiting_collection"
        else:
            state["status"] = "pending" if len(state["attempts"]) < 3 else "exhausted"
            state["retry_source"] = "single_image_qa"
        self.event(manifest, "single_review_recorded", args.image, verdict=visual["verdict"])
        self.m.save_manifest(run, manifest)
        return record

    def ready_items(self, assignment, manifest):
        items = []
        terminal = {"technical_blocked", "exhausted", "collection_failed", "safety_blocked"}
        for image in assignment["images"]:
            state = manifest["images"][image["id"]]
            self.require(state["status"] in terminal | {"awaiting_collection", "collection_accepted"},
                         f"Resolve {image['id']} before collection review")
            selected = state["attempts"][-1] if state["status"] in {
                "awaiting_collection", "collection_accepted"} else None
            items.append({"image": image["id"], "idea_id": image["idea_id"],
                          "premise": image["premise"], "core_text": image["core_text"],
                          "candidate": selected["candidate"] if selected else None,
                          "sha256": selected["candidate_sha256"] if selected else None,
                          "attempt_id": selected["attempt_id"] if selected else None,
                          "status": state["status"]})
        return items
    def build_sheet(self, args):
        run, assignment, manifest = self.load(args)
        group = manifest["collection"]
        self.require(group["status"] in {"pending", "repairing"}, "Collection is already reviewed or awaiting review")
        items = self.ready_items(assignment, manifest)
        if not any(i["candidate"] for i in items):
            group["status"] = "complete"
            self.event(manifest, "collection_skipped", reason="no eligible candidates")
            self.m.save_manifest(run, manifest)
            return {"skipped": "no eligible candidates"}
        number = len(group["reviews"])
        self.require(number < 2, "Collection review limit reached")
        folder = run / "collection" / f"review-{number:02d}"
        folder.mkdir(parents=True, exist_ok=True)
        loader = importlib.util.spec_from_file_location("comic_review_sheet", self.m.SKILL_ROOT / "scripts/build-review-sheet.py")
        module = importlib.util.module_from_spec(loader)
        loader.loader.exec_module(module)
        sheet = folder / "sheet.png"
        pending = folder / "inputs.json"
        projection = {"assignment_sha256": manifest["assignment_sha256"], "round": number, "items": items}
        if pending.exists():
            self.require(self.m.read_json(pending) == projection, "Interrupted sheet inputs changed")
        else:
            self.require(not sheet.exists(), "Unbound existing review sheet")
            self.m.write_json(pending, projection)
        if not sheet.exists():
            module.compose(items, sheet)
        index = {"assignment_sha256": manifest["assignment_sha256"], "round": number,
                 "sheet": str(sheet), "sheet_sha256": self.m.sha256(sheet), "items": items,
                 "focus": group.get("repair_targets", []), "created_at": self.m.now()}
        if ((folder / "index.json").exists()):
            stored = self.m.read_json(folder / "index.json")
            self.require(all(stored[k] == v for k, v in index.items() if k != "created_at"), "Interrupted sheet index changed")
            index = stored
        self.m.write_json(folder / "index.json", index)
        group["sheets"].append({"index": str(folder / "index.json"),
                                "index_sha256": self.m.sha256(folder / "index.json")})
        group["status"] = "awaiting_review"
        self.event(manifest, "sheet_created", round=number)
        self.m.save_manifest(run, manifest)
        return index
    def record_collection(self, args):
        run, assignment, manifest = self.load(args)
        group = manifest["collection"]
        self.require(group["status"] == "awaiting_review", "No unreviewed collection sheet")
        stored = group["sheets"][-1]
        self.require(self.m.sha256(Path(stored["index"])) == stored["index_sha256"], "Collection index changed")
        index = self.m.read_json(Path(stored["index"]))
        self.require(self.m.sha256(Path(index["sheet"])) == index["sheet_sha256"], "Collection sheet changed")
        current = self.ready_items(assignment, manifest)
        self.require(current == index["items"], "Collection candidates changed; stale review")
        for item in current:
            if item["candidate"]:
                self.require(self.m.sha256(Path(item["candidate"])) == item["sha256"], "Collection candidate changed")
        review = self.m.read_json(Path(args.review_json))
        self.require(review.get("review_status") == "reviewed", "Collection review must be reviewed")
        self.require(review.get("sheet_sha256") == index["sheet_sha256"], "Review belongs to another sheet")
        self.m.text(review.get("reviewer"), "reviewer")
        self.m.text(review.get("observation"), "collection observation")
        checks = {"distinctness", "consistency", "overall"}
        checked = review.get("checked")
        self.require(isinstance(checked, list) and all(isinstance(k, str) for k in checked)
                     and set(checked) == checks and len(checked) == 3,
                     "Collection review must cover the three set-level checks")
        core, minor = review.get("core_defects"), review.get("minor_issues")
        self.findings(core, checks)
        self.findings(minor, checks)
        eligible = {i["image"] for i in current if i["candidate"]}
        targets = set()
        for defect in core:
            ids = defect.get("images")
            self.require(isinstance(ids, list) and ids and all(isinstance(i, str) for i in ids) and set(ids) <= eligible,
                         "Collection defects must identify eligible images")
            self.m.text(defect.get("targeted_retry"), "targeted_retry")
            targets.update(ids)
        self.require(review.get("verdict") == ("FAIL" if targets else "PASS"), "Collection verdict contradicts defects")
        round_number = len(group["reviews"])
        if round_number == 1:
            self.require(targets <= set(group["repair_targets"]), "Recheck only the original repair targets")
        review_path = Path(stored["index"]).with_name("visual.json")
        self.require(not review_path.exists() or ((self.m.read_json(review_path) == review)),
                     "Collection already has a different visual review")
        self.m.write_json(review_path, review)
        group["reviews"].append({"path": str(review_path), "sha256": self.m.sha256(review_path),
                                  "sheet_sha256": index["sheet_sha256"], "round": round_number,
                                  "verdict": review["verdict"], "targets": sorted(targets),
                                  "created_at": self.m.now()})
        pending = []
        for image_id in eligible:
            state = manifest["images"][image_id]
            if image_id not in targets:
                state["status"] = "collection_accepted"
            elif round_number == 0 and len(state["attempts"]) < 3:
                state["status"] = "pending"
                state["retry_source"] = "collection_review"
                pending.append(image_id)
            else:
                state["status"] = "collection_failed"
        if targets and round_number == 0:
            group["repair_targets"] = sorted(targets)
            group["repair_rounds"] = 1
        group["status"] = "repairing" if pending else "complete"
        self.event(manifest, "collection_review_recorded", round=round_number, verdict=review["verdict"])
        self.m.save_manifest(run, manifest)
        return {"status": group["status"], "repair_images": pending, "repair_rounds": group["repair_rounds"]}

    def promote(self, args, run, assignment, manifest):
        self.require(manifest["status"] == "in_progress" and manifest["collection"]["status"] == "complete",
                     "Complete collection review before promotion")
        state = self.m.state_for(manifest, args.image)
        self.require(state["status"] == "collection_accepted", "Image has not passed collection review")
        selected = state["attempts"][-1]
        source = Path(selected["candidate"])
        self.require(self.m.sha256(source) == selected["candidate_sha256"], "Candidate SHA-256 mismatch")
        spec = next(i for i in assignment["images"] if i["id"] == args.image)
        self.require(self.m.sha256(Path(selected["visual_qa"])) == selected["visual_sha256"], "Recorded visual review changed")
        for review in manifest["collection"]["reviews"]:
            self.require(self.m.sha256(Path(review["path"])) == review["sha256"], "Recorded collection review changed")
        visual = self.validate_qa(self.m.read_json(Path(selected["visual_qa"])), selected["candidate_sha256"], spec)
        automatic = self.m.validate_automatic(Path(selected["automatic_qa"]), selected["candidate_sha256"], spec["output"])
        self.require(visual["verdict"] == automatic["overall"] == "PASS", "Promotion requires recorded PASS")
        destination = run / "final" / f"{args.image}.png"
        if (destination.exists()):
            self.require(self.m.sha256(destination) == selected["candidate_sha256"], "Interrupted final differs")
        else:
            self.m.copy_once(source, destination)
        state.update(status="passed", final_path=str(destination), final_sha256=selected["candidate_sha256"])
        self.event(manifest, "promoted", args.image)
        self.m.save_manifest(run, manifest)
        return {"final": str(destination), "sha256": selected["candidate_sha256"]}

    def before_finalize(self, run, assignment, manifest):
        self.m.extension_module("provider_policy").guard(self.m, manifest, assignment)
        self.require(manifest["collection"]["status"] == "complete", "Complete or skip empty collection before finalizing")
        terminal = {"passed", "technical_blocked", "exhausted", "collection_failed", "safety_blocked"}
        self.require(all(s["status"] in terminal for s in manifest["images"].values()),
                     "Resolve or promote every image before finalizing")
        self.event(manifest, "finalized")

    def block(self, args):
        run, assignment, manifest = self.load(args)
        self.require((getattr(self.m, "task_local", False)),
                     "Use image-task for single-image mutations")
        state = self.m.state_for(manifest, args.image)
        self.require(state["status"] not in {"passed", "technical_blocked", "exhausted", "collection_failed"},
                     "Task is already terminal")
        self.m.text(args.reason, "technical block reason")
        state.update(status="technical_blocked", technical_error=args.reason)
        self.event(manifest, "technical_blocked", args.image, reason=args.reason)
        self.m.save_manifest(run, manifest)
        return {"status": "technical_blocked", "regenerate": False}

    def mark(self, args):
        run, assignment, manifest = self.load(args)
        self.require((getattr(self.m, "task_local", False)),
                     "Use image-task for single-image mutations")
        state = self.m.state_for(manifest, args.image)
        expected = "pending" if args.event == "generation_started" else "awaiting_review"
        self.require(state["status"] == expected, "Event does not match task state")
        self.event(manifest, args.event, args.image)
        self.m.save_manifest(run, manifest)
        return {"event": args.event, "at": manifest["events"][-1]["at"]}
    def register(self, commands):
        sheet = commands.add_parser("build-review-sheet", help="Build one N-slot collection contact sheet")
        sheet.add_argument("--run-dir", required=True)
        sheet.set_defaults(handler=self.build_sheet)
        review = commands.add_parser("record-collection-review", help="Record the sole set review or its one focused recheck")
        review.add_argument("--run-dir", required=True)
        review.add_argument("--review-json", required=True)
        review.set_defaults(handler=self.record_collection)
