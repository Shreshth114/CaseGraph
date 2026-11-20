// Keep the force layout for dense networks. Give small disconnected groups room
// to breathe when isolated entities occupy most of the map.
function prepareMap(nodes, edges) {
  const byId = new Map(nodes.map(node => [node.id, node]));
  const adjacency = new Map(nodes.map(node => [node.id, new Set()]));
  for (const edge of edges) {
    if (edge.decision === "rejected" || edge.source === edge.target) continue;
    adjacency.get(edge.source).add(edge.target);
    adjacency.get(edge.target).add(edge.source);
  }
  const groups = [], isolated = [], visited = new Set();
  for (const node of nodes) {
    if (!adjacency.get(node.id).size) {
      isolated.push(node);
      continue;
    }
    if (visited.has(node.id)) continue;
    const group = [node];
    visited.add(node.id);
    for (const member of group) {
      for (const id of adjacency.get(member.id)) {
        if (visited.has(id)) continue;
        visited.add(id);
        group.push(byId.get(id));
      }
    }
    group.sort((a, b) => b.degree - a.degree || a.label.localeCompare(b.label));
    groups.push(group);
  }
  const positions = new Map();
  if (groups.length >= 2 && groups.length <= 9 && isolated.length >= nodes.length / 3
      && groups.every(group => group.length <= 6)) {
    const columns = Math.ceil(Math.sqrt(groups.length));
    const rows = Math.ceil(groups.length / columns);
    groups.forEach((group, index) => {
      const row = Math.floor(index / columns);
      const rowLength = Math.min(columns, groups.length - row * columns);
      const cx = ((index % columns + .5) / rowLength - .5) * 1.65;
      const cy = ((row + .5) / rows - .5) * 1.48;
      const centerX = group.reduce((sum, n) => sum + n.x, 0) / group.length;
      const centerY = group.reduce((sum, n) => sum + n.y, 0) / group.length;
      const spread = Math.max(.0001, ...group.map(n => Math.hypot(n.x - centerX, n.y - centerY)));
      for (const n of group) {
        positions.set(n.id, { x: cx + (n.x - centerX) / spread * .36 / columns,
          y: cy + (n.y - centerY) / spread * .42 / rows });
      }
    });
    isolated.forEach((n, index) => {
      const angle = 2 * Math.PI * index / isolated.length;
      positions.set(n.id, { x: Math.cos(angle), y: Math.sin(angle) });
    });
  }
  const anchors = new Set(groups.map(group => group[0].id));
  const labels = [...nodes].sort((a, b) => Number(anchors.has(b.id)) - Number(anchors.has(a.id))
    || b.degree - a.degree || a.label.localeCompare(b.label));
  return { positions, labels, anchors };
}
