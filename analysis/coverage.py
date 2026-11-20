from fractions import Fraction

from analysis.edges import vertical_section
from analysis.intervals import ClosedInterval, intersect_closed_intervals, merge_closed_intervals


def _interior_crossing(first_start, first_end, second_start, second_end, left, right):
    """Return the strict interior root of the difference of two affine bounds."""
    start_gap = first_start - second_start
    end_gap = first_end - second_end
    if start_gap == 0 or end_gap == 0 or start_gap * end_gap > 0:
        return None
    return left + (right - left) * start_gap / (start_gap - end_gap)


def _covers_band(sections, lower, upper):
    """Whether closed sections chained from lower reach upper without a gap."""
    covered_to = None
    for left, right in sorted(sections):
        if left <= lower:
            covered_to = right if covered_to is None else max(covered_to, right)
        elif covered_to is not None and left <= covered_to:
            covered_to = max(covered_to, right)
    return covered_to is not None and covered_to >= upper


def _band_sections(polygons, x):
    sections = []
    for polygon in polygons:
        section = vertical_section(polygon, x)
        if section is not None:
            sections.append((section.left, section.right))
    return sections


def full_height_spans(polygons, request):
    """Closed x-spans where the union of polygons covers the whole head band.

    Every polygon vertex x starts a slab; inside one slab each section bound is
    affine, so coverage can only change at vertex x's or where two bounds cross
    each other or the band edges. All such crossings are rational and are
    evaluated exactly, keeping closed seams and isolated covered points.
    """
    rail = ClosedInterval(request.rail_left, request.rail_right)
    polygons = tuple(polygons)
    if not polygons:
        return ()
    vertices = sorted({x for polygon in polygons for x, _ in polygon})
    critical = set(vertices)
    for left, right in zip(vertices, vertices[1:]):
        affine = []
        for polygon in polygons:
            at_left = vertical_section(polygon, left)
            at_right = vertical_section(polygon, right)
            if at_left is None or at_right is None:
                continue
            affine.append((at_left.left, at_right.left))
            affine.append((at_left.right, at_right.right))
        for first_start, first_end in affine:
            for bound in (request.lower, request.upper):
                root = _interior_crossing(first_start, first_end, bound, bound, left, right)
                if root is not None:
                    critical.add(root)
            for second_start, second_end in affine:
                root = _interior_crossing(first_start, first_end, second_start, second_end, left, right)
                if root is not None:
                    critical.add(root)
    points = sorted(critical)
    spans = []
    for x in points:
        if _covers_band(_band_sections(polygons, x), request.lower, request.upper):
            spans.append(ClosedInterval(x, x))
    for left, right in zip(points, points[1:]):
        mid = Fraction(left + right, 2)
        if _covers_band(_band_sections(polygons, mid), request.lower, request.upper):
            spans.append(ClosedInterval(left, right))
    return tuple(
        clipped
        for span in merge_closed_intervals(spans)
        if (clipped := intersect_closed_intervals(span, rail)) is not None
    )
