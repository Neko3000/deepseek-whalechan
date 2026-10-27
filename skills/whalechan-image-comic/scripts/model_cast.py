"""Model identities within the current visual-plan and single-review contracts."""
from pathlib import Path


class ModelCast:
    def __init__(self, manager):
        self.m = manager
        value = manager.read_json(manager.SKILL_ROOT / 'references/model-characters.json')
        if value.get('schema_version') != 1 or not isinstance(value.get('characters'), dict):
            raise manager.RunError('Invalid model character registry')
        self.characters = value['characters']

    def resolve(self, value):
        key = value.strip().casefold()
        for identifier, profile in self.characters.items():
            names = [identifier, profile['display_name'], *profile['aliases']]
            if key in {name.casefold() for name in names}:
                return identifier
        return None

    def normalize(self, image, participants, proportion):
        m = self.m
        sources = {p['id']: p for p in participants}
        result = []
        for member in image['cast_plan']:
            item = dict(member)
            source = sources[item['participant']]
            named = self.resolve(source['role'])
            explicit = source.get('character_id')
            if explicit and named and explicit != named:
                raise m.RunError('Source character_id conflicts with its named model role')
            expected = explicit or named or self.resolve(source['id']) or 'abstract-user'
            identifier = item.get('character_id', expected)
            if identifier not in {'abstract-user', *self.characters} or identifier != expected:
                raise m.RunError('Cast character does not match its source participant')
            # Leave old abstract-only plans and their confirmation hashes unchanged.
            if identifier == 'abstract-user' and not any(k in item for k in (
                    'character_id', 'character_profile', 'profile_sha256', 'form', 'target_head_ratio',
                    'identity_form', 'reference', 'reference_sha256')):
                result.append(item)
                continue
            visible = item['representation'] in {'physical', 'avatar'}
            if identifier == 'abstract-user':
                profile = None
                form = target = anchor = None
                reference = 'assets/supporting-character-references/abstract-user-pose-sheet.webp' if visible else None
            else:
                for key in ('performance', 'interaction'):
                    m.text(item.get(key), 'cast.' + key)
                profile = {k: self.characters[identifier][k] for k in
                           ('display_name', 'visual_identity', 'costume', 'personality', 'localized')}
                form = item.get('form', proportion['preset'] or 'custom')
                if form not in m.FORMS | {'custom'}:
                    raise m.RunError('cast.form must name a preset or custom')
                forms = m.read_json(m.CATALOG_PATH)['character_forms']
                if form == 'custom':
                    if 'target_head_ratio' not in item and proportion['mode'] != 'custom':
                        raise m.RunError('Custom model form requires target_head_ratio')
                    target = item.get('target_head_ratio', proportion['target_head_ratio'])
                    custom, nearest = m.normalize_proportion(
                        {'proportion': {'mode': 'custom', 'target_head_ratio': target}}, forms, 'cast')
                    target = custom['target_head_ratio']
                    anchor = item.get('identity_form', nearest)
                else:
                    target = forms[form]['mean_head_ratio']
                    anchor = form
                if anchor not in m.FORMS:
                    raise m.RunError('cast.identity_form must name a preset')
                reference = self.characters[identifier]['references'][anchor] if visible else None
            frozen = {'character_id': identifier, 'form': form, 'target_head_ratio': target,
                      'identity_form': anchor, 'reference': reference,
                      'reference_sha256': m.sha256(m.SKILL_ROOT / reference) if reference else None,
                      'character_profile': profile, 'profile_sha256': m.contract_hash(profile)}
            for key, value in frozen.items():
                if key in item and item[key] != value:
                    raise m.RunError(f'cast.{key} is stale or does not match its character')
            item.update(frozen)
            result.append(item)
        return result

    def validate_references(self, cast, refs):
        m = self.m
        required = {}
        for member in cast:
            if member['representation'] not in {'physical', 'avatar'}:
                continue
            relative = member.get('reference') or 'assets/supporting-character-references/abstract-user-pose-sheet.webp'
            required.setdefault(str((m.SKILL_ROOT / relative).resolve()), []).append(member)
        actual = {str(Path(r['path']).resolve()): r for r in refs
                  if Path(r['path']).resolve().is_relative_to(m.SKILL_ROOT / 'assets/supporting-character-references')}
        if set(actual) != set(required):
            raise m.RunError('Supporting references must match the visible cast exactly')
        if len(refs) > 5:
            raise m.RunError('Visual plan exceeds five references; resolve cast before confirmation')
        for path, members in required.items():
            ref = actual[path]
            if 'identity' not in ref['roles']:
                raise m.RunError('Supporting reference must control its assigned identity')
            for member in members:
                if member.get('character_profile'):
                    if set(ref['roles']) - {'identity', 'costume', 'proportion'}:
                        raise m.RunError('Model sheets cannot control style, action or composition')
                    if member['form'] == 'custom' and 'proportion' in ref['roles']:
                        raise m.RunError('Custom model proportions cannot use preset reference proportions')
                    if member['reference_sha256'] != ref['sha256']:
                        raise m.RunError('Supporting reference hash differs from confirmed cast')

    def contract(self, cast):
        base = ('participant', 'representation', 'panels', 'staging')
        extra = ('character_id', 'form', 'target_head_ratio', 'identity_form', 'reference',
                 'reference_sha256', 'character_profile', 'profile_sha256', 'performance', 'interaction',
                 'display_performance', 'display_interaction')
        return [{**{k: member.get(k) for k in base},
                 **{k: member[k] for k in extra if k in member}} for member in cast]

    def validate_qa(self, review, image):
        members = [c for c in image['cast_plan'] if c.get('character_profile')]
        if not members:
            return
        observed = review.get('cast_observations')
        if not isinstance(observed, list) or len(observed) != len(members):
            raise self.m.RunError('Model cast requires candidate-bound cast_observations')
        keys = ('participant', 'character_id', 'representation', 'panels', 'form', 'target_head_ratio')
        for actual, expected in zip(observed, members, strict=True):
            if not isinstance(actual, dict) or any(actual.get(k) != expected.get(k) for k in keys):
                raise self.m.RunError('cast_observations must match each frozen model identity and form')
            self.m.string_list(actual.get('observed_cues'), 'cast_observations.observed_cues')

    def plan_text(self, cast, words, assignment, language):
        lines = []
        for member in cast:
            profile = member.get('character_profile')
            localized = self.localized_profile(assignment, member, language) if profile else None
            lines.append(words['cast_role'].format(participant=member['participant'],
                         identity=member.get('character_id', 'abstract-user'),
                         representation=words['representations'][member['representation']]))
            if profile:
                lines.append(words['cast_form'].format(form=member['form'], ratio=member['target_head_ratio']))
                lines.append(words['cast_personality'].format(text=localized['personality_summary']))
                for key in ('performance', 'interaction'):
                    scoped = (assignment.get('schema_version') == 20 and
                              self.m.language_policy().effective(assignment, 'prompt') != language)
                    text = member['display_' + key] if scoped else member[key]
                    lines.append(words['cast_' + key].format(text=text))
                if member['reference']:
                    path = (self.m.SKILL_ROOT / member['reference']).resolve().as_posix()
                    lines.append(f"![{member['character_id']}]({path})")
        return '\n'.join(lines) or words['cast_none']

    def localized_profile(self, assignment, member, language):
        profile = member['character_profile']
        supplied = assignment.get('localizations', {}).get(language, {}).get('characters', {})
        result = supplied.get(member['character_id'], profile['localized'].get(language))
        if result is None:
            raise self.m.RunError(f"Author {language} character translations before confirmation")
        expected = profile['localized']['en']
        if not isinstance(result, dict) or set(result) != set(expected):
            raise self.m.RunError('Character translations must cover name, identity, costume and personality')
        for key in ('display_name', 'costume', 'personality_summary'):
            self.m.text(result.get(key), 'character translation.' + key)
        self.m.string_list(result.get('visual_identity'), 'character translation.visual_identity')
        return result

    def prompt_lines(self, assignment, cast, refs, words, language):
        lines = []
        for member in cast:
            if not member.get('character_profile') or member['representation'] not in {'physical', 'avatar'}:
                continue
            p = self.localized_profile(assignment, member, language)
            lines.append(words['model'].format(participant=member['participant'], name=p['display_name'],
                         identity='; '.join(p['visual_identity']), costume=p['costume'],
                         ratio=member['target_head_ratio'], personality=p['personality_summary'],
                         performance=member['performance'], interaction=member['interaction']))
            number = next(n for n,r in enumerate(refs,1) if r['sha256'] == member['reference_sha256'])
            lines.append(words['reference'].format(number=number, participant=member['participant']))
        return lines
