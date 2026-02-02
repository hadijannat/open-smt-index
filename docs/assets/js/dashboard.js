/**
 * SMT Index Dashboard JavaScript
 * Handles chart rendering, network graph, and interactive table
 */

(function() {
  'use strict';

  // Color palettes
  const statusColors = {
    'Published': '#38ef7d',
    'In Development': '#4facfe',
    'In Review': '#f5576c',
    'Proposal submitted': '#fa709a',
    'unknown': '#9ca3af'
  };

  const sourceColors = {
    'idta': '#155799',
    'github_only': '#24292e',
    'external': '#6b7280'
  };

  // Base URL for GitHub Pages (auto-detect)
  function getBaseUrl() {
    const path = window.location.pathname;
    // If running on GitHub Pages, extract the repo name
    const match = path.match(/^\/([^\/]+)\//);
    return match ? '/' + match[1] : '';
  }

  // Load stats data
  async function loadStats() {
    const baseUrl = getBaseUrl();
    try {
      const response = await fetch(baseUrl + '/data/stats.json');
      if (!response.ok) throw new Error('Failed to load stats');
      return await response.json();
    } catch (error) {
      console.error('Error loading stats:', error);
      return null;
    }
  }

  // Safe DOM element creation helper
  function createElement(tag, attributes, children) {
    const el = document.createElement(tag);
    if (attributes) {
      Object.entries(attributes).forEach(([key, value]) => {
        if (key === 'class') {
          el.className = value;
        } else if (key === 'text') {
          el.textContent = value;
        } else {
          el.setAttribute(key, value);
        }
      });
    }
    if (children) {
      children.forEach(child => {
        if (typeof child === 'string') {
          el.appendChild(document.createTextNode(child));
        } else if (child) {
          el.appendChild(child);
        }
      });
    }
    return el;
  }

  // Render metric cards using safe DOM methods
  function renderMetricCards(stats) {
    const container = document.getElementById('metric-cards');
    if (!container || !stats) return;

    const totals = stats.totals;
    const byStatus = stats.by_status;

    const cards = [
      { value: totals.templates, label: 'Total Templates', cssClass: '' },
      { value: byStatus['Published'] || 0, label: 'Published', cssClass: 'published' },
      { value: byStatus['In Development'] || 0, label: 'In Development', cssClass: 'development' },
      { value: byStatus['In Review'] || 0, label: 'In Review', cssClass: 'review' },
      { value: totals.versions, label: 'Total Versions', cssClass: 'versions' }
    ];

    container.replaceChildren();
    cards.forEach(card => {
      const cardEl = createElement('div', { class: 'metric-card ' + card.cssClass }, [
        createElement('div', { class: 'metric-value', text: String(card.value) }),
        createElement('div', { class: 'metric-label', text: card.label })
      ]);
      container.appendChild(cardEl);
    });
  }

  // Render status distribution chart (doughnut)
  function renderStatusChart(stats) {
    const canvas = document.getElementById('status-chart');
    if (!canvas || !stats) return;

    const ctx = canvas.getContext('2d');
    const byStatus = stats.by_status;
    const labels = Object.keys(byStatus);
    const data = Object.values(byStatus);
    const colors = labels.map(status => statusColors[status] || '#9ca3af');

    new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: colors,
          borderWidth: 2,
          borderColor: '#fff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: {
              padding: 15,
              usePointStyle: true,
              pointStyle: 'circle'
            }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const percentage = ((context.raw / total) * 100).toFixed(1);
                return context.label + ': ' + context.raw + ' (' + percentage + '%)';
              }
            }
          }
        },
        cutout: '60%'
      }
    });
  }

  // Render source distribution chart (bar)
  function renderSourceChart(stats) {
    const canvas = document.getElementById('source-chart');
    if (!canvas || !stats) return;

    const ctx = canvas.getContext('2d');
    const bySource = stats.by_source;

    const labels = ['IDTA Registered', 'GitHub Only', 'External'];
    const keys = ['idta', 'github_only', 'external'];
    const data = keys.map(k => bySource[k] || 0);
    const colors = keys.map(k => sourceColors[k]);

    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Templates',
          data: data,
          backgroundColor: colors,
          borderRadius: 8,
          borderSkipped: false
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const total = data.reduce((a, b) => a + b, 0);
                const percentage = ((context.raw / total) * 100).toFixed(1);
                return context.raw + ' templates (' + percentage + '%)';
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: '#f0f0f0'
            }
          },
          x: {
            grid: {
              display: false
            }
          }
        }
      }
    });
  }

  // Render mini status chart for index page
  function renderMiniStatusChart(stats) {
    const canvas = document.getElementById('mini-status-chart');
    if (!canvas || !stats) return;

    const ctx = canvas.getContext('2d');
    const byStatus = stats.by_status;
    const labels = Object.keys(byStatus);
    const data = Object.values(byStatus);
    const colors = labels.map(status => statusColors[status] || '#9ca3af');

    new Chart(ctx, {
      type: 'pie',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: colors,
          borderWidth: 2,
          borderColor: '#fff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              padding: 10,
              usePointStyle: true,
              pointStyle: 'circle',
              font: { size: 11 }
            }
          }
        }
      }
    });
  }

  // Render quick stats badges for index page using safe DOM methods
  function renderQuickStats(stats) {
    const container = document.getElementById('quick-stats');
    if (!container || !stats) return;

    const byStatus = stats.by_status;
    const badges = [
      { value: stats.totals.templates, label: 'Templates', cssClass: 'total' },
      { value: byStatus['Published'] || 0, label: 'Published', cssClass: 'published' },
      { value: byStatus['In Development'] || 0, label: 'In Dev', cssClass: 'development' },
      { value: byStatus['In Review'] || 0, label: 'In Review', cssClass: 'review' }
    ];

    container.replaceChildren();
    badges.forEach(badge => {
      const span = createElement('span', {
        class: 'stat-badge ' + badge.cssClass,
        text: badge.value + ' ' + badge.label
      });
      container.appendChild(span);
    });
  }

  // Render network graph
  function renderNetworkGraph(stats) {
    const container = document.getElementById('network-graph');
    if (!container || !stats || !stats.families) return;

    // Build nodes and edges from families
    const nodes = [];
    const edges = [];

    // Create family nodes
    const familyNodeMap = {};
    stats.families.forEach((family, idx) => {
      const familyId = 'family-' + idx;
      familyNodeMap[family.name] = familyId;
      nodes.push({
        id: familyId,
        label: family.name,
        group: 'family',
        shape: 'box',
        color: {
          background: '#159957',
          border: '#155799',
          highlight: { background: '#38ef7d', border: '#155799' }
        },
        font: { color: '#fff', bold: true, size: 14 },
        margin: 10
      });
    });

    // Create template nodes and edges
    const templateMap = {};
    stats.templates.forEach(t => {
      templateMap[t.id] = t;
    });

    stats.families.forEach((family, idx) => {
      const familyId = 'family-' + idx;
      family.templates.forEach(templateId => {
        const template = templateMap[templateId];
        if (template) {
          const label = template.name.length > 30
            ? template.name.substring(0, 27) + '...'
            : template.name;
          nodes.push({
            id: templateId,
            label: label,
            title: template.name + '\nStatus: ' + template.status + '\nVersions: ' + template.version_count,
            group: 'template',
            shape: 'ellipse',
            color: {
              background: statusColors[template.status] || '#9ca3af',
              border: '#333',
              highlight: { background: '#fff', border: '#159957' }
            },
            font: { size: 11 }
          });
          edges.push({
            from: familyId,
            to: templateId,
            color: { color: '#ccc', highlight: '#159957' }
          });
        }
      });
    });

    // Create network
    const data = { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) };
    const options = {
      physics: {
        enabled: true,
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {
          gravitationalConstant: -100,
          centralGravity: 0.01,
          springLength: 150,
          springConstant: 0.08
        },
        stabilization: { iterations: 100 }
      },
      interaction: {
        hover: true,
        tooltipDelay: 200
      },
      layout: {
        improvedLayout: true
      }
    };

    new vis.Network(container, data, options);
  }

  // Render interactive table using safe DOM methods
  function renderDataTable(stats) {
    const tbody = document.getElementById('templates-tbody');
    if (!tbody || !stats || !stats.templates) return;

    // Clear existing content
    tbody.replaceChildren();

    // Populate table body using safe DOM methods
    stats.templates.forEach(t => {
      const tr = document.createElement('tr');

      // ID cell
      const tdId = createElement('td', { text: t.id });
      tr.appendChild(tdId);

      // Name cell
      const tdName = createElement('td', { text: t.name });
      tr.appendChild(tdName);

      // Status cell with badge
      const statusClass = t.status.toLowerCase().replace(/\s+/g, '-');
      const tdStatus = document.createElement('td');
      tdStatus.appendChild(createElement('span', {
        class: 'status-badge ' + statusClass,
        text: t.status
      }));
      tr.appendChild(tdStatus);

      // IDTA number cell
      const tdIdta = createElement('td', { text: t.idta_number || '-' });
      tr.appendChild(tdIdta);

      // Version count cell
      const tdVersions = createElement('td', { text: String(t.version_count) });
      tr.appendChild(tdVersions);

      // Latest version cell
      const tdLatest = createElement('td', { text: t.latest_version || '-' });
      tr.appendChild(tdLatest);

      // Links cell
      const tdLinks = document.createElement('td');
      if (t.has_pdf) {
        tdLinks.appendChild(createElement('span', {
          class: 'source-indicator idta',
          text: 'PDF'
        }));
        tdLinks.appendChild(document.createTextNode(' '));
      }
      if (t.has_github) {
        tdLinks.appendChild(createElement('span', {
          class: 'source-indicator github',
          text: 'GitHub'
        }));
      }
      if (!t.has_pdf && !t.has_github) {
        tdLinks.textContent = '-';
      }
      tr.appendChild(tdLinks);

      tbody.appendChild(tr);
    });

    // Initialize DataTables
    if (typeof $ !== 'undefined' && $.fn.DataTable) {
      const table = $('#templates-table').DataTable({
        pageLength: 15,
        lengthMenu: [[10, 15, 25, 50, -1], [10, 15, 25, 50, 'All']],
        order: [[0, 'asc']],
        language: {
          search: 'Search:',
          lengthMenu: 'Show _MENU_ entries',
          info: 'Showing _START_ to _END_ of _TOTAL_ templates',
          paginate: { previous: '\u2190', next: '\u2192' }
        },
        columnDefs: [
          { orderable: false, targets: [6] }
        ]
      });

      // Custom filter buttons
      document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
          document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
          this.classList.add('active');

          const filter = this.dataset.filter;
          if (filter === 'all') {
            table.column(2).search('').draw();
          } else {
            table.column(2).search(filter).draw();
          }
        });
      });
    }
  }

  // Show error message in container using safe DOM methods
  function showError(container, message) {
    container.replaceChildren();
    const p = createElement('p', {
      text: message
    });
    p.style.color = '#dc3545';
    container.appendChild(p);
  }

  // Initialize dashboard
  async function initDashboard() {
    const stats = await loadStats();
    if (!stats) {
      console.error('Could not load stats data');
      document.querySelectorAll('.loading').forEach(el => {
        showError(el, 'Failed to load data. Please try refreshing.');
      });
      return;
    }

    // Render components based on what's on the page
    renderMetricCards(stats);
    renderStatusChart(stats);
    renderSourceChart(stats);
    renderNetworkGraph(stats);
    renderDataTable(stats);

    // Index page components
    renderMiniStatusChart(stats);
    renderQuickStats(stats);
  }

  // Run when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboard);
  } else {
    initDashboard();
  }
})();
