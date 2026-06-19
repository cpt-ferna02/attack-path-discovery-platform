
from flask import jsonify
from data.fake_ad_generator import generate_fake_ad
from graph.builder import build_graph
from analysis.pathfinder import find_attack_paths
from analysis.risk_scorer import score_all_paths
from analysis.detections import run_all_detections


def register_routes(app):

    @app.route("/api/health")
    def health():
        return jsonify({"status": "online", "platform": "Attack Path Discovery Platform"})

    @app.route("/api/environment")
    def environment():
        env = generate_fake_ad()
        return jsonify(env.summary())

    @app.route("/api/graph")
    def graph():
        env = generate_fake_ad()
        G = build_graph(env)

        nodes = []
        for node, data in G.nodes(data=True):
            nodes.append({"id": node, **data})

        edges = []
        for u, v, data in G.edges(data=True):
            edges.append({"from": u, "to": v, **data})

        return jsonify({"nodes": nodes, "edges": edges})

    @app.route("/api/paths")
    def paths():
        env = generate_fake_ad()
        G = build_graph(env)
        attack_paths = find_attack_paths(G, target="Domain Admins")
        scored = score_all_paths(attack_paths, G)

        results = []
        for sp in scored:
            results.append({
                "source": sp.path.source,
                "target": sp.path.target,
                "path": sp.path.path,
                "hops": sp.path.length,
                "score": sp.score,
                "risk_level": sp.risk_level,
                "factors": sp.factors,
                "reaches_da": sp.path.reaches_da
            })

        return jsonify({"count": len(results), "paths": results})

    @app.route("/api/detections")
    def detections():
        env = generate_fake_ad()
        G = build_graph(env)
        findings = run_all_detections(G)

        results = []
        for d in findings:
            results.append({
                "technique": d.technique,
                "severity": d.severity,
                "affected_object": d.affected_object,
                "mitre_technique": d.mitre_technique,
                "description": d.description,
                "recommendation": d.recommendation
            })

        return jsonify({"count": len(results), "detections": results})
