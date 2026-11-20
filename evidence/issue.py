from evidence.envelope import seal_envelope
from evidence.payload import CoveragePayload, encode_coverage
from intake.revisions import get_revision
from quality.disposition import evaluate_revision


def _convex_outline(footprints):
    points = sorted({point for footprint in footprints for point in footprint})

    def chain(ordered):
        boundary = []
        for point in ordered:
            while len(boundary) > 1:
                start, end = boundary[-2:]
                turn = ((end[0] - start[0]) * (point[1] - start[1])
                        - (end[1] - start[1]) * (point[0] - start[0]))
                if turn > 0:
                    break
                boundary.pop()
            boundary.append(point)
        return boundary

    return tuple(chain(points)[:-1] + chain(reversed(points))[:-1])


def issue_piece(store, revision_id):
    revision = get_revision(store, revision_id)
    dispositions = evaluate_revision(revision)
    footprints = tuple(item.footprint for item in dispositions if item.footprint is not None)
    if len(footprints) > 1:
        footprints = (_convex_outline(footprints),)
    payload = encode_coverage(CoveragePayload(footprints))
    return seal_envelope(
        revision.station_id, revision.batch_id, revision.revision_id, revision.domain, payload,
    )
