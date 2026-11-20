from analysis.edges import vertical_section
from analysis.intervals import ClosedInterval, intersect_closed_intervals, merge_closed_intervals


def full_height_spans(polygons, request):
    rail = ClosedInterval(request.rail_left, request.rail_right)
    spans = []
    for polygon in polygons:
        transposed = tuple((y, x) for x, y in polygon)
        lower = vertical_section(transposed, request.lower)
        upper = vertical_section(transposed, request.upper)
        if lower is None or upper is None:
            continue
        span = intersect_closed_intervals(lower, upper)
        if span is not None:
            clipped = intersect_closed_intervals(span, rail)
            if clipped is not None:
                spans.append(clipped)
    return merge_closed_intervals(spans)
