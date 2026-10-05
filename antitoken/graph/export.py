"""Export skeletons / the public topic graph as Cypher or node-link JSON."""

from __future__ import annotations

import json

from ..models import Skeleton


def _lit(v) -> str:
    """Cypher literal for a JSON-compatible value."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_lit(x) for x in v) + "]"
    return json.dumps(str(v), ensure_ascii=False)  # JSON string escaping is valid Cypher


def _props(d: dict) -> str:
    return "{" + ", ".join(f"{k}: {_lit(v)}" for k, v in d.items()) + "}"


def skeleton_cypher(sk: Skeleton) -> str:
    m = sk.metrics
    conv = {
        "id": sk.id, "source": sk.source, "language": sk.language, "agenda": sk.agenda,
        "created_at": sk.created_at, "compute_units": m["compute_units"],
        "optimized_compute_units": m["optimized_compute_units"], "savings_pct": m["savings_pct"],
        "max_depth": m["max_depth"], "branches": m["branches"],
    }
    out = [f"MERGE (c:Conversation {{id: {_lit(sk.id)}}}) SET c += {_props(conv)};"]
    for t in sk.turns:
        props = {k: v for k, v in t.__dict__.items() if k != "topics"}
        tid = f"{sk.id}:{t.index}"
        out.append(
            f"MERGE (t:Turn {{id: {_lit(tid)}}}) SET t += {_props(props)} "
            f"WITH t MATCH (c:Conversation {{id: {_lit(sk.id)}}}) MERGE (c)-[:HAS_TURN]->(t);"
        )
        for rank, label in enumerate(t.topics):
            out.append(
                f"MATCH (t:Turn {{id: {_lit(tid)}}}) MERGE (p:Topic {{label: {_lit(label)}}}) "
                f"MERGE (t)-[:ABOUT {{rank: {rank}}}]->(p);"
            )
    for e in sk.edges:
        out.append(
            f"MATCH (a:Turn {{id: {_lit(f'{sk.id}:{e.src}')}}}), (b:Turn {{id: {_lit(f'{sk.id}:{e.dst}')}}}) "
            f"MERGE (a)-[:{e.type}]->(b);"
        )
    for rank, label in enumerate(sk.agenda):
        out.append(
            f"MATCH (c:Conversation {{id: {_lit(sk.id)}}}) MERGE (p:Topic {{label: {_lit(label)}}}) "
            f"MERGE (c)-[:COVERS {{rank: {rank}}}]->(p);"
        )
    return "\n".join(out) + "\n"


def topics_cypher(graph: dict) -> str:
    out = ["// k-anonymous public topic graph (k = %d)" % graph["k"]]
    for n in graph["nodes"]:
        out.append(f"MERGE (p:Topic {{label: {_lit(n['label'])}}}) SET p += {_props(n)};")
    for l in graph["links"]:
        out.append(
            f"MATCH (a:Topic {{label: {_lit(l['source'])}}}), (b:Topic {{label: {_lit(l['target'])}}}) "
            f"MERGE (a)-[r:CO_OCCURS]->(b) SET r.count = {l['count']};"
        )
    return "\n".join(out) + "\n"


def skeleton_graph_json(sk: Skeleton) -> dict:
    nodes = [{"id": f"t{t.index}", "kind": "turn", **{k: v for k, v in t.__dict__.items()}} for t in sk.turns]
    topics = sorted({x for t in sk.turns for x in t.topics} | set(sk.agenda))
    nodes += [{"id": f"p:{x}", "kind": "topic", "label": x, "agenda": x in sk.agenda} for x in topics]
    links = [{"source": f"t{e.src}", "target": f"t{e.dst}", "type": e.type} for e in sk.edges]
    links += [{"source": f"t{t.index}", "target": f"p:{x}", "type": "ABOUT"} for t in sk.turns for x in t.topics]
    return {"id": sk.id, "nodes": nodes, "links": links}
