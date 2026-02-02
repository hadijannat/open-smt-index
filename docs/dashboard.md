---
layout: default
title: Dashboard
---

# SMT Index Dashboard

<div class="dashboard-intro">
<p>Interactive visualizations of the AAS Submodel Template index. Explore template status distribution, source breakdown, and family relationships.</p>
</div>

---

## Key Metrics

<div id="metric-cards" class="metric-cards">
  <div class="loading">Loading metrics...</div>
</div>

---

## Status Distribution

<div class="chart-row">
  <div class="chart-container">
    <h3 class="chart-title">Templates by Status</h3>
    <div class="chart-wrapper">
      <canvas id="status-chart"></canvas>
    </div>
  </div>

  <div class="chart-container">
    <h3 class="chart-title">Templates by Source</h3>
    <div class="chart-wrapper">
      <canvas id="source-chart"></canvas>
    </div>
  </div>
</div>

---

## Template Families

<div class="network-container">
  <h3 class="chart-title">Template Family Network</h3>
  <p style="font-size: 0.9rem; color: #666; margin-bottom: 1rem;">
    Templates grouped by family (e.g., Digital Battery Passport, Technical Data).
    Hover over nodes for details. Drag to rearrange.
  </p>
  <div id="network-graph" class="network-wrapper"></div>
</div>

---

## All Templates

<div class="table-container">
  <h3 class="chart-title">Template Index</h3>

  <div class="filter-buttons">
    <button class="filter-btn active" data-filter="all">All</button>
    <button class="filter-btn" data-filter="Published">Published</button>
    <button class="filter-btn" data-filter="In Development">In Development</button>
    <button class="filter-btn" data-filter="In Review">In Review</button>
    <button class="filter-btn" data-filter="Proposal">Proposal</button>
  </div>

  <table id="templates-table" class="display" style="width:100%">
    <thead>
      <tr>
        <th>ID</th>
        <th>Name</th>
        <th>Status</th>
        <th>IDTA #</th>
        <th>Versions</th>
        <th>Latest</th>
        <th>Links</th>
      </tr>
    </thead>
    <tbody id="templates-tbody">
      <tr><td colspan="7" class="loading">Loading templates...</td></tr>
    </tbody>
  </table>
</div>

---

## Data Sources

| Source | Description |
|--------|-------------|
| **IDTA Content Hub** | Official registry with status, descriptions, and PDF specifications |
| **GitHub Repository** | Version folders and AASX files from admin-shell-io/submodel-templates |
| **External** | Additional templates from external contributions |

---

[View Raw Data](https://github.com/hadijannat/open-smt-index/tree/main/dist) | [API Documentation](api-reference.md)
