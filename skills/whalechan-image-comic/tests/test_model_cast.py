"""Model cast integration with current planning, prompting, and QA contracts."""
import argparse
import copy
import json
import tempfile
import unittest
from pathlib import Path

import test_manage_run as fixtures

m = fixtures.manage


def model_assignment(models=('gpt',), abstract=True):
    value = fixtures.assignment()
    value.update(schema_version=20, language='en', run_title='Model cast fixture',
                 language_resolution={'source':'explicit','reason':'Synthetic English task'})
    value['input']['language'] = 'en'
    ids = list(models) + (['abstract-user'] if abstract else [])
    value['input']['participants'] = [
        {'id':f'actor_{n}', 'role':identifier if identifier != 'abstract-user' else 'user',
         'source_evidence':'Synthetic direct participant', 'character_id':identifier}
        for n,identifier in enumerate(ids)]
    for image in value['images']:
        image['title'] = 'A model joins the scene'
        image['cast_plan'] = []
        for n,identifier in enumerate(ids):
            image['cast_plan'].append({'participant':f'actor_{n}', 'character_id':identifier,
                'representation':'physical', 'panels':list(range(1,image['panel_count']+1)),
                'staging':'Standing by the table', 'reason':'Direct interlocutor',
                'performance':'Studies the result carefully.', 'interaction':'Responds to the visible mistake.'})
            path = ('assets/supporting-character-references/abstract-user-pose-sheet.webp'
                    if identifier == 'abstract-user' else
                    f'assets/supporting-character-references/models/{identifier}/semi-chibi.webp')
            image['references'].append({'id':f'actor-{n}', 'path':str(m.SKILL_ROOT/path),
                                         'roles':['identity'], 'instruction':f'Identity of actor_{n} only.'})
    return value


