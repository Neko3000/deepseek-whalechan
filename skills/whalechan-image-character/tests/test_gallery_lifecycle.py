"""Exercise export using actual run-manager output and synthetic QA fixtures."""
import argparse

import helpers as fixtures
from test_gallery import gallery, payload


class GalleryLifecycleTests(fixtures.FixtureCase):
    def test_finalized_run_exports_without_mutating_records(self):
        run = self.initialize()
        args = self.candidate(run)
        fixtures.manage_run.cmd_record_candidate(args)
        fixtures.manage_run.cmd_promote(argparse.Namespace(run_dir=str(run), image=args.image, attempt=1))
        fixtures.manage_run.cmd_finalize(argparse.Namespace(run_dir=str(run), allow_failures=False))
        before = {name: (run / name).read_bytes() for name in ('manifest.json', 'assignment.json')}
        result = gallery.export_gallery([run])
        group = payload(result['gallery'])['groups'][0]
        self.assertEqual(group['passed'], 1)
        self.assertEqual(group['calls'], 1)
        self.assertEqual(group['warnings'], [])
        self.assertEqual(group['proposals'][0]['images'][0]['origin']['prompt'], 'Synthetic Whale-chan prompt.')
        self.assertEqual(before, {name: (run / name).read_bytes() for name in before})
