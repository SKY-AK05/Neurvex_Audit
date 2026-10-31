<template>
  <div class="orgs-page animate-in">
    <!-- Compact Hero Header matching Overview / Reference Image -->
    <section class="hero-section" aria-label="Organisation Search Banner">
      <div class="hero-content">
        <h1 class="hero-title">Organisation Assessment &amp; Reporting</h1>
        <p class="hero-subtitle">
          Aggregate multi-respondent audits, analyze workplace inclusion maturity across departments and demographics, and dispatch executive reports.
        </p>

        <!-- Search & Filter Bar -->
        <div class="search-banner-card">
          <div class="search-input-group">
            <svg class="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <input
              v-model="orgSearch"
              type="text"
              placeholder="Search organisation by name or keyword…"
              aria-label="Search organisation"
            />
            <button v-if="orgSearch" class="btn-clear-search" @click="orgSearch = ''" title="Clear search">✕</button>
          </div>

          <div class="search-divider"></div>

          <div class="search-filter-group">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true">
              <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
            </svg>
            <select v-model="orgFilter" aria-label="Filter organisation status">
              <option value="all">All Organisations ({{ orgs.length }})</option>
              <option value="with_submissions">With Submissions ({{ orgsWithSubsCount }})</option>
              <option value="linked">Linked Accounts ({{ linkedOrgsCount }})</option>
              <option value="unlinked">Unlinked Pools ({{ unlinkedOrgsCount }})</option>
            </select>
          </div>
        </div>
      </div>
    </section>

    <!-- Main 2-Column Dashboard Grid matching Overview & Reference Image -->
    <div class="main-orgs-grid">

      <!-- LEFT COLUMN: Organisation Directory Card (like Filters in Overview) -->
      <aside class="org-sidebar-card" aria-label="Organisation Selector">
        <div class="osc-header">
          <div>
            <h2 class="osc-title">Organisations</h2>
            <span class="osc-subtitle">{{ filteredOrgs.length }} organisations found</span>
          </div>
          <div class="osc-header-right">
            <span class="osc-badge">{{ orgFilter === 'all' ? 'All' : orgFilter }}</span>
            <button
              type="button"
              class="mobile-dir-toggle-btn"
              @click="mobileDirectoryOpen = !mobileDirectoryOpen"
              :aria-expanded="mobileDirectoryOpen"
            >
              {{ mobileDirectoryOpen ? 'Hide Directory ▲' : 'Switch Org ▼' }}
            </button>
          </div>
        </div>

        <!-- Mobile Quick Summary when collapsed -->
        <div class="osc-mobile-selected" v-if="selectedOrg && !mobileDirectoryOpen">
          <span class="oms-label">Active:</span>
          <strong class="oms-name">{{ selectedOrg.name }}</strong>
          <span class="oms-badge">{{ selectedOrg.org_avg != null ? selectedOrg.org_avg + '/20' : '—' }}</span>
        </div>

        <div class="osc-collapsible-body" :class="{ 'mobile-open': mobileDirectoryOpen }">
          <!-- Filter Chips in Sidebar -->
          <div class="sidebar-filter-pills">
            <button
              class="s-pill"
              :class="{ active: orgFilter === 'all' }"
              @click="orgFilter = 'all'"
            >All</button>
            <button
              class="s-pill"
              :class="{ active: orgFilter === 'with_submissions' }"
              @click="orgFilter = 'with_submissions'"
            >With Audits</button>
            <button
              class="s-pill"
              :class="{ active: orgFilter === 'linked' }"
              @click="orgFilter = 'linked'"
            >Linked</button>
            <button
              class="s-pill"
              :class="{ active: orgFilter === 'unlinked' }"
              @click="orgFilter = 'unlinked'"
            >Pools</button>
          </div>

          <!-- Scrollable Organisations List -->
          <div v-if="loading" class="sidebar-loading">
            <div class="spinner"></div>
            <span>Loading organisations…</span>
          </div>

          <div v-else-if="filteredOrgs.length === 0" class="sidebar-empty">
            <p>No matching organisations</p>
            <button class="btn-reset-filter" @click="orgSearch = ''; orgFilter = 'all'">Reset</button>
          </div>

          <div v-else class="sidebar-orgs-list" role="tablist">
            <button
              v-for="org in filteredOrgs"
              :key="org.id"
              role="tab"
              :aria-selected="selectedOrg?.id === org.id"
              class="sidebar-org-item"
              :class="{
                'active': selectedOrg?.id === org.id,
                'virtual': org.is_virtual,
                'has-subs': org.respondent_count > 0
              }"
              @click="selectOrg(org)"
            >
              <div class="soi-left">
                <div class="soi-monogram" :style="{ backgroundColor: getMonogramColor(org.name) }">
                  {{ getMonogram(org.name) }}
                </div>
                <div class="soi-text">
                  <span class="soi-name" :title="org.name">{{ org.name }}</span>
                  <span class="soi-count">
                    {{ org.respondent_count }} {{ org.respondent_count === 1 ? 'submission' : 'submissions' }}
                  </span>
                </div>
              </div>

              <div class="soi-right">
                <span class="soi-score" :class="getScoreColorClass(org.org_avg)">
                  {{ org.org_avg != null ? org.org_avg + '/20' : '—' }}
                </span>
                <span v-if="org.is_virtual" class="soi-tag-pool">Pool</span>
                <span v-else class="soi-tag-linked">Linked</span>
              </div>
            </button>
          </div>
        </div>
      </aside>

      <!-- RIGHT COLUMN: Active Organisation Analysis & Reporting Workspace -->
      <main class="org-main-workspace" v-if="selectedOrg">

        <!-- Active Organisation Hero Card -->
        <section class="org-hero-card">
          <div class="org-hero-main">
            <div class="org-hero-left">
              <div class="org-hero-monogram" :style="{ backgroundColor: getMonogramColor(selectedOrg.name) }">
                {{ getMonogram(selectedOrg.name) }}
              </div>
              <div class="org-hero-info">
                <div class="org-hero-type-row">
                  <span v-if="selectedOrg.is_virtual" class="pill-warning">
                    ⚠️ Unlinked Submission Pool
                  </span>
                  <span v-else class="pill-success">
                    ✓ Official Linked Organisation Account
                  </span>
                  <span v-if="currentScore?.org_level" :class="['pill-level', levelClass(currentScore.org_level)]">
                    {{ currentScore.org_level }}
                  </span>
                </div>
                <h2 class="org-hero-name">{{ selectedOrg.name }}</h2>
                <p class="org-hero-summary">
                  Aggregated inclusion metrics calculated from
                  <strong>{{ detail?.respondents?.length || selectedOrg.respondent_count }} employee submissions</strong>.
                </p>
              </div>
            </div>

            <!-- Score Metric & Quick CTAs -->
            <div class="org-hero-right">
              <div class="hero-score-stat">
                <div class="stat-num-box">
                  <span class="stat-num">{{ currentScore?.org_avg != null ? currentScore.org_avg : '—' }}</span>
                  <span class="stat-denom">/ 20</span>
                </div>
                <span class="stat-label">Weighted NIWI Index</span>
                <div class="stat-progress-bar">
                  <div
                    class="stat-progress-fill"
                    :style="{ width: `${Math.min(100, Math.max(0, ((currentScore?.org_avg || 0) / 20) * 100))}%` }"
                  ></div>
                </div>
              </div>

              <!-- Action CTAs -->
              <div class="org-hero-actions">
                <button
                  v-if="selectedOrg.is_virtual"
                  class="btn btn-secondary-action"
                  :disabled="creatingOrg"
                  @click="createOrg(selectedOrg)"
                  title="Create formal organization record and link all matching submissions"
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                  {{ creatingOrg ? 'Linking…' : 'Link & Create Org' }}
                </button>

                <button
                  class="btn btn-primary-cta"
                  :disabled="!detail?.respondents?.length"
                  @click="activeTab = 'report'"
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,12 2,6"></polyline></svg>
                  Send Org Report
                </button>

                <button
                  class="btn btn-outline"
                  :disabled="!detail?.respondents?.length"
                  @click="exportOrgCSV"
                  title="Export complete submissions, scores, and question responses as CSV"
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                  Export CSV
                </button>
              </div>
            </div>
          </div>

          <!-- Virtual notice banner -->
          <div v-if="selectedOrg.is_virtual" class="unlinked-notice-banner">
            <div class="unb-icon">💡</div>
            <div class="unb-content">
              <strong>Unlinked Submissions Pool:</strong> These {{ selectedOrg.respondent_count }} responses were submitted by employees who specified "{{ selectedOrg.name }}".
              Click <strong>"Link &amp; Create Org"</strong> to assign individual respondent weights and enable automated email delivery.
            </div>
          </div>
        </section>

        <!-- Navigation Tabs Bar -->
        <nav class="analysis-tabs-nav" aria-label="Organisation Analysis Navigation">
          <button
            class="nav-tab-btn"
            :class="{ active: activeTab === 'pillars' }"
            @click="activeTab = 'pillars'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
            8 Core Pillars
          </button>

          <button
            class="nav-tab-btn"
            :class="{ active: activeTab === 'segments' }"
            @click="activeTab = 'segments'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
            Segment-Level Analysis
            <span class="tab-highlight-badge">DEI Insights</span>
          </button>

          <button
            class="nav-tab-btn"
            :class="{ active: activeTab === 'inputs' }"
            @click="activeTab = 'inputs'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
            Granular Input Analysis (Q5–Q44)
            <span class="tab-badge">40 Inputs</span>
          </button>

          <button
            class="nav-tab-btn"
            :class="{ active: activeTab === 'respondents' }"
            @click="activeTab = 'respondents'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
            Employee Submissions
            <span class="tab-count-pill">{{ detail?.respondents?.length || 0 }}</span>
          </button>

          <button
            class="nav-tab-btn"
            :class="{ active: activeTab === 'report' }"
            @click="activeTab = 'report'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,12 2,6"></polyline></svg>
            Send Executive Report
          </button>
        </nav>

        <!-- Loading State for Detail -->
        <div v-if="loadingDetail" class="detail-loading-box">
          <div class="spinner"></div>
          <span>Calculating multi-respondent weighted scores and segment metrics…</span>
        </div>

        <!-- Empty State if 0 Respondents -->
        <div v-else-if="!detail?.respondents?.length" class="no-respondents-card">
          <div class="empty-icon-box">📭</div>
          <h3>No employee audit submissions found yet</h3>
          <p>This organisation account has been created, but no employee or leader has submitted a self-assessment using "{{ selectedOrg.name }}".</p>
          <button class="btn btn-outline" @click="copyOrgInviteLink">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
            Copy Self-Assessment Invite Link
          </button>
        </div>

        <!-- Tab Content Area -->
        <div v-else class="tab-content-wrapper">

          <!-- TAB 1: 8 CORE PILLARS SCORECARD -->
          <section v-if="activeTab === 'pillars'" class="pillars-view animate-fade">
            <!-- Strengths vs Growth Priorities Grid -->
            <div class="highlights-grid">
              <div class="highlight-card strength-card">
                <div class="hl-header">
                  <span class="hl-icon">🏆</span>
                  <div>
                    <h4 class="hl-title">Top Organisational Strengths</h4>
                    <p class="hl-sub">Pillars with highest average maturity across all submissions</p>
                  </div>
                </div>
                <div class="hl-items">
                  <div v-for="p in topPillars" :key="p.id" class="hl-item">
                    <div class="hl-item-left">
                      <span class="hl-pillar-icon">{{ p.icon }}</span>
                      <span class="hl-pillar-name">{{ p.title }}</span>
                    </div>
                    <div class="hl-item-right">
                      <span class="hl-score-badge">{{ p.score }} / 20</span>
                      <span class="hl-tier-badge" :class="levelClass(p.level)">{{ p.level }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div class="highlight-card priority-card">
                <div class="hl-header">
                  <span class="hl-icon">🎯</span>
                  <div>
                    <h4 class="hl-title">Priority Growth Focus Areas</h4>
                    <p class="hl-sub">Pillars requiring policy, physical, or leadership intervention</p>
                  </div>
                </div>
                <div class="hl-items">
                  <div v-for="p in lowestPillars" :key="p.id" class="hl-item">
                    <div class="hl-item-left">
                      <span class="hl-pillar-icon">{{ p.icon }}</span>
                      <span class="hl-pillar-name">{{ p.title }}</span>
                    </div>
                    <div class="hl-item-right">
                      <span class="hl-score-badge priority">{{ p.score }} / 20</span>
                      <span class="hl-tier-badge" :class="levelClass(p.level)">{{ p.level }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- All 8 Pillars Cards Grid -->
            <div class="pillars-cards-grid">
              <div
                v-for="pillar in pillarScorecards"
                :key="pillar.id"
                class="pillar-card"
              >
                <div class="pc-top">
                  <div class="pc-icon-wrap">
                    <span class="pc-icon">{{ pillar.icon }}</span>
                    <div>
                      <h3 class="pc-title">{{ pillar.title }}</h3>
                      <span class="pc-category">NIWI Dimension {{ pillar.id.toUpperCase() }}</span>
                    </div>
                  </div>
                  <div class="pc-score-box">
                    <span class="pc-score">{{ pillar.score }}</span>
                    <span class="pc-max">/ 20</span>
                  </div>
                </div>

                <div class="pc-bar-wrap">
                  <div class="pc-bar-bg">
                    <div class="pc-bar-fill" :style="{ width: `${(pillar.score / 20) * 100}%` }"></div>
                  </div>
                  <div class="pc-bar-labels">
                    <span class="pc-level-tag" :class="levelClass(pillar.level)">{{ pillar.level }}</span>
                    <span class="pc-pct">{{ Math.round((pillar.score / 20) * 100) }}%</span>
                  </div>
                </div>

                <p class="pc-summary">{{ pillar.summary }}</p>

                <div class="pc-key-points">
                  <span v-for="(pt, idx) in pillar.points" :key="idx" class="pc-chip">
                    • {{ pt }}
                  </span>
                </div>
              </div>
            </div>
          </section>

          <!-- TAB 2: SEGMENT-LEVEL ANALYSIS -->
          <section v-if="activeTab === 'segments'" class="segments-view animate-fade">
            <div class="segments-control-card">
              <div class="scc-header">
                <div>
                  <h3 class="scc-title">Select Demographic / Organizational Segment</h3>
                  <p class="scc-sub">Compare audit scores and perception variances across groups in {{ selectedOrg.name }}</p>
                </div>
                <div class="segment-switcher">
                  <button
                    v-for="seg in segmentOptions"
                    :key="seg.key"
                    class="seg-btn"
                    :class="{ active: selectedSegmentKey === seg.key }"
                    @click="selectedSegmentKey = seg.key"
                  >
                    <span class="seg-btn-icon">{{ seg.icon }}</span>
                    {{ seg.label }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Perception Gap Callout if available -->
            <div v-if="perceptionGapNotice" class="gap-alert-card">
              <div class="gap-icon">⚠️</div>
              <div class="gap-text">
                <h4 class="gap-title">{{ perceptionGapNotice.title }}</h4>
                <p class="gap-desc">{{ perceptionGapNotice.desc }}</p>
              </div>
              <div class="gap-metric">
                <span class="gap-num">{{ perceptionGapNotice.delta }}</span>
                <span class="gap-label">Variance Gap</span>
              </div>
            </div>

            <!-- Segment Groups Cards -->
            <div class="segment-groups-grid">
              <div
                v-for="group in activeSegmentData"
                :key="group.name"
                class="segment-group-card"
              >
                <div class="sgc-header">
                  <div>
                    <h4 class="sgc-title">{{ group.name || 'Not Specified' }}</h4>
                    <span class="sgc-count-tag">
                      {{ group.count }} respondents ({{ group.pctOfTotal }}% of audit sample)
                    </span>
                  </div>
                  <div class="sgc-score-badge">
                    <span class="sgc-score">{{ group.avgScore }}</span>
                    <span class="sgc-denom">/ 20</span>
                  </div>
                </div>

                <!-- Delta vs Org Average -->
                <div class="sgc-delta-row">
                  <span class="sgc-delta-label">Comparison to Org Avg ({{ currentScore?.org_avg }}/20):</span>
                  <span
                    class="sgc-delta-val"
                    :class="{
                      'positive': group.delta > 0,
                      'negative': group.delta < 0,
                      'neutral': group.delta === 0
                    }"
                  >
                    {{ group.delta > 0 ? '+' : '' }}{{ group.delta }} pts
                  </span>
                </div>

                <!-- Mini Pillar Breakdown for this Segment -->
                <div class="sgc-pillars-table-wrap">
                  <h5 class="sgc-pt-heading">Pillar Scores for {{ group.name }}:</h5>
                  <div class="sgc-pillars-grid">
                    <div
                      v-for="(val, pkey) in group.sectionAvgs"
                      :key="pkey"
                      class="sgc-pillar-chip"
                    >
                      <span class="sgc-pc-name">{{ getSectionLabelShort(pkey) }}</span>
                      <span class="sgc-pc-score">{{ val }}/20</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- TAB 3: GRANULAR INPUT ANALYSIS (Q5–Q44) -->
          <section v-if="activeTab === 'inputs'" class="inputs-view animate-fade">
            <div class="inputs-filter-bar">
              <div class="ifb-pillar-select">
                <label for="input-pillar-filter">Filter by Pillar:</label>
                <select id="input-pillar-filter" v-model="selectedInputPillar">
                  <option value="all">All 8 Pillars (40 Questions)</option>
                  <option v-for="sec in DEFAULT_SECTIONS" :key="sec.id" :value="sec.id">
                    {{ sec.icon }} {{ sec.title }} (5 Questions)
                  </option>
                </select>
              </div>

              <div class="ifb-search-wrap">
                <input
                  v-model="inputSearchQuery"
                  type="text"
                  placeholder="Search question text or keyword (e.g. interview, lighting, ERG)…"
                />
              </div>
            </div>

            <div class="questions-list">
              <div
                v-for="q in filteredQuestionsList"
                :key="q.field"
                class="question-analytics-card"
              >
                <div class="qac-top">
                  <div class="qac-identifiers">
                    <span class="qac-num-badge">{{ q.field.toUpperCase() }}</span>
                    <span class="qac-section-tag">{{ q.sectionTitle }}</span>
                    <span class="qac-short-tag">{{ q.short }}</span>
                  </div>
                  <div class="qac-flag-wrap">
                    <span v-if="q.stats.yesPct >= 60" class="flag-pill flag-strong">
                      ✓ Strong Practice ({{ q.stats.yesPct }}% Yes)
                    </span>
                    <span v-else-if="q.stats.noPct >= 40" class="flag-pill flag-gap">
                      ⚠️ Critical Gap ({{ q.stats.noPct }}% No)
                    </span>
                    <span v-else-if="q.stats.notSurePct >= 40" class="flag-pill flag-awareness">
                      ❓ Low Awareness ({{ q.stats.notSurePct }}% Not Sure)
                    </span>
                    <span v-else class="flag-pill flag-transition">
                      ⚡ Developing
                    </span>
                  </div>
                </div>

                <p class="qac-question-text">{{ q.text }}</p>

                <!-- Stacked Distribution Bar -->
                <div class="qac-bar-container">
                  <div class="qac-distribution-bar">
                    <div
                      v-if="q.stats.yesPct > 0"
                      class="bar-seg bar-yes"
                      :style="{ width: `${q.stats.yesPct}%` }"
                      :title="`Yes: ${q.stats.yes} (${q.stats.yesPct}%)`"
                    ></div>
                    <div
                      v-if="q.stats.partiallyPct > 0"
                      class="bar-seg bar-partially"
                      :style="{ width: `${q.stats.partiallyPct}%` }"
                      :title="`Partially: ${q.stats.partially} (${q.stats.partiallyPct}%)`"
                    ></div>
                    <div
                      v-if="q.stats.noPct > 0"
                      class="bar-seg bar-no"
                      :style="{ width: `${q.stats.noPct}%` }"
                      :title="`No: ${q.stats.no} (${q.stats.noPct}%)`"
                    ></div>
                    <div
                      v-if="q.stats.notSurePct > 0"
                      class="bar-seg bar-notsure"
                      :style="{ width: `${q.stats.notSurePct}%` }"
                      :title="`Not Sure / NA: ${q.stats.notSure} (${q.stats.notSurePct}%)`"
                    ></div>
                  </div>

                  <div class="qac-bar-legend">
                    <span class="leg-item leg-yes">
                      <span class="leg-dot"></span>
                      <strong>Yes:</strong> {{ q.stats.yes }} ({{ q.stats.yesPct }}%)
                    </span>
                    <span class="leg-item leg-partially">
                      <span class="leg-dot"></span>
                      <strong>Partially:</strong> {{ q.stats.partially }} ({{ q.stats.partiallyPct }}%)
                    </span>
                    <span class="leg-item leg-no">
                      <span class="leg-dot"></span>
                      <strong>No:</strong> {{ q.stats.no }} ({{ q.stats.noPct }}%)
                    </span>
                    <span class="leg-item leg-notsure">
                      <span class="leg-dot"></span>
                      <strong>Not Sure:</strong> {{ q.stats.notSure }} ({{ q.stats.notSurePct }}%)
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- TAB 4: EMPLOYEE SUBMISSIONS & WEIGHTS -->
          <section v-if="activeTab === 'respondents'" class="respondents-view animate-fade">
            <div class="resp-table-header-box">
              <div>
                <h3 class="resp-table-title">Individual Employee Audit Responses</h3>
                <p class="resp-table-sub">Click any respondent to expand their detailed 40-question breakdown, or adjust scoring weights.</p>
              </div>
              <div class="resp-table-actions">
                <button class="btn btn-outline btn-sm" @click="exportOrgCSV">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                  Export All Submissions
                </button>
              </div>
            </div>

            <div class="table-container">
              <table class="modern-resp-table">
                <thead>
                  <tr>
                    <th style="width: 25%">Respondent &amp; Designation</th>
                    <th style="width: 20%">Function &amp; Role</th>
                    <th style="width: 15%">Score</th>
                    <th style="width: 15%" v-if="!selectedOrg.is_virtual">Audit Weight</th>
                    <th style="width: 15%">Demographics</th>
                    <th style="width: 10%; text-align: center">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <template v-for="r in detail.respondents" :key="r.id">
                    <tr
                      class="resp-row"
                      :class="{ 'expanded': expandedRespondentId === r.id }"
                      @click="toggleRespondent(r.id)"
                    >
                      <td>
                        <div class="resp-cell-user">
                          <span class="resp-chevron" :class="{ 'rotated': expandedRespondentId === r.id }">▶</span>
                          <div>
                            <span class="resp-user-name">{{ r.name || 'Anonymous' }}</span>
                            <span class="resp-user-email">{{ r.email }}</span>
                          </div>
                        </div>
                      </td>

                      <td>
                        <div class="resp-role-cell">
                          <span class="role-bold">{{ r.designation || r.answers?.role || '—' }}</span>
                          <span class="func-muted">{{ r.answers?.function || 'General' }}</span>
                        </div>
                      </td>

                      <td>
                        <div class="resp-score-cell">
                          <span class="score-badge-inline">{{ r.overall_avg }}/20</span>
                          <span class="score-level-inline" :class="levelClass(r.overall_level)">
                            {{ shortLevel(r.overall_level) }}
                          </span>
                        </div>
                      </td>

                      <td v-if="!selectedOrg.is_virtual" @click.stop>
                        <select
                          :value="r.weight"
                          @change="updateWeight(r.id, $event.target.value)"
                          class="modern-weight-select"
                          title="Multiplier for aggregated org score"
                        >
                          <option value="0.5">0.5× (Light)</option>
                          <option value="1">1.0× (Standard)</option>
                          <option value="2">2.0× (Double)</option>
                          <option value="3">3.0× (Triple)</option>
                        </select>
                      </td>

                      <td>
                        <div class="demog-tags">
                          <span v-if="r.answers?.is_neurodivergent === 'Yes'" class="dtag dtag-nd">ND</span>
                          <span v-else-if="r.answers?.is_neurodivergent === 'No'" class="dtag dtag-nt">NT</span>
                          <span v-if="r.answers?.is_pwd === 'Yes'" class="dtag dtag-pwd">PwD</span>
                          <span v-if="r.answers?.gender" class="dtag dtag-gender">{{ r.answers.gender }}</span>
                        </div>
                      </td>

                      <td style="text-align: center" @click.stop>
                        <button
                          class="btn-icon-direct"
                          title="Send Direct Message to this Respondent"
                          @click="openMsgPanel(r)"
                        >
                          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                            <polyline points="22,6 12,12 2,6"/>
                          </svg>
                        </button>
                      </td>
                    </tr>

                    <!-- Expanded Detail Row -->
                    <tr v-if="expandedRespondentId === r.id" class="resp-expand-row">
                      <td :colspan="!selectedOrg.is_virtual ? 6 : 5" class="resp-expand-cell">
                        <div class="resp-expand-card">
                          <div class="rec-header">
                            <h4>Individual Section Breakdown — {{ r.name }}</h4>
                            <span class="rec-date">Submitted: {{ formatDate(r.submitted_at) }}</span>
                          </div>
                          <ScoreTable :data="r" />
                        </div>
                      </td>
                    </tr>
                  </template>
                </tbody>
              </table>
            </div>
          </section>

          <!-- TAB 5: SEND EXECUTIVE ORG REPORT -->
          <section v-if="activeTab === 'report'" class="report-view animate-fade">
            <div v-if="selectedOrg.is_virtual" class="report-virtual-warning">
              <div class="rvw-icon">⚠️</div>
              <div class="rvw-text">
                <h4>Organisation Linking Required for Automated Delivery</h4>
                <p>
                  To generate official signed email links and deliver the aggregated report to stakeholders,
                  please click <strong>"Link &amp; Create Org"</strong> first.
                </p>
                <button class="btn btn-secondary-action btn-sm" @click="createOrg(selectedOrg)" :disabled="creatingOrg">
                  {{ creatingOrg ? 'Linking…' : 'Link & Create Organisation Account Now' }}
                </button>
              </div>
            </div>

            <div class="report-panel-layout">
              <div class="rpl-form-card">
                <h3 class="rpl-title">Email Dispatch Settings</h3>
                <p class="rpl-sub">Select executive recipients who will receive the full organisational score breakdown.</p>

                <div class="field-block">
                  <label class="field-label">Subject Line</label>
                  <input
                    v-model="report.subject"
                    type="text"
                    class="modern-input"
                    placeholder="Subject line for email report…"
                  />
                </div>

                <div class="field-block">
                  <div class="recipients-header">
                    <label class="field-label">Recipients ({{ report.selected.length }}/{{ report.respondents.length }})</label>
                    <label class="select-all-toggle">
                      <input type="checkbox" :checked="allChecked" @change="toggleAll" />
                      Select All
                    </label>
                  </div>

                  <div class="recipients-scroll-box">
                    <label
                      v-for="r in report.respondents"
                      :key="r.id"
                      class="recipient-check-row"
                    >
                      <input type="checkbox" :value="r" v-model="report.selected" />
                      <div class="rcr-text">
                        <span class="rcr-name">{{ r.name || 'Anonymous' }}</span>
                        <span class="rcr-email">{{ r.email }}</span>
                      </div>
                    </label>
                  </div>
                </div>

                <div v-if="report.error" class="error-banner">{{ report.error }}</div>
                <div v-if="report.success" class="success-banner">{{ report.success }}</div>

                <button
                  class="btn btn-primary-cta btn-full"
                  :disabled="!report.selected.length || report.sending || selectedOrg.is_virtual"
                  @click="sendOrgReport"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
                  {{ report.sending ? 'Delivering Report…' : `Send to ${report.selected.length} Recipient${report.selected.length !== 1 ? 's' : ''}` }}
                </button>
              </div>

              <div class="rpl-preview-card">
                <div class="preview-header">
                  <span class="ph-title">Live Email Report Preview</span>
                  <button
                    class="btn-refresh-preview"
                    @click="fetchPreview(selectedOrg.id)"
                    :disabled="report.loadingPreview || selectedOrg.is_virtual"
                    title="Reload preview"
                  >
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
                    Refresh Preview
                  </button>
                </div>

                <div v-if="report.loadingPreview" class="preview-loading-state">
                  <div class="spinner"></div>
                  <span>Generating live report HTML…</span>
                </div>

                <div v-else-if="report.previewHtml" class="iframe-container">
                  <iframe :srcdoc="report.previewHtml" sandbox="allow-same-origin" class="report-iframe"></iframe>
                </div>

                <div v-else class="preview-empty-state">
                  <p v-if="selectedOrg.is_virtual">Link this organisation account to generate an email preview.</p>
                  <p v-else>No preview available.</p>
                </div>
              </div>
            </div>
          </section>

        </div>
      </main>

    </div>

    <!-- Send Direct Message Modal -->
    <div v-if="msgPanel.open" class="modal-backdrop" @click.self="msgPanel.open = false">
      <div class="modal-card">
        <div class="modal-header">
          <div>
            <h3 class="modal-title">Send Direct Message</h3>
            <p class="modal-sub">To: <strong>{{ msgPanel.recipient?.name }}</strong> ({{ msgPanel.recipient?.email }})</p>
          </div>
          <button class="btn-close-modal" @click="msgPanel.open = false">✕</button>
        </div>

        <div class="modal-body">
          <div class="field-block">
            <label class="field-label">Subject</label>
            <input v-model="msgPanel.subject" type="text" class="modern-input" placeholder="Message subject…" />
          </div>

          <div class="field-block">
            <label class="field-label">Message</label>
            <textarea v-model="msgPanel.body" rows="5" class="modern-textarea" placeholder="Write your message to the respondent…"></textarea>
          </div>

          <div v-if="msgPanel.error" class="error-banner">{{ msgPanel.error }}</div>
          <div v-if="msgPanel.success" class="success-banner">{{ msgPanel.success }}</div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-outline" @click="msgPanel.open = false">Cancel</button>
          <button
            class="btn btn-primary-cta"
            :disabled="!msgPanel.subject || !msgPanel.body || msgPanel.sending"
            @click="sendMessage"
          >
            {{ msgPanel.sending ? 'Sending…' : 'Send Message' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Toast Popup -->
    <div v-if="toast.show" class="toast-popup" :class="toast.type">
      {{ toast.message }}
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue';
import ScoreTable from '../components/ScoreTable.vue';
import { DEFAULT_SECTIONS } from '../utils/defaultSections.js';
import { downloadFilteredSubmissions } from '../utils/csvExport.js';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

function getAuthHeaders() {
  const token = sessionStorage.getItem('nd_auth_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// State
const loading = ref(true);
const orgs = ref([]);
const selectedOrg = ref(null);
const detail = ref(null);
const loadingDetail = ref(false);
const liveScore = ref(null);
const creatingOrg = ref(false);
const expandedRespondentId = ref(null);

// Navigation & Filters
const activeTab = ref('pillars');
const orgSearch = ref('');
const orgFilter = ref('all');
const selectedSegmentKey = ref('function');
const selectedInputPillar = ref('all');
const inputSearchQuery = ref('');
const mobileDirectoryOpen = ref(false);

// Toast
const toast = reactive({ show: false, message: '', type: 'success' });
function showToast(message, type = 'success') {
  toast.message = message;
  toast.type = type;
  toast.show = true;
  setTimeout(() => { toast.show = false; }, 3500);
}

// Send Report State
const report = reactive({
  respondents: [],
  selected: [],
  subject: '',
  sending: false,
  error: '',
  success: '',
  previewHtml: '',
  loadingPreview: false,
});

// Direct Message State
const msgPanel = reactive({
  open: false,
  recipient: null,
  subject: '',
  body: '',
  sending: false,
  error: '',
  success: '',
});

// Demographic Segment Config
const segmentOptions = [
  { key: 'function', label: 'Department / Function', icon: '🏢' },
  { key: 'role', label: 'Seniority & Role', icon: '👔' },
  { key: 'is_neurodivergent', label: 'Neurodiversity Status', icon: '🧠' },
  { key: 'is_pwd', label: 'Disability Status (PwD)', icon: '♿' },
  { key: 'gender', label: 'Gender Diversity', icon: '⚧' },
];

function getMonogram(name) {
  if (!name) return 'O';
  const clean = name.replace(/[^a-zA-Z0-9\s]/g, '').trim();
  const words = clean.split(/\s+/);
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase();
  }
  return clean.slice(0, 2).toUpperCase() || 'O';
}

const MONO_COLORS = ['#161057', '#04907C', '#E05A47', '#4338CA', '#0284C7', '#B45309', '#0F766E'];
function getMonogramColor(name) {
  if (!name) return MONO_COLORS[0];
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  return MONO_COLORS[Math.abs(hash) % MONO_COLORS.length];
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  } catch {
    return dateStr;
  }
}

function levelClass(level) {
  if (!level) return '';
  const l = level.toLowerCase();
  if (l.includes('1') || l.includes('foundational')) return 'level-foundational';
  if (l.includes('2') || l.includes('early')) return 'level-early';
  if (l.includes('3') || l.includes('developing')) return 'level-developing';
  if (l.includes('4') || l.includes('proficient')) return 'level-proficient';
  return 'level-leading';
}

function shortLevel(level) {
  if (!level) return '';
  if (level.includes('1')) return 'L1 Foundational';
  if (level.includes('2')) return 'L2 Early Progress';
  if (level.includes('3')) return 'L3 Developing';
  if (level.includes('4')) return 'L4 Proficient';
  return 'L5 Leading';
}

function getScoreColorClass(score) {
  if (score == null) return 'text-muted';
  if (score >= 14) return 'score-high';
  if (score >= 8) return 'score-med';
  return 'score-low';
}

function getSectionLabelShort(key) {
  const map = {
    lc: 'Leadership',
    ro: 'Recruitment',
    we: 'Work Environment',
    be: 'Sensory & Built',
    tm: 'Talent & Dev',
    ca: 'Communication',
    pc: 'Products & CX',
    sp: 'Procurement'
  };
  return map[key] || key.toUpperCase();
}

// Pure Weighted Scoring Helper
function computeOrgScores(respondents) {
  if (!respondents || respondents.length === 0) return null;
  const totalWeight = respondents.reduce((acc, r) => acc + (parseFloat(r.weight) || 1.0), 0);
  if (totalWeight === 0) return null;

  const orgAvg = respondents.reduce((acc, r) => acc + ((parseFloat(r.overall_avg) || 0) * (parseFloat(r.weight) || 1.0)), 0) / totalWeight;

  const sectionKeys = ['lc', 'ro', 'we', 'be', 'tm', 'ca', 'pc', 'sp'];
  const sectionAvgs = {};
  sectionKeys.forEach(k => {
    sectionAvgs[k] = respondents.reduce((acc, r) => acc + ((parseFloat(r[`${k}_score`]) || 0) * (parseFloat(r.weight) || 1.0)), 0) / totalWeight;
  });

  function getLevel(s) {
    if (s <= 6) return 'Level 1 — Foundational';
    if (s <= 14) return 'Level 2 — Early Progress';
    return 'Level 3 — Developing';
  }

  const sectionLevels = {};
  sectionKeys.forEach(k => {
    sectionLevels[k] = getLevel(sectionAvgs[k]);
  });

  return {
    org_avg: Math.round(orgAvg * 100) / 100,
    org_level: getLevel(orgAvg),
    respondent_count: respondents.length,
    total_weight: totalWeight,
    section_avgs: {
      lc: Math.round(sectionAvgs.lc * 100) / 100,
      ro: Math.round(sectionAvgs.ro * 100) / 100,
      we: Math.round(sectionAvgs.we * 100) / 100,
      be: Math.round(sectionAvgs.be * 100) / 100,
      tm: Math.round(sectionAvgs.tm * 100) / 100,
      ca: Math.round(sectionAvgs.ca * 100) / 100,
      pc: Math.round(sectionAvgs.pc * 100) / 100,
      sp: Math.round(sectionAvgs.sp * 100) / 100,
    },
    section_levels: sectionLevels,
    respondents: respondents.map(r => ({
      ...r,
      weighted_contribution_pct: Math.round(((parseFloat(r.weight) || 1.0) / totalWeight) * 1000) / 10
    }))
  };
}

// Computed
const currentScore = computed(() => {
  return liveScore.value || (selectedOrg.value ? {
    org_avg: selectedOrg.value.org_avg,
    org_level: selectedOrg.value.org_level,
    respondent_count: selectedOrg.value.respondent_count,
    section_avgs: {},
    section_levels: {},
  } : null);
});

const orgsWithSubsCount = computed(() => orgs.value.filter(o => o.respondent_count > 0).length);
const linkedOrgsCount = computed(() => orgs.value.filter(o => !o.is_virtual).length);
const unlinkedOrgsCount = computed(() => orgs.value.filter(o => o.is_virtual).length);

const filteredOrgs = computed(() => {
  let list = orgs.value;

  if (orgSearch.value.trim()) {
    const q = orgSearch.value.toLowerCase().trim();
    list = list.filter(o => o.name.toLowerCase().includes(q));
  }

  if (orgFilter.value === 'with_submissions') {
    list = list.filter(o => o.respondent_count > 0);
  } else if (orgFilter.value === 'linked') {
    list = list.filter(o => !o.is_virtual);
  } else if (orgFilter.value === 'unlinked') {
    list = list.filter(o => o.is_virtual);
  }

  return list;
});

const pillarScorecards = computed(() => {
  const avgs = currentScore.value?.section_avgs || {};
  const levels = currentScore.value?.section_levels || {};

  return DEFAULT_SECTIONS.map(s => {
    const score = avgs[s.id] != null ? avgs[s.id] : 0;
    const level = levels[s.id] || (score <= 6 ? 'Level 1 — Foundational' : score <= 14 ? 'Level 2 — Early Progress' : 'Level 3 — Developing');
    return {
      id: s.id,
      title: s.title,
      icon: s.icon,
      summary: s.summary,
      points: s.points,
      score: score,
      level: level
    };
  });
});

const topPillars = computed(() => {
  return [...pillarScorecards.value].sort((a, b) => b.score - a.score).slice(0, 2);
});

const lowestPillars = computed(() => {
  return [...pillarScorecards.value].sort((a, b) => a.score - b.score).slice(0, 2);
});

const activeSegmentData = computed(() => {
  const respondents = detail.value?.respondents || [];
  if (!respondents.length) return [];

  const dimKey = selectedSegmentKey.value;
  const groups = {};

  respondents.forEach(r => {
    let rawVal = r.answers?.[dimKey] ?? r[dimKey];
    if (rawVal === undefined || rawVal === null || rawVal === '') {
      rawVal = 'Not Specified';
    }
    const val = String(rawVal).trim();
    if (!groups[val]) {
      groups[val] = {
        name: val,
        count: 0,
        scores: [],
        sectionScores: { lc: [], ro: [], we: [], be: [], tm: [], ca: [], pc: [], sp: [] }
      };
    }
    groups[val].count++;
    if (r.overall_avg != null) groups[val].scores.push(parseFloat(r.overall_avg));
    ['lc', 'ro', 'we', 'be', 'tm', 'ca', 'pc', 'sp'].forEach(k => {
      const s = r[`${k}_score`];
      if (s != null) groups[val].sectionScores[k].push(parseFloat(s));
    });
  });

  const orgAvg = currentScore.value?.org_avg || 0;

  return Object.values(groups).map(g => {
    const avg = g.scores.length ? (g.scores.reduce((a, b) => a + b, 0) / g.scores.length) : 0;
    const roundedAvg = Math.round(avg * 100) / 100;
    const delta = Math.round((roundedAvg - orgAvg) * 100) / 100;

    const sectionAvgs = {};
    Object.keys(g.sectionScores).forEach(k => {
      const arr = g.sectionScores[k];
      sectionAvgs[k] = arr.length ? Math.round((arr.reduce((a, b) => a + b, 0) / arr.length) * 10) / 10 : 0;
    });

    return {
      name: g.name,
      count: g.count,
      pctOfTotal: Math.round((g.count / respondents.length) * 100),
      avgScore: roundedAvg,
      delta,
      sectionAvgs,
    };
  }).sort((a, b) => b.count - a.count);
});

const perceptionGapNotice = computed(() => {
  const respondents = detail.value?.respondents || [];
  if (respondents.length < 2) return null;

  if (selectedSegmentKey.value === 'is_neurodivergent') {
    const ndGroup = activeSegmentData.value.find(g => g.name.toLowerCase() === 'yes');
    const ntGroup = activeSegmentData.value.find(g => g.name.toLowerCase() === 'no');
    if (ndGroup && ntGroup) {
      const diff = Math.round((ntGroup.avgScore - ndGroup.avgScore) * 100) / 100;
      if (Math.abs(diff) >= 0.5) {
        return {
          title: diff > 0 ? 'Perception Gap: Neurotypical vs Neurodivergent' : 'Higher Rating Among Neurodivergent Staff',
          desc: diff > 0
            ? `Neurodivergent staff rated the workplace ${Math.abs(diff)} points lower on average than neurotypical peers.`
            : `Neurodivergent team members rated inclusion ${Math.abs(diff)} points higher than neurotypical colleagues.`,
          delta: `${diff > 0 ? '-' : '+'}${Math.abs(diff)} pts`
        };
      }
    }
  } else if (selectedSegmentKey.value === 'role') {
    const leadGroup = activeSegmentData.value.find(g => g.name.toLowerCase().includes('lead') || g.name.toLowerCase().includes('exec') || g.name.toLowerCase().includes('c-suite'));
    const icGroup = activeSegmentData.value.find(g => g.name.toLowerCase().includes('contributor') || g.name.toLowerCase().includes('individual'));
    if (leadGroup && icGroup) {
      const diff = Math.round((leadGroup.avgScore - icGroup.avgScore) * 100) / 100;
      if (Math.abs(diff) >= 0.5) {
        return {
          title: 'Leadership Alignment Variance',
          desc: `Senior leadership rates the workplace index ${diff > 0 ? `${diff} points higher` : `${Math.abs(diff)} points lower`} than individual contributors.`,
          delta: `${diff > 0 ? '+' : '-'}${Math.abs(diff)} pts`
        };
      }
    }
  }
  return null;
});

const allQuestionsFlat = computed(() => {
  const respondents = detail.value?.respondents || [];
  const list = [];

  DEFAULT_SECTIONS.forEach(sec => {
    sec.questions.forEach(q => {
      let yes = 0, partially = 0, no = 0, notSure = 0;
      respondents.forEach(r => {
        const ans = String(r[q.field] || r.answers?.[q.field] || '').trim().toLowerCase();
        if (ans === 'yes') yes++;
        else if (ans === 'partially') partially++;
        else if (ans === 'no') no++;
        else if (ans === 'not sure' || ans === 'not_sure') notSure++;
        else if (ans) notSure++;
      });
      const total = yes + partially + no + notSure || respondents.length || 1;
      list.push({
        field: q.field,
        sectionId: sec.id,
        sectionTitle: sec.title,
        short: q.short,
        text: q.text,
        stats: {
          yes,
          partially,
          no,
          notSure,
          total,
          yesPct: Math.round((yes / total) * 100),
          partiallyPct: Math.round((partially / total) * 100),
          noPct: Math.round((no / total) * 100),
          notSurePct: Math.round((notSure / total) * 100),
        }
      });
    });
  });

  return list;
});

const filteredQuestionsList = computed(() => {
  let list = allQuestionsFlat.value;
  if (selectedInputPillar.value !== 'all') {
    list = list.filter(q => q.sectionId === selectedInputPillar.value);
  }
  if (inputSearchQuery.value.trim()) {
    const q = inputSearchQuery.value.toLowerCase().trim();
    list = list.filter(item =>
      item.text.toLowerCase().includes(q) ||
      item.short.toLowerCase().includes(q) ||
      item.field.toLowerCase().includes(q)
    );
  }
  return list;
});

// Fetch Operations
async function fetchOrgs() {
  loading.value = true;
  try {
    const res = await fetch(`${API_BASE}/manage/orgs`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to load organisations');
    orgs.value = await res.json();
    if (orgs.value.length > 0 && !selectedOrg.value) {
      const preferred = orgs.value.find(o => o.respondent_count > 0) || orgs.value[0];
      selectOrg(preferred);
    }
  } catch (e) {
    console.error(e);
    showToast('Failed to load organisations', 'error');
  } finally {
    loading.value = false;
  }
}

async function fetchDetail(org) {
  loadingDetail.value = true;
  detail.value = null;
  liveScore.value = null;
  try {
    if (org.is_virtual) {
      const params = new URLSearchParams({ company_name: org.name });
      const res = await fetch(`${API_BASE}/manage/orgs/unlinked?${params}`, { headers: getAuthHeaders() });
      if (!res.ok) throw new Error('Failed to load unlinked submissions');
      const subs = await res.json();
      const respondents = subs.map(s => ({ ...s, weight: 1.0 }));
      const computedScores = computeOrgScores(respondents);
      detail.value = { respondents, scores: computedScores };
      liveScore.value = computedScores;
    } else {
      const res = await fetch(`${API_BASE}/manage/orgs/${org.id}`, { headers: getAuthHeaders() });
      if (!res.ok) throw new Error('Failed to load organisation detail');
      const data = await res.json();
      detail.value = data;
      liveScore.value = data.scores || computeOrgScores(data.respondents);
    }
  } catch (e) {
    console.error(e);
    showToast('Failed to load organisation detail', 'error');
  } finally {
    loadingDetail.value = false;
  }
}

async function fetchPreview(orgId) {
  if (selectedOrg.value?.is_virtual) return;
  report.loadingPreview = true;
  report.previewHtml = '';
  try {
    const res = await fetch(`${API_BASE}/manage/orgs/${orgId}/report-preview`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to load report preview');
    const data = await res.json();
    report.previewHtml = data.html;
  } catch (e) {
    console.error(e);
  } finally {
    report.loadingPreview = false;
  }
}

async function selectOrg(org) {
  mobileDirectoryOpen.value = false;
  if (selectedOrg.value?.id === org.id) return;
  selectedOrg.value = org;
  expandedRespondentId.value = null;
  report.error = '';
  report.success = '';
  msgPanel.open = false;
  await fetchDetail(org);
  initReportForm();
}

function toggleRespondent(id) {
  expandedRespondentId.value = expandedRespondentId.value === id ? null : id;
}

function initReportForm() {
  const respondents = detail.value?.respondents ?? [];
  report.respondents = respondents;
  report.selected = [...respondents];
  report.subject = `${selectedOrg.value?.name} — NIWI Neuro-Inclusive Workplace Index Executive Summary`;
  report.error = '';
  report.success = '';
  report.previewHtml = '';
  if (!selectedOrg.value?.is_virtual) {
    fetchPreview(selectedOrg.value.id);
  }
}

watch(() => activeTab.value, (tab) => {
  if (tab === 'report') initReportForm();
});

const allChecked = computed(() =>
  report.respondents.length > 0 && report.selected.length === report.respondents.length
);

function toggleAll(e) {
  report.selected = e.target.checked ? [...report.respondents] : [];
}

async function sendOrgReport() {
  if (!selectedOrg.value || selectedOrg.value.is_virtual) return;
  report.sending = true;
  report.error = '';
  report.success = '';
  try {
    const res = await fetch(`${API_BASE}/manage/orgs/${selectedOrg.value.id}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({
        subject: report.subject,
        body: '',
        recipients: report.selected.map(r => ({ email: r.email, name: r.name })),
        is_org_report: true,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to dispatch report');
    report.success = `Successfully sent executive report to ${report.selected.length} recipient(s).`;
    showToast(`Executive report dispatched to ${report.selected.length} recipient(s).`);
  } catch (e) {
    report.error = e.message;
  } finally {
    report.sending = false;
  }
}

async function updateWeight(submissionId, weight) {
  if (selectedOrg.value?.is_virtual) {
    const r = detail.value?.respondents.find(r => r.id === submissionId);
    if (r) r.weight = parseFloat(weight);
    const updated = computeOrgScores(detail.value.respondents);
    liveScore.value = updated;
    showToast('Updated local weighting.');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/manage/orgs/${selectedOrg.value.id}/links/${submissionId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({ weight: parseFloat(weight) }),
    });
    if (!res.ok) throw new Error('Failed to update weight');
    const data = await res.json();
    liveScore.value = data.scores;
    const r = detail.value?.respondents.find(r => r.id === submissionId);
    if (r) r.weight = parseFloat(weight);
    const org = orgs.value.find(o => o.id === selectedOrg.value.id);
    if (org && data.scores) {
      org.org_avg = data.scores.org_avg;
      org.org_level = data.scores.org_level;
    }
    showToast('Respondent weight updated.');
  } catch (e) {
    console.error(e);
    showToast('Failed to update weight', 'error');
  }
}

function openMsgPanel(recipient) {
  msgPanel.recipient = recipient;
  msgPanel.subject = `${selectedOrg.value?.name} — Regarding your NIWI Audit Submission`;
  msgPanel.body = `Hello ${recipient.name || 'there'},

Thank you for contributing to the Neurodiversity & Inclusion Audit for ${selectedOrg.value?.name}.

`;
  msgPanel.error = '';
  msgPanel.success = '';
  msgPanel.sending = false;
  msgPanel.open = true;
}

async function sendMessage() {
  msgPanel.sending = true;
  msgPanel.error = '';
  msgPanel.success = '';
  try {
    const res = await fetch(`${API_BASE}/manage/orgs/${selectedOrg.value.id}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({
        subject: msgPanel.subject,
        body: msgPanel.body,
        recipients: [{ email: msgPanel.recipient.email, name: msgPanel.recipient.name }],
        is_org_report: false,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to send message');
    msgPanel.success = 'Message successfully delivered.';
    showToast(`Message sent to ${msgPanel.recipient.email}`);
    setTimeout(() => { msgPanel.open = false; }, 1600);
  } catch (e) {
    msgPanel.error = e.message;
  } finally {
    msgPanel.sending = false;
  }
}

async function createOrg(org) {
  creatingOrg.value = true;
  try {
    const res = await fetch(`${API_BASE}/manage/orgs/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({ company_name: org.name }),
    });
    if (!res.ok) throw new Error('Failed to create and link organisation');
    const data = await res.json();
    showToast(`Created official organisation account and linked ${data.linked_count} respondents!`);
    await fetchOrgs();
    const newOrg = orgs.value.find(o => o.name.toLowerCase() === org.name.toLowerCase() && !o.is_virtual);
    if (newOrg) {
      await selectOrg(newOrg);
    }
  } catch (e) {
    console.error(e);
    showToast(e.message, 'error');
  } finally {
    creatingOrg.value = false;
  }
}

function exportOrgCSV() {
  const respondents = detail.value?.respondents;
  if (!respondents || !respondents.length) {
    showToast('No submissions to export', 'error');
    return;
  }
  const cleanName = (selectedOrg.value?.name || 'Organisation').replace(/[^a-zA-Z0-9_-]/g, '_');
  downloadFilteredSubmissions(respondents, cleanName, 'Full_Analysis');
  showToast('Detailed CSV downloaded.');
}

function copyOrgInviteLink() {
  const auditUrl = `${window.location.origin}/`;
  navigator.clipboard.writeText(auditUrl).then(() => {
    showToast('Assessment URL copied to clipboard!');
  });
}

onMounted(fetchOrgs);
</script>

<style scoped>
/* Page Root */
.orgs-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  width: 100%;
  color: var(--primary, #161057);
}

.animate-in {
  animation: pageFadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.animate-fade {
  animation: tabFade 0.25s ease-out;
}

@keyframes pageFadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes tabFade {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ==========================================================================
   Hero Section (Compact & Centered matching Overview)
   ========================================================================== */
.hero-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 16px 0 8px;
}

.hero-content {
  max-width: 860px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.hero-title {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 2.35rem;
  font-weight: 800;
  color: var(--primary, #161057);
  letter-spacing: -0.03em;
  margin-bottom: 6px;
  line-height: 1.15;
}

.hero-subtitle {
  font-family: var(--font-body);
  font-size: 0.95rem;
  color: #64748B;
  max-width: 620px;
  margin-bottom: 20px;
  line-height: 1.5;
}

/* Unified Search Banner Card */
.search-banner-card {
  display: flex;
  align-items: center;
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 12px;
  box-shadow: 3px 3px 0px rgba(22, 16, 87, 0.12);
  padding: 6px 10px 6px 16px;
  width: 100%;
  max-width: 780px;
  transition: all 0.2s ease;
}

.search-banner-card:focus-within {
  box-shadow: 4px 4px 0px rgba(22, 16, 87, 0.2);
}

.search-input-group {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1.4;
}

.search-icon {
  color: #64748B;
  flex-shrink: 0;
}

.search-input-group input {
  width: 100%;
  border: none;
  outline: none;
  font-family: var(--font-body);
  font-size: 0.95rem;
  color: var(--primary, #161057);
  background: transparent;
}

.search-input-group input::placeholder {
  color: #94A3B8;
}

.btn-clear-search {
  background: none;
  border: none;
  color: #94A3B8;
  cursor: pointer;
  padding: 4px;
}

.search-divider {
  width: 1px;
  height: 28px;
  background: #CBD5E1;
  margin: 0 12px;
}

.search-filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #64748B;
}

.search-filter-group select {
  border: none;
  outline: none;
  background: transparent;
  font-family: var(--font-body);
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--primary, #161057);
  cursor: pointer;
  padding-right: 8px;
}

/* ==========================================================================
   Main 2-Column Dashboard Grid (matches Overview.vue & Reference Layout)
   ========================================================================== */
.main-orgs-grid {
  display: grid;
  grid-template-columns: 310px 1fr;
  gap: 24px;
  align-items: start;
}

@media (max-width: 1024px) {
  .main-orgs-grid {
    grid-template-columns: 1fr;
  }
}

/* ==========================================================================
   LEFT COLUMN: Organisation Directory Card (like Filters Card in Reference)
   ========================================================================== */
.org-sidebar-card {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 14px;
  box-shadow: 3px 3px 0px rgba(22, 16, 87, 0.1);
  padding: 18px 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  position: sticky;
  top: 90px;
  max-height: calc(100vh - 110px);
  overflow: hidden;
}

.osc-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding-bottom: 10px;
  border-bottom: 1.5px solid #F1F5F9;
  gap: 8px;
}

.osc-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mobile-dir-toggle-btn {
  display: none;
  align-items: center;
  padding: 6px 12px;
  background: #FAF9F5;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--primary, #161057);
  cursor: pointer;
  min-height: 38px;
}

.osc-mobile-selected {
  display: none;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #FAF9F5;
  border-radius: 8px;
  font-size: 0.85rem;
  border: 1px solid rgba(22, 16, 87, 0.08);
}

.oms-label {
  color: #64748B;
  font-size: 0.78rem;
}

.oms-name {
  color: var(--primary, #161057);
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.oms-badge {
  font-weight: 800;
  color: #04907C;
  font-family: monospace;
}

.osc-collapsible-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.osc-title {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--primary, #161057);
}

.osc-subtitle {
  font-size: 0.78rem;
  color: #64748B;
  display: block;
}

.osc-badge {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  background: #F1F5F9;
  color: #475569;
  text-transform: capitalize;
}

.sidebar-filter-pills {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.s-pill {
  padding: 4px 10px;
  background: #F8FAFC;
  border: 1px solid #CBD5E1;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  transition: all 0.15s ease;
}

.s-pill:hover {
  border-color: var(--primary, #161057);
  color: var(--primary, #161057);
}

.s-pill.active {
  background: var(--primary, #161057);
  color: #FFFFFF;
  border-color: var(--primary, #161057);
}

.sidebar-loading, .sidebar-empty {
  padding: 24px;
  text-align: center;
  font-size: 0.85rem;
  color: #64748B;
}

.sidebar-orgs-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
  padding-right: 4px;
  scrollbar-width: thin;
}

.sidebar-org-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: #FFFFFF;
  border: 1.5px solid #E2E8F0;
  border-radius: 10px;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s ease;
  width: 100%;
}

.sidebar-org-item:hover {
  border-color: var(--primary, #161057);
  background: #F8FAFC;
  transform: translateY(-1px);
}

.sidebar-org-item.active {
  background: #F8FAFC;
  border: 2px solid var(--primary, #161057);
  box-shadow: 2px 2px 0px var(--primary, #161057);
}

.soi-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.soi-monogram {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  color: #FFFFFF;
  font-weight: 700;
  font-size: 0.84rem;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.soi-text {
  min-width: 0;
  flex: 1;
}

.soi-name {
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--primary, #161057);
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.soi-count {
  font-size: 0.74rem;
  color: #64748B;
  display: block;
}

.soi-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  flex-shrink: 0;
  margin-left: 8px;
}

.soi-score {
  font-size: 0.82rem;
  font-weight: 700;
}

.soi-tag-pool {
  font-size: 0.68rem;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  background: #FEF3C7;
  color: #B45309;
  text-transform: uppercase;
}

.soi-tag-linked {
  font-size: 0.68rem;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(4, 144, 124, 0.12);
  color: #04907C;
  text-transform: uppercase;
}

.score-high { color: #04907C; }
.score-med { color: #B45309; }
.score-low { color: #E05A47; }

/* ==========================================================================
   RIGHT COLUMN: Main Workspace Area
   ========================================================================== */
.org-main-workspace {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

.org-hero-card {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 14px;
  box-shadow: 3px 3px 0px rgba(22, 16, 87, 0.1);
  padding: 22px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.org-hero-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.org-hero-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1 1 360px;
}

.org-hero-monogram {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  color: #FFFFFF;
  font-size: 1.45rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.org-hero-type-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 4px;
}

.pill-warning {
  padding: 2px 8px;
  background: #FEF3C7;
  color: #B45309;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
}

.pill-success {
  padding: 2px 8px;
  background: rgba(4, 144, 124, 0.12);
  color: #04907C;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
}

.pill-level {
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
}

.level-foundational { background: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }
.level-early { background: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; }
.level-developing { background: #E0E7FF; color: #3730A3; border: 1px solid #A5B4FC; }
.level-proficient { background: #CCFBF1; color: #115E59; border: 1px solid #5EEAD4; }
.level-leading { background: #D1FAE5; color: #065F46; border: 1px solid #6EE7B7; }

.org-hero-name {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 1.7rem;
  font-weight: 800;
  color: var(--primary, #161057);
  line-height: 1.2;
}

.org-hero-summary {
  font-size: 0.85rem;
  color: #64748B;
  margin-top: 2px;
}

.org-hero-right {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.hero-score-stat {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  text-align: right;
  min-width: 130px;
}

.stat-num-box {
  display: flex;
  align-items: baseline;
  gap: 3px;
}

.stat-num {
  font-size: 2rem;
  font-weight: 800;
  color: var(--primary, #161057);
  line-height: 1;
}

.stat-denom {
  font-size: 0.95rem;
  font-weight: 600;
  color: #94A3B8;
}

.stat-label {
  font-size: 0.74rem;
  font-weight: 700;
  text-transform: uppercase;
  color: #64748B;
  letter-spacing: 0.04em;
  margin-top: 2px;
}

.stat-progress-bar {
  width: 100%;
  height: 6px;
  background: #E2E8F0;
  border-radius: 999px;
  overflow: hidden;
  margin-top: 5px;
}

.stat-progress-fill {
  height: 100%;
  background: #04907C;
  border-radius: 999px;
  transition: width 0.4s ease;
}

.org-hero-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 700;
  font-size: 0.85rem;
  padding: 8px 16px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.btn-primary-cta {
  background: #E05A47;
  color: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  box-shadow: 2px 2px 0px var(--primary, #161057);
}

.btn-primary-cta:hover:not(:disabled) {
  background: #D04835;
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0px var(--primary, #161057);
}

.btn-secondary-action {
  background: #04907C;
  color: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  box-shadow: 2px 2px 0px var(--primary, #161057);
}

.btn-secondary-action:hover:not(:disabled) {
  background: #037A69;
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0px var(--primary, #161057);
}

.btn-outline {
  background: #FFFFFF;
  color: var(--primary, #161057);
  border: 1.5px solid var(--primary, #161057);
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.1);
}

.btn-outline:hover:not(:disabled) {
  background: #F8FAFC;
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0px rgba(22, 16, 87, 0.2);
}

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

.unlinked-notice-banner {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 14px;
  background: #FFFBEB;
  border: 1px solid #FCD34D;
  border-radius: 8px;
  font-size: 0.84rem;
  color: #92400E;
  line-height: 1.45;
}

/* ==========================================================================
   Navigation Tabs Bar
   ========================================================================== */
.analysis-tabs-nav {
  display: flex;
  gap: 6px;
  border-bottom: 2px solid #E2E8F0;
  padding-bottom: 2px;
  overflow-x: auto;
}

.nav-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  color: #64748B;
  font-weight: 700;
  font-size: 0.88rem;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
  margin-bottom: -2px;
}

.nav-tab-btn:hover {
  color: var(--primary, #161057);
}

.nav-tab-btn.active {
  color: var(--primary, #161057);
  border-bottom-color: var(--primary, #161057);
}

.tab-badge {
  padding: 1px 6px;
  background: #F1F5F9;
  color: #475569;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
}

.tab-count-pill {
  padding: 1px 6px;
  background: rgba(22, 16, 87, 0.08);
  color: var(--primary, #161057);
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
}

.tab-highlight-badge {
  padding: 1px 6px;
  background: rgba(4, 144, 124, 0.12);
  color: #04907C;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
}

/* Loading & Empty States */
.detail-loading-box, .no-respondents-card {
  padding: 40px;
  background: #FFFFFF;
  border: 1.5px solid #E2E8F0;
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 14px;
  color: #64748B;
}

.empty-icon-box {
  font-size: 2.2rem;
}

.spinner {
  width: 26px;
  height: 26px;
  border: 3px solid #E2E8F0;
  border-top-color: var(--primary, #161057);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ==========================================================================
   TAB 1: 8 Core Pillars Scorecard
   ========================================================================== */
.pillars-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.highlights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 14px;
}

.highlight-card {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 16px;
  border: 1.5px solid #E2E8F0;
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.06);
}

.strength-card {
  border-left: 5px solid #04907C;
}

.priority-card {
  border-left: 5px solid #E05A47;
}

.hl-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.hl-icon {
  font-size: 1.6rem;
}

.hl-title {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--primary, #161057);
}

.hl-sub {
  font-size: 0.78rem;
  color: #64748B;
}

.hl-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hl-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  background: #F8FAFC;
  border-radius: 6px;
}

.hl-item-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.hl-pillar-icon {
  color: var(--primary, #161057);
  font-weight: bold;
}

.hl-pillar-name {
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--primary, #161057);
}

.hl-item-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.hl-score-badge {
  font-size: 0.82rem;
  font-weight: 700;
  color: #04907C;
}

.hl-score-badge.priority {
  color: #E05A47;
}

.hl-tier-badge {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 999px;
}

.pillars-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.pillar-card {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 12px;
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.08);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: all 0.2s ease;
}

.pillar-card:hover {
  transform: translateY(-2px);
  box-shadow: 3px 3px 0px rgba(22, 16, 87, 0.14);
}

.pc-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.pc-icon-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pc-icon {
  font-size: 1.2rem;
  color: var(--primary, #161057);
}

.pc-title {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 0.98rem;
  font-weight: 700;
  color: var(--primary, #161057);
  line-height: 1.25;
}

.pc-category {
  font-size: 0.7rem;
  font-weight: 700;
  color: #64748B;
  text-transform: uppercase;
}

.pc-score-box {
  display: flex;
  align-items: baseline;
  gap: 2px;
  background: #F8FAFC;
  padding: 3px 8px;
  border-radius: 6px;
  border: 1px solid #E2E8F0;
}

.pc-score {
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--primary, #161057);
}

.pc-max {
  font-size: 0.75rem;
  color: #94A3B8;
  font-weight: 600;
}

.pc-bar-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.pc-bar-bg {
  width: 100%;
  height: 6px;
  background: #F1F5F9;
  border-radius: 999px;
  overflow: hidden;
}

.pc-bar-fill {
  height: 100%;
  background: #04907C;
  border-radius: 999px;
  transition: width 0.4s ease;
}

.pc-bar-labels {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pc-level-tag {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 999px;
}

.pc-pct {
  font-size: 0.75rem;
  font-weight: 700;
  color: #64748B;
}

.pc-summary {
  font-size: 0.82rem;
  color: #475569;
  line-height: 1.45;
}

.pc-key-points {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: auto;
  padding-top: 6px;
  border-top: 1px dashed #E2E8F0;
}

.pc-chip {
  font-size: 0.72rem;
  background: #F8FAFC;
  color: #475569;
  padding: 2px 6px;
  border-radius: 4px;
}

/* ==========================================================================
   TAB 2: Segment Analysis
   ========================================================================== */
.segments-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.segments-control-card {
  background: #FFFFFF;
  border: 1.5px solid #CBD5E1;
  border-radius: 12px;
  padding: 16px;
}

.scc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.scc-title {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--primary, #161057);
}

.scc-sub {
  font-size: 0.8rem;
  color: #64748B;
}

.segment-switcher {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.seg-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: #F8FAFC;
  border: 1.5px solid #CBD5E1;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
  transition: all 0.15s ease;
}

.seg-btn:hover {
  border-color: var(--primary, #161057);
  color: var(--primary, #161057);
}

.seg-btn.active {
  background: var(--primary, #161057);
  color: #FFFFFF;
  border-color: var(--primary, #161057);
}

.gap-alert-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  background: #FFFBEB;
  border: 1.5px solid #F59E0B;
  border-radius: 10px;
}

.gap-icon {
  font-size: 1.6rem;
  flex-shrink: 0;
}

.gap-text {
  flex: 1;
}

.gap-title {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 0.98rem;
  font-weight: 700;
  color: #92400E;
}

.gap-desc {
  font-size: 0.82rem;
  color: #78350F;
  margin-top: 2px;
  line-height: 1.4;
}

.gap-metric {
  text-align: right;
  flex-shrink: 0;
}

.gap-num {
  font-size: 1.35rem;
  font-weight: 800;
  color: #B45309;
  display: block;
  line-height: 1;
}

.gap-label {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  color: #92400E;
}

.segment-groups-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.segment-group-card {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 12px;
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.08);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sgc-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.sgc-title {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--primary, #161057);
}

.sgc-count-tag {
  font-size: 0.76rem;
  color: #64748B;
  display: block;
}

.sgc-score-badge {
  display: flex;
  align-items: baseline;
  gap: 2px;
  background: #F8FAFC;
  padding: 3px 8px;
  border-radius: 6px;
  border: 1px solid #E2E8F0;
}

.sgc-score {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--primary, #161057);
}

.sgc-denom {
  font-size: 0.8rem;
  color: #94A3B8;
  font-weight: 600;
}

.sgc-delta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 5px 10px;
  background: #F8FAFC;
  border-radius: 6px;
  font-size: 0.78rem;
}

.sgc-delta-label {
  color: #64748B;
}

.sgc-delta-val {
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 999px;
}

.sgc-delta-val.positive { background: rgba(4, 144, 124, 0.12); color: #04907C; }
.sgc-delta-val.negative { background: #FEE2E2; color: #B91C1C; }
.sgc-delta-val.neutral { background: #F1F5F9; color: #475569; }

.sgc-pillars-table-wrap {
  margin-top: 4px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sgc-pt-heading {
  font-size: 0.74rem;
  font-weight: 700;
  text-transform: uppercase;
  color: #64748B;
}

.sgc-pillars-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 5px;
}

.sgc-pillar-chip {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 8px;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 4px;
  font-size: 0.75rem;
}

.sgc-pc-name { color: #334155; font-weight: 500; }
.sgc-pc-score { font-weight: 700; color: var(--primary, #161057); }

/* ==========================================================================
   TAB 3: Granular Input Analysis (Q5–Q44)
   ========================================================================== */
.inputs-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.inputs-filter-bar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
  background: #FFFFFF;
  border: 1.5px solid #CBD5E1;
  border-radius: 10px;
  padding: 10px 14px;
}

.ifb-pillar-select {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--primary, #161057);
}

.ifb-pillar-select select {
  padding: 5px 10px;
  border: 1.5px solid #CBD5E1;
  border-radius: 6px;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--primary, #161057);
  background: #FFFFFF;
  outline: none;
}

.ifb-search-wrap {
  flex: 1;
  min-width: 220px;
}

.ifb-search-wrap input {
  width: 100%;
  padding: 6px 12px;
  border: 1.5px solid #CBD5E1;
  border-radius: 6px;
  font-size: 0.85rem;
  outline: none;
  font-family: inherit;
}

.questions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.question-analytics-card {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 10px;
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.08);
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.qac-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.qac-identifiers {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.qac-num-badge {
  background: var(--primary, #161057);
  color: #FFFFFF;
  font-weight: 800;
  font-size: 0.74rem;
  padding: 2px 6px;
  border-radius: 4px;
}

.qac-section-tag { font-size: 0.72rem; font-weight: 700; color: #64748B; text-transform: uppercase; }
.qac-short-tag { font-size: 0.78rem; font-weight: 700; color: var(--primary, #161057); }

.flag-pill { font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 999px; }
.flag-strong { background: rgba(4, 144, 124, 0.12); color: #04907C; }
.flag-gap { background: #FEE2E2; color: #B91C1C; }
.flag-awareness { background: #F1F5F9; color: #475569; }
.flag-transition { background: #FEF3C7; color: #B45309; }

.qac-question-text {
  font-size: 0.88rem;
  color: #1E293B;
  line-height: 1.45;
}

.qac-bar-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 2px;
}

.qac-distribution-bar {
  display: flex;
  width: 100%;
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
  background: #F1F5F9;
}

.bar-seg { height: 100%; transition: width 0.3s ease; }
.bar-yes { background: #04907C; }
.bar-partially { background: #F59E0B; }
.bar-no { background: #E05A47; }
.bar-notsure { background: #94A3B8; }

.qac-bar-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 0.76rem;
}

.leg-item { display: inline-flex; align-items: center; gap: 4px; }
.leg-dot { width: 7px; height: 7px; border-radius: 50%; }
.leg-yes .leg-dot { background: #04907C; }
.leg-partially .leg-dot { background: #F59E0B; }
.leg-no .leg-dot { background: #E05A47; }
.leg-notsure .leg-dot { background: #94A3B8; }

/* ==========================================================================
   TAB 4: Respondents Table & Weights
   ========================================================================== */
.respondents-view {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.resp-table-header-box {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.resp-table-title {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--primary, #161057);
}

.resp-table-sub { font-size: 0.78rem; color: #64748B; }

.table-container {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 12px;
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.08);
  overflow-x: auto;
}

.modern-resp-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.modern-resp-table th {
  padding: 10px 14px;
  background: #F8FAFC;
  border-bottom: 2px solid var(--primary, #161057);
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--primary, #161057);
}

.resp-row { cursor: pointer; border-bottom: 1px solid #E2E8F0; transition: background 0.15s ease; }
.resp-row:hover { background: #F8FAFC; }
.resp-row.expanded { background: #F1F5F9; }
.resp-row td { padding: 10px 14px; font-size: 0.85rem; }

.resp-cell-user { display: flex; align-items: center; gap: 8px; }
.resp-chevron { font-size: 0.7rem; color: #64748B; transition: transform 0.2s ease; }
.resp-chevron.rotated { transform: rotate(90deg); }
.resp-user-name { font-weight: 700; color: var(--primary, #161057); display: block; }
.resp-user-email { font-size: 0.74rem; color: #64748B; display: block; }

.resp-role-cell { display: flex; flex-direction: column; }
.role-bold { font-weight: 600; color: #1E293B; }
.func-muted { font-size: 0.74rem; color: #64748B; }

.resp-score-cell { display: flex; align-items: center; gap: 6px; }
.score-badge-inline { font-weight: 800; font-size: 0.9rem; color: var(--primary, #161057); }
.score-level-inline { font-size: 0.7rem; font-weight: 700; padding: 2px 5px; border-radius: 999px; }

.modern-weight-select {
  padding: 3px 6px;
  border: 1.5px solid #CBD5E1;
  border-radius: 4px;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--primary, #161057);
  background: #FFFFFF;
}

.demog-tags { display: flex; flex-wrap: wrap; gap: 3px; }
.dtag { font-size: 0.68rem; font-weight: 700; padding: 1px 5px; border-radius: 4px; }
.dtag-nd { background: rgba(4, 144, 124, 0.15); color: #04907C; }
.dtag-nt { background: #E2E8F0; color: #475569; }
.dtag-pwd { background: #FEF3C7; color: #B45309; }
.dtag-gender { background: #E0E7FF; color: #3730A3; }

.btn-icon-direct {
  background: none;
  border: 1px solid #CBD5E1;
  border-radius: 6px;
  color: var(--primary, #161057);
  padding: 5px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-icon-direct:hover {
  background: var(--primary, #161057);
  color: #FFFFFF;
  border-color: var(--primary, #161057);
}

.resp-expand-cell { padding: 14px 16px !important; background: #FAFAF8; border-bottom: 2px solid var(--primary, #161057); }
.resp-expand-card { background: #FFFFFF; border: 1.5px solid #CBD5E1; border-radius: 10px; padding: 14px 16px; }

.rec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid #E2E8F0;
}

.rec-header h4 { font-family: var(--font-heading, 'Fraunces', serif); font-size: 0.95rem; font-weight: 700; color: var(--primary, #161057); }
.rec-date { font-size: 0.75rem; color: #64748B; }

/* ==========================================================================
   TAB 5: Send Org Report
   ========================================================================== */
.report-view { display: flex; flex-direction: column; gap: 16px; }
.report-virtual-warning {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  background: #FFFBEB;
  border: 1.5px solid #F59E0B;
  border-radius: 10px;
}
.rvw-icon { font-size: 1.6rem; }
.rvw-text h4 { font-family: var(--font-heading, 'Fraunces', serif); font-size: 0.98rem; font-weight: 700; color: #92400E; }
.rvw-text p { font-size: 0.82rem; color: #78350F; margin: 3px 0 8px; }

.report-panel-layout {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 16px;
  align-items: flex-start;
}

@media (max-width: 900px) {
  .report-panel-layout { grid-template-columns: 1fr; }
}

.rpl-form-card, .rpl-preview-card {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 12px;
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.08);
  padding: 18px;
}

.rpl-title { font-family: var(--font-heading, 'Fraunces', serif); font-size: 1.1rem; font-weight: 700; color: var(--primary, #161057); }
.rpl-sub { font-size: 0.8rem; color: #64748B; margin-top: 2px; margin-bottom: 14px; }

.field-block { display: flex; flex-direction: column; gap: 5px; margin-bottom: 14px; }
.field-label { font-size: 0.78rem; font-weight: 700; color: var(--primary, #161057); }

.modern-input, .modern-textarea {
  width: 100%;
  padding: 7px 10px;
  border: 1.5px solid #CBD5E1;
  border-radius: 6px;
  font-size: 0.85rem;
  font-family: inherit;
  color: #1E293B;
  outline: none;
}

.recipients-header { display: flex; justify-content: space-between; align-items: center; }
.select-all-toggle { font-size: 0.75rem; font-weight: 600; color: var(--primary, #161057); cursor: pointer; display: flex; align-items: center; gap: 5px; }

.recipients-scroll-box {
  max-height: 180px;
  overflow-y: auto;
  border: 1.5px solid #E2E8F0;
  border-radius: 6px;
  padding: 4px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.recipient-check-row { display: flex; align-items: center; gap: 8px; padding: 5px 8px; border-radius: 4px; cursor: pointer; }
.recipient-check-row:hover { background: #F8FAFC; }
.rcr-text { display: flex; flex-direction: column; font-size: 0.78rem; }
.rcr-name { font-weight: 600; color: #1E293B; }
.rcr-email { font-size: 0.72rem; color: #64748B; }

.btn-full { width: 100%; justify-content: center; padding: 10px; margin-top: 6px; }
.error-banner { padding: 8px 10px; background: #FEE2E2; color: #B91C1C; border-radius: 6px; font-size: 0.78rem; margin-bottom: 10px; }
.success-banner { padding: 8px 10px; background: rgba(4, 144, 124, 0.15); color: #04907C; border-radius: 6px; font-size: 0.78rem; margin-bottom: 10px; font-weight: 600; }

.preview-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.ph-title { font-family: var(--font-heading, 'Fraunces', serif); font-size: 1.05rem; font-weight: 700; color: var(--primary, #161057); }

.btn-refresh-preview {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: none;
  border: 1px solid #CBD5E1;
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--primary, #161057);
  cursor: pointer;
}

.preview-loading-state, .preview-empty-state {
  height: 440px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #64748B;
  background: #F8FAFC;
  border: 1.5px dashed #CBD5E1;
  border-radius: 6px;
  font-size: 0.85rem;
}

.iframe-container { height: 540px; border: 1px solid #CBD5E1; border-radius: 6px; overflow: hidden; }
.report-iframe { width: 100%; height: 100%; border: none; }

/* Modal & Toast */
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(22, 16, 87, 0.4); backdrop-filter: blur(3px);
  display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 20px;
}
.modal-card {
  background: #FFFFFF; border: 2px solid var(--primary, #161057); border-radius: 14px;
  box-shadow: 6px 6px 0px rgba(22, 16, 87, 0.25); max-width: 480px; width: 100%; overflow: hidden;
}
.modal-header { padding: 16px 20px; border-bottom: 1.5px solid #E2E8F0; display: flex; justify-content: space-between; align-items: flex-start; }
.modal-title { font-family: var(--font-heading, 'Fraunces', serif); font-size: 1.15rem; font-weight: 700; color: var(--primary, #161057); }
.modal-sub { font-size: 0.78rem; color: #64748B; margin-top: 2px; }
.btn-close-modal { background: none; border: none; font-size: 1.2rem; color: #94A3B8; cursor: pointer; padding: 4px; }
.modal-body { padding: 18px 20px; }
.modal-footer { padding: 12px 20px; background: #F8FAFC; border-top: 1.5px solid #E2E8F0; display: flex; justify-content: flex-end; gap: 8px; }

.toast-popup {
  position: fixed; bottom: 24px; right: 24px; padding: 10px 18px; border-radius: 8px; font-weight: 600;
  font-size: 0.88rem; box-shadow: 4px 4px 0px rgba(22, 16, 87, 0.15); z-index: 9999; animation: toastSlide 0.25s ease-out;
}
.toast-popup.success { background: #04907C; color: #FFFFFF; border: 1.5px solid var(--primary, #161057); }
.toast-popup.error { background: #E05A47; color: #FFFFFF; border: 1.5px solid var(--primary, #161057); }

@keyframes toastSlide {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 900px) {
  .main-orgs-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  .org-sidebar-card {
    position: static;
    top: auto;
    max-height: none;
    padding: 14px 16px;
  }
  .mobile-dir-toggle-btn {
    display: inline-flex;
  }
  .osc-mobile-selected {
    display: flex;
  }
  .osc-collapsible-body {
    display: none;
  }
  .osc-collapsible-body.mobile-open {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-top: 10px;
    max-height: 400px;
  }
  .sidebar-orgs-list {
    max-height: 280px;
  }
  .search-banner-card {
    flex-direction: column;
    align-items: stretch;
    padding: 10px 14px;
    gap: 10px;
  }
  .search-divider {
    display: none;
  }
  .search-filter-group select {
    width: 100%;
    padding: 6px 0;
  }
}

@media (max-width: 640px) {
  .hero-title {
    font-size: clamp(1.4rem, 5vw, 1.85rem);
  }
  .org-hero-card {
    padding: 16px 14px;
  }
  .org-hero-main {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  .org-hero-left {
    flex: 1 1 100%;
    width: 100%;
  }
  .org-hero-right {
    width: 100%;
    justify-content: space-between;
    gap: 12px;
  }
  .org-hero-actions {
    width: 100%;
  }
  .org-hero-actions .btn {
    flex: 1;
    min-height: 44px;
    justify-content: center;
  }
  .pillars-cards-grid {
    grid-template-columns: 1fr;
  }
  .highlights-grid {
    grid-template-columns: 1fr;
  }
  .qac-top {
    flex-direction: column;
    align-items: flex-start;
  }
  .modal-card {
    width: 95%;
    margin: 10px;
  }
}

@media (max-width: 480px) {
  .org-hero-actions {
    flex-direction: column;
  }
  .org-hero-actions .btn {
    width: 100%;
  }
  .hero-score-stat {
    align-items: flex-start;
    text-align: left;
  }
}
</style>