class ModelCastTests(unittest.TestCase):
    def normalize(self, value):
        value = fixtures.confirm_fixture_plan(value)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'assignment.json';path.write_text(json.dumps(value))
            return m.validate_assignment(path)
    def test_registry_and_catalog_keep_all_eight_models_and_five_forms(self):
        cast=m.model_cast();assets,_,_=m.catalog()
        self.assertEqual(len(cast.characters),8)
        self.assertEqual(cast.resolve('ChatGPT'),'gpt')
        self.assertEqual(cast.resolve('Seed'),'doubao')
        for identifier,profile in cast.characters.items():
            self.assertEqual(set(profile['references']),m.FORMS)
            for form,relative in profile['references'].items():
                entry=assets[str((m.SKILL_ROOT/relative).resolve())]
                self.assertEqual((entry['character_id'],entry['form']),(identifier,form))

    def test_mixed_cast_keeps_distinct_roles_in_prompt_and_confirmation(self):
        value=self.normalize(model_assignment())
        image=value['images'][0]
        prompt=m.visual_prompt().render(value,image)
        for word in ('actor_0 (GPT)','dragon horns','white scaled dragon tail',
                     'blank round heads','ONE character','Studies the result carefully.'):
            self.assertIn(word,prompt)
        self.assertIn('Only the ordinary-person roles',prompt)
        self.assertNotIn('Supporting figures have',prompt)
        plan=m.plan_markdown(value)
        for word in ('Cast and settings','gpt','abstract-user','2.8','organizer'):
            self.assertIn(word,plan)
        self.assertEqual(value['schema_version'],20)
        self.assertEqual(image['qa_contract_version'],11)
        self.assertEqual(value['execution']['planning_mode'],'independent-priority-ranking')

    def test_source_roles_reject_invented_or_swapped_actors(self):
        for mode in ('missing','mismatch','unknown'):
            value=model_assignment()
            if mode=='missing':value['input']['participants'].pop()
            elif mode=='mismatch':value['images'][0]['cast_plan'][0]['character_id']='kimi'
            else:value['input']['participants'][0]['character_id']='unknown'
            with self.subTest(mode=mode), self.assertRaises(m.RunError):
                self.normalize(value)

    def test_a_model_mentioned_in_dialogue_does_not_add_a_character(self):
        value=model_assignment((),True)
        value['input']['content']='The user mentions GPT but only the user participates.'
        normalized=self.normalize(value)
        self.assertNotIn('dragon horns',m.visual_prompt().render(normalized,normalized['images'][0]))
    def test_custom_ratios_and_reference_roles_are_enforced(self):
        value=model_assignment()
        member=value['images'][0]['cast_plan'][0]
        member.update(form='custom',target_head_ratio=3.7,identity_form='semi-chibi')
        normalized=self.normalize(value)
        self.assertEqual(normalized['images'][0]['cast_plan'][0]['target_head_ratio'],3.7)
        value['images'][0]['references'][1]['roles'].append('proportion')
        with self.assertRaisesRegex(m.RunError,'Custom model'):
            self.normalize(value)
        value=model_assignment();value['images'][0]['cast_plan'][0]['form']='custom'
        with self.assertRaisesRegex(m.RunError,'target_head_ratio'):
            self.normalize(value)

    def test_wrong_reference_missing_reference_and_excess_cast_fail_before_approval(self):
        for mode in ('wrong','missing','style','hash'):
            value=model_assignment();refs=value['images'][0]['references']
            if mode=='wrong':refs[1]['path']=str(m.SKILL_ROOT/'assets/supporting-character-references/models/kimi/semi-chibi.webp')
            elif mode=='missing':refs.pop(1)
            elif mode=='style':refs[1]['roles'].append('style')
            else:refs[1]['sha256']='0'*64
            with self.subTest(mode=mode),self.assertRaises(m.RunError):self.normalize(value)
        with self.assertRaisesRegex(m.RunError,'five references'):
            self.normalize(model_assignment(('gpt','kimi','claude'),True))

    def test_offscreen_model_keeps_profile_but_loads_no_reference(self):
        value=model_assignment(('kimi',),False)
        for image in value['images']:
            image['cast_plan'][0].update(representation='offscreen',staging=None)
            image['references'].pop()
        normalized=self.normalize(value);member=normalized['images'][0]['cast_plan'][0]
        self.assertIsNone(member['reference'])
        self.assertEqual(member['character_id'],'kimi')
        prompt=m.visual_prompt().render(normalized,normalized['images'][0])
        self.assertNotIn('Silver-white',prompt)

    def test_cast_changes_invalidate_single_confirmation(self):
        value=fixtures.confirm_fixture_plan(model_assignment())
        for field,new in [('performance','A different action'),('form','chibi'),
                          ('interaction','A different response')]:
            changed=copy.deepcopy(value);changed['images'][0]['cast_plan'][0][field]=new
            with self.subTest(field=field),self.assertRaises(m.RunError):m.validate_approval(changed)
    def test_normalized_profiles_cannot_be_silently_rewritten(self):
        value=self.normalize(model_assignment())
        value['images'][0]['cast_plan'][0]['character_profile']['costume']='An unrelated outfit'
        with self.assertRaisesRegex(m.RunError,'stale'):
            m.selection_summary(value)

    def test_model_visual_observations_are_required_and_bound(self):
        image=self.normalize(model_assignment())['images'][0]
        image['proportion_check']='visible-only'
        member=image['cast_plan'][0]
        observation={k:member[k] for k in ('participant','character_id','representation','panels','form','target_head_ratio')}
        observation['observed_cues']=['Synthetic test evidence only, not an image review.']
        qa={'review_status':'reviewed','candidate_sha256':'a'*64,'reviewer':'synthetic-test',
            'method':'direct-image-inspection','checked':list(m.CONFIGURABLE_GATES),
            'panels':[{'panel':1,'observed_scene':'Synthetic scene for validator testing.'}],
            'text_transcription':image['core_text'],'core_defects':[],'minor_issues':[],
            'verdict':'PASS','targeted_retry':None,
            'form_evidence':{'mode':'visible-only','reason':'Synthetic cropped scene',
                             'observed_cues':['Synthetic body observations']}}
        workflow=m.review_workflow()
        with self.assertRaisesRegex(m.RunError,'cast_observations'):workflow.validate_qa(qa,'a'*64,image)
        qa['cast_observations']=[observation]
        self.assertEqual(workflow.validate_qa(qa,'a'*64,image)['verdict'],'PASS')
        observation['character_id']='kimi'
        with self.assertRaisesRegex(m.RunError,'frozen model'):workflow.validate_qa(qa,'a'*64,image)

    def test_chinese_and_english_cast_text_follow_task_language(self):
        value=model_assignment()
        english=self.normalize(value)
        self.assertIn('reliable, thorough organizer',m.plan_markdown(english))
        value.update(language='zh-Hans',run_title='角色测试')
        value['input']['language']='zh-Hans'
        chinese=self.normalize(value)
        self.assertIn('性格：可靠',m.plan_markdown(chinese))
        prompt=m.visual_prompt().render(chinese,chinese['images'][0])
        self.assertIn('两只浅色龙角',prompt)
        self.assertNotIn('CHARACTERS',prompt)
    def test_current_model_run_initializes_and_resumes_without_new_approval(self):
        value=fixtures.confirm_fixture_plan(model_assignment(('kimi',),True))
        before=value['confirmation']['summary_sha256']
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'assignment.json';path.write_text(json.dumps(value))
            result=m.cmd_init(argparse.Namespace(assignment=str(path),root=str(Path(directory)/'runs'),effective_parallelism=1))
            _,frozen,manifest=m.load_run(result['run_dir'])
            self.assertEqual(frozen['schema_version'],20)
            self.assertEqual(m.selection_summary(frozen)['summary_sha256'],before)
            self.assertEqual(manifest['review_workflow_version'],1)
            self.assertEqual(frozen['images'][0]['cast_plan'][0]['character_id'],'kimi')
            self.assertIn('Kimi',m.visual_prompt().render(frozen,frozen['images'][0]))

    def test_scoped_cast_display_is_required_and_bound_to_confirmation(self):
        value=model_assignment();value['language_overrides']={'communication':'zh-Hans'}
        for option in value['proposal']['options']:option['display_staging']='测试场景。'
        with self.assertRaisesRegex(m.RunError,'display_performance'):
            fixtures.confirm_fixture_plan(value)
        for image in value['images']:
            image['cast_plan'][0].update(display_performance='认真看结果。',display_interaction='回应眼前的错误。')
        value=fixtures.confirm_fixture_plan(value)
        self.assertIn('认真看结果',m.plan_markdown(value))
        self.assertIn('Studies the result carefully.',m.visual_prompt().render(value,value['images'][0]))
        value['images'][0]['cast_plan'][0]['display_performance']='换了另一种表现。'
        with self.assertRaisesRegex(m.RunError,'stale'):m.validate_approval(value)

    def test_model_presets_inherit_image_form_and_allow_explicit_override(self):
        value=model_assignment(('gemini',),False)
        for image in value['images']:
            image['proportion']={'mode':'preset','preset':'compact'}
            image['references'][1]['path']=str(m.SKILL_ROOT/'assets/supporting-character-references/models/gemini/compact.webp')
        image=value['images'][0]
        image['cast_plan'][0]['form']='chibi'
        image['references'][1]['path']=str(m.SKILL_ROOT/'assets/supporting-character-references/models/gemini/chibi.webp')
        normalized=self.normalize(value)
        self.assertEqual(normalized['images'][0]['cast_plan'][0]['target_head_ratio'],2.5)
        self.assertEqual(normalized['images'][1]['cast_plan'][0]['target_head_ratio'],3.3)
