import unittest
import test_manage_run as fixtures

manage = fixtures.manage


class ExecutionTests(unittest.TestCase):
    def test_capacity_is_resolved_before_consent(self):
        cases = [(25, 20, 20, 10, False, 10), (10, 3, 10, 10, False, 3),
                 (10, 8, 2, 10, False, 2), (10, 8, 8, 4, False, 4),
                 (1, 8, 8, 10, False, 1), (10, 0, 8, 10, False, 0),
                 (10, 8, 8, 10, True, 0)]
        for ready, slots, provider, limit, serial, expected in cases:
            with self.subTest(expected=expected, inputs=(ready, slots, provider, limit, serial)):
                plan = manage.plan_execution(ready, slots, provider, limit, serial)
                self.assertEqual(plan["subagent_count"], expected)
                self.assertEqual(plan["requested_parallelism"], max(1, expected))
                self.assertEqual(plan["mode"], "parallel" if expected > 1 else "sequential")
                self.assertEqual(plan["max_parallelism"], 10)
        for inputs in ((0, 3, 3), (3, -1, 3), (3, 3, 0), (3, True, 3)):
            with self.assertRaises(manage.RunError):
                manage.plan_execution(*inputs)

    def test_worker_limits_and_runtime_reduction(self):
        plan = manage.plan_execution(10, 10, 10)
        for count in (-1, 11, True, None):
            with self.subTest(count=count), self.assertRaises(manage.RunError):
                manage.normalize_execution({**plan, "subagent_count": count})
        with self.assertRaises(manage.RunError):
            manage.normalize_execution({**plan, "requested_parallelism": 11})
        self.assertEqual(manage.effective_subagents(plan, 3, 3), 3)
        self.assertEqual(manage.effective_subagents(plan, 1, 0), 0)
        for parallel, count in ((11, 11), (3, 4), (1, -1), (1, None), (True, 1)):
            with self.assertRaises(manage.RunError):
                manage.effective_subagents(plan, parallel, count)


    def test_gate_two_binds_worker_count_and_init_records_reduction(self):
        import argparse
        import json
        import tempfile
        from pathlib import Path

        value = fixtures.selected_assignment([{'choice': 'A', 'count': 3}])
        value['execution'] = manage.plan_execution(3, 3, 3)
        fixtures.confirm_fixture_selection(value)
        self.assertIn('3 个子代理', manage.selection_markdown(manage.selection_summary(value)))
        value['execution'] = manage.plan_execution(3, 2, 3)
        with self.assertRaisesRegex(manage.RunError, 'Gate 2 confirmation is stale'):
            manage.validate_approval(value)
        value['execution'] = manage.plan_execution(3, 3, 3)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'assignment.json'
            path.write_text(json.dumps(value))
            args = argparse.Namespace(assignment=str(path), root=directory,
                                      effective_parallelism=4, effective_subagents=4)
            with self.assertRaisesRegex(manage.RunError, 'parallelism'):
                manage.cmd_init(args)
            args.effective_parallelism, args.effective_subagents = 1, 0
            run = Path(manage.cmd_init(args)['run_dir'])
            manifest = manage.load_run(str(run))[2]
            self.assertEqual(manifest['execution']['subagent_count'], 3)
            self.assertEqual(manifest['execution']['effective_subagent_count'], 0)
            manifest['execution']['effective_subagent_count'] = 4
            manage.write_json(run / 'manifest.json', manifest)
            with self.assertRaisesRegex(manage.RunError, 'confirmed limit'):
                manage.load_run(str(run))
