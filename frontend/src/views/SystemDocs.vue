<template>
  <div class="dashboard-page animate-in system-docs-page">
    <!-- Hero / Title Header Banner matching SuperDashboard & Overview design language -->
    <section class="hero-section" aria-label="System Documentation Header">
      <div class="hero-content">
        <div class="super-kicker-pill">
          <span class="kicker-tag">Restricted • Super Admin</span>
          <span class="kicker-divider">•</span>
          <span class="kicker-status live-on">
            <span class="pulse-indicator"></span>
            System Specifications &amp; Architecture Portal
          </span>
          <span class="kicker-divider">•</span>
          <span class="kicker-badge-green">Reconstruct v2.29 Pass</span>
        </div>

        <h1 class="hero-title">System Architecture &amp; Specifications</h1>
        <p class="hero-subtitle">
          Interactive implementation-ready specifications, live database entity dictionary, REST API contracts, UI design tokens, and modular feature PRDs.
        </p>

        <!-- Metric Highlights Strip -->
        <div class="specs-metrics-strip" v-if="docsData">
          <div class="metric-pill">
            <span class="mp-val">{{ docsData.metrics?.total_files || 236 }}</span>
            <span class="mp-lbl">Source Files</span>
          </div>
          <div class="metric-pill">
            <span class="mp-val">{{ formatNumber(docsData.metrics?.total_lines || 62498) }}</span>
            <span class="mp-lbl">Lines of Code</span>
          </div>
          <div class="metric-pill">
            <span class="mp-val">{{ docsData.interfaces?.length || 33 }}</span>
            <span class="mp-lbl">API Operations</span>
          </div>
          <div class="metric-pill">
            <span class="mp-val">{{ Object.keys(docsData.data_model?.entities || {}).length || 19 }}</span>
            <span class="mp-lbl">Database Tables</span>
          </div>
          <div class="metric-pill">
            <span class="mp-val">{{ docsData.features?.length || 13 }}</span>
            <span class="mp-lbl">Feature PRDs</span>
          </div>
          <div class="metric-pill">
            <span class="mp-val">{{ docsData.diagrams?.length || 9 }}</span>
            <span class="mp-lbl">Architecture Diagrams</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Top Navigation Sub-Tabs -->
    <div class="docs-nav-bar">
      <div class="docs-nav-tabs" role="tablist">
        <button
          v-for="tab in availableTabs"
          :key="tab.id"
          type="button"
          class="doc-tab-btn"
          :class="{ active: currentTab === tab.id }"
          @click="currentTab = tab.id"
          role="tab"
          :aria-selected="currentTab === tab.id"
        >
          <span class="tab-icon" v-html="tab.icon"></span>
          <span class="tab-label">{{ tab.label }}</span>
          <span v-if="tab.badge" class="tab-count-badge">{{ tab.badge }}</span>
        </button>
      </div>

      <div class="docs-nav-actions">
        <button type="button" class="btn btn-outline btn-sm" @click="fetchDocs(true)" :disabled="loading">
          <svg class="refresh-spinner" :class="{ spinning: loading }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
            <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
          </svg>
          <span>{{ loading ? 'Loading…' : 'Reload Specs' }}</span>
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && !docsData" class="loading-state-card card">
      <div class="loading-spinner"></div>
      <p class="loading-text">Loading and parsing system specifications from <code>docs/</code>…</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="alert-banner-error">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      <div class="alert-text">
        <strong>Unable to load documentation:</strong> {{ error }}
      </div>
      <button class="btn-retry-engine" @click="fetchDocs(true)">Retry</button>
    </div>

    <!-- MAIN VIEW CONTAINER -->
    <main v-if="docsData" class="docs-main-container">

      <!-- =================================================================== -->
      <!-- TAB 1: SYSTEM OVERVIEW & PRD -->
      <!-- =================================================================== -->
      <section v-if="currentTab === 'overview'" class="tab-section animate-in">
        <div class="card overview-card">
          <div class="overview-header-row">
            <div>
              <span class="section-tag-kicker">EXECUTIVE SUMMARY</span>
              <h2 class="overview-main-title">Neuro-Inclusive Workplace Index (NIWI)</h2>
            </div>
            <span class="build-tier-badge">Enterprise v3.1 Spec</span>
          </div>

          <p class="overview-body-quote">
            "{{ docsData.overview?.product_summary || 'NIWI is an enterprise assessment, benchmarking, and organizational intelligence platform engineered by Orchvate. NIWI enables enterprises to evaluate, score, and systematically enhance workplace inclusion for neurodivergent professionals.' }}"
          </p>

          <div class="pillars-showcase">
            <h3 class="subsection-title">The 8 Core Inclusion Dimensions (0–20 Scale)</h3>
            <div class="pillars-grid">
              <div v-for="(pillar, idx) in pillarsList" :key="idx" class="pillar-card">
                <div class="pillar-num">{{ idx + 1 }}</div>
                <div class="pillar-details">
                  <div class="pillar-name">{{ pillar.name }}</div>
                  <div class="pillar-desc">{{ pillar.desc }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Progression Tiers -->
          <div class="tiers-showcase">
            <h3 class="subsection-title">5-Level Progression Maturity Framework</h3>
            <div class="tiers-grid">
              <div v-for="tier in maturityTiers" :key="tier.name" class="tier-card" :class="'tier-' + tier.color">
                <div class="tier-top">
                  <span class="tier-name">{{ tier.name }}</span>
                  <span class="tier-range">{{ tier.range }}</span>
                </div>
                <p class="tier-desc">{{ tier.description }}</p>
                <div class="tier-bar">
                  <div class="tier-bar-fill" :style="{ width: tier.pct + '%' }"></div>
                </div>
              </div>
            </div>
          </div>

          <!-- Personas & Architecture Foundations -->
          <div class="personas-grid">
            <div class="card inner-card">
              <h3 class="inner-card-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                Target User Personas
              </h3>
              <ul class="clean-bullet-list">
                <li><strong>Public Survey Respondents:</strong> Complete 44-question confidential audits; receive instant reflection feedback with zero deanonymization risk.</li>
                <li><strong>Organization HR &amp; DEI Leaders:</strong> Manage departmental invitation tokens, monitor response quotas, and analyze inclusion radar profiles.</li>
                <li><strong>Orchvate Super Administrators:</strong> Oversee multi-tenant directory, replay dead-lettered queues, manage rate limit thresholds, and inspect telemetry.</li>
                <li><strong>DevOps &amp; Infrastructure Engineers:</strong> Monitor connection pool metrics, supervisord processes, and Azure cloud resources.</li>
              </ul>
            </div>

            <div class="card inner-card">
              <h3 class="inner-card-title">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
                Core Architecture Pillars
              </h3>
              <ul class="clean-bullet-list">
                <li><strong>Sub-25ms Ingestion:</strong> Synchronous <code>POST /api/submit</code> acknowledges with HTTP 202; persists into transactional outbox.</li>
                <li><strong>Decoupled Concurrency:</strong> Background daemon polls outbox using <code>SELECT FOR UPDATE SKIP LOCKED</code>.</li>
                <li><strong>Enterprise Identity:</strong> Microsoft Entra ID (Azure AD) OAuth2 OIDC with RS256 JWKS validation and 1h memory cache.</li>
                <li><strong>Secrets Hygiene:</strong> Azure Key Vault integration via System-Assigned Managed Identity (zero hard-coded credentials).</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <!-- =================================================================== -->
      <!-- TAB 2: ARCHITECTURE & TOPOLOGY -->
      <!-- =================================================================== -->
      <section v-if="currentTab === 'architecture'" class="tab-section animate-in">
        <div class="card topo-overview-card">
          <div class="results-header-bar sub-header-bar">
            <div>
              <span class="section-tag-kicker">INFRASTRUCTURE ARCHITECTURE</span>
              <h2 class="results-title">End-to-End System Topologies</h2>
            </div>
          </div>

          <!-- 5-Tier Architecture Layers -->
          <div class="arch-layers-stack">
            <div class="arch-layer-item">
              <div class="ali-header">
                <span class="ali-badge">LAYER 1: CLIENTS &amp; INGRESS</span>
                <span class="ali-sub">Desktop / Mobile Browsers &amp; Nginx Reverse Proxy</span>
              </div>
              <p class="ali-text">
                Respondents access Vue 3 SPA via HTTPS (Port 443) terminated by host Nginx with automated Let's Encrypt TLS. Requests to <code>/api/*</code> proxy internally to port 8000; all static routes serve pre-compiled Vue bundles with client-side history routing.
              </p>
            </div>

            <div class="arch-layer-item">
              <div class="ali-header">
                <span class="ali-badge">LAYER 2: APPLICATION RUNTIME</span>
                <span class="ali-sub">FastAPI Engine &amp; Uvicorn (127.0.0.1:8000)</span>
              </div>
              <p class="ali-text">
                FastAPI handles routing with Pydantic serialization, SlowAPI IP-based rate limiting, and <code>jwks_middleware</code> bearer token validation. Connections to PostgreSQL are multiplexed via a <code>ThreadedConnectionPool</code> (5–25 pooled connections, 15s statement timeout).
              </p>
            </div>

            <div class="arch-layer-item">
              <div class="ali-header">
                <span class="ali-badge">LAYER 3: TRANSACTIONAL OUTBOX</span>
                <span class="ali-sub">PostgreSQL Durable Staging Queue</span>
              </div>
              <p class="ali-text">
                Survey submissions write atomically into <code>raw_submissions</code> and <code>service_bus_outbox</code> within a single ACID transaction. The respondent receives <code>HTTP 202 Accepted</code> in &lt;25ms while message stays staged for asynchronous worker consumption.
              </p>
            </div>

            <div class="arch-layer-item">
              <div class="ali-header">
                <span class="ali-badge">LAYER 4: BACKGROUND FLEET</span>
                <span class="ali-sub">Outbox Dispatcher &amp; Service Bus Workers</span>
              </div>
              <p class="ali-text">
                The <code>outbox_dispatcher</code> polls staged records every 5 seconds using <code>SELECT ... FOR UPDATE SKIP LOCKED</code>, ensuring multi-replica safety. The <code>service_bus_worker</code> deterministically calculates 8 pillar scores (0–160 total), stores results in <code>submissions</code>, and dispatches HTML scorecards.
              </p>
            </div>

            <div class="arch-layer-item">
              <div class="ali-header">
                <span class="ali-badge">LAYER 5: CLUSTER SERVICES</span>
                <span class="ali-sub">Azure Key Vault, Entra ID &amp; Communication Services</span>
              </div>
              <p class="ali-text">
                Database passwords and tokens are acquired at container boot from Azure Key Vault (<code>kv-niwi-prod</code>) via Managed Identity. Outgoing audit report emails are routed via Azure Communication Services (<code>donotreply@orchvate.in</code>).
              </p>
            </div>
          </div>

          <!-- External Services Cards -->
          <div class="external-services-grid" v-if="docsData.architecture?.external_services?.length">
            <h3 class="subsection-title">External Integrations &amp; Failure Contracts</h3>
            <div class="ext-grid">
              <div v-for="(svc, idx) in docsData.architecture.external_services" :key="idx" class="card ext-card">
                <div class="ext-card-header">
                  <span class="ext-icon-pill">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                  </span>
                  <h4 class="ext-name">{{ svc.name }}</h4>
                </div>
                <div class="ext-desc" v-html="formatMarkdownToHtml(svc.description)"></div>
              </div>
            </div>
          </div>

          <!-- Cross-cutting policies -->
          <div class="policies-grid" v-if="docsData.architecture?.policies?.length">
            <h3 class="subsection-title">Cross-Cutting Security &amp; Rate Limit Policies</h3>
            <div class="ext-grid">
              <div v-for="(pol, idx) in docsData.architecture.policies" :key="idx" class="card ext-card">
                <div class="ext-card-header">
                  <span class="ext-icon-pill icon-pill-blue">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                  </span>
                  <h4 class="ext-name">{{ pol.name }}</h4>
                </div>
                <div class="ext-desc" v-html="formatMarkdownToHtml(pol.description)"></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- =================================================================== -->
      <!-- TAB 3: MERMAID DIAGRAMS GALLERY -->
      <!-- =================================================================== -->
      <section v-if="currentTab === 'diagrams'" class="tab-section animate-in">
        <div class="card diagram-gallery-card">
          <div class="diagram-selector-bar">
            <div class="dsb-left">
              <span class="section-tag-kicker">INTERACTIVE ARCHITECTURE VISUALIZATIONS</span>
              <h2 class="results-title">9 Verified Mermaid Diagrams</h2>
            </div>

            <!-- Selector Pills -->
            <div class="diag-pills-wrap">
              <button
                v-for="(diag, idx) in docsData.diagrams"
                :key="diag.id"
                type="button"
                class="diag-pill-btn"
                :class="{ active: selectedDiagramIdx === idx }"
                @click="selectDiagram(idx)"
              >
                {{ idx + 1 }}. {{ getCleanDiagramTitle(diag.title) }}
              </button>
            </div>
          </div>

          <!-- Active Diagram Viewer -->
          <div v-if="activeDiagram" class="active-diagram-container">
            <div class="diagram-header-strip">
              <div>
                <h3 class="diag-display-title">{{ activeDiagram.title }}</h3>
                <span class="diag-type-badge">Mermaid &amp; SVG Specification</span>
              </div>

              <div class="diag-view-controls">
                <!-- Zoom Controls -->
                <div class="zoom-controls" v-if="diagViewMode === 'rendered'">
                  <button type="button" class="btn-zoom" @click="zoomLevel = Math.max(0.6, zoomLevel - 0.15)" title="Zoom Out">−</button>
                  <span class="zoom-val">{{ Math.round(zoomLevel * 100) }}%</span>
                  <button type="button" class="btn-zoom" @click="zoomLevel = Math.min(2.5, zoomLevel + 0.15)" title="Zoom In">+</button>
                  <button type="button" class="btn-zoom-reset" @click="zoomLevel = 1.0" title="Reset Zoom">Reset</button>
                </div>

                <button
                  type="button"
                  class="btn btn-sm"
                  :class="diagViewMode === 'rendered' ? 'btn-primary' : 'btn-outline'"
                  @click="diagViewMode = 'rendered'"
                >
                  Visual Flow
                </button>
                <button
                  type="button"
                  class="btn btn-sm"
                  :class="diagViewMode === 'code' ? 'btn-primary' : 'btn-outline'"
                  @click="diagViewMode = 'code'"
                >
                  Source Code
                </button>
                <button type="button" class="btn btn-outline btn-sm" @click="copyCode(activeDiagram.code)">
                  {{ copyStatus === activeDiagram.id ? 'Copied ✓' : 'Copy Mermaid' }}
                </button>
              </div>
            </div>

            <!-- Visual Flow Renderer -->
            <div v-show="diagViewMode === 'rendered'" class="diagram-render-box">
              <div v-if="activeDiagram.svg" class="mermaid-svg-target" :style="{ transform: `scale(${zoomLevel})`, transformOrigin: 'top center', transition: 'transform 0.15s ease' }" v-html="activeDiagram.svg"></div>
              <div v-else ref="mermaidSvgContainer" class="mermaid-svg-target" :style="{ transform: `scale(${zoomLevel})`, transformOrigin: 'top center', transition: 'transform 0.15s ease' }"></div>
            </div>

            <!-- Code Mode -->
            <div v-show="diagViewMode === 'code'" class="diagram-code-box">
              <pre class="code-pre"><code>{{ activeDiagram.code }}</code></pre>
            </div>
          </div>
        </div>
      </section>

      <!-- =================================================================== -->
      <!-- TAB 4: API INTERFACES EXPLORER -->
      <!-- =================================================================== -->
      <section v-if="currentTab === 'interfaces'" class="tab-section animate-in">
        <div class="card table-card-wrap">
          <div class="table-top-bar">
            <div>
              <span class="section-tag-kicker">API CONTRACT CATALOG</span>
              <h2 class="results-title">Resolved Interface Operations</h2>
              <p class="table-subtext">33 production operations spanning public surveys, administrative management, and background queues.</p>
            </div>

            <!-- Search & Filters -->
            <div class="api-filter-controls">
              <div class="search-input-group api-search">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <input v-model="apiSearch" type="text" placeholder="Filter by endpoint path, method, or handler…" />
              </div>

              <div class="method-filter-pills">
                <button
                  type="button"
                  class="mf-pill"
                  :class="{ active: apiMethodFilter === '' }"
                  @click="apiMethodFilter = ''"
                >
                  All ({{ docsData.interfaces?.length || 0 }})
                </button>
                <button
                  v-for="m in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']"
                  :key="m"
                  type="button"
                  class="mf-pill"
                  :class="['mf-' + m.toLowerCase(), { active: apiMethodFilter === m }]"
                  @click="apiMethodFilter = m"
                >
                  {{ m }}
                </button>
              </div>
            </div>
          </div>

          <!-- Table -->
          <div class="table-scroll-container">
            <table class="engine-table">
              <thead>
                <tr>
                  <th style="width: 90px;">Method</th>
                  <th style="width: 280px;">Path / Operation</th>
                  <th style="width: 130px;">Kind</th>
                  <th style="width: 140px;">Authorization</th>
                  <th>Handler &amp; Side Effects</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, idx) in filteredInterfaces" :key="idx" class="api-row">
                  <td>
                    <span :class="['method-tag', 'method-' + row.method.toLowerCase()]">
                      {{ row.method }}
                    </span>
                  </td>
                  <td>
                    <code class="endpoint-code">{{ row.path }}</code>
                  </td>
                  <td>
                    <span class="kind-badge">{{ row.kind }}</span>
                  </td>
                  <td>
                    <span class="auth-badge" :class="getAuthBadgeClass(row.auth)">
                      {{ row.auth || 'None (Public)' }}
                    </span>
                  </td>
                  <td>
                    <div class="handler-text">{{ row.handler }}</div>
                    <div class="notes-text" v-if="row.notes">{{ row.notes }}</div>
                  </td>
                </tr>
                <tr v-if="filteredInterfaces.length === 0">
                  <td colspan="5" class="engine-empty-table">
                    No matching API operations found for "{{ apiSearch }}"
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- =================================================================== -->
      <!-- TAB 5: DATABASE SCHEMA & DATA MODEL -->
      <!-- =================================================================== -->
      <section v-if="currentTab === 'datamodel'" class="tab-section animate-in">
        <div class="data-model-layout">
          <!-- Left: Table Selection Sidebar -->
          <div class="card dm-sidebar">
            <div class="dms-header">
              <h3 class="dms-title">Database Tables</h3>
              <span class="results-count-pill">{{ Object.keys(docsData.data_model?.entities || {}).length }}</span>
            </div>

            <div class="dms-search-wrap">
              <input v-model="tableSearch" type="text" placeholder="Search tables…" class="dms-search" />
            </div>

            <div class="dms-list">
              <button
                v-for="tbl in filteredTables"
                :key="tbl"
                type="button"
                class="dms-table-btn"
                :class="{ active: selectedTable === tbl }"
                @click="selectedTable = tbl"
              >
                <span class="tbl-icon">▦</span>
                <span class="tbl-name">{{ tbl }}</span>
                <span class="tbl-col-count">{{ docsData.data_model?.entities[tbl]?.length }} cols</span>
              </button>
            </div>

            <!-- Enums Quick Anchor -->
            <div class="dms-enum-anchor">
              <button
                type="button"
                class="dms-table-btn enum-special-btn"
                :class="{ active: selectedTable === '__enums__' }"
                @click="selectedTable = '__enums__'"
              >
                <span class="tbl-icon">✦</span>
                <span class="tbl-name">Enums &amp; Fixed Types</span>
                <span class="tbl-col-count">{{ docsData.data_model?.enums?.length || 0 }} sets</span>
              </button>
            </div>
          </div>

          <!-- Right: Selected Table Details / Enums -->
          <div class="card dm-details-card">
            <!-- Table Columns View -->
            <div v-if="selectedTable !== '__enums__' && activeTableColumns.length">
              <div class="table-detail-header">
                <div>
                  <span class="section-tag-kicker">RELATIONAL ENTITY DEFINITION</span>
                  <h2 class="tdh-title"><code>{{ selectedTable }}</code></h2>
                </div>
                <div class="tdh-stats">
                  <span class="stat-pill">{{ activeTableColumns.length }} Columns</span>
                  <span class="stat-pill stat-pill-green">Catalog: nd_audit</span>
                </div>
              </div>

              <div class="table-scroll-container">
                <table class="engine-table">
                  <thead>
                    <tr>
                      <th style="width: 200px;">Column Name</th>
                      <th style="width: 140px;">Type</th>
                      <th>Constraints</th>
                      <th>Relation / Foreign Key</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="col in activeTableColumns" :key="col.field">
                      <td>
                        <div class="col-name-wrap">
                          <code class="col-name">{{ col.field }}</code>
                          <span v-if="col.constraints.includes('PRIMARY KEY')" class="pk-tag">PK</span>
                          <span v-else-if="col.constraints.includes('FOREIGN KEY') || col.constraints.includes('REFERENCES')" class="fk-tag">FK</span>
                          <span v-else-if="col.constraints.includes('UNIQUE')" class="uk-tag">UK</span>
                        </div>
                      </td>
                      <td>
                        <span class="type-tag">{{ col.type }}</span>
                      </td>
                      <td>
                        <span class="constraints-text">{{ col.constraints }}</span>
                      </td>
                      <td>
                        <span class="relation-text">{{ col.relation || '—' }}</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Enums View -->
            <div v-else-if="selectedTable === '__enums__'" class="enums-panel">
              <div class="table-detail-header">
                <div>
                  <span class="section-tag-kicker">DOMAIN VALUE SETS</span>
                  <h2 class="tdh-title">Enums &amp; Fixed Domains</h2>
                  <p class="table-subtext">Comprehensive enumerated types and status state-machines governing platform workflows.</p>
                </div>
              </div>

              <div class="enums-grid">
                <div v-for="en in docsData.data_model?.enums" :key="en.name" class="card enum-card">
                  <div class="enum-header">
                    <h3 class="enum-name"><code>{{ en.name }}</code></h3>
                    <span class="enum-desc">{{ en.description }}</span>
                  </div>
                  <div class="enum-values-list">
                    <span v-for="(v, i) in en.items" :key="i" class="enum-item-pill">
                      {{ v }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- =================================================================== -->
      <!-- TAB 6: DESIGN SYSTEM TOKENS -->
      <!-- =================================================================== -->
      <section v-if="currentTab === 'design'" class="tab-section animate-in">
        <div class="card design-system-card">
          <div class="results-header-bar sub-header-bar">
            <div>
              <span class="section-tag-kicker">VISUAL DESIGN TOKENS</span>
              <h2 class="results-title">NIWI Unified Enterprise Palette</h2>
              <p class="table-subtext">Exact CSS variables, hex/rgba values, and WCAG 2.1 AA accessibility contracts.</p>
            </div>
          </div>

          <!-- Color Swatches Grid -->
          <div class="colors-showcase">
            <h3 class="subsection-title">Core Colors (Click to Copy Hex)</h3>
            <div class="colors-grid">
              <div
                v-for="c in colorPaletteList"
                :key="c.name"
                class="swatch-card"
                @click="copyCode(c.hex)"
                title="Click to copy color value"
              >
                <div class="swatch-preview" :style="{ backgroundColor: c.hex || '#161057' }">
                  <span class="swatch-copy-hint">{{ copyStatus === c.hex ? 'Copied!' : 'Copy' }}</span>
                </div>
                <div class="swatch-info">
                  <div class="swatch-name">{{ c.name }}</div>
                  <div class="swatch-meta">
                    <code class="swatch-hex">{{ c.hex }}</code>
                    <span class="swatch-var">{{ c.var }}</span>
                  </div>
                  <div class="swatch-purpose">{{ c.purpose }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Typography Tokens -->
          <div class="type-showcase">
            <h3 class="subsection-title">Typography Stack</h3>
            <div class="type-grid">
              <div class="card type-card">
                <span class="type-role">HEADINGS FONT</span>
                <div class="type-sample font-fraunces">Fraunces Serif • Bold 700</div>
                <code class="type-family">'Fraunces', Georgia, serif</code>
                <p class="type-notes">Used for all H1/H2 page headers, score numbers, and section titles.</p>
              </div>

              <div class="card type-card">
                <span class="type-role">BODY &amp; INTERFACE FONT</span>
                <div class="type-sample font-geist">Geist &amp; Inter • Regular / Medium</div>
                <code class="type-family">'Geist', 'Inter', -apple-system, sans-serif</code>
                <p class="type-notes">Used for survey questions, form labels, data tables, and body copy.</p>
              </div>

              <div class="card type-card">
                <span class="type-role">MONOSPACE FONT</span>
                <div class="type-sample font-mono">Geist Mono • 0123456789</div>
                <code class="type-family">'Geist Mono', Consolas, monospace</code>
                <p class="type-notes">Used for UUIDs, session tokens, API endpoints, and timestamps.</p>
              </div>
            </div>
          </div>

          <!-- Interactive UI Components Preview -->
          <div class="components-showcase">
            <h3 class="subsection-title">Standardized Component Primitives</h3>
            <div class="comp-demo-grid">
              <div class="card comp-card">
                <span class="comp-name">Button Primitives</span>
                <div class="btn-group-demo">
                  <button type="button" class="btn btn-primary">Primary Action</button>
                  <button type="button" class="btn btn-outline">Outline Action</button>
                  <button type="button" class="btn btn-danger">Destructive</button>
                  <button type="button" class="btn btn-outline" disabled>Disabled</button>
                </div>
              </div>

              <div class="card comp-card">
                <span class="comp-name">Likert 5-Point Scale</span>
                <div class="likert-demo">
                  <div v-for="num in 5" :key="num" class="likert-step" :class="{ selected: selectedDemoRating === num }" @click="selectedDemoRating = num">
                    <span class="likert-radio"></span>
                    <span class="likert-num">{{ num }}</span>
                  </div>
                </div>
                <span class="likert-lbl">Selected Rating: {{ selectedDemoRating }} / 5 ({{ getLikertLabel(selectedDemoRating) }})</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- =================================================================== -->
      <!-- TAB 7: FEATURE PRD SUITE -->
      <!-- =================================================================== -->
      <section v-if="currentTab === 'features'" class="tab-section animate-in">
        <div class="features-layout">
          <!-- 13 Feature Cards Grid -->
          <div class="features-header-bar">
            <div>
              <span class="section-tag-kicker">MODULAR SPECIFICATIONS</span>
              <h2 class="results-title">13 Feature PRDs (Spine Depth)</h2>
              <p class="table-subtext">Each module includes context, exhaustive user stories, functional requirements, Given/When/Then acceptance scenarios, and failure modes.</p>
            </div>
          </div>

          <div class="features-grid">
            <div
              v-for="feat in docsData.features"
              :key="feat.slug"
              class="card feature-card"
              :class="{ 'card-active': selectedFeature?.slug === feat.slug }"
              @click="openFeatureDetail(feat)"
            >
              <div class="fc-top">
                <span class="fc-slug-badge">{{ feat.slug }}</span>
                <span class="fc-status-pill">Ready to Build</span>
              </div>

              <h3 class="fc-title">{{ feat.title }}</h3>
              <p class="fc-summary">{{ feat.summary }}</p>

              <div class="fc-meta-strip">
                <span class="fc-meta-item">
                  <strong>{{ feat.stories?.length || 0 }}</strong> Stories
                </span>
                <span class="fc-meta-item">
                  <strong>{{ feat.requirements?.length || 0 }}</strong> Requirements
                </span>
                <span class="fc-meta-item">
                  <strong>{{ feat.acceptance?.length || 0 }}</strong> Scenarios
                </span>
              </div>

              <button type="button" class="btn btn-outline btn-sm fc-view-btn">
                Inspect PRD Specification →
              </button>
            </div>
          </div>
        </div>

        <!-- PRD DETAIL DRAWER / MODAL -->
        <div v-if="selectedFeature" class="prd-modal-overlay" @click.self="selectedFeature = null">
          <div class="prd-modal-content card animate-in">
            <div class="prd-modal-header">
              <div>
                <span class="fc-slug-badge">{{ selectedFeature.slug }}</span>
                <h2 class="prd-modal-title">{{ selectedFeature.title }}</h2>
              </div>
              <button type="button" class="prd-close-btn" @click="selectedFeature = null">✕</button>
            </div>

            <div class="prd-modal-body">
              <!-- Context -->
              <div class="prd-section">
                <h3 class="prd-sec-title">Context &amp; Goal</h3>
                <p class="prd-sec-text">{{ selectedFeature.context }}</p>
              </div>

              <!-- Stories -->
              <div class="prd-section">
                <h3 class="prd-sec-title">User Stories</h3>
                <ul class="prd-story-list">
                  <li v-for="(s, idx) in selectedFeature.stories" :key="idx">{{ s }}</li>
                </ul>
              </div>

              <!-- Requirements -->
              <div class="prd-section">
                <h3 class="prd-sec-title">Functional Requirements</h3>
                <div class="prd-req-list">
                  <div v-for="(r, idx) in selectedFeature.requirements" :key="idx" class="prd-req-item">
                    <span class="req-check">✓</span>
                    <span class="req-text">{{ r }}</span>
                  </div>
                </div>
              </div>

              <!-- Acceptance Criteria (Given/When/Then) -->
              <div class="prd-section">
                <h3 class="prd-sec-title">Acceptance Criteria (Gherkin Scenarios)</h3>
                <div class="prd-acceptance-list">
                  <div v-for="(a, idx) in selectedFeature.acceptance" :key="idx" class="prd-scenario-card">
                    <span class="scenario-num">Scenario {{ idx + 1 }}</span>
                    <div class="scenario-text" v-html="formatGherkin(a)"></div>
                  </div>
                </div>
              </div>

              <!-- Edge Cases -->
              <div class="prd-section" v-if="selectedFeature.edge_cases?.length">
                <h3 class="prd-sec-title">Edge Cases &amp; Failure Modes</h3>
                <ul class="clean-bullet-list">
                  <li v-for="(e, idx) in selectedFeature.edge_cases" :key="idx">{{ e }}</li>
                </ul>
              </div>

              <!-- Improvements -->
              <div class="prd-section" v-if="selectedFeature.improvements?.length">
                <h3 class="prd-sec-title">Complex Mode Improvements &amp; Refactors</h3>
                <ul class="clean-bullet-list">
                  <li v-for="(imp, idx) in selectedFeature.improvements" :key="idx">{{ imp }}</li>
                </ul>
              </div>
            </div>

            <div class="prd-modal-footer">
              <button type="button" class="btn btn-outline" @click="selectedFeature = null">Close Specification</button>
            </div>
          </div>
        </div>
      </section>

      <!-- =================================================================== -->
      <!-- TAB 8: REBUILD PLAN & ENVIRONMENT MATRIX -->
      <!-- =================================================================== -->
      <section v-if="currentTab === 'rebuild'" class="tab-section animate-in">
        <div class="card rebuild-card">
          <div class="results-header-bar sub-header-bar">
            <div>
              <span class="section-tag-kicker">IMPLEMENTATION RUNBOOK</span>
              <h2 class="results-title">Project Rebuild Order &amp; Validation</h2>
              <p class="table-subtext">Tiered dependency build order and exhaustive configuration matrix for complete reconstruction.</p>
            </div>
          </div>

          <!-- Build Order -->
          <div class="build-order-section">
            <h3 class="subsection-title">13-Step Dependency-Tiered Build Order</h3>
            <div class="bo-grid">
              <div v-for="(step, idx) in rebuildSteps" :key="idx" class="bo-item">
                <div class="bo-step-num">{{ idx + 1 }}</div>
                <div class="bo-step-info">
                  <div class="bo-step-name">{{ step.name }}</div>
                  <div class="bo-step-file"><code>{{ step.file }}</code></div>
                </div>
              </div>
            </div>
          </div>

          <!-- Environment Variables Matrix -->
          <div class="env-vars-section">
            <div class="env-header-row">
              <h3 class="subsection-title">45 Tracked Environment Variables</h3>
              <div class="search-input-group api-search">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <input v-model="envSearch" type="text" placeholder="Search environment variables…" />
              </div>
            </div>

            <div class="env-table-wrap">
              <table class="engine-table">
                <thead>
                  <tr>
                    <th style="width: 320px;">Variable Name</th>
                    <th style="width: 140px;">Category</th>
                    <th>Functional Purpose &amp; Contract</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="v in filteredEnvVars" :key="v.name">
                    <td>
                      <div class="env-name-row">
                        <code class="env-code">{{ v.name }}</code>
                        <button type="button" class="env-copy-btn" @click="copyCode(v.name)" title="Copy variable name">
                          {{ copyStatus === v.name ? '✓' : 'Copy' }}
                        </button>
                      </div>
                    </td>
                    <td>
                      <span class="env-cat-tag" :class="'cat-' + v.cat.toLowerCase()">{{ v.cat }}</span>
                    </td>
                    <td>
                      <span class="env-desc-text">{{ v.desc }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from "vue";
import { getSystemDocs } from "../api.js";
import { SYSTEM_DOCS_FALLBACK } from "../utils/systemDocsData.js";

// State
const loading = ref(false);
const error = ref(null);
const docsData = ref(SYSTEM_DOCS_FALLBACK);
const currentTab = ref("overview");
const copyStatus = ref(null);
const zoomLevel = ref(1.0);

// Sub-Tab Navigation
const availableTabs = [
  { id: "overview", label: "Overview & PRD", icon: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>` },
  { id: "architecture", label: "Architecture", icon: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>` },
  { id: "diagrams", label: "Diagrams Gallery", badge: "9", icon: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>` },
  { id: "interfaces", label: "API Contracts", badge: "33", icon: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>` },
  { id: "datamodel", label: "Data Model & Schema", badge: "19", icon: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>` },
  { id: "design", label: "Design System", icon: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a14.5 14.5 0 0 0 0 20 10 10 0 0 0 0-20"></path></svg>` },
  { id: "features", label: "Feature PRDs", badge: "13", icon: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>` },
  { id: "rebuild", label: "Rebuild Runbook", icon: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 11 12 14 22 4"></polyline><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>` }
];

// Diagrams State
const selectedDiagramIdx = ref(0);
const diagViewMode = ref("rendered");
const mermaidRendering = ref(false);
const mermaidSvgContainer = ref(null);

const activeDiagram = computed(() => {
  const diags = docsData.value?.diagrams?.length ? docsData.value.diagrams : SYSTEM_DOCS_FALLBACK.diagrams;
  if (!diags?.length) return null;
  return diags[selectedDiagramIdx.value] || diags[0];
});

// API Explorer Filter State
const apiSearch = ref("");
const apiMethodFilter = ref("");

const filteredInterfaces = computed(() => {
  if (!docsData.value?.interfaces) return [];
  return docsData.value.interfaces.filter(row => {
    const matchSearch = !apiSearch.value ||
      row.path.toLowerCase().includes(apiSearch.value.toLowerCase()) ||
      row.handler.toLowerCase().includes(apiSearch.value.toLowerCase()) ||
      (row.notes && row.notes.toLowerCase().includes(apiSearch.value.toLowerCase()));
    const matchMethod = !apiMethodFilter.value || row.method.toUpperCase() === apiMethodFilter.value.toUpperCase();
    return matchSearch && matchMethod;
  });
});

// Data Model State
const selectedTable = ref("organizations");
const tableSearch = ref("");

const filteredTables = computed(() => {
  const tables = Object.keys(docsData.value?.data_model?.entities || {});
  if (!tableSearch.value) return tables;
  return tables.filter(t => t.toLowerCase().includes(tableSearch.value.toLowerCase()));
});

const activeTableColumns = computed(() => {
  if (selectedTable.value === "__enums__") return [];
  return docsData.value?.data_model?.entities?.[selectedTable.value] || [];
});

// Features PRD State
const selectedFeature = ref(null);

function openFeatureDetail(feat) {
  selectedFeature.value = feat;
}

// Design System Demo State
const selectedDemoRating = ref(4);

function getLikertLabel(val) {
  const map = { 1: "Strongly Disagree", 2: "Disagree", 3: "Neutral", 4: "Agree", 5: "Strongly Agree" };
  return map[val] || "";
}

// Colors
const colorPaletteList = [
  { name: "Primary Deep Navy", var: "--primary", hex: "#161057", purpose: "Brand anchor, headings, main contrast" },
  { name: "Primary Dark Hover", var: "--primary-hover", hex: "#0F0A42", purpose: "Pressed & hover states on primary elements" },
  { name: "Accent Teal", var: "--accent", hex: "#04907C", purpose: "Primary CTAs, active selections, focus rings" },
  { name: "Accent Hover", var: "--accent-hover", hex: "#037A69", purpose: "Button hover state" },
  { name: "Canvas Warm Off-White", var: "--bg", hex: "#FAFAF8", purpose: "Calming, low-sensory-fatigue background" },
  { name: "Surface Pure White", var: "--surface", hex: "#FFFFFF", purpose: "Card surfaces, modal sheets" },
  { name: "Surface Subtle Alt", var: "--surface-alt", hex: "#F8FAFC", purpose: "Table headers, secondary containers" },
  { name: "Text Main Charcoal", var: "--text-main", hex: "#1E293B", purpose: "High-contrast AAA body copy" },
  { name: "Text Muted Slate", var: "--text-muted", hex: "#64748B", purpose: "Secondary descriptions & timestamps" },
  { name: "Success Emerald", var: "--success", hex: "#059669", purpose: "Successful submissions, confirmed states" },
  { name: "Warning Amber", var: "--warning", hex: "#D97706", purpose: "Attention badges, queue warnings" },
  { name: "Danger Coral", var: "--danger", hex: "#E05A47", purpose: "Destructive actions, error alerts" }
];

// Pillars
const pillarsList = [
  { name: "Physical Environment", desc: "Sensory workplace accessibility, sound zones, lighting & quiet rooms." },
  { name: "Hiring & Recruitment", desc: "Neuro-inclusive interview formats, explicit task requirements & unbiased evaluation." },
  { name: "Culture & Leadership", desc: "Executive sponsorship, open psychological safety & stigma eradication." },
  { name: "Policies & Practices", desc: "Documented accommodation pathways, flexible working hours & remote arrangements." },
  { name: "Career Development", desc: "Transparent promotion pathways, mentorship & fair performance appraisals." },
  { name: "Communication", desc: "Multi-modal communication channels & clear asynchronous expectations." },
  { name: "Daily Operations", desc: "Meeting structures, advance agenda distribution & uninterrupted focus time." },
  { name: "Wellbeing & Support", desc: "Employee Resource Groups (ERGs), specialized health coaching & mental health benefits." }
];

// Maturity Tiers
const maturityTiers = [
  { name: "Foundational", range: "0–39 points", pct: 24, color: "red", description: "Baseline legal compliance; minimal formal accommodations; high sensory friction." },
  { name: "Early Progress", range: "40–79 points", pct: 48, color: "amber", description: "Ad-hoc support; isolated champions; emerging awareness without enterprise policies." },
  { name: "Developing", range: "80–119 points", pct: 72, color: "blue", description: "Standardized inclusion policies; formalized accommodation request procedures." },
  { name: "Proficient", range: "120–139 points", pct: 86, color: "teal", description: "Widespread cultural integration; active executive sponsorship; structured feedback loops." },
  { name: "Leading", range: "140–160 points", pct: 100, color: "emerald", description: "Best-in-class industry benchmark; systemic neuro-inclusion embedded in all operations." }
];

// Rebuild Steps
const rebuildSteps = [
  { name: "Core Application Architecture", file: "features/01-core/PRD.md" },
  { name: "Project Setup & Tooling", file: "features/02-project-setup/PRD.md" },
  { name: "Database Migrations (001–022)", file: "features/03-migrations/PRD.md" },
  { name: "Auxiliary SQL Routines", file: "features/04-sql/PRD.md" },
  { name: "Domain & Pydantic Models", file: "features/05-models/PRD.md" },
  { name: "Stateless Utilities & Cryptography", file: "features/06-utils/PRD.md" },
  { name: "Deterministic Scoring Engine", file: "features/07-services/PRD.md" },
  { name: "REST API Controller Layer", file: "features/08-api/PRD.md" },
  { name: "Vue 3 Single Page Application", file: "features/09-frontend/PRD.md" },
  { name: "Operational Scripts & Seeders", file: "features/10-scripts/PRD.md" },
  { name: "Outbox & Service Bus Daemons", file: "features/11-tasks/PRD.md" },
  { name: "Automated Pytest & Playwright Suite", file: "features/12-tests/PRD.md" },
  { name: "Technical Documentation & Runbooks", file: "features/13-documentation/PRD.md" }
];

// Environment Variables
const envSearch = ref("");
const envVarsList = [
  { name: "PGHOST", cat: "Database", desc: "PostgreSQL Flexible Server host address (e.g. niwi-db.postgres.database.azure.com)" },
  { name: "PGDATABASE", cat: "Database", desc: "Target database name (default: nd_audit)" },
  { name: "PGUSER", cat: "Database", desc: "Database user credentials" },
  { name: "PGPASSWORD", cat: "Database", desc: "Database password (retrieved from Azure Key Vault in production)" },
  { name: "PGPORT", cat: "Database", desc: "Database port (default: 5432)" },
  { name: "PGOPTIONS", cat: "Database", desc: "Connection parameters (-c statement_timeout=15000)" },
  { name: "KEY_VAULT_NAME", cat: "Security", desc: "Azure Key Vault name (kv-niwi-prod) accessed via Managed Identity" },
  { name: "REQUIRE_KEYVAULT", cat: "Security", desc: "Boolean flag enforcing Key Vault connectivity before boot" },
  { name: "ENTRA_TENANT_ID", cat: "Auth", desc: "Microsoft Entra ID (Azure AD) corporate tenant UUID" },
  { name: "ENTRA_CLIENT_ID", cat: "Auth", desc: "Microsoft Entra ID OAuth2 App Registration client ID" },
  { name: "JWT_SECRET", cat: "Security", desc: "HMAC fallback signing secret for local mock session tokens" },
  { name: "ACS_CONNECTION_STRING", cat: "Email", desc: "Azure Communication Services connection string for email dispatch" },
  { name: "ACS_SENDER_ADDRESS", cat: "Email", desc: "Verified sender address (donotreply@orchvate.in)" },
  { name: "ACS_SENDER_NAME", cat: "Email", desc: "Display sender name (NIWI Audit System)" },
  { name: "HUBSPOT_ACCESS_TOKEN", cat: "CRM", desc: "HubSpot API token for synchronization of prospective audit leads" },
  { name: "ENABLE_DEV_BYPASS", cat: "Security", desc: "Local developer auth bypass; strictly disallowed in production" },
  { name: "OUTBOX_POLL_INTERVAL", cat: "Workers", desc: "Polling interval in seconds for outbox dispatcher daemon (default: 5)" },
  { name: "OUTBOX_BATCH_SIZE", cat: "Workers", desc: "Maximum batch of pending messages claimed per polling cycle (default: 10)" },
  { name: "ENVIRONMENT", cat: "System", desc: "Deployment environment (development, staging, production)" },
  { name: "CORS_ORIGINS", cat: "Security", desc: "Comma-separated allowed client origins (e.g. https://niwi.orchvate.in)" },
  { name: "VITE_API_BASE", cat: "Frontend", desc: "Base API proxy URL for Vue SPA client (default: /api)" }
];

const filteredEnvVars = computed(() => {
  if (!envSearch.value) return envVarsList;
  const q = envSearch.value.toLowerCase();
  return envVarsList.filter(v => v.name.toLowerCase().includes(q) || v.cat.toLowerCase().includes(q) || v.desc.toLowerCase().includes(q));
});

// Helpers
function formatNumber(num) {
  return Number(num).toLocaleString();
}

function getCleanDiagramTitle(t) {
  return t.replace(/^\d+\.\s*/, "");
}

function getAuthBadgeClass(auth) {
  if (!auth || auth.includes("None") || auth.includes("Public")) return "badge-green";
  if (auth.includes("super")) return "badge-coral";
  if (auth.includes("admin")) return "badge-blue";
  return "badge-slate";
}

function formatMarkdownToHtml(md) {
  if (!md) return "";
  return md
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n\s*-\s*/g, "<br/>• ");
}

function formatGherkin(text) {
  if (!text) return "";
  return text
    .replace(/Given\s+/g, "<span class='gh-kw'>Given</span> ")
    .replace(/When\s+/g, "<br/><span class='gh-kw'>When</span> ")
    .replace(/Then\s+/g, "<br/><span class='gh-kw'>Then</span> ");
}

function copyCode(text) {
  if (!text) return;
  navigator.clipboard.writeText(text);
  copyStatus.value = text;
  setTimeout(() => {
    if (copyStatus.value === text) copyStatus.value = null;
  }, 2000);
}

// Diagram Selection & Mermaid Rendering
async function selectDiagram(idx) {
  selectedDiagramIdx.value = idx;
  zoomLevel.value = 1.0;
  await nextTick();
  if (!activeDiagram.value?.svg) {
    renderActiveMermaid();
  }
}

async function renderActiveMermaid() {
  if (!activeDiagram.value || !mermaidSvgContainer.value) return;
  mermaidRendering.value = true;
  mermaidSvgContainer.value.innerHTML = "";

  try {
    let mermaid = window.mermaid;
    if (!mermaid) {
      const module = await import("mermaid");
      mermaid = module.default;
      mermaid.initialize({
        startOnLoad: false,
        theme: "base",
        themeVariables: {
          primaryColor: "#161057",
          primaryTextColor: "#FFFFFF",
          primaryBorderColor: "#161057",
          lineColor: "#04907C",
          secondaryColor: "#FAF9F5",
          tertiaryColor: "#F8FAFC",
          fontSize: "13px",
          fontFamily: "'Geist', 'Inter', sans-serif"
        }
      });
      window.mermaid = mermaid;
    }

    const id = "mermaid-svg-" + Math.floor(Math.random() * 100000);
    const { svg } = await mermaid.render(id, activeDiagram.value.code);
    if (mermaidSvgContainer.value) {
      mermaidSvgContainer.value.innerHTML = svg;
    }
  } catch (err) {
    console.warn("Mermaid dynamic render failed, switching to code view:", err);
    diagViewMode.value = "code";
  } finally {
    mermaidRendering.value = false;
  }
}

// Fetch Documentation
async function fetchDocs(force = false) {
  loading.value = true;
  error.value = null;
  try {
    const live = await getSystemDocs();
    if (live && Array.isArray(live.diagrams) && live.diagrams.length > 0) {
      docsData.value = {
        ...SYSTEM_DOCS_FALLBACK,
        ...live,
        diagrams: live.diagrams.map((d, i) => ({
          ...d,
          svg: d.svg || SYSTEM_DOCS_FALLBACK.diagrams?.[i]?.svg || ""
        }))
      };
    } else {
      docsData.value = SYSTEM_DOCS_FALLBACK;
    }
    await nextTick();
    if (!activeDiagram.value?.svg) {
      renderActiveMermaid();
    }
  } catch (err) {
    console.warn("Using offline bundled docs data:", err);
    docsData.value = SYSTEM_DOCS_FALLBACK;
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  fetchDocs();
});
</script>

<style scoped>
/* ==========================================================================
   NIWI — System Specs & Documentation Portal Styles
   Implements exact design language from style.css, SuperDashboard & Overview
   ========================================================================== */

.system-docs-page {
  padding-bottom: 80px;
}

/* Metric Highlights Strip inside Hero */
.specs-metrics-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 24px;
}

.metric-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid var(--border);
  padding: 6px 14px;
  border-radius: var(--radius-full);
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(8px);
}

