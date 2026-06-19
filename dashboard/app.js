const API = 'http://192.168.1.80:5000/api';

// Color map for node types
const NODE_COLORS = {
    user: '#00d4ff',
    group: '#00ff88',
    computer: '#ff8c00',
    service_account: '#ff3d3d'
};

const NODE_SIZES = {
    user: 10,
    group: 14,
    computer: 12,
    service_account: 13
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
        function renderGraph(graphData) {
    const container = document.getElementById('graph-container');
    const width = 550;
    const height = 700;

    const svg = d3.select('#graph-svg')
        .attr('width', width)
        .attr('height', height);

    svg.selectAll('*').remove();

    svg.append('defs').append('marker')
        .attr('id', 'arrow')
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 22)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', '#1e2d45');

    const g = svg.append('g');

    svg.call(d3.zoom().scaleExtent([0.3, 3]).on('zoom', e => {
        g.attr('transform', e.transform);
    }));

    // Create index map for nodes
    const nodeMap = {};
    const nodes = graphData.nodes.map(n => {
        const node = { ...n };
        nodeMap[n.id] = node;
        return node;
    });

    // Only include edges where both nodes exist
    const edges = graphData.edges
        .filter(e => nodeMap[e.from] && nodeMap[e.to])
        .map(e => ({
            relationship: e.relationship,
            source: e.from,
            target: e.to
        }));

    const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(edges)
            .id(d => d.id)
            .distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide(30));

    const link = g.append('g').selectAll('line')
        .data(edges)
        .join('line')
        .attr('stroke', '#1e2d45')
        .attr('stroke-width', 1.5)
        .attr('marker-end', 'url(#arrow)');

    const edgeLabel = g.append('g').selectAll('text')
        .data(edges)
        .join('text')
        .attr('font-size', 7)
        .attr('fill', '#374151')
        .attr('text-anchor', 'middle')
        .text(d => d.relationship);

    const node = g.append('g').selectAll('g')
        .data(nodes)
        .join('g')
        .call(d3.drag()
            .on('start', (e, d) => { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
            .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y; })
            .on('end', (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }));

    node.append('circle')
        .attr('r', d => NODE_SIZES[d.type] || 10)
        .attr('fill', d => NODE_COLORS[d.type] || '#64748b')
        .attr('fill-opacity', 0.15)
        .attr('stroke', d => NODE_COLORS[d.type] || '#64748b')
        .attr('stroke-width', 2);

    node.append('text')
        .attr('dy', d => (NODE_SIZES[d.type] || 10) + 12)
        .attr('text-anchor', 'middle')
        .attr('font-size', 9)
        .attr('fill', '#64748b')
        .text(d => d.id);

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
}

        renderPaths(paths);
        renderDetections(detections);

        document.getElementById('domain-name').textContent = env.domain;

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
    const width = 550;
    const height = 700;

    const svg = d3.select('#graph-svg')
        .attr('width', width)
        .attr('height', height);

    svg.selectAll('*').remove();

    const g = svg.append('g');

    svg.call(d3.zoom().scaleExtent([0.3, 3]).on('zoom', e => {
        g.attr('transform', e.transform);
    }));

    // Build nodes array
    const nodes = graphData.nodes.map(n => ({ ...n }));

    // Build index lookup
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

    const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(edges).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide(30));

    const link = g.append('g').selectAll('line')
        .data(edges)
        .join('line')
        .attr('stroke', '#1e2d45')
        .attr('stroke-width', 1.5);

    const edgeLabel = g.append('g').selectAll('text')
        .data(edges)
        .join('text')
        .attr('font-size', 7)
        .attr('fill', '#374151')
        .attr('text-anchor', 'middle')
        .text(d => d.relationship);

    const node = g.append('g').selectAll('g')
        .data(nodes)
        .join('g')
        .call(d3.drag()
            .on('start', (e, d) => { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
            .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y; })
            .on('end', (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }));

    node.append('circle')
        .attr('r', d => NODE_SIZES[d.type] || 10)
        .attr('fill', d => NODE_COLORS[d.type] || '#64748b')
        .attr('fill-opacity', 0.15)
        .attr('stroke', d => NODE_COLORS[d.type] || '#64748b')
        .attr('stroke-width', 2);

    node.append('text')
        .attr('dy', d => (NODE_SIZES[d.type] || 10) + 12)
        .attr('text-anchor', 'middle')
        .attr('font-size', 9)
        .attr('fill', '#64748b')
        .text(d => d.id);

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
        const shortDesc = d.description.length > 100
            ? d.description.substring(0, 100) + '...'
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

// Load on start

// Wait for layout before rendering graph
window.addEventListener('load', () => {
    setTimeout(fetchAll, 500);
});