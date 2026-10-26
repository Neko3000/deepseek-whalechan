"""Render confirmed-plan facts with the task's communication locale."""
from collections import Counter


def render(manager, value, summary):
    policy = manager.language_policy()
    words = policy.locale(value, policy.effective(value, 'communication'), 'plan')
    cell = manager.markdown_cell
    lines = ['# ' + cell(value['run_title']), '', words['tiered_header'], '|---|---|---|---|---|---|---|---|']
    has_cast = any(c.get('character_id') for image in summary['visual_plan'] for c in image['cast'])
    if has_cast:
        language = policy.effective(value, 'communication')
        cast_words = policy.locale(value, language, 'cast')
        lines[-2] = lines[-2].rstrip(' |') + ' | ' + cast_words['heading'] + ' |'
        lines[-1] += '---|'
    options = value['proposal']['options']
    for index, item in enumerate(options, 1):
        visual = summary['visual_plan'][index - 1]
        staging = '\n'.join(f"{a['panel']}: {a['action']} {e['visual_description']}" for a, e in zip(visual['actions'], visual['expressions']))
        # When prompt and communication languages differ, authors supply a faithful display version.
        if policy.effective(value, 'prompt') != policy.effective(value, 'communication'):
            staging = manager.text(item.get('display_staging'), 'proposal.display_staging')
        tier = words['tiers'][item['exaggeration']]
        if item.get('contrast'):
            c = item['contrast']
            tier = words['contrast'].format(tier=tier, axes=words['list'].join(words['axes'][a] for a in c['axes']), lowered=c['lowered_to'])
        cells = [str(index), item['title'] + words['colon'] + item['premise'], words['directions'][item['direction']] + words['colon'] + item['twist'], str(item['panel_count']), tier, staging, '\n'.join(item['key_lines']), item['selection_reason']]
        if has_cast:
            cells.append(manager.model_cast().plan_text(visual['cast'], cast_words, value, language))
        lines.append('| ' + ' | '.join(cell(x) for x in cells) + ' |')
    panels = Counter(i['panel_count'] for i in options)
    tiers = Counter(i['exaggeration'] for i in options)
    lines += ['', words['panels'] + words['list'].join(words['panel_item'].format(count=k, n=v) for k, v in sorted(panels.items()))]
    n = len(options)
    counts = ' / '.join(str(tiers[k]) for k in 'ABC')
    if value['exaggeration_policy']['mode'] == 'target-ratio':
        lines += [words['ratio'].format(counts=counts, percent=' / '.join(f'{100*tiers[k]/n:.1f}%' for k in 'ABC'), deviation=' / '.join(f'{tiers[k]-n*r:+.1f}' for k,r in zip('ABC', [.6,.2,.2])))]
    else:
        lines += [words['tier_counts'].format(counts=counts)]
    if n < 3:
        lines += [words['small_set']]
    lines += [words['proportion'] + words['list'].join(words['head_ratio'].format(row=i, kind=words['forms'].get(p['preset'], words['custom_ratio']), ratio=p['target_head_ratio']) for i,p in enumerate(summary['proportions'],1)), words['legend']]
    for field, key in [('panel_policy','panel_override'), ('exaggeration_policy','tier_override')]:
        if value.get(field, {}).get('mode') == 'user-override':
            lines += [words[key] + cell(value[field]['user_instruction'])]
    execution = summary['execution']
    lines += ['', words['totals'].format(n=n,calls=3*n), words['workers'].format(**execution['role_limits']), words['batch_cap'].format(cap=execution['batch_limit']), words['review'], words['tool'].format(**execution['tool']), words['language'].format(language=value['language'], overrides=policy.overrides_text(value, words)), '', words['question']]
    return '\n'.join(lines) + '\n'