.mp-val {
  font-family: var(--font-heading);
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--primary);
}

.mp-lbl {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* Sub-Tab Navigation Bar */
.docs-nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 12px;
  overflow-x: auto;
}

.docs-nav-tabs {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow-x: auto;
  scrollbar-width: none;
}
.docs-nav-tabs::-webkit-scrollbar {
  display: none;
}

.doc-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  white-space: nowrap;
}

.doc-tab-btn:hover {
  color: var(--primary);
  background: rgba(22, 16, 87, 0.04);
}

.doc-tab-btn.active {
  color: var(--primary);
  background: #FFFFFF;
  border-color: var(--border);
  box-shadow: var(--shadow-sm);
}

.tab-icon {
  display: flex;
  align-items: center;
  color: inherit;
}

.tab-count-badge {
  font-size: 0.75rem;
  padding: 2px 7px;
  border-radius: 999px;
  background: rgba(22, 16, 87, 0.08);
  color: var(--primary);
  font-weight: 700;
}

.doc-tab-btn.active .tab-count-badge {
  background: var(--accent);
  color: #FFFFFF;
}

/* Loading Card */
.loading-state-card {
  padding: 48px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(4, 144, 124, 0.2);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.loading-text {
  font-size: 0.95rem;
  color: var(--text-muted);
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Section Tag Kicker */
.section-tag-kicker {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--accent);
  margin-bottom: 4px;
  display: block;
}

/* ==========================================================================
   TAB 1: OVERVIEW STYLES
   ========================================================================== */
.overview-card {
  padding: 32px;
}

.overview-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.overview-main-title {
  font-family: var(--font-heading);
  font-size: 1.8rem;
  color: var(--primary);
}

.build-tier-badge {
  background: rgba(4, 144, 124, 0.1);
  color: var(--accent);
  font-weight: 700;
  font-size: 0.8rem;
  padding: 4px 12px;
  border-radius: var(--radius-full);
}

.overview-body-quote {
  font-size: 1.05rem;
  line-height: 1.6;
  color: var(--text-main);
  background: var(--bg-cream);
  border-left: 4px solid var(--accent);
  padding: 16px 20px;
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  margin-bottom: 32px;
}

.subsection-title {
  font-family: var(--font-heading);
  font-size: 1.25rem;
  color: var(--primary);
  margin-bottom: 16px;
}

/* 8 Pillars Grid */
.pillars-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-bottom: 36px;
}

