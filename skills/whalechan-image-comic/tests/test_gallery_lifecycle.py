"""Exercise export using actual run-manager output and synthetic QA fixtures."""
import argparse
import unittest

import test_manage_run as fixtures
from test_gallery import gallery, payload


class GalleryLifecycleTests(unittest.TestCase):
    setUp = fixtures.RunStateTests.setUp
    initialize = fixtures.RunStateTests.initialize
    files = fixtures.RunStateTests.files

    def test_finalized_run_exports_without_mutating_records(self):
        self.initialize([{'choice': 'A', 'count': 1}])
        args = self.files(1, 'PASS')
        fixtures.manage.record_image(args, component=False)
        fixtures.manage.cmd_promote(argparse.Namespace(run_dir=str(self.run_dir), image=args.image))
        fixtures.manage.cmd_finalize(argparse.Namespace(run_dir=str(self.run_dir), allow_partial=False))
        before = {name: (self.run_dir / name).read_bytes() for name in ('manifest.json', 'assignment.json')}
        result = gallery.export_gallery([self.run_dir])
        group = payload(result['gallery'])['groups'][0]
        self.assertEqual(group['passed'], 1)
        self.assertEqual(group['calls'], 1)
        self.assertEqual(group['warnings'], [])
        self.assertEqual(group['proposals'][0]['images'][0]['origin']['prompt'], 'test prompt')
        self.assertEqual(before, {name: (self.run_dir / name).read_bytes() for name in before})
