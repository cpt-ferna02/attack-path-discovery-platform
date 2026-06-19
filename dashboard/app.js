const API = 'http://192.168.1.80:5000/api';

const NODE_COLORS = {
    user: '#00d4ff',
    group: '#00ff88',
    computer: '#ff8c00',
    service_account: '#ff3d3d'
};

const NODE_SIZES = {
    user: 12,
    group: 16,
    computer: 14,
    service_account: 15
};

async function fetchAll() {
    try {
        const [env, graph, paths, detections] = await Promise.all([
            fetch(`${API}/environment`).then(r => r.json()),
            fetch(`${API}/graph`).then(r => r.json()),
            fetch(`${API}/paths`).then(r => r.json()),
            fetch(`${API}/detections`).then(r => r.json())
        ]);

        updateStats(env, graph, paths, detections);
        renderPaths(paths);
        renderDetections(detections);

        document.getElementById('domain-name').textContent = env.domain;

        // Delay graph render to ensure DOM is fully laid out
        setTimeout(() => renderGraph(graph), 300);

    } catch (err) {
        console.error('API error:', err);
        document.getElementById('domain-name').textContent = 'API Offline';
    }
}

function updateStats(env, graph, paths, detections) {
    document.getElementById('stat-paths').textContent = paths.count;
    document.getElementById('stat-detections').textContent = detections.count;
    document.getElementById('stat-nodes').textContent = graph.nodes.length;
    document.getElementById('stat-edges').textContent = graph.edges.length;
    document.getElementById('stat-users').textContent = env.users;
    document.getElementById('stat-groups').textContent = env.groups;
    document.getElementById('paths-badge').textContent = `${paths.count} CRITICAL`;
    document.getElementById('detections-badge').textContent = detections.count;
}

function renderGraph(graphData) {
    try {
        const container = document.getElementById('graph-container');
        const width = container.clientWidth || 800;
        const height = container.clientHeight || 600;

        console.log('Rendering graph — container:', width, 'x', height);
        console.log('Nodes:', graphData.nodes.length, 'Edges:', graphData.edges.length);

        const svg = d3.select('#graph-svg')
            .attr('width', width)
            .attr('height', height)
            .attr('viewBox', `0 0 ${width} ${height}`);

        svg.selectAll('*').remove();

        // Arrow marker
        svg.append('defs').append('marker')
            .attr('id', 'arrow')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 25)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', '#2e4060');

        const g = svg.append('g');

        svg.call(d3.zoom()
            .scaleExtent([0.2, 4])
            .on('zoom', e => g.attr('transform', e.transform))
        );

        // Build nodes
        const nodes = graphData.nodes.map(n => ({ ...n }));

        // Build index map
        const idToIndex = {};
        nodes.forEach((n, i) => { idToIndex[n.id] = i; });

        // Build edges using numeric indices
        const edges = [];
        graphData.edges.forEach(e => {
            const si = idToIndex[e.from];
            const ti = idToIndex[e.to];
            if (si !== undefined && ti !== undefined) {
                edges.push({
                    source: si,
                    target: ti,
                    relationship: e.relationship
                });
            }
        });

        console.log('Valid edges built:', edges.length);

        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(edges).distance(120))
            .force('charge', d3.forceManyBody().strength(-400))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide(35));

        // Draw edges
        const link = g.append('g')
            .selectAll('line')
            .data(edges)
            .join('line')
            .attr('stroke', '#2e4060')
            .attr('stroke-width', 1.5)
            .attr('marker-end', 'url(#arrow)');

        // Edge labels
        const edgeLabel = g.append('g')
            .selectAll('text')
            .data(edges)
            .join('text')
            .attr('font-size', 8)
            .attr('fill', '#3a5070')
            .attr('text-anchor', 'middle')
            .text(d => d.relationship);

        // Draw nodes
        const node = g.append('g')
            .selectAll('g')
            .data(nodes)
            .join('g')
            .call(d3.drag()
                .on('start', (e, d) => {
                    if (!e.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x; d.fy = d.y;
                })
                .on('drag', (e, d) => {
                    d.fx = e.x; d.fy = e.y;
                })
                .on('end', (e, d) => {
                    if (!e.active) simulation.alphaTarget(0);
                    d.fx = null; d.fy = null;
                })
            );

        // Node glow effect
        node.append('circle')
            .attr('r', d => (NODE_SIZES[d.type] || 12) + 4)
            .attr('fill', d => NODE_COLORS[d.type] || '#64748b')
            .attr('fill-opacity', 0.08)
            .attr('stroke', 'none');

        // Node circle
        node.append('circle')
            .attr('r', d => NODE_SIZES[d.type] || 12)
            .attr('fill', d => NODE_COLORS[d.type] || '#64748b')
            .attr('fill-opacity', 0.2)
            .attr('stroke', d => NODE_COLORS[d.type] || '#64748b')
            .attr('stroke-width', 2);

        // Node label
        node.append('text')
            .attr('dy', d => (NODE_SIZES[d.type] || 12) + 14)
            .attr('text-anchor', 'middle')
            .attr('font-size', 10)
            .attr('font-family', 'Courier New, monospace')
            .attr('fill', '#8899aa')
            .text(d => d.id);

        // Tooltip on hover
        node.append('title')
            .text(d => `${d.id}\nType: ${d.type}`);

        simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            edgeLabel
                .attr('x', d => (d.source.x + d.target.x) / 2)
                .attr('y', d => (d.source.y + d.target.y) / 2);

            node.attr('transform', d => `translate(${d.x},${d.y})`);
        });

        console.log('Graph render complete');

    } catch (err) {
        console.error('Graph render error:', err);
    }
}

function renderPaths(data) {
    const container = document.getElementById('paths-list');
    container.innerHTML = '';

    data.paths.forEach(p => {
        const card = document.createElement('div');
        card.className = 'path-card';

        const hopsHtml = p.path.map((node, i) => {
            const isLast = i === p.path.length - 1;
            const nodeHtml = `<span class="hop-node ${isLast ? 'domain-admin' : ''}">${node}</span>`;
            return i < p.path.length - 1
                ? nodeHtml + `<span class="hop-arrow">→</span>`
                : nodeHtml;
        }).join('');

        const topFactors = p.factors.slice(0, 3).join(' · ');

        card.innerHTML = `
            <div class="path-header">
                <span class="path-source">${p.source}</span>
                <span class="path-score">${p.score}/100</span>
            </div>
            <div class="path-hops">${hopsHtml}</div>
            <div class="path-factors">${topFactors}</div>
        `;
        container.appendChild(card);
    });
}

function renderDetections(data) {
    const container = document.getElementById('detections-list');
    container.innerHTML = '';

    data.detections.forEach(d => {
        const card = document.createElement('div');
        card.className = 'detection-card';
        const shortDesc = d.description.length > 120
            ? d.description.substring(0, 120) + '...'
            : d.description;

        card.innerHTML = `
            <div class="detection-header">
                <div>
                    <span class="detection-technique">${d.technique}</span>
                    <span class="detection-mitre"> · ${d.mitre_technique}</span>
                </div>
                <span class="severity-badge severity-${d.severity}">${d.severity}</span>
            </div>
            <div class="detection-object">${d.affected_object}</div>
            <div class="detection-desc">${shortDesc}</div>
        `;
        container.appendChild(card);
    });
}

// Auto-load on page ready
window.addEventListener('load', () => {
    setTimeout(fetchAll, 500);
});