.pillar-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px;
  background: var(--surface-alt);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.pillar-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.pillar-num {
  width: 28px;
  height: 28px;
  background: var(--primary);
  color: #FFFFFF;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  font-weight: 700;
  flex-shrink: 0;
}

.pillar-name {
  font-weight: 700;
  font-size: 0.95rem;
  color: var(--primary);
  margin-bottom: 4px;
}

.pillar-desc {
  font-size: 0.82rem;
  color: var(--text-muted);
  line-height: 1.4;
}

/* Progression Tiers Grid */
.tiers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
  margin-bottom: 36px;
}

.tier-card {
  padding: 18px;
  border-radius: var(--radius-md);
  background: #FFFFFF;
  border: 1.5px solid var(--border);
}

.tier-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 8px;
}

.tier-name {
  font-weight: 700;
  font-size: 1rem;
  color: var(--primary);
}

.tier-range {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted);
}

.tier-desc {
  font-size: 0.82rem;
  color: var(--text-muted);
  line-height: 1.4;
  margin-bottom: 12px;
  min-height: 48px;
}

.tier-bar {
  height: 6px;
  background: var(--surface-alt);
  border-radius: 999px;
  overflow: hidden;
}

.tier-bar-fill {
  height: 100%;
  border-radius: 999px;
}

