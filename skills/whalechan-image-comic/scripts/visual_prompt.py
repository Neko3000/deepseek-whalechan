"""Drawing-only prompt and stable pre-confirmation visual contract for current assignments."""
import copy
import json
from pathlib import Path


class VisualPrompt:
    def __init__(self, manager):
        self.m = manager

    def contract(self, assignment):
        images = assignment.get("images")
        if not isinstance(images, list) or len(images) != self.m.target_images(assignment):
            raise self.m.RunError("All selected visual image plans are required before confirmation")
        return [self.spec(assignment, image) for image in images]

    def spec(self, assignment, original):
        m = self.m
        image = copy.deepcopy(original)
        label = "visual_plan"
        panels = image.get("panel_count")
        layouts = {1: {"single"}, 2: {"left-right", "top-bottom"}, 4: {"2x2"}}
        if type(panels) is not int or panels not in layouts or image.get("layout") not in layouts[panels]:
            raise m.RunError("visual_plan has invalid panel count or layout")
        for field in ("action_plan", "expression_plan"):
            entries = image.get(field)
            if (not isinstance(entries, list) or len(entries) != panels
                    or any(not isinstance(e, dict) or e.get("panel") != n
                           for n, e in enumerate(entries, 1))):
                raise m.RunError(f"visual_plan.{field} must cover every panel in order")
        for action in image["action_plan"]:
            action["action"] = m.text(action.get("action"), "action_plan.action")
        presets, performances = m.expression_presets()
        for expression in image["expression_plan"]:
            if expression.get("preset") not in presets or expression.get("performance") not in performances:
                raise m.RunError("visual_plan.expression_plan has an unknown preset or performance")
            m.text(expression.get("visual_description"), "expression_plan.visual_description")
        image["core_text"] = m.string_list(image.get("core_text"), "core_text")
        m.validate_design(image, m.validate_participants(assignment["input"]), label)
        for line in image["dialogue_plan"]:
            m.text(line.get("placement"), "dialogue_plan.placement")
        m.text(image.get("lettering_description"), "lettering_description")
        if image.get("exaggeration") not in m.TIER_ORDER:
            raise m.RunError("visual_plan.exaggeration must be A, B or C")
        tiers = m.exaggeration_tiers()
        m.normalize_exaggeration(image, tiers, label)
        profiles = m.read_json(m.CATALOG_PATH)["character_forms"]
        proportion, anchor = m.normalize_proportion(image, profiles, label)
        style = m.normalize_named_mode(image.get("style"), m.STYLE_MODES, "canonical", m.DEFAULT_STYLE, "style")
        costume = m.normalize_named_mode(image.get("costume"), m.COSTUME_MODES, "canonical", m.DEFAULT_COSTUME, "costume")
        background = m.normalize_background(image.get("background"), "background", image["exaggeration"], tiers)
        composition = image.get("composition", {})
        if not isinstance(composition, dict):
            raise m.RunError("visual_plan.composition must be an object")
        for key in ("shot", "staging"):
            if key in composition:
                m.text(composition[key], f"composition.{key}")
        image["cast_plan"] = m.model_cast().normalize(image, assignment["input"]["participants"], proportion)
        models = [c for c in image['cast_plan'] if c.get('character_profile')]
        if models:
            policy = m.language_policy()
            languages = ({policy.effective(assignment, scope) for scope in ('communication', 'prompt')}
                         if assignment.get('schema_version') == 20 else {'en', 'zh-Hans'})
            if assignment.get('schema_version') == 20 and len(languages) > 1:
                for member in models:
                    for key in ('display_performance', 'display_interaction'):
                        m.text(member.get(key), 'cast.' + key)
            for language in languages:
                policy.locale(assignment, language, 'cast')
                for member in models:
                    m.model_cast().localized_profile(assignment, member, language)
        refs = self.references(image, profiles[anchor]["primary"],
                               m.default_identity_roles(style, costume, proportion))
        return {
            "idea_id": image["idea_id"], "panel_count": panels, "layout": image["layout"],
            "language": assignment["input"]["language"], "output": m.normalize_output(image, label),
            "style": style, "costume": costume, "background": background,
            "proportion": proportion, "references": refs,
            "composition": {k: composition.get(k, "") for k in ("shot", "staging")},
            "lettering": image["lettering_description"],
            "actions": [{"panel": e["panel"], "action": e["action"]} for e in image["action_plan"]],
            "expressions": [{k: e[k] for k in ("panel", "preset", "performance", "tier", "visual_description")}
                            for e in image["expression_plan"]],
            "dialogue": [{**{k: e[k] for k in ("panel", "speaker", "delivery", "placement")},
                          "text": image["core_text"][e["text_index"]], "prop": e.get("prop")}
                         for e in image["dialogue_plan"]],
            "cast": m.model_cast().contract(image["cast_plan"]),
            "landing_panel": image["landing_panel"],
            "effects": [e["effect"] for e in image["effects_plan"]],
        }

    def references(self, image, primary, identity_roles):
        m = self.m
        # Draft external references must be absolute; bundled paths are skill-relative.
        refs = copy.deepcopy(image.get("references", []))
        if (not isinstance(refs, list) or any(not isinstance(r, dict) or not isinstance(r.get("path"), str)
                                            for r in refs)):
            raise m.RunError("visual_plan.references must contain reference objects with paths")
        path_for = lambda ref: Path(m.resolve_reference(ref["path"], m.SKILL_ROOT / "draft.json"))
        primary = (m.SKILL_ROOT / primary).resolve()
        if not any(path_for(ref) == primary for ref in refs):
            refs.insert(0, {"id": "canonical-identity", "path": str(primary), "roles": identity_roles,
                           "instruction": "Preserve only the declared canonical Whale-chan roles; never copy its facial expression"})
        result = []
        for ref in refs:
            ref_id = m.text(ref.get("id"), "reference.id")
            role_list = m.string_list(ref.get("roles"), "reference.roles")
            if not set(role_list) <= m.REFERENCE_ROLES:
                raise m.RunError("Unknown reference role")
            path = path_for(ref)
            if not path.is_file():
                raise m.RunError(f"Visual reference must exist; use absolute external paths: {path}")
            digest = m.sha256(path)
            if ref.get("sha256", digest) != digest:
                raise m.RunError(f"Reference SHA-256 mismatch: {path}")
            instruction = ref.get("instruction")
            if instruction is not None:
                instruction = m.text(instruction, "reference.instruction")
            result.append({"id": ref_id, "roles": role_list,
                           "instruction": instruction, "sha256": digest})
        m.model_cast().validate_references(image["cast_plan"], [
            {**result[n], "path": str(path_for(ref))} for n, ref in enumerate(refs)])
        return result

    def render(self, assignment, image):
        if assignment.get("schema_version") == 20:
            policy = self.m.language_policy()
            return self.render_localized(assignment, image, policy.locale(assignment, policy.effective(assignment, "prompt"), "prompt"))
        p = self.spec(assignment, image)
        layouts = {"single": "one panel", "left-right": "two panels side by side, read left to right",
                   "top-bottom": "two stacked panels, read top to bottom",
                   "2x2": "four panels in a 2 by 2 grid, read left to right then top to bottom"}
        style = ("Clean rounded linework and cel shading" if p["style"]["mode"] == "canonical"
                 else p["style"]["description"])
        costume = ("a navy-and-white maid outfit with a white frilled headpiece and blue bow"
                   if p["costume"]["mode"] == "canonical" else p["costume"]["description"])
        background = p["background"]["description"]
        if (p["background"]["origin"] == "tier" and background ==
                self.m.exaggeration_tiers()["tiers"][image["exaggeration"]]["default_background"]):
            background = {"A": "A detailed setting with perspective and unlettered props.",
                          "B": "A simple graphic effect background.",
                          "C": "A pure white background."}[image["exaggeration"]]
        lines = [f"IMAGE\nA {p['output']['aspect_ratio']} comic with {layouts[p['layout']]}. "
                 + ("Clear gutters between panels. " if p["panel_count"] > 1 else "")
                 + f"{style}. {background}\n{p['lettering']}"]
        lines.append("CHARACTERS AND REFERENCES\nWhale-chan has a broad round face, blue-gradient eyes, "
                     "deep-blue hair with cyan curled ends, paired whale-fin ears, a forward ahoge and one whale tail. "
                     f"She wears {costume}. Her standing body proportions are about "
                     f"{p['proportion']['target_head_ratio']:g} heads tall; retain these proportions in partial views.")
        if any(c["representation"] in {"physical", "avatar"} and not c.get("character_profile") for c in p["cast"]):
            if any(c.get("character_profile") for c in p["cast"]):
                ordinary = ", ".join(c["participant"] for c in p["cast"] if not c.get("character_profile")
                                     and c["representation"] in {"physical", "avatar"})
                lines.append(self.m.language_policy().locale({}, "en", "cast")["abstract"].format(participants=ordinary))
            else:
                lines.append("Supporting figures have blank round heads and simple desaturated indigo bodies, "
                             "without detailed facial features, hairstyles or costumes.")
        words = self.m.language_policy().locale({}, "en", "cast")
        lines.extend(self.m.model_cast().prompt_lines(assignment, p["cast"], p["references"], words, "en"))
        roles = {"identity": "character appearance", "style": "rendering", "costume": "clothing",
                 "proportion": "body proportions", "typography": "lettering appearance",
                 "pose_action": "pose and action", "composition": "framing", "background": "setting"}
        for n, ref in enumerate(p["references"], 1):
            detail = ref["instruction"]
            if detail == "Preserve only the declared canonical Whale-chan roles; never copy its facial expression":
                detail = None
            lines.append(f"Reference {n}: {', '.join(roles[r] for r in ref['roles'])}."
                         + (f" {detail}" if detail else ""))
        framing = " ".join(v for v in p["composition"].values() if v)
        if framing:
            lines.append(framing)
        for action, expression in zip(p["actions"], p["expressions"], strict=True):
            panel = action["panel"]
            lines.append(f"PANEL {panel}\n{action['action']}\n{expression['visual_description']}")
            for member in p["cast"]:
                if panel not in member["panels"]:
                    continue
                form = {"physical": "bodily present", "avatar": "a flat avatar",
                        "offscreen": "outside the frame"}[member["representation"]]
                lines.append(f"{member['participant']} is {form}." +
                             (f" {member['staging']}" if member["staging"] else ""))
            if panel == p["landing_panel"]:
                lines.extend(p["effects"])
            for item in p["dialogue"]:
                if item["panel"] != panel:
                    continue
                delivery = item["delivery"]
                if delivery == "label":
                    target = f"Writing on {item['prop']}"
                    if item["speaker"] != "narrator":
                        target += f", written by {item['speaker']}"
                elif delivery == "sfx":
                    target = "Drawn sound effect without a balloon"
                elif delivery == "caption":
                    target = "Caption without a speech tail"
                    if item["speaker"] != "narrator":
                        target += f", in {item['speaker']}'s voice"
                else:
                    speaker = "the in-scene device" if item["speaker"] == "device" else item["speaker"]
                    target = f"{delivery.capitalize()} balloon from {speaker}"
                lines.append(f"{target}, {item['placement']}, reads exactly: "
                             + json.dumps(item["text"], ensure_ascii=False))
        lines.append("Only the quoted text is visible; other surfaces have no writing.")
        return "\n\n".join(lines) + "\n"


    def render_localized(self, assignment, image, messages):
        t = lambda key, **values: messages[key].format(**values)
        speakers = {p['id']: p['role'] for p in assignment['input']['participants']}
        speakers.update({key: messages[key] for key in ('whalechan', 'narrator', 'device')})
        p = self.spec(assignment, image)
        layouts = {'single': t('layout_single'), 'left-right': t('layout_left_right'), 'top-bottom': t('layout_top_bottom'), '2x2': t('layout_grid')}
        style = t('canonical_style') if p['style']['mode'] == 'canonical' else p['style']['description']
        costume = t('canonical_costume') if p['costume']['mode'] == 'canonical' else p['costume']['description']
        background = p['background']['description']
        if p['background']['origin'] == 'tier' and background == self.m.exaggeration_tiers()['tiers'][image['exaggeration']]['default_background']:
            background = {'A': t('background_a'), 'B': t('background_b'), 'C': t('background_c')}[image['exaggeration']]
        lines = [t('image_header', v0=p['output']['aspect_ratio'], v1=layouts[p['layout']]) + (t('gutters') if p['panel_count'] > 1 else '') + t('appearance', v0=style, v1=background, v2=p['lettering'])]
        lines.append(t('identity', v0=costume, v1=p['proportion']['target_head_ratio']))
        if any(c['representation'] in {'physical', 'avatar'} and not c.get('character_profile') for c in p['cast']):
            if any(c.get('character_profile') for c in p['cast']):
                policy = self.m.language_policy()
                words = policy.locale(assignment, policy.effective(assignment, 'prompt'), 'cast')
                ordinary = ', '.join(speakers[c['participant']] for c in p['cast'] if not c.get('character_profile')
                                     and c['representation'] in {'physical', 'avatar'})
                lines.append(words['abstract'].format(participants=ordinary))
            else:
                lines.append(t('supporting'))
        if any(c.get('character_profile') for c in p['cast']):
            policy = self.m.language_policy()
            language = policy.effective(assignment, 'prompt')
            words = policy.locale(assignment, language, 'cast')
            lines.extend(self.m.model_cast().prompt_lines(assignment, p['cast'], p['references'], words, language))
        roles = {'identity': t('identity_role'), 'style': t('rendering'), 'costume': t('clothing'), 'proportion': t('proportion_role'), 'typography': t('typography_role'), 'pose_action': t('action_role'), 'composition': t('framing'), 'background': t('setting')}
        for n, ref in enumerate(p['references'], 1):
            detail = ref['instruction']
            if detail == 'Preserve only the declared canonical Whale-chan roles; never copy its facial expression':
                detail = None
            lines.append(t('reference', v0=n, v1=', '.join((roles[r] for r in ref['roles']))) + (t('extra', v0=detail) if detail else ''))
        framing = ' '.join((v for v in p['composition'].values() if v))
        if framing:
            lines.append(framing)
        for action, expression in zip(p['actions'], p['expressions'], strict=True):
            panel = action['panel']
            lines.append(t('panel', v0=panel, v1=action['action'], v2=expression['visual_description']))
            for member in p['cast']:
                if panel not in member['panels']:
                    continue
                form = {'physical': t('physical'), 'avatar': t('avatar'), 'offscreen': t('offscreen')}[member['representation']]
                lines.append(t('cast', v0=speakers[member['participant']], v1=form) + (t('extra', v0=member['staging']) if member['staging'] else ''))
            if panel == p['landing_panel']:
                lines.extend(p['effects'])
            for item in p['dialogue']:
                if item['panel'] != panel:
                    continue
                delivery = item['delivery']
                if delivery == 'label':
                    target = t('label', v0=item['prop'])
                    if item['speaker'] != 'narrator':
                        target += t('written_by', v0=speakers[item['speaker']])
                elif delivery == 'sfx':
                    target = t('sfx')
                elif delivery == 'caption':
                    target = t('caption')
                    if item['speaker'] != 'narrator':
                        target += t('voice', v0=speakers[item['speaker']])
                else:
                    speaker = t('device_description') if item['speaker'] == 'device' else speakers[item['speaker']]
                    target = t('balloon', v0=t(delivery), v1=speaker)
                lines.append(t('exact_text', v0=target, v1=item['placement']) + json.dumps(item['text'], ensure_ascii=False))
        lines.append(t('no_other_text'))
        return '\n\n'.join(lines) + '\n'
