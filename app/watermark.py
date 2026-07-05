from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, NameObject


DEFAULT_WATERMARK_PIXELS = {(312, 90)}


def _image_xobject_names(page, watermark_sizes: set[tuple[int, int]]) -> set[NameObject]:
    resources = page.get("/Resources")
    xobject_ref = resources.get("/XObject") if resources else None
    xobjects = xobject_ref.get_object() if xobject_ref else {}
    names: set[NameObject] = set()
    for name, obj_ref in xobjects.items():
        obj = obj_ref.get_object()
        if obj.get("/Subtype") != "/Image":
            continue
        width = int(obj.get("/Width"))
        height = int(obj.get("/Height"))
        if (width, height) in watermark_sizes:
            names.add(NameObject(name))
    return names


def _recent_cm(operations: list[tuple[list, bytes]], index: int) -> tuple[float, float, float, float, float, float] | None:
    for operands, operator in reversed(operations[max(0, index - 5) : index]):
        if operator == b"Do":
            return None
        if operator != b"cm" or len(operands) != 6:
            continue
        try:
            return tuple(float(x) for x in operands)  # type: ignore[return-value]
        except Exception:
            return None
    return None


def _is_bottom_right_watermark(page, operations: list[tuple[list, bytes]], index: int) -> bool:
    matrix = _recent_cm(operations, index)
    if matrix is None:
        return False
    a, b, c, d, e, f = matrix
    page_width = float(page.mediabox.width)
    page_height = float(page.mediabox.height)
    drawn_width = abs(a)
    drawn_height = abs(d)

    no_rotation = abs(b) < 0.01 and abs(c) < 0.01
    right_side = e >= page_width * 0.65
    bottom_band = f <= page_height * 0.08
    plausible_size = 60 <= drawn_width <= 180 and 15 <= drawn_height <= 70
    return no_rotation and right_side and bottom_band and plausible_size


def _names_used_by_content(stream: ContentStream) -> set[NameObject]:
    used: set[NameObject] = set()
    for operands, operator in stream.operations:
        if operator == b"Do" and operands:
            used.add(NameObject(operands[0]))
    return used


def _remove_unused_watermark_xobjects(page, watermark_names: set[NameObject], used_names: set[NameObject]) -> None:
    resources = page.get("/Resources")
    xobject_ref = resources.get("/XObject") if resources else None
    xobjects = xobject_ref.get_object() if xobject_ref else None
    if not xobjects:
        return
    for name in list(xobjects.keys()):
        normalized = NameObject(name)
        if normalized in watermark_names and normalized not in used_names:
            del xobjects[name]


def remove_camscanner_watermark(
    source: Path,
    destination: Path,
    watermark_sizes: set[tuple[int, int]] | None = None,
    force_size_only: bool = False,
) -> int:
    sizes = watermark_sizes or DEFAULT_WATERMARK_PIXELS
    reader = PdfReader(str(source))
    writer = PdfWriter()
    removed = 0

    for page in reader.pages:
        candidate_names = _image_xobject_names(page, sizes)
        contents = page.get_contents()
        if contents is None:
            writer.add_page(page)
            continue

        stream = ContentStream(contents, reader)
        kept = []
        for index, (operands, operator) in enumerate(stream.operations):
            candidate_draw = (
                operator == b"Do"
                and len(operands) == 1
                and NameObject(operands[0]) in candidate_names
            )
            if candidate_draw and (
                force_size_only or _is_bottom_right_watermark(page, stream.operations, index)
            ):
                removed += 1
                continue
            kept.append((operands, operator))

        stream.operations = kept
        page[NameObject("/Contents")] = stream
        _remove_unused_watermark_xobjects(page, candidate_names, _names_used_by_content(stream))
        writer.add_page(page)

    if reader.metadata:
        writer.add_metadata(dict(reader.metadata))

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as file:
        writer.write(file)
    return removed