.tier-red .tier-bar-fill { background: var(--danger); }
.tier-amber .tier-bar-fill { background: var(--warning); }
.tier-blue .tier-bar-fill { background: #3B82F6; }
.tier-teal .tier-bar-fill { background: var(--accent); }
.tier-emerald .tier-bar-fill { background: var(--success); }

/* Personas & Architecture Inner Cards */
.personas-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 20px;
}

.inner-card {
  padding: 24px;
  background: var(--surface-alt);
}

.inner-card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-heading);
  font-size: 1.15rem;
  color: var(--primary);
  margin-bottom: 16px;
}

.clean-bullet-list {
  margin: 0;
  padding-left: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-size: 0.9rem;
  line-height: 1.5;
  color: var(--text-main);
}

/* ==========================================================================
   TAB 2: ARCHITECTURE STYLES
   ========================================================================== */
.topo-overview-card {
  padding: 32px;
}

.arch-layers-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 40px;
}

.arch-layer-item {
  padding: 20px;
  background: #FFFFFF;
  border: 1px solid var(--border);
  border-left: 5px solid var(--accent);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}

.ali-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.ali-badge {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  font-weight: 700;
  padding: 3px 8px;
  background: var(--primary);
  color: #FFFFFF;
  border-radius: 4px;
}

