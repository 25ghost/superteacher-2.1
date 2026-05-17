from __future__ import annotations

from typing import Any


def _contains(text: str, *terms: str) -> bool:
    return any(term in text for term in terms)


def infer_lesson_diagrams(
    title: str,
    subject: str = "",
    unit: str = "",
) -> list[dict[str, Any]]:
    """Choose a useful rendered visual without loading an external asset."""
    topic = f"{title} {unit}".lower()
    subject_key = subject.lower()
    caption = f"Visual model for {title}."

    if _contains(topic, "slope", "intercept", "straight line", "linear graph"):
        return [{"type": "cartesian", "params": {"function": "linear", "m": 1, "c": 1}, "caption": "A straight line showing positive slope and its y-intercept."}]
    if _contains(topic, "quadratic", "parabola"):
        return [{"type": "cartesian", "params": {"function": "quadratic", "a": 1, "b": 0, "c": -2}, "caption": "A quadratic graph showing symmetry, roots and turning point."}]
    if _contains(topic, "function", "coordinate", "graph", "relation"):
        return [{"type": "cartesian", "params": {"function": "linear", "m": 2, "c": -1}, "caption": "Coordinate representation linking input, output and graph."}]
    if _contains(topic, "set", "venn", "intersection", "union"):
        return [{"type": "venn", "params": {"sets": 2, "values": {"A": "A only", "AB": "A ∩ B", "B": "B only"}}, "caption": "Overlapping sets and their intersection."}]
    if _contains(topic, "number line", "integer", "rational number", "ordering", "inequality"):
        return [{"type": "number_line", "params": {"min": -5, "max": 5, "highlight": [-3, 0, 2, 4]}, "caption": "Numbers positioned by value on a number line."}]
    if _contains(topic, "trigonom", "sine", "cosine", "tangent"):
        return [{"type": "unit_circle", "params": {"angle": 45, "show_sin": True, "show_cos": True}, "caption": "Sine and cosine as coordinates on the unit circle."}]
    if _contains(topic, "pythag", "right triangle", "triangle"):
        return [{"type": "triangle", "params": {"a": 3, "b": 4, "c": 5}, "caption": "A labelled right triangle for side and angle reasoning."}]
    if _contains(topic, "angle", "parallel line", "transversal"):
        return [{"type": "angles", "params": {"type": "parallel_lines", "angle": 60}, "caption": "Angle relationships formed by parallel lines and a transversal."}]
    if _contains(topic, "transform", "translation", "reflection", "rotation", "enlargement"):
        return [{"type": "transformation", "params": {"type": "translation", "dx": 90, "dy": -25}, "caption": "An object and its transformed image."}]
    if _contains(topic, "circle", "chord", "diameter", "radius"):
        return [{"type": "geometry", "params": {"shape": "circle"}, "caption": "A labelled circle with centre and diameter."}]
    if _contains(topic, "statistics", "frequency", "bar graph", "data presentation", "survey"):
        return [{"type": "bar_chart", "params": {"labels": ["A", "B", "C", "D"], "values": [4, 8, 6, 10]}, "caption": "A bar chart for comparing categorical data."}]
    if _contains(topic, "probability", "outcome", "sample space"):
        return [{"type": "tree", "params": {}, "caption": "A probability tree showing sequential outcomes."}]
    if _contains(topic, "wave", "sound", "frequency", "wavelength", "oscillation"):
        return [{"type": "wave", "params": {"cycles": 2.5}, "caption": "A transverse wave with crests, troughs and wavelength."}]
    if _contains(topic, "circuit", "electric", "current", "voltage", "resistance", "ohm"):
        return [{"type": "circuit", "params": {}, "caption": "A closed series circuit with a cell, resistor and lamp."}]
    if _contains(topic, "force", "newton", "friction", "weight", "equilibrium"):
        return [{"type": "force_diagram", "params": {}, "caption": "A free-body diagram separating the forces acting on an object."}]
    if _contains(topic, "motion", "velocity", "acceleration", "distance-time"):
        return [{"type": "cartesian", "params": {"function": "linear", "m": 1, "c": 0}, "caption": "A motion graph connecting change in position with time."}]
    if _contains(topic, "cycle", "respiration", "reproduction", "ecosystem", "food chain", "water", "carbon"):
        return [{"type": "cycle", "params": {"labels": ["Input", "Process", "Transfer", "Return"]}, "caption": "A cycle model showing transfer through connected stages."}]
    if subject_key in {"history", "history-citizenship"} or _contains(topic, "colonial", "independence", "cold war", "chronology"):
        return [{"type": "timeline", "params": {"labels": ["Context", "Cause", "Event", "Consequence"]}, "caption": "A timeline for organising historical cause, change and consequence."}]
    if subject_key in {"ict", "computer-science", "software-development", "networking"}:
        return [{"type": "process_flow", "params": {"labels": ["Input", "Process", "Store", "Output"]}, "caption": "Information moving through a digital system."}]
    if _contains(topic, "process", "procedure", "algorithm", "production", "processing", "workflow"):
        return [{"type": "process_flow", "params": {"labels": ["Prepare", "Perform", "Check", "Improve"]}, "caption": "A process model with preparation, action, checking and improvement."}]

    center = title if len(title) <= 28 else title[:25].rstrip() + "…"
    return [{
        "type": "concept_map",
        "params": {
            "center": center,
            "nodes": ["Key terms", "How it works", "Example", "Check"],
        },
        "caption": caption,
    }]
