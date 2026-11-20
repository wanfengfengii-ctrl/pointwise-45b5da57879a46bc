from analysis.head import HeadRequest
from analysis.intervals import ClosedInterval
from demo import DOMAIN, GATE, IDENTITY, OUTER_BANDS, RAIL, rectangle
from evidence.issue import issue_piece
from evidence.payload import decode_coverage
from intake.batches import freeze_batch, register_batch
from intake.frames import ScanFrame
from intake.store import StationStore
from quality.footprints import canonical_polygon
from reports.publish import publish_head
from tests import ProjectCase, endpoints


class UnionCoverageTests(ProjectCase):
    def test_piece_preserves_actual_union(self):
        frames = [ScanFrame('low-band', OUTER_BANDS[0], 2), ScanFrame('high-band', OUTER_BANDS[1], 1)]
        with StationStore(self.root / 'a.sqlite', 'A') as store:
            register_batch(store, 'shift', 'Two separated bands')
            freeze_batch(store, 'shift', 'r1', frames, IDENTITY, GATE, DOMAIN)
            piece = issue_piece(store, 'r1')
        polygons = decode_coverage(piece.payload).polygons
        expected = tuple(sorted(canonical_polygon(band) for band in OUTER_BANDS))
        self.assertEqual(polygons, expected)
        self.scenario('n10.piece_preserves_actual_union', {'bands': 2, 'gap': ['1/2', '3/2']},
                      2, len(polygons), expected, polygons,
                      ['evidence/issue.py', 'evidence/payload.py'],
                      'Two qualifying bands stay two polygons. Their convex hull would invent the empty middle band.')

    def test_inner_band_gap_blocks_release(self):
        with self.center() as center:
            parents = self.pair(center, OUTER_BANDS, ())
            report = publish_head(center, *parents, RAIL)
            counts = self.counts(center)
        self.assertEqual(report.positions, ())
        self.scenario('n10.inner_band_gap_blocks_release', {'A': 'bands with empty middle', 'B': 'empty'},
                      [], endpoints(report.positions), (1, 1), counts,
                      ['evidence/issue.py', 'analysis/coverage.py', 'analysis/positions.py', 'reports/publish.py'],
                      'No station covers y=1 anywhere, so the union leaves a real gap and the empty result is still signed.')

    def test_closed_seam_joins_across_stations(self):
        halves = (rectangle(0, 2, 0, 2),), (rectangle(2, 4, 0, 2),)
        with self.center() as center:
            parents = self.pair(center, *halves)
            report = publish_head(center, *parents, HeadRequest(0, 4, 1, 0, 2))
        self.assertEqual(report.positions, (ClosedInterval('1/2', '7/2'),))
        self.scenario('n10.closed_seam_joins_across_stations', {'A': [0, 2], 'B': [2, 4], 'seam': 2},
                      [['1/2', '7/2']], endpoints(report.positions),
                      (parents,), (report.parent_ids,),
                      ['analysis/coverage.py', 'analysis/positions.py', 'reports/publish.py'],
                      'Neither half fits the head alone. The shared closed edge at x=2 joins them into one span.')

    def test_real_gap_keeps_isolated_points(self):
        islands = (rectangle(0, 1, 0, 2),), (rectangle(2, 3, 0, 2),)
        with self.center() as center:
            parents = self.pair(center, *islands)
            report = publish_head(center, *parents, HeadRequest(0, 3, 1, 0, 2))
        expected = (ClosedInterval('1/2', '1/2'), ClosedInterval('5/2', '5/2'))
        self.assertEqual(report.positions, expected)
        self.scenario('n10.real_gap_keeps_isolated_points', {'A': [0, 1], 'B': [2, 3], 'gap': [1, 2]},
                      [['1/2', '1/2'], ['5/2', '5/2']], endpoints(report.positions),
                      (parents,), (report.parent_ids,),
                      ['analysis/coverage.py', 'analysis/positions.py', 'reports/publish.py'],
                      'Each island fits the head at exactly one center. The open gap between them cannot be bridged.')