.ali-sub {
  font-weight: 700;
  font-size: 0.95rem;
  color: var(--primary);
}

.ali-text {
  font-size: 0.9rem;
  color: var(--text-muted);
  line-height: 1.5;
  margin: 0;
}

.ali-text code {
  background: rgba(22, 16, 87, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.85em;
  color: var(--primary);
}

/* External Services Grid */
.ext-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 18px;
  margin-bottom: 36px;
}

.ext-card {
  padding: 20px;
  background: var(--surface-alt);
}

.ext-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.ext-icon-pill {
  width: 32px;
  height: 32px;
  background: rgba(4, 144, 124, 0.1);
  color: var(--accent);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-pill-blue {
  background: rgba(59, 130, 246, 0.1);
  color: #3B82F6;
}

.ext-name {
  font-size: 1rem;
  font-weight: 700;
  color: var(--primary);
  margin: 0;
}

.ext-desc {
  font-size: 0.85rem;
  color: var(--text-muted);
  line-height: 1.5;
}

/* ==========================================================================
   TAB 3: MERMAID GALLERY STYLES
   ========================================================================== */
.diagram-gallery-card {
  padding: 28px;
}

.diagram-selector-bar {
  border-bottom: 1px solid var(--border);
  padding-bottom: 20px;
  margin-bottom: 24px;
}

.diag-pills-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.diag-pill-btn {
  padding: 7px 14px;
  border-radius: var(--radius-full);
  border: 1px solid var(--border);
  background: #FFFFFF;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}

.diag-pill-btn:hover {
  color: var(--primary);
  border-color: var(--primary);
}

.diag-pill-btn.active {
  background: var(--primary);
  color: #FFFFFF;
  border-color: var(--primary);
}

.diagram-header-strip {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.diag-display-title {
  font-family: var(--font-heading);
  font-size: 1.3rem;
  color: var(--primary);
  margin: 0 0 4px 0;
}

.diag-type-badge {
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(4, 144, 124, 0.1);
  color: var(--accent);
  font-weight: 600;
}

.diag-view-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.zoom-controls {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--surface-alt, #F8FAFC);
  padding: 3px 8px;
  border-radius: var(--radius-md, 8px);
  border: 1px solid var(--border, #E2E8F0);
  margin-right: 6px;
}

.btn-zoom {
  background: #FFFFFF;
  border: 1px solid var(--border, #CBD5E1);
  border-radius: 4px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-weight: 700;
  font-size: 14px;
  color: var(--text-main, #1E293B);
  line-height: 1;
  transition: all 0.15s ease;
}

.btn-zoom:hover {
  background: var(--surface-alt, #F1F5F9);
  border-color: var(--primary, #161057);
}

.zoom-val {
  font-size: 11px;
  font-family: var(--font-mono, monospace);
  font-weight: 600;
  color: var(--text-muted, #64748B);
  min-width: 38px;
  text-align: center;
}

.btn-zoom-reset {
  background: transparent;
  border: none;
  font-size: 11px;
  cursor: pointer;
  color: var(--accent, #04907C);
  text-decoration: underline;
  padding: 0 4px;
  font-weight: 600;
}

.btn-zoom-reset:hover {
  color: var(--accent-hover, #037A69);
}

.diagram-render-box {
  background: #FFFFFF;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 32px 20px;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
}

.mermaid-svg-target {
  width: 100%;
  max-width: 100%;
  display: flex;
  justify-content: center;
}

.mermaid-svg-target svg {
  max-width: 100%;
  height: auto;
}

.diagram-code-box {
  background: #0F172A;
  border-radius: var(--radius-md);
  padding: 20px;
  overflow: auto;
  max-height: 550px;
}

.code-pre {
  margin: 0;
  color: #F8FAFC;
  font-family: var(--font-mono);
  font-size: 0.85rem;
  line-height: 1.5;
}

/* ==========================================================================
   TAB 4: API INTERFACES EXPLORER
   ========================================================================== */
.api-filter-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
}

.api-search {
  min-width: 280px;
}

.method-filter-pills {
  display: flex;
  gap: 6px;
}

.mf-pill {
  padding: 5px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: #FFFFFF;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-muted);
  cursor: pointer;
}

.mf-pill.active {
  background: var(--primary);
  color: #FFFFFF;
  border-color: var(--primary);
}

.method-tag {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  font-weight: 700;
  text-align: center;
  min-width: 55px;
}

.method-get { background: #E0F2FE; color: #0369A1; }
.method-post { background: #D1FAE5; color: #047857; }
.method-put { background: #FEF3C7; color: #B45309; }
.method-patch { background: #F3E8FF; color: #7E22CE; }
.method-delete { background: #FEE2E2; color: #B91C1C; }

.endpoint-code {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--primary);
}

.kind-badge {
  font-size: 0.75rem;
  padding: 2px 7px;
  border-radius: 4px;
  background: var(--surface-alt);
  border: 1px solid var(--border);
  color: var(--text-muted);
}

.auth-badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  white-space: nowrap;
}

.badge-green { background: #D1FAE5; color: #047857; }
.badge-blue { background: #DBEAFE; color: #1D4ED8; }
.badge-coral { background: #FFE4E6; color: #E11D48; }
.badge-slate { background: #F1F5F9; color: #475569; }

.handler-text {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 2px;
}

.notes-text {
  font-size: 0.82rem;
  color: var(--text-main);
  line-height: 1.35;
}

/* ==========================================================================
   TAB 5: DATA MODEL STYLES
   ========================================================================== */
.data-model-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
}

.dm-sidebar {
  padding: 18px;
  height: fit-content;
}

.dms-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.dms-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--primary);
  margin: 0;
}

.dms-search-wrap {
  margin-bottom: 12px;
}

.dms-search {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
}

.dms-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 520px;
  overflow-y: auto;
}

.dms-table-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  text-align: left;
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.dms-table-btn:hover {
  background: var(--surface-alt);
}

.dms-table-btn.active {
  background: #FFFFFF;
  border-color: var(--border);
  box-shadow: var(--shadow-sm);
  font-weight: 700;
}

.tbl-name {
  flex: 1;
  font-family: var(--font-mono);
  color: var(--primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tbl-col-count {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.dms-enum-anchor {
  border-top: 1px solid var(--border);
  margin-top: 12px;
  padding-top: 12px;
}

.enum-special-btn {
  background: rgba(4, 144, 124, 0.05);
  color: var(--accent);
}

.dm-details-card {
  padding: 28px;
}

.table-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  border-bottom: 1px solid var(--border);
  padding-bottom: 16px;
  margin-bottom: 20px;
}

.tdh-title code {
  font-family: var(--font-heading);
  font-size: 1.5rem;
  color: var(--primary);
}

.col-name-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}

.col-name {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--primary);
}

.pk-tag {
  font-size: 0.65rem;
  font-weight: 800;
  background: #FEF3C7;
  color: #B45309;
  padding: 1px 4px;
  border-radius: 3px;
}

.fk-tag {
  font-size: 0.65rem;
  font-weight: 800;
  background: #DBEAFE;
  color: #1E40AF;
  padding: 1px 4px;
  border-radius: 3px;
}

.uk-tag {
  font-size: 0.65rem;
  font-weight: 800;
  background: #E0E7FF;
  color: #4338CA;
  padding: 1px 4px;
  border-radius: 3px;
}

.type-tag {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  color: var(--text-muted);
}

/* Enums Display Grid */
.enums-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.enum-card {
  padding: 18px;
  background: var(--surface-alt);
}

.enum-header {
  margin-bottom: 12px;
}

.enum-name code {
  font-family: var(--font-mono);
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--primary);
}

.enum-desc {
  font-size: 0.78rem;
  color: var(--text-muted);
  display: block;
  margin-top: 2px;
}

.enum-values-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.enum-item-pill {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  padding: 3px 8px;
  background: #FFFFFF;
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text-main);
}

/* ==========================================================================
   TAB 6: DESIGN SYSTEM STYLES
   ========================================================================== */
.design-system-card {
  padding: 32px;
}

.colors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 36px;
}

.swatch-card {
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: #FFFFFF;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.swatch-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.swatch-preview {
  height: 60px;
  width: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
  padding: 6px;
}

.swatch-copy-hint {
  font-size: 0.7rem;
  padding: 2px 6px;
  background: rgba(0, 0, 0, 0.4);
  color: #FFFFFF;
  border-radius: 4px;
  backdrop-filter: blur(4px);
}

.swatch-info {
  padding: 12px;
}

.swatch-name {
  font-weight: 700;
  font-size: 0.88rem;
  color: var(--primary);
  margin-bottom: 2px;
}

.swatch-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  margin-bottom: 6px;
}

.swatch-hex {
  font-family: var(--font-mono);
  font-weight: 700;
  color: var(--accent);
}

.swatch-var {
  font-family: var(--font-mono);
  color: var(--text-muted);
}

.swatch-purpose {
  font-size: 0.75rem;
  color: var(--text-muted);
  line-height: 1.3;
}

.type-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 36px;
}

.type-card {
  padding: 20px;
  background: var(--surface-alt);
}

.type-role {
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  color: var(--accent);
  margin-bottom: 8px;
  display: block;
}

.type-sample {
  font-size: 1.3rem;
  margin-bottom: 8px;
  color: var(--primary);
}

.font-fraunces { font-family: var(--font-heading); font-weight: 700; }
.font-geist { font-family: var(--font-body); }
.font-mono { font-family: var(--font-mono); }

.type-family {
  font-size: 0.75rem;
  color: var(--text-muted);
  display: block;
  margin-bottom: 8px;
}

.type-notes {
  font-size: 0.8rem;
  color: var(--text-main);
  line-height: 1.4;
  margin: 0;
}

.comp-demo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

.comp-card {
  padding: 20px;
  background: var(--surface-alt);
}

.comp-name {
  font-weight: 700;
  font-size: 0.9rem;
  color: var(--primary);
  margin-bottom: 12px;
  display: block;
}

.btn-group-demo {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.likert-demo {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}

.likert-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.likert-radio {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-strong);
  border-radius: 50%;
  background: #FFFFFF;
}

.likert-step.selected .likert-radio {
  border-color: var(--accent);
  background: var(--accent);
  box-shadow: inset 0 0 0 3px #FFFFFF;
}

.likert-num {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--primary);
}

.likert-lbl {
  font-size: 0.8rem;
  color: var(--accent);
  font-weight: 600;
}

/* ==========================================================================
   TAB 7: FEATURES PRD GRID & MODAL
   ========================================================================== */
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 18px;
}

.feature-card {
  padding: 22px;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  display: flex;
  flex-direction: column;
}

.feature-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--primary);
}

.fc-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.fc-slug-badge {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(22, 16, 87, 0.08);
  color: var(--primary);
}

.fc-status-pill {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--accent);
}

.fc-title {
  font-family: var(--font-heading);
  font-size: 1.15rem;
  color: var(--primary);
  margin: 0 0 8px 0;
}

.fc-summary {
  font-size: 0.84rem;
  color: var(--text-muted);
  line-height: 1.4;
  margin-bottom: 16px;
  flex: 1;
}

.fc-meta-strip {
  display: flex;
  gap: 14px;
  padding: 8px 0;
  border-top: 1px solid var(--border);
  margin-bottom: 14px;
}

.fc-meta-item {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.fc-meta-item strong {
  color: var(--primary);
}

.fc-view-btn {
  width: 100%;
}

/* PRD Detail Modal */
.prd-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.prd-modal-content {
  width: 100%;
  max-width: 850px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}

.prd-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px 28px;
  border-bottom: 1px solid var(--border);
  background: var(--surface-alt);
}

.prd-modal-title {
  font-family: var(--font-heading);
  font-size: 1.5rem;
  color: var(--primary);
  margin: 4px 0 0 0;
}

.prd-close-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: #FFFFFF;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.prd-modal-body {
  padding: 28px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.prd-sec-title {
  font-family: var(--font-heading);
  font-size: 1.1rem;
  color: var(--primary);
  border-bottom: 1px solid var(--border);
  padding-bottom: 6px;
  margin-bottom: 10px;
}

.prd-sec-text {
  font-size: 0.9rem;
  line-height: 1.5;
  color: var(--text-main);
  margin: 0;
}

.prd-story-list {
  margin: 0;
  padding-left: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 0.88rem;
  color: var(--text-main);
}

.prd-req-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.prd-req-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 0.88rem;
  color: var(--text-main);
  line-height: 1.4;
}

.req-check {
  color: var(--accent);
  font-weight: 800;
}

.prd-acceptance-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.prd-scenario-card {
  padding: 14px;
  background: var(--surface-alt);
  border-left: 3px solid var(--accent);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

.scenario-num {
  font-size: 0.72rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--accent);
  display: block;
  margin-bottom: 4px;
}

.scenario-text {
  font-size: 0.88rem;
  line-height: 1.45;
  color: var(--text-main);
}

.scenario-text :deep(.gh-kw) {
  font-weight: 800;
  color: var(--primary);
}

.prd-modal-footer {
  padding: 16px 28px;
  border-top: 1px solid var(--border);
  background: var(--surface-alt);
  display: flex;
  justify-content: flex-end;
}

/* ==========================================================================
   TAB 8: REBUILD PLAN & ENVIRONMENT VARIABLES
   ========================================================================== */
.rebuild-card {
  padding: 32px;
}

.bo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
  margin-bottom: 40px;
}

.bo-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background: var(--surface-alt);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.bo-step-num {
  width: 24px;
  height: 24px;
  background: var(--primary);
  color: #FFFFFF;
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.bo-step-name {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--primary);
}

.bo-step-file code {
  font-size: 0.72rem;
  color: var(--text-muted);
}

.env-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.env-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.env-code {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--primary);
}

.env-copy-btn {
  font-size: 0.7rem;
  padding: 2px 6px;
  border: 1px solid var(--border);
  background: #FFFFFF;
  border-radius: 4px;
  cursor: pointer;
  color: var(--text-muted);
}

.env-cat-tag {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 4px;
  white-space: nowrap;
}

.cat-database { background: #E0E7FF; color: #4338CA; }
.cat-security { background: #FEF3C7; color: #B45309; }
.cat-auth { background: #DBEAFE; color: #1E40AF; }
.cat-email { background: #D1FAE5; color: #047857; }
.cat-crm { background: #FCE7F3; color: #BE185D; }
.cat-workers { background: #EDE9FE; color: #6D28D9; }
.cat-system { background: #F1F5F9; color: #475569; }
.cat-frontend { background: #CCFBF1; color: #0F766E; }

.env-desc-text {
  font-size: 0.84rem;
  color: var(--text-muted);
  line-height: 1.4;
}

/* Responsive Adjustments */
@media (max-width: 900px) {
  .data-model-layout {
    grid-template-columns: 1fr;
  }
}
</style>

