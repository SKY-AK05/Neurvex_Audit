<template>
  <div class="orgs-page animate-in">
    <!-- Compact Hero Header matching Overview / Reference Image -->
    <section class="hero-section" aria-label="Organisation Search Banner">
      <div class="hero-content">
        <div class="hero-header-left">
          <h1 class="hero-title">Organisation Assessment &amp; Reporting</h1>
          <p class="hero-subtitle">
            Aggregate multi-respondent audits, analyze workplace inclusion maturity across departments and demographics, and dispatch executive reports.
          </p>
        </div>

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
            <button
              type="button"
              class="btn-new-org-sm"
              @click="openCreateOrgModal"
              title="Create new organisation"
            >
              + New Org
            </button>
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
                  <span v-if="!selectedOrg.is_virtual && selectedOrg.is_active !== false" class="pill-status-active-badge">
                    ● Active
                  </span>
                  <span v-if="!selectedOrg.is_virtual && selectedOrg.is_active === false" class="pill-status-inactive-badge">
                    ⏸ Inactive
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
                  v-if="!selectedOrg.is_virtual"
                  class="btn btn-secondary-action"
                  @click="copyOrgAuditLink"
                  title="Copy audit link for this organization - respondents can use this to submit audits"
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                  Copy Audit Link
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

                <!-- Official Org Management Dropdown / Actions -->
                <template v-if="!selectedOrg.is_virtual">
                  <button
                    class="btn btn-outline btn-icon-only"
                    @click="openEditOrgModal(selectedOrg)"
                    title="Edit organisation name"
                  >
                    ✏️ Edit
                  </button>
                  <button
                    class="btn btn-outline btn-icon-only"
                    @click="toggleOrgStatus(selectedOrg)"
                    :title="selectedOrg.is_active === false ? 'Activate organisation' : 'Deactivate organisation'"
                  >
                    {{ selectedOrg.is_active === false ? '▶ Activate' : '⏸ Deactivate' }}
                  </button>
                  <button
                    class="btn btn-outline btn-icon-only btn-danger-action"
                    @click="openDeleteOrgModal(selectedOrg)"
                    title="Soft delete organisation"
                  >
                    🗑 Delete
                  </button>
                
    <!-- Modal: Create New Organisation -->
    <div v-if="showCreateOrgModal" class="modal-backdrop" @click.self="showCreateOrgModal = false">
      <div class="modal-card modal-card-sm">
        <div class="modal-header">
          <h3 class="modal-title">Create Organisation</h3>
          <button class="btn-close-modal" @click="showCreateOrgModal = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="field-block">
            <label class="field-label">Organisation Name *</label>
            <input
              v-model="createOrgName"
              type="text"
              class="modern-input"
              placeholder="e.g. Nexora Technologies"
              @keyup.enter="handleCreateOrg"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="showCreateOrgModal = false">Cancel</button>
          <button
            class="btn btn-primary-cta"
            :disabled="!createOrgName.trim() || creatingOrgSaving"
            @click="handleCreateOrg"
          >
            {{ creatingOrgSaving ? 'Creating…' : 'Create Organisation' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal: Edit Organisation Name -->
    <div v-if="showEditOrgModal" class="modal-backdrop" @click.self="showEditOrgModal = false">
      <div class="modal-card modal-card-sm">
        <div class="modal-header">
          <h3 class="modal-title">Edit Organisation Name</h3>
          <button class="btn-close-modal" @click="showEditOrgModal = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="field-block">
            <label class="field-label">Organisation Name *</label>
            <input
              v-model="editOrgName"
              type="text"
              class="modern-input"
              @keyup.enter="handleUpdateOrg"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="showEditOrgModal = false">Cancel</button>
          <button
            class="btn btn-primary-cta"
            :disabled="!editOrgName.trim() || editingOrgSaving"
            @click="handleUpdateOrg"
          >
            {{ editingOrgSaving ? 'Saving…' : 'Save Changes' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal: Soft Delete Confirmation -->
    <div v-if="showDeleteOrgModal" class="modal-backdrop" @click.self="showDeleteOrgModal = false">
      <div class="modal-card modal-card-sm">
        <div class="modal-header">
          <h3 class="modal-title" style="color: #DC2626;">Delete Organisation</h3>
          <button class="btn-close-modal" @click="showDeleteOrgModal = false">✕</button>
        </div>
        <div class="modal-body">
          <p style="font-size: 0.95rem; color: #374151; line-height: 1.5; margin-bottom: 1rem;">
            Are you sure you want to delete <strong>{{ selectedOrg?.name }}</strong>?
          </p>
          <p style="font-size: 0.85rem; color: #6B7280; line-height: 1.4;">
            This will soft-delete the organisation and revoke all active invitation links.
            Existing historical employee submissions and scoring records will be preserved.
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="showDeleteOrgModal = false">Cancel</button>
          <button
            class="btn btn-primary-cta"
            style="background: #DC2626; border-color: #DC2626;"
            :disabled="deletingOrgSaving"
            @click="handleDeleteOrg"
          >
            {{ deletingOrgSaving ? 'Deleting…' : 'Confirm Delete' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal: Generate New Invitation -->
    <div v-if="showCreateInviteModal" class="modal-backdrop" @click.self="showCreateInviteModal = false">
      <div class="modal-card modal-card-md">
        <div class="modal-header">
          <div>
            <h3 class="modal-title">Generate Invitation Link</h3>
            <p class="modal-sub">For {{ selectedOrg?.name }}</p>
          </div>
          <button class="btn-close-modal" @click="showCreateInviteModal = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="field-block">
            <label class="field-label">Invitation Label (Optional)</label>
            <input
              v-model="inviteForm.invitation_name"
              type="text"
              class="modern-input"
              placeholder="e.g. Q4 Company-wide Assessment"
            />
          </div>

          <div class="field-grid-2">
            <div class="field-block">
              <label class="field-label">Expiration Date (Optional)</label>
              <input
                v-model="inviteForm.expires_at"
                type="datetime-local"
                class="modern-input"
              />
            </div>
            <div class="field-block">
              <label class="field-label">Max Submissions (Optional)</label>
              <input
                v-model.number="inviteForm.max_submissions"
                type="number"
                min="1"
                class="modern-input"
                placeholder="Unlimited"
              />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="showCreateInviteModal = false">Cancel</button>
          <button
            class="btn btn-primary-cta"
            :disabled="creatingInviteSaving"
            @click="handleCreateInvite"
          >
            {{ creatingInviteSaving ? 'Generating…' : 'Generate Link' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal: Invitation Link Created (One-Time Raw Token Display) -->
    <div v-if="generatedInviteLink" class="modal-backdrop" @click.self="generatedInviteLink = null">
      <div class="modal-card modal-card-md">
        <div class="modal-header">
          <div>
            <h3 class="modal-title">🎉 Invitation Link Ready</h3>
            <p class="modal-sub">{{ generatedInviteLink.invitation_name }}</p>
          </div>
          <button class="btn-close-modal" @click="generatedInviteLink = null">✕</button>
        </div>
        <div class="modal-body">
          <div class="inv-link-box">
            <label class="field-label">Shareable Link</label>
            <div class="inv-copy-row">
              <input
                :value="generatedInviteLink.full_url"
                type="text"
                class="modern-input inv-link-input"
                readonly
              />
              <button class="btn btn-primary-cta" @click="copyText(generatedInviteLink.full_url)">
                📋 Copy
              </button>
            </div>
          </div>
          <p class="inv-security-note">
            🔒 <strong>Security Note:</strong> This unique link includes a cryptographically secure token.
            Anyone opening this link will have <strong>{{ selectedOrg?.name }}</strong> automatically pre-filled and locked.
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-primary-cta" @click="generatedInviteLink = null">Done</button>
        </div>
      </div>
    </div>

</template>
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
            v-if="!selectedOrg.is_virtual"
            class="nav-tab-btn"
            :class="{ active: activeTab === 'invitations' }"
            @click="activeTab = 'invitations'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
            Invitations &amp; Links
            <span v-if="invitations.length" class="tab-count-pill">{{ invitations.length }}</span>
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
            <!-- Expandable Organisation-Level Score Explanation (Requirement 5.4) -->
            <div class="score-explanation-card">
              <div class="sec-toggle-header" @click="showScoreExplanation = !showScoreExplanation">
                <div class="sec-toggle-left">
                  <svg class="sec-info-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="16" x2="12" y2="12"></line>
                    <line x1="12" y1="8" x2="12.01" y2="8"></line>
                  </svg>
                  <div>
                    <h4 class="sec-toggle-title">How Was This Organisation's Score Calculated?</h4>
                    <span class="sec-toggle-sub">View full 8-pillar mathematical reconciliation &amp; weighting methodology</span>
                  </div>
                </div>
                <button type="button" class="btn-toggle-sec">
                  {{ showScoreExplanation ? 'Hide Calculation ▲' : 'Inspect Calculation ▼' }}
                </button>
              </div>

              <div v-if="showScoreExplanation" class="sec-calc-body animate-fade">
                <p class="sec-intro-text">
                  The Weighted NIWI Index of <strong>{{ currentScore?.org_avg }}/20</strong> is calculated across
                  <strong>{{ detail?.respondents?.length || 0 }} employee submissions</strong> (total audit weight: {{ currentScore?.total_weight || detail?.respondents?.length || 0 }}×).
                  Each of the 8 core inclusion pillars contributes equally (<strong>12.5% / weight 0.125</strong>).
                  Summing all 8 weighted pillar contributions equals the final Weighted NIWI Index out of 20.
                </p>

                <div class="reconciliation-table-wrap">
                  <table class="reconciliation-table">
                    <thead>
                      <tr>
                        <th>Pillar Name</th>
                        <th>Dimension</th>
                        <th>Pillar Score (out of 20)</th>
                        <th>Pillar Weight</th>
                        <th>Weighted Contribution</th>
                        <th>Maturity Level</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="p in pillarScorecards" :key="p.id">
                        <td class="pillar-name-cell">
                          <span class="pnc-icon">{{ p.icon }}</span>
                          <strong>{{ p.title }}</strong>
                        </td>
                        <td><span class="dim-tag">{{ p.id.toUpperCase() }}</span></td>
                        <td><strong>{{ p.score }}</strong> / 20</td>
                        <td>12.5% (0.125)</td>
                        <td class="contrib-cell">
                          <strong>{{ (p.score * 0.125).toFixed(3) }}</strong> pts
                        </td>
                        <td>
                          <span class="pill-tier" :class="levelClass(p.level)">{{ p.level }}</span>
                        </td>
                      </tr>
                    </tbody>
                    <tfoot>
                      <tr class="reconciliation-total-row">
                        <td colspan="2"><strong>Reconciled Weighted NIWI Index:</strong></td>
                        <td><strong>{{ currentScore?.org_avg }} / 20</strong></td>
                        <td><strong>100% (1.000)</strong></td>
                        <td class="contrib-cell">
                          <strong class="total-contrib-badge">{{ currentScore?.org_avg }} / 20</strong>
                        </td>
                        <td>
                          <span class="pill-tier" :class="levelClass(currentScore?.org_level)">{{ currentScore?.org_level }}</span>
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>

                <div class="formula-box">
                  <span class="fb-title">Authoritative Aggregation Formula:</span>
                  <code class="fb-code">
                    Weighted NIWI Index = &Sigma;(Employee Score<sub>i</sub> &times; Weight<sub>i</sub>) / &Sigma; Weight<sub>i</sub> = &Sigma;(Pillar Score<sub>k</sub> &times; 0.125)
                  </code>
                  <p class="fb-note">
                    All calculations come directly from database submission records and follow NIWI's additive scoring engine with exact reconciliation.
                  </p>
                </div>
              </div>
            </div>

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
                :class="{ 'card-expanded': expandedPillarId === pillar.id }"
              >
                <!-- SECTION 1: PILLAR IDENTITY -->
                <div class="pc-top">
                  <div class="pc-icon-wrap">
                    <span class="pc-icon">{{ pillar.icon }}</span>
                    <div>
                      <h3 class="pc-title">{{ pillar.title }}</h3>
                      <span class="pc-category">NIWI DIMENSION {{ pillar.id.toUpperCase() }}</span>
                    </div>
                  </div>
                  <div class="pc-score-box">
                    <span class="pc-score">{{ pillar.score }}</span>
                    <span class="pc-max">/ 20</span>
                  </div>
                </div>

                <!-- Pillar Progress Bar & Level -->
                <div class="pc-bar-wrap">
                  <div class="pc-bar-bg">
                    <div class="pc-bar-fill" :style="{ width: `${(pillar.score / 20) * 100}%` }"></div>
                  </div>
                  <div class="pc-bar-labels">
                    <span class="pc-level-tag" :class="levelClass(pillar.level)">{{ pillar.level }}</span>
                    <span class="pc-pct">{{ Math.round((pillar.score / 20) * 100) }}%</span>
                  </div>
                </div>

                <!-- Description & Indicator Chips -->
                <p class="pc-summary">{{ pillar.summary }}</p>

                <div class="pc-key-points">
                  <span v-for="(pt, idx) in pillar.points" :key="idx" class="pc-chip">
                    • {{ pt }}
                  </span>
                </div>

                <!-- SECTION 2 & 3: AGGREGATED PILLAR RESPONSES & MARKS SUMMARY (Requirement 4) -->
                <div class="pillar-agg-box">
                  <div class="pab-header">
                    <span class="pab-title">Pillar Aggregated Responses (5 Questions)</span>
                    <span class="pab-count-badge">
                      {{ pillar.agg?.totalResponses || 0 }} responses ({{ pillar.agg?.employeeCount || 0 }} employees)
                    </span>
                  </div>

                  <!-- Horizontally Stacked Distribution Bar with NIWI Colors -->
                  <div class="pab-distribution-bar">
                    <div
                      v-if="pillar.agg?.yesPct > 0"
                      class="pab-seg pab-yes"
                      :style="{ width: `${pillar.agg.yesPct}%`, backgroundColor: '#04907C' }"
                      :title="`Yes: ${pillar.agg.yes} (${pillar.agg.yesPct}%)`"
                    ></div>
                    <div
                      v-if="pillar.agg?.partiallyPct > 0"
                      class="pab-seg pab-partially"
                      :style="{ width: `${pillar.agg.partiallyPct}%`, backgroundColor: '#F59E0B' }"
                      :title="`Partially: ${pillar.agg.partially} (${pillar.agg.partiallyPct}%)`"
                    ></div>
                    <div
                      v-if="pillar.agg?.noPct > 0"
                      class="pab-seg pab-no"
                      :style="{ width: `${pillar.agg.noPct}%`, backgroundColor: '#E05A47' }"
                      :title="`No: ${pillar.agg.no} (${pillar.agg.noPct}%)`"
                    ></div>
                    <div
                      v-if="pillar.agg?.notSurePct > 0"
                      class="pab-seg pab-notsure"
                      :style="{ width: `${pillar.agg.notSurePct}%`, backgroundColor: '#94A3B8' }"
                      :title="`Not Sure / NA: ${pillar.agg.notSure} (${pillar.agg.notSurePct}%)`"
                    ></div>
                    <div
                      v-if="!pillar.agg || pillar.agg.totalResponses === 0"
                      class="pab-seg-empty"
                      title="No employee responses recorded yet"
                    ></div>
                  </div>

                  <!-- 4-Item Legend -->
                  <div class="pab-legend">
                    <span class="pab-leg-item leg-yes">
                      <span class="leg-dot" style="background-color: #04907C"></span>
                      <strong>Yes:</strong> {{ pillar.agg?.yes || 0 }} ({{ pillar.agg?.yesPct || 0 }}%)
                    </span>
                    <span class="pab-leg-item leg-partially">
                      <span class="leg-dot" style="background-color: #F59E0B"></span>
                      <strong>Partially:</strong> {{ pillar.agg?.partially || 0 }} ({{ pillar.agg?.partiallyPct || 0 }}%)
                    </span>
                    <span class="pab-leg-item leg-no">
                      <span class="leg-dot" style="background-color: #E05A47"></span>
                      <strong>No:</strong> {{ pillar.agg?.no || 0 }} ({{ pillar.agg?.noPct || 0 }}%)
                    </span>
                    <span class="pab-leg-item leg-notsure">
                      <span class="leg-dot" style="background-color: #94A3B8"></span>
                      <strong>Not Sure:</strong> {{ pillar.agg?.notSure || 0 }} ({{ pillar.agg?.notSurePct || 0 }}%)
                    </span>
                  </div>

                  <!-- Marks Breakdown & Reconciliation Row -->
                  <div class="pab-marks-summary">
                    <div class="pms-formula">
                      <code>{{ pillar.agg?.yes || 0 }} Yes × 4 + {{ pillar.agg?.partially || 0 }} Partially × 2 = {{ pillar.agg?.rawMarksEarned || 0 }} / {{ pillar.agg?.maxRawMarks || 0 }} raw marks</code>
                    </div>
                    <div class="pms-stats-grid">
                      <div class="pms-stat-col">
                        <span class="pms-lbl">Pillar Score</span>
                        <span class="pms-val"><strong>{{ pillar.score }}</strong> / 20</span>
                      </div>
                      <div class="pms-stat-col">
                        <span class="pms-lbl">Pillar Weight</span>
                        <span class="pms-val">12.5%</span>
                      </div>
                      <div class="pms-stat-col">
                        <span class="pms-lbl">Weighted Contrib.</span>
                        <span class="pms-val"><strong>{{ pillar.agg?.weightedContribution || '0.000' }}</strong> pts</span>
                      </div>
                      <div class="pms-stat-col">
                        <span class="pms-lbl">Maturity Level</span>
                        <span class="pms-badge" :class="levelClass(pillar.level)">{{ shortLevel(pillar.level) }}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- SECTION 4: ACCORDION EXPAND/COLLAPSE TRIGGER (Requirement 5) -->
                <div class="pc-accordion-action">
                  <button
                    type="button"
                    class="btn-pillar-accordion"
                    :class="{ 'expanded': expandedPillarId === pillar.id }"
                    @click="togglePillarExpand(pillar.id)"
                  >
                    <span>{{ expandedPillarId === pillar.id ? 'Hide Questions ↑' : 'View 5 Questions ↓' }}</span>
                  </button>
                </div>

                <!-- SECTION 5: EXPANDED 5 QUESTIONS BREAKDOWN (Requirements 6 & 7) -->
                <div v-if="expandedPillarId === pillar.id" class="pc-expanded-questions animate-fade">
                  <div class="peq-intro-banner">
                    <span>Individual 5 Assessment Questions for <strong>{{ pillar.title }}</strong>:</span>
                  </div>

                  <div
                    v-for="pq in getPillarQuestions(pillar.id)"
                    :key="pq.field"
                    class="pillar-question-card"
                  >
                    <!-- Question Top Row -->
                    <div class="pqc-top-row">
                      <div class="pqc-left-meta">
                        <span class="pqc-num-badge">{{ pq.field.toUpperCase() }}</span>
                        <span class="pqc-short-title">{{ pq.short }}</span>
                      </div>
                      <div class="pqc-right-meta">
                        <span class="pqc-score-pill">{{ pq.questionScore }} / 4.00</span>
                        <span v-if="pq.stats.yesPct >= 60" class="flag-pill flag-strong">✓ Strong</span>
                        <span v-else-if="pq.stats.noPct >= 40" class="flag-pill flag-gap">⚠️ Gap</span>
                        <span v-else-if="pq.stats.notSurePct >= 40" class="flag-pill flag-awareness">❓ Low Awareness</span>
                        <span v-else class="flag-pill flag-transition">⚡ Developing</span>
                      </div>
                    </div>

                    <!-- Full Question Text with Generous Width -->
                    <p class="pqc-question-text">{{ pq.text }}</p>

                    <!-- Question Distribution Bar with Explicit NIWI Colors -->
                    <div class="pqc-bar-wrap">
                      <div class="qac-distribution-bar">
                        <div
                          v-if="pq.stats.yesPct > 0"
                          class="bar-seg bar-yes"
                          :style="{ width: `${pq.stats.yesPct}%`, backgroundColor: '#04907C' }"
                          :title="`Yes: ${pq.stats.yes} (${pq.stats.yesPct}%)`"
                        ></div>
                        <div
                          v-if="pq.stats.partiallyPct > 0"
                          class="bar-seg bar-partially"
                          :style="{ width: `${pq.stats.partiallyPct}%`, backgroundColor: '#F59E0B' }"
                          :title="`Partially: ${pq.stats.partially} (${pq.stats.partiallyPct}%)`"
                        ></div>
                        <div
                          v-if="pq.stats.noPct > 0"
                          class="bar-seg bar-no"
                          :style="{ width: `${pq.stats.noPct}%`, backgroundColor: '#E05A47' }"
                          :title="`No: ${pq.stats.no} (${pq.stats.noPct}%)`"
                        ></div>
                        <div
                          v-if="pq.stats.notSurePct > 0"
                          class="bar-seg bar-notsure"
                          :style="{ width: `${pq.stats.notSurePct}%`, backgroundColor: '#94A3B8' }"
                          :title="`Not Sure / NA: ${pq.stats.notSure} (${pq.stats.notSurePct}%)`"
                        ></div>
                        <div
                          v-if="pq.stats.total === 0"
                          class="bar-seg-empty"
                          title="No responses recorded"
                        ></div>
                      </div>

                      <div class="qac-bar-legend">
                        <span class="leg-item leg-yes">
                          <span class="leg-dot" style="background-color: #04907C"></span>
                          <strong>Yes:</strong> {{ pq.stats.yes }} ({{ pq.stats.yesPct }}%)
                        </span>
                        <span class="leg-item leg-partially">
                          <span class="leg-dot" style="background-color: #F59E0B"></span>
                          <strong>Partially:</strong> {{ pq.stats.partially }} ({{ pq.stats.partiallyPct }}%)
                        </span>
                        <span class="leg-item leg-no">
                          <span class="leg-dot" style="background-color: #E05A47"></span>
                          <strong>No:</strong> {{ pq.stats.no }} ({{ pq.stats.noPct }}%)
                        </span>
                        <span class="leg-item leg-notsure">
                          <span class="leg-dot" style="background-color: #94A3B8"></span>
                          <strong>Not Sure:</strong> {{ pq.stats.notSure }} ({{ pq.stats.notSurePct }}%)
                        </span>
                      </div>
                    </div>

                    <!-- Footnote Calculation -->
                    <div class="pqc-calc-footnote">
                      <span><strong>Calculation:</strong> {{ pq.stats.yes }} Yes × 4 + {{ pq.stats.partially }} Partially × 2 = {{ pq.marksEarned }} / {{ pq.maxMarks }} marks</span>
                      <span><strong>Weight:</strong> 20.0% of Pillar</span>
                      <span><strong>Normalised:</strong> {{ pq.questionScore }} / 4.00</span>
                    </div>
                  </div>
                </div>
              </div>
            </div></section>

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
            <!-- Filter & Controls Toolbar -->
            <div class="inputs-filter-bar">
              <div class="ifb-control-group">
                <label for="input-pillar-filter">Pillar:</label>
                <select id="input-pillar-filter" v-model="selectedInputPillar">
                  <option value="all">All 8 Pillars (40 Questions)</option>
                  <option v-for="sec in DEFAULT_SECTIONS" :key="sec.id" :value="sec.id">
                    {{ sec.icon }} {{ sec.title }} (5 Questions)
                  </option>
                </select>
              </div>

              <div class="ifb-control-group">
                <label for="input-practice-filter">Practice Status:</label>
                <select id="input-practice-filter" v-model="selectedPracticeFilter">
                  <option value="all">All Practice Levels</option>
                  <option value="strong">✓ Strong Practice (&ge;60% Yes)</option>
                  <option value="developing">⚡ Developing</option>
                  <option value="awareness">❓ Low Awareness (&ge;40% Not Sure)</option>
                  <option value="gap">⚠️ Critical Gap (&ge;40% No)</option>
                </select>
              </div>

              <div class="ifb-control-group">
                <label for="input-sort-filter">Sort:</label>
                <select id="input-sort-filter" v-model="inputSortBy">
                  <option value="order">Question Order (Q5–Q44)</option>
                  <option value="score_asc">Score: Lowest First (Priority Gaps)</option>
                  <option value="score_desc">Score: Highest First (Strengths)</option>
                </select>
              </div>

              <div class="ifb-search-wrap">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="ifb-search-icon">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
                <input
                  v-model="inputSearchQuery"
                  type="text"
                  placeholder="Search question text or keyword (e.g. interview, sensory, ERG)..."
                />
                <button v-if="inputSearchQuery" class="ifb-clear-btn" @click="inputSearchQuery = ''" title="Clear">✕</button>
              </div>
            </div>

            <!-- Transparency Banner -->
            <div class="inputs-transparency-banner">
              <div class="itb-icon">ℹ️</div>
              <div class="itb-text">
                <strong>Scoring Methodology Single Source of Truth:</strong> Each assessment question awards <strong>4 marks for "Yes"</strong>, <strong>2 marks for "Partially"</strong>, and <strong>0 marks for "No" / "Not Sure / NA"</strong>. Total raw marks are divided by maximum available marks (4 × eligible responses) and normalised to 4.00 max points per question. Each pillar aggregates its 5 questions equally (summing to 20.00 max points).
              </div>
            </div>

            <div class="questions-list">
              <div
                v-for="q in filteredQuestionsList"
                :key="q.field"
                class="question-analytics-card"
                :class="{ 'card-expanded': isQuestionExpanded(q.field) }"
              >
                <div class="qac-top">
                  <div class="qac-identifiers">
                    <span class="qac-num-badge">{{ q.field.toUpperCase() }}</span>
                    <span class="qac-section-tag">{{ q.sectionTitle }}</span>
                    <span class="qac-short-tag">{{ q.short }}</span>
                  </div>
                  <div class="qac-right-metrics">
                    <div class="qac-score-pill">
                      <span class="qac-score-val">{{ q.questionScore }}</span>
                      <span class="qac-score-max">/ 4.00</span>
                      <span class="qac-score-pct">({{ q.questionPct }}%)</span>
                    </div>
                    <div class="qac-flag-wrap">
                      <span v-if="q.stats.yesPct >= 60" class="flag-pill flag-strong">
                        ✓ Strong Practice
                      </span>
                      <span v-else-if="q.stats.noPct >= 40" class="flag-pill flag-gap">
                        ⚠️ Critical Gap
                      </span>
                      <span v-else-if="q.stats.notSurePct >= 40" class="flag-pill flag-awareness">
                        ❓ Low Awareness
                      </span>
                      <span v-else class="flag-pill flag-transition">
                        ⚡ Developing
                      </span>
                    </div>
                  </div>
                </div>

                <p class="qac-question-text">{{ q.text }}</p>

                <!-- Stacked Distribution Bar -->
                <div class="qac-bar-container">
                  <div class="qac-distribution-bar">
                    <div
                      v-if="q.stats.yesPct > 0"
                      class="bar-seg bar-yes"
                      :style="{ width: `${q.stats.yesPct}%`, backgroundColor: '#04907C' }"
                      :title="`Yes: ${q.stats.yes} responses (${q.stats.yesPct}%)`"
                    ></div>
                    <div
                      v-if="q.stats.partiallyPct > 0"
                      class="bar-seg bar-partially"
                      :style="{ width: `${q.stats.partiallyPct}%`, backgroundColor: '#F59E0B' }"
                      :title="`Partially: ${q.stats.partially} responses (${q.stats.partiallyPct}%)`"
                    ></div>
                    <div
                      v-if="q.stats.noPct > 0"
                      class="bar-seg bar-no"
                      :style="{ width: `${q.stats.noPct}%`, backgroundColor: '#E05A47' }"
                      :title="`No: ${q.stats.no} responses (${q.stats.noPct}%)`"
                    ></div>
                    <div
                      v-if="q.stats.notSurePct > 0"
                      class="bar-seg bar-notsure"
                      :style="{ width: `${q.stats.notSurePct}%`, backgroundColor: '#94A3B8' }"
                      :title="`Not Sure / NA: ${q.stats.notSure} responses (${q.stats.notSurePct}%)`"
                    ></div>
                    <div
                      v-if="q.stats.total === 0"
                      class="bar-seg-empty"
                      title="No employee responses recorded yet"
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

                <!-- Score Calculation Transparency Box -->
                <div class="qac-scoring-transparency-box">
                  <div class="qstb-header">
                    <span class="qstb-title">📊 Score Calculation &amp; Marks Breakdown</span>
                    <button
                      type="button"
                      class="qstb-toggle-btn"
                      @click="toggleQuestionExpand(q.field)"
                    >
                      {{ isQuestionExpanded(q.field) ? '▲ Hide Answer Breakdown' : '▼ Inspect Response Breakdown Table' }}
                    </button>
                  </div>
                  <div class="qstb-formula">
                    <code>{{ q.formulaText }}</code>
                  </div>
                  <div class="qstb-meta-row">
                    <span><strong>Total Responses:</strong> {{ q.stats.total }}</span>
                    <span><strong>Raw Marks Earned:</strong> {{ q.marksEarned }} / {{ q.maxMarks }}</span>
                    <span><strong>Question Weight:</strong> 20.0% of Pillar</span>
                    <span><strong>Normalised Score:</strong> {{ q.questionScore }} / 4.00</span>
                  </div>

                  <!-- Expandable Detailed Answer Breakdown Table (Section 5.1 & 5.2 requirement) -->
                  <div v-if="isQuestionExpanded(q.field)" class="qstb-table-wrap">
                    <table class="q-breakdown-table">
                      <thead>
                        <tr>
                          <th>Response Option</th>
                          <th style="text-align: right">Employees</th>
                          <th style="text-align: right">Marks Each</th>
                          <th style="text-align: right">Total Marks Earned</th>
                          <th style="text-align: right">Share %</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr class="row-yes">
                          <td><span class="opt-dot dot-yes"></span> Yes</td>
                          <td style="text-align: right; font-weight: 600">{{ q.stats.yes }}</td>
                          <td style="text-align: right">4</td>
                          <td style="text-align: right; font-weight: 700">{{ q.stats.yes * 4 }}</td>
                          <td style="text-align: right">{{ q.stats.yesPct }}%</td>
                        </tr>
                        <tr class="row-partially">
                          <td><span class="opt-dot dot-partially"></span> Partially</td>
                          <td style="text-align: right; font-weight: 600">{{ q.stats.partially }}</td>
                          <td style="text-align: right">2</td>
                          <td style="text-align: right; font-weight: 700">{{ q.stats.partially * 2 }}</td>
                          <td style="text-align: right">{{ q.stats.partiallyPct }}%</td>
                        </tr>
                        <tr class="row-no">
                          <td><span class="opt-dot dot-no"></span> No</td>
                          <td style="text-align: right; font-weight: 600">{{ q.stats.no }}</td>
                          <td style="text-align: right">0</td>
                          <td style="text-align: right; font-weight: 700">0</td>
                          <td style="text-align: right">{{ q.stats.noPct }}%</td>
                        </tr>
                        <tr class="row-notsure">
                          <td><span class="opt-dot dot-notsure"></span> Not Sure / NA</td>
                          <td style="text-align: right; font-weight: 600">{{ q.stats.notSure }}</td>
                          <td style="text-align: right">0</td>
                          <td style="text-align: right; font-weight: 700">0</td>
                          <td style="text-align: right">{{ q.stats.notSurePct }}%</td>
                        </tr>
                      </tbody>
                      <tfoot>
                        <tr>
                          <th>Total Eligible Responses</th>
                          <th style="text-align: right">{{ q.stats.total }}</th>
                          <th style="text-align: right">—</th>
                          <th style="text-align: right">{{ q.marksEarned }} / {{ q.maxMarks }}</th>
                          <th style="text-align: right">{{ q.questionPct }}%</th>
                        </tr>
                      </tfoot>
                    </table>
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

            <!-- Source Filter Chips -->
            <div class="resp-source-filter-row">
              <span class="rsf-label">Submission Method:</span>
              <button
                class="rsf-pill"
                :class="{ active: submissionSourceFilter === 'all' }"
                @click="submissionSourceFilter = 'all'"
              >
                All ({{ detail.respondents.length }})
              </button>
              <button
                class="rsf-pill"
                :class="{ active: submissionSourceFilter === 'direct' }"
                @click="submissionSourceFilter = 'direct'"
              >
                🌐 Direct Website ({{ countDirect }})
              </button>
              <button
                class="rsf-pill"
                :class="{ active: submissionSourceFilter === 'invitation' }"
                @click="submissionSourceFilter = 'invitation'"
              >
                🔗 Invitation Link ({{ countInvite }})
              </button>
            </div>

            <div class="table-container">
              <table class="modern-resp-table">
                <thead>
                  <tr>
                    <th style="width: 22%; min-width: 160px">Respondent &amp; Designation</th>
                    <th style="width: 12%; min-width: 90px">Method</th>
                    <th style="width: 16%; min-width: 120px">Function &amp; Role</th>
                    <th style="width: 15%; min-width: 120px">Score &amp; Level</th>
                    <th style="width: 13%; min-width: 100px" v-if="!selectedOrg.is_virtual">Audit Weight</th>
                    <th style="width: 12%; min-width: 100px">Demographics</th>
                    <th style="width: 10%; min-width: 80px; text-align: center">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <template v-for="r in filteredRespondents" :key="r.id">
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
                        <span
                          v-if="(r.submission_source || '').toUpperCase() === 'INVITATION'"
                          class="pill-source-invite"
                          :title="r.invitation_name ? `Invitation: ${r.invitation_name}` : 'Submitted via unique organisation invitation link'"
                        >
                          🔗 Invitation
                        </span>
                        <span
                          v-else
                          class="pill-source-direct"
                          title="Submitted directly via website organisation dropdown"
                        >
                          🌐 Direct
                        </span>
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

                    <!-- Expanded Detail Row with Colspan: 7 when non-virtual, 6 when virtual -->
                    <tr v-if="expandedRespondentId === r.id" class="resp-expand-row">
                      <td :colspan="!selectedOrg.is_virtual ? 7 : 6" class="resp-expand-cell">
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

          <!-- TAB 6: INVITATIONS & LINKS -->
          <section v-if="activeTab === 'invitations'" class="invitations-view animate-fade">
            <div class="invitations-header-card">
              <div class="ihc-left">
                <h3 class="ihc-title">Organisation Invitation Links</h3>
                <p class="ihc-subtitle">
                  Generate secure, trackable links that auto-fill and lock <strong>{{ selectedOrg.name }}</strong> for new respondents.
                  Perfect for company-wide assessments where you want to ensure all submissions are linked to this organisation.
                </p>
              </div>
              <div class="ihc-right">
                <button
                  class="btn btn-primary-cta"
                  @click="showCreateInviteModal = true"
                  :disabled="selectedOrg.is_virtual"
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                  Generate New Link
                </button>
              </div>
            </div>

            <!-- Invitations List -->
            <div v-if="invitations.length === 0" class="invitations-empty-state">
              <div class="ies-icon">🔗</div>
              <h4>No Invitation Links Created Yet</h4>
              <p>Create your first invitation link to start collecting pre-linked submissions for {{ selectedOrg.name }}.</p>
              <button class="btn btn-primary-cta" @click="showCreateInviteModal = true">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                Create First Invitation
              </button>
            </div>

            <div v-else class="invitations-grid">
              <div
                v-for="inv in invitations"
                :key="inv.id"
                class="invitation-card"
                :class="{ 'inv-expired': !inv.is_active || (inv.expires_at && new Date(inv.expires_at) < new Date()) }"
              >
                <div class="invc-header">
                  <div class="invc-name-section">
                    <h4 class="invc-name">{{ inv.invitation_name || 'Untitled Link' }}</h4>
                    <div class="invc-meta-tags">
                      <span v-if="inv.is_active" class="invc-tag invc-tag-active">✓ Active</span>
                      <span v-else class="invc-tag invc-tag-inactive">⏸ Inactive</span>
                      <span v-if="inv.expires_at" class="invc-tag invc-tag-expires">
                        Expires {{ formatDate(inv.expires_at) }}
                      </span>
                      <span v-if="inv.max_submissions" class="invc-tag invc-tag-limit">
                        {{ inv.submission_count || 0 }} / {{ inv.max_submissions }} used
                      </span>
                      <span v-else class="invc-tag invc-tag-unlimited">
                        {{ inv.submission_count || 0 }} submissions
                      </span>
                    </div>
                  </div>
                </div>

                <div class="invc-link-row">
                  <div class="invc-link-display">
                    <code class="invc-link-code">{{ window.location.origin }}/?invite={{ inv.token }}</code>
                  </div>
                  <button
                    class="btn btn-sm btn-outline"
                    @click="copyText(`${window.location.origin}/?invite=${inv.token}`)"
                    title="Copy invitation link"
                  >
                    📋 Copy
                  </button>
                </div>

                <div class="invc-footer">
                  <span class="invc-created">Created {{ formatDate(inv.created_at) }}</span>
                  <div class="invc-actions">
                    <button
                      v-if="inv.is_active"
                      class="btn-text-action"
                      @click="revokeInvitation(inv.id)"
                      title="Revoke this invitation"
                    >
                      🚫 Revoke
                    </button>
                    <button
                      class="btn-text-action"
                      @click="regenerateInvitation(inv.id)"
                      title="Generate new token (invalidates old link)"
                    >
                      🔄 Regenerate
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Info Box -->
            <div class="invitations-info-box">
              <div class="iib-icon">💡</div>
              <div class="iib-content">
                <h5>How Invitation Links Work:</h5>
                <ul>
                  <li><strong>Auto-filled Organisation:</strong> When someone opens the link, "{{ selectedOrg.name }}" is pre-filled and locked in the audit form.</li>
                  <li><strong>Secure Tokens:</strong> Each link contains a unique cryptographic token that can be tracked, revoked, or regenerated.</li>
                  <li><strong>Submission Limits:</strong> Optionally set max submissions or expiry dates to control link usage.</li>
                  <li><strong>Centralized Reporting:</strong> All submissions via these links automatically aggregate into this organisation's dashboard.</li>
                </ul>
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
import {
  createOrganisation,
  updateOrganisation,
  toggleOrganisationStatus,
  deleteOrganisation,
  getOrgInvitations,
  createOrgInvitation,
  revokeOrgInvitation,
  regenerateOrgInvitation
} from '../api.js';

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

// Score Transparency & Drilldown State
const showScoreExplanation = ref(false);
const expandedPillarId = ref(null);
function togglePillarExpand(id) {
  expandedPillarId.value = expandedPillarId.value === id ? null : id;
}
function getPillarQuestions(pillarId) {
  return allQuestionsFlat.value.filter(q => q.sectionId === pillarId);
}

// Granular Input Analysis Filters & Expansions
const selectedPracticeFilter = ref('all');
const inputSortBy = ref('order');
const expandedInputQuestions = ref(new Set());
function toggleQuestionExpand(field) {
  const next = new Set(expandedInputQuestions.value);
  if (next.has(field)) {
    next.delete(field);
  } else {
    next.add(field);
  }
  expandedInputQuestions.value = next;
}
function isQuestionExpanded(field) {
  return expandedInputQuestions.value.has(field);
}

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

// Invitations State
const invitations = ref([]);
const submissionSourceFilter = ref('all');
const showCreateInviteModal = ref(false);
const inviteForm = reactive({
  invitation_name: '',
  expires_at: '',
  max_submissions: null,
});
const creatingInviteSaving = ref(false);
const generatedInviteLink = ref(null);

// Organisation Management Modals
const showCreateOrgModal = ref(false);
const createOrgName = ref('');
const creatingOrgSaving = ref(false);

const showEditOrgModal = ref(false);
const editOrgName = ref('');
const editingOrgSaving = ref(false);

const showDeleteOrgModal = ref(false);
const deletingOrgSaving = ref(false);

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
  const l = String(level).toLowerCase();
  if (l.includes('1') || l.includes('foundational')) return 'L1 Foundational';
  if (l.includes('2') || l.includes('early')) return 'L2 Early Progress';
  if (l.includes('3') || l.includes('developing')) return 'L3 Developing';
  if (l.includes('4') || l.includes('proficient')) return 'L4 Proficient';
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

const allQuestionsFlat = computed(() => {
  const respondents = detail.value?.respondents || [];
  const list = [];

  DEFAULT_SECTIONS.forEach(sec => {
    sec.questions.forEach((q, qIndex) => {
      let yes = 0, partially = 0, no = 0, notSure = 0;
      respondents.forEach(r => {
        const ansObj = typeof r.answers === 'string' ? JSON.parse(r.answers) : (r.answers || {});
        const rawAns = String(r[q.field] ?? ansObj[q.field] ?? r[q.field.toUpperCase()] ?? ansObj[q.field.toUpperCase()] ?? '').trim().toLowerCase();
        
        if (rawAns === 'yes' || rawAns === 'true' || rawAns === '1' || rawAns === 'often' || rawAns === 'always') {
          yes++;
        } else if (rawAns === 'partially' || rawAns === 'sometimes' || rawAns === 'partial' || rawAns === 'somewhat') {
          partially++;
        } else if (rawAns === 'no' || rawAns === 'false' || rawAns === '0' || rawAns === 'rarely' || rawAns === 'never') {
          no++;
        } else if (rawAns === 'not sure' || rawAns === 'not_sure' || rawAns === 'n/a' || rawAns === 'na' || rawAns === 'unsure' || rawAns === 'not applicable') {
          notSure++;
        } else if (rawAns) {
          notSure++;
        }
      });
      const total = yes + partially + no + notSure;
      const denom = total > 0 ? total : 1;
      const yesPct = total > 0 ? Math.round((yes / denom) * 100) : 0;
      const partiallyPct = total > 0 ? Math.round((partially / denom) * 100) : 0;
      const noPct = total > 0 ? Math.round((no / denom) * 100) : 0;
      const notSurePct = total > 0 ? Math.round((notSure / denom) * 100) : 0;

      const marksEarned = (yes * 4) + (partially * 2);
      const maxMarks = total > 0 ? (total * 4) : 4;
      const questionScore = maxMarks > 0 ? Math.round((marksEarned / maxMarks) * 4 * 100) / 100 : 0;
      const questionPct = maxMarks > 0 ? Math.round((marksEarned / maxMarks) * 100) : 0;

      let practiceFlag = 'developing';
      if (yesPct >= 60) practiceFlag = 'strong';
      else if (noPct >= 40) practiceFlag = 'gap';
      else if (notSurePct >= 40) practiceFlag = 'awareness';

      const formulaText = `${yes} Yes × 4 marks + ${partially} Partially × 2 marks = ${marksEarned} marks earned out of ${maxMarks} max (${questionPct}%)`;

      list.push({
        field: q.field,
        qNumber: parseInt(q.field.replace(/\D/g, '')) || (qIndex + 5),
        sectionId: sec.id,
        sectionTitle: sec.title,
        short: q.short,
        text: q.text,
        marksEarned,
        maxMarks,
        questionScore,
        questionPct,
        practiceFlag,
        formulaText,
        stats: {
          yes,
          partially,
          no,
          notSure,
          total,
          yesPct,
          partiallyPct,
          noPct,
          notSurePct,
        }
      });
    });
  });

  return list;
});

const pillarScorecards = computed(() => {
  const avgs = currentScore.value?.section_avgs || {};
  const levels = currentScore.value?.section_levels || {};
  const respondents = detail.value?.respondents || [];
  const allQs = allQuestionsFlat.value;

  return DEFAULT_SECTIONS.map(s => {
    const score = avgs[s.id] != null ? avgs[s.id] : 0;
    const level = levels[s.id] || (score <= 6 ? 'Level 1 — Foundational' : score <= 14 ? 'Level 2 — Early Progress' : 'Level 3 — Developing');

    // Aggregate metrics across the 5 questions belonging to this pillar
    const pQs = allQs.filter(q => q.sectionId === s.id);
    let aggYes = 0, aggPartially = 0, aggNo = 0, aggNotSure = 0;
    let aggMarksEarned = 0, aggMaxMarks = 0;

    pQs.forEach(q => {
      aggYes += q.stats.yes;
      aggPartially += q.stats.partially;
      aggNo += q.stats.no;
      aggNotSure += q.stats.notSure;
      aggMarksEarned += q.marksEarned;
      aggMaxMarks += q.maxMarks;
    });

    const totalResponses = aggYes + aggPartially + aggNo + aggNotSure;
    const denom = totalResponses > 0 ? totalResponses : 1;
    const yesPct = totalResponses > 0 ? Math.round((aggYes / denom) * 100) : 0;
    const partiallyPct = totalResponses > 0 ? Math.round((aggPartially / denom) * 100) : 0;
    const noPct = totalResponses > 0 ? Math.round((aggNo / denom) * 100) : 0;
    const notSurePct = totalResponses > 0 ? Math.round((aggNotSure / denom) * 100) : 0;

    return {
      id: s.id,
      title: s.title,
      icon: s.icon,
      summary: s.summary,
      points: s.points,
      score: score,
      level: level,
      agg: {
        totalResponses,
        employeeCount: respondents.length,
        yes: aggYes,
        partially: aggPartially,
        no: aggNo,
        notSure: aggNotSure,
        yesPct,
        partiallyPct,
        noPct,
        notSurePct,
        yesMarks: aggYes * 4,
        partiallyMarks: aggPartially * 2,
        rawMarksEarned: aggMarksEarned,
        maxRawMarks: aggMaxMarks,
        weightedContribution: (score * 0.125).toFixed(3),
      }
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
    const ans = typeof r.answers === 'string' ? JSON.parse(r.answers) : (r.answers || {});
    let rawVal = ans[dimKey] ?? r[dimKey];
    if (rawVal === undefined || rawVal === null || rawVal === '') {
      rawVal = ans['demo_' + dimKey] ?? 'Not Specified';
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
      if (s != null && s !== 'NA') groups[val].sectionScores[k].push(parseFloat(s));
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
    const leadGroup = activeSegmentData.value.find(g => g.name.toLowerCase().includes('lead') || g.name.toLowerCase().includes('exec') || g.name.toLowerCase().includes('c-suite') || g.name.toLowerCase().includes('manager'));
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

const filteredQuestionsList = computed(() => {
  let list = allQuestionsFlat.value;

  // Pillar filter
  if (selectedInputPillar.value !== 'all') {
    list = list.filter(q => q.sectionId === selectedInputPillar.value);
  }

  // Practice flag filter
  if (selectedPracticeFilter.value !== 'all') {
    list = list.filter(q => q.practiceFlag === selectedPracticeFilter.value);
  }

  // Search query
  if (inputSearchQuery.value.trim()) {
    const q = inputSearchQuery.value.toLowerCase().trim();
    list = list.filter(item =>
      item.text.toLowerCase().includes(q) ||
      item.short.toLowerCase().includes(q) ||
      item.field.toLowerCase().includes(q)
    );
  }

  // Sorting
  if (inputSortBy.value === 'score_asc') {
    list = [...list].sort((a, b) => a.questionScore - b.questionScore);
  } else if (inputSortBy.value === 'score_desc') {
    list = [...list].sort((a, b) => b.questionScore - a.questionScore);
  } else {
    list = [...list].sort((a, b) => a.qNumber - b.qNumber);
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
  if (!org.is_virtual) {
    fetchInvitations(org.id);
  }
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

// Invitations Management
async function fetchInvitations(orgId) {
  if (!orgId) return;
  try {
    const data = await getOrgInvitations(orgId);
    invitations.value = data || [];
  } catch (e) {
    console.error('Failed to fetch invitations:', e);
    invitations.value = [];
  }
}

async function handleCreateInvite() {
  if (!selectedOrg.value || selectedOrg.value.is_virtual) return;
  creatingInviteSaving.value = true;
  try {
    const data = await createOrgInvitation(selectedOrg.value.id, inviteForm);
    generatedInviteLink.value = data;
    await fetchInvitations(selectedOrg.value.id);
    showToast('Invitation created successfully!');
    showCreateInviteModal.value = false;
    inviteForm.invitation_name = '';
    inviteForm.expires_at = '';
    inviteForm.max_submissions = null;
  } catch (e) {
    showToast(e.message || 'Failed to create invitation', 'error');
  } finally {
    creatingInviteSaving.value = false;
  }
}

async function revokeInvitation(invId) {
  if (!confirm('Are you sure you want to revoke this invitation? The link will no longer work.')) return;
  try {
    await revokeOrgInvitation(invId);
    showToast('Invitation revoked successfully');
    await fetchInvitations(selectedOrg.value.id);
  } catch (e) {
    showToast(e.message || 'Failed to revoke invitation', 'error');
  }
}

async function regenerateInvitation(invId) {
  if (!confirm('This will generate a new token and invalidate the old link. Continue?')) return;
  try {
    const data = await regenerateOrgInvitation(invId);
    generatedInviteLink.value = data;
    showToast('Invitation regenerated with new token!');
    await fetchInvitations(selectedOrg.value.id);
  } catch (e) {
    showToast(e.message || 'Failed to regenerate invitation', 'error');
  }
}

function copyText(text) {
  navigator.clipboard.writeText(text).then(() => {
    showToast('Copied to clipboard!');
  }).catch(() => {
    showToast('Failed to copy', 'error');
  });
}

function copyOrgAuditLink() {
  if (!selectedOrg.value || selectedOrg.value.is_virtual) return;
  
  // Build the audit URL with org name pre-filled
  const baseUrl = window.location.origin;
  const orgName = encodeURIComponent(selectedOrg.value.name);
  const auditUrl = `${baseUrl}/audit?org=${orgName}`;
  
  copyText(auditUrl);
}

// Organisation Lifecycle Management
function openCreateOrgModal() {
  showCreateOrgModal.value = true;
  createOrgName.value = '';
}

async function handleCreateOrg() {
  if (!createOrgName.value.trim()) return;
  creatingOrgSaving.value = true;
  try {
    await createOrganisation(createOrgName.value.trim());
    showToast('Organisation created successfully!');
    showCreateOrgModal.value = false;
    createOrgName.value = '';
    await fetchOrgs();
  } catch (e) {
    showToast(e.message || 'Failed to create organisation', 'error');
  } finally {
    creatingOrgSaving.value = false;
  }
}

function openEditOrgModal(org) {
  showEditOrgModal.value = true;
  editOrgName.value = org.name;
}

async function handleUpdateOrg() {
  if (!selectedOrg.value || !editOrgName.value.trim()) return;
  editingOrgSaving.value = true;
  try {
    await updateOrganisation(selectedOrg.value.id, editOrgName.value.trim());
    showToast('Organisation updated successfully!');
    showEditOrgModal.value = false;
    editOrgName.value = '';
    await fetchOrgs();
  } catch (e) {
    showToast(e.message || 'Failed to update organisation', 'error');
  } finally {
    editingOrgSaving.value = false;
  }
}

function openDeleteOrgModal(org) {
  showDeleteOrgModal.value = true;
}

async function handleDeleteOrg() {
  if (!selectedOrg.value) return;
  deletingOrgSaving.value = true;
  try {
    await deleteOrganisation(selectedOrg.value.id);
    showToast('Organisation deleted successfully!');
    showDeleteOrgModal.value = false;
    selectedOrg.value = null;
    await fetchOrgs();
  } catch (e) {
    showToast(e.message || 'Failed to delete organisation', 'error');
  } finally {
    deletingOrgSaving.value = false;
  }
}

async function toggleOrgStatus(org) {
  try {
    await toggleOrganisationStatus(org.id);
    const newStatus = org.is_active === false ? 'activated' : 'deactivated';
    showToast(`Organisation ${newStatus} successfully!`);
    await fetchOrgs();
  } catch (e) {
    showToast(e.message || 'Failed to toggle organisation status', 'error');
  }
}

// Computed for filtered respondents
const filteredRespondents = computed(() => {
  const respondents = detail.value?.respondents || [];
  if (submissionSourceFilter.value === 'all') return respondents;
  if (submissionSourceFilter.value === 'direct') {
    return respondents.filter(r => !r.invited_by);
  }
  if (submissionSourceFilter.value === 'invited') {
    return respondents.filter(r => r.invited_by);
  }
  return respondents;
});

const countDirect = computed(() => {
  const respondents = detail.value?.respondents || [];
  return respondents.filter(r => !r.invited_by).length;
});

const countInvite = computed(() => {
  const respondents = detail.value?.respondents || [];
  return respondents.filter(r => r.invited_by).length;
});

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
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}

@media (max-width: 1024px) {
  .main-orgs-grid {
    grid-template-columns: 1fr;
    gap: 16px;
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
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.analysis-tabs-nav::-webkit-scrollbar {
  display: none;
}

.nav-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  min-height: 44px;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  color: #64748B;
  font-weight: 700;
  font-size: 0.88rem;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
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
  -webkit-overflow-scrolling: touch;
  width: 100%;
}

.modern-resp-table {
  width: 100%;
  min-width: 680px;
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
  white-space: nowrap;
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

.resp-score-cell {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.score-badge-inline {
  font-weight: 800;
  font-size: 0.88rem;
  color: var(--primary, #161057);
  white-space: nowrap;
  letter-spacing: -0.01em;
}

.score-level-inline {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: 700;
  line-height: 1.2;
  padding: 3px 8px;
  border-radius: 6px;
  white-space: nowrap;
  text-align: center;
  letter-spacing: 0.01em;
  flex-shrink: 0;
  box-sizing: border-box;
}

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

@media (max-width: 1024px) {
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
    align-items: stretch;
    gap: 14px;
  }
  .org-hero-left {
    flex: 1 1 100%;
    width: 100%;
  }
  .org-hero-right {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  .hero-score-stat {
    width: 100%;
    align-items: flex-start;
    text-align: left;
    background: #F8FAFC;
    border: 1.5px solid #E2E8F0;
    border-radius: 10px;
    padding: 10px 14px;
    box-sizing: border-box;
  }
  .org-hero-actions {
    width: 100%;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  .org-hero-actions .btn {
    flex: 1 1 calc(50% - 4px);
    min-height: 44px;
    justify-content: center;
    padding: 8px 12px;
    font-size: 0.82rem;
  }
  .pillars-cards-grid {
    grid-template-columns: 1fr;
  }
  .highlights-grid {
    grid-template-columns: 1fr;
  }
  .segment-groups-grid {
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
    flex: 1 1 100%;
  }
  .hero-score-stat {
    align-items: flex-start;
    text-align: left;
  }
}

/* Dual Assessment Entry & Org Management Enhancements */
.btn-new-org-sm {
  background: #047C69;
  color: #FFFFFF;
  border: none;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s ease;
}
.btn-new-org-sm:hover {
  background: #036858;
}

.pill-status-active-badge {
  font-size: 0.75rem;
  font-weight: 700;
  color: #065F46;
  background: #D1FAE5;
  padding: 0.2rem 0.6rem;
  border-radius: 99px;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}

.pill-status-inactive-badge {
  font-size: 0.75rem;
  font-weight: 700;
  color: #92400E;
  background: #FEF3C7;
  padding: 0.2rem 0.6rem;
  border-radius: 99px;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}

.btn-icon-only {
  font-size: 0.8rem;
  padding: 0.45rem 0.75rem;
}

.btn-danger-action {
  color: #DC2626 !important;
  border-color: #FCA5A5 !important;
}
.btn-danger-action:hover {
  background: #FEF2F2 !important;
}

.resp-source-filter-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.875rem;
  padding: 0.5rem 0.75rem;
  background: #F9FAFB;
  border-radius: 8px;
  border: 1px solid #E5E7EB;
  flex-wrap: wrap;
}

.rsf-label {
  font-size: 0.78rem;
  font-weight: 600;
  color: #6B7280;
}

.rsf-pill {
  border: 1px solid #D1D5DB;
  background: #FFFFFF;
  color: #374151;
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.25rem 0.65rem;
  border-radius: 99px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.rsf-pill:hover {
  border-color: #9CA3AF;
}

.rsf-pill.active {
  background: #161057;
  color: #FFFFFF;
  border-color: #161057;
}

.pill-source-invite {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: #047C69;
  background: #E6F4F1;
  padding: 0.2rem 0.55rem;
  border-radius: 99px;
  border: 1px solid rgba(4, 124, 105, 0.2);
}

.pill-source-direct {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: #4B5563;
  background: #F3F4F6;
  padding: 0.2rem 0.55rem;
  border-radius: 99px;
  border: 1px solid #E5E7EB;
}

.empty-invitations-card {
  text-align: center;
  padding: 3rem 1.5rem;
  background: #FFFFFF;
  border: 1px dashed #D1D5DB;
  border-radius: 12px;
  margin: 1.5rem 0;
}
.empty-invitations-card h4 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #111827;
  margin: 0.75rem 0 0.5rem;
}
.empty-invitations-card p {
  color: #6B7280;
  font-size: 0.9rem;
  margin-bottom: 1.25rem;
}

.inv-label-cell {
  display: flex;
  flex-direction: column;
}
.inv-id-muted {
  font-size: 0.7rem;
  color: #9CA3AF;
  font-family: monospace;
}

.badge-uses {
  font-size: 0.8rem;
  font-weight: 600;
  color: #374151;
  background: #F3F4F6;
  padding: 0.2rem 0.5rem;
  border-radius: 6px;
}

.pill-status-active {
  font-size: 0.72rem;
  font-weight: 700;
  color: #065F46;
  background: #D1FAE5;
  padding: 0.2rem 0.5rem;
  border-radius: 99px;
}
.pill-status-expired {
  font-size: 0.72rem;
  font-weight: 700;
  color: #92400E;
  background: #FEF3C7;
  padding: 0.2rem 0.5rem;
  border-radius: 99px;
}
.pill-status-revoked {
  font-size: 0.72rem;
  font-weight: 700;
  color: #991B1B;
  background: #FEE2E2;
  padding: 0.2rem 0.5rem;
  border-radius: 99px;
}

.inv-action-btns {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}
.btn-action-sm {
  border: 1px solid #D1D5DB;
  background: #FFFFFF;
  padding: 0.25rem 0.55rem;
  border-radius: 6px;
  font-size: 0.72rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-regen-token {
  color: #1E40AF;
  border-color: #BFDBFE;
}
.btn-regen-token:hover {
  background: #EFF6FF;
}
.btn-revoke-token {
  color: #DC2626;
  border-color: #FECACA;
}
.btn-revoke-token:hover {
  background: #FEF2F2;
}

.modal-card-sm {
  max-width: 440px !important;
}
.modal-card-md {
  max-width: 540px !important;
}
.field-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}
.inv-copy-row {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.4rem;
}
.inv-link-input {
  font-family: monospace;
  font-size: 0.85rem;
  background: #F9FAFB !important;
}
.inv-security-note {
  font-size: 0.8rem;
  color: #4B5563;
  line-height: 1.45;
  background: #F3F4F6;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-top: 1rem;
}

/* ==========================================================================
   TAB 6: Invitations & Links
   ========================================================================== */
.invitations-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.invitations-header-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.ihc-left {
  flex: 1;
}

.ihc-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--primary, #161057);
  margin-bottom: 6px;
}

.ihc-subtitle {
  font-size: 0.95rem;
  color: #6b7280;
  line-height: 1.5;
}

.invitations-empty-state {
  background: white;
  border-radius: 12px;
  padding: 60px 32px;
  text-align: center;
  border: 1.5px dashed #d1d5db;
}

.ies-icon {
  font-size: 3.5rem;
  margin-bottom: 16px;
}

.invitations-empty-state h4 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--primary, #161057);
  margin-bottom: 8px;
}

.invitations-empty-state p {
  color: #6b7280;
  margin-bottom: 20px;
}

.invitations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
  gap: 16px;
}

.invitation-card {
  background: white;
  border-radius: 12px;
  border: 1.5px solid #e5e7eb;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.invitation-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 2px 8px rgba(22, 16, 87, 0.08);
}

.invitation-card.inv-expired {
  opacity: 0.65;
  background: #f9fafb;
}

.invc-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.invc-name {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--primary, #161057);
  margin-bottom: 8px;
}

.invc-meta-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.invc-tag {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  border: 1px solid;
}

.invc-tag-active {
  background: #d1fae5;
  color: #065f46;
  border-color: #6ee7b7;
}

.invc-tag-inactive {
  background: #fee2e2;
  color: #991b1b;
  border-color: #fca5a5;
}

.invc-tag-expires,
.invc-tag-limit,
.invc-tag-unlimited {
  background: #e0e7ff;
  color: #3730a3;
  border-color: #a5b4fc;
}

.invc-link-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.invc-link-display {
  flex: 1;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 10px 14px;
  overflow: hidden;
}

.invc-link-code {
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 0.85rem;
  color: #4b5563;
  word-break: break-all;
}

.invc-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f3f4f6;
}

.invc-created {
  font-size: 0.85rem;
  color: #9ca3af;
}

.invc-actions {
  display: flex;
  gap: 12px;
}

.btn-text-action {
  background: none;
  border: none;
  color: var(--primary, #161057);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s ease;
}

.btn-text-action:hover {
  background: #f3f4f6;
}

.invitations-info-box {
  background: #eff6ff;
  border: 1.5px solid #bfdbfe;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  gap: 16px;
}

.iib-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.iib-content h5 {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--primary, #161057);
  margin-bottom: 10px;
}

.iib-content ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.iib-content li {
  font-size: 0.9rem;
  color: #374151;
  line-height: 1.5;
  padding-left: 20px;
  position: relative;
}

.iib-content li::before {
  content: '•';
  position: absolute;
  left: 6px;
  color: #3b82f6;
  font-weight: 700;
}


/* =====================================================================
   NIWI SCORE TRANSPARENCY & RESPONSIVE REFINEMENTS
   ===================================================================== */

/* Sidebar Independent Scrolling Fix */
.org-sidebar-card {
  position: sticky !important;
  top: 85px !important;
  max-height: calc(100vh - 105px) !important;
  display: flex !important;
  flex-direction: column !important;
  overflow: hidden !important;
}

.osc-collapsible-body {
  display: flex !important;
  flex-direction: column !important;
  flex: 1 !important;
  min-height: 0 !important;
  overflow: hidden !important;
}

.sidebar-orgs-list {
  display: flex !important;
  flex-direction: column !important;
  gap: 8px !important;
  flex: 1 !important;
  min-height: 0 !important;
  max-height: calc(100vh - 280px) !important;
  overflow-y: auto !important;
  padding-right: 6px !important;
  scrollbar-width: thin;
  scrollbar-color: #CBD5E1 transparent;
}

.sidebar-orgs-list::-webkit-scrollbar {
  width: 6px;
}
.sidebar-orgs-list::-webkit-scrollbar-track {
  background: transparent;
}
.sidebar-orgs-list::-webkit-scrollbar-thumb {
  background: #CBD5E1;
  border-radius: 4px;
}

/* Organisation Overview Header */
.hero-header-left {
  text-align: left;
  margin-bottom: 12px;
}
.hero-title {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 2rem;
  font-weight: 800;
  color: var(--primary, #161057);
  letter-spacing: -0.02em;
  margin-bottom: 6px;
}
.hero-subtitle {
  font-size: 0.95rem;
  color: #475569;
  max-width: 800px;
  line-height: 1.5;
}

/* How Was This Organisation's Score Calculated Card */
.score-explanation-card {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 14px;
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.08);
  padding: 20px;
  margin-bottom: 20px;
}
.sec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.sec-title {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--primary, #161057);
}
.sec-badge {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 3px 10px;
  background: #EEF2FF;
  color: #3730A3;
  border-radius: 999px;
  border: 1px solid #C7D2FE;
}
.sec-intro {
  font-size: 0.85rem;
  color: #475569;
  line-height: 1.5;
  margin-bottom: 16px;
}
.formula-callout {
  background: #F8FAFC;
  border: 1.5px dashed #CBD5E1;
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 16px;
}
.formula-callout-title {
  font-size: 0.76rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--primary, #161057);
  margin-bottom: 4px;
  display: block;
}
.formula-callout code {
  display: block;
  font-family: monospace;
  font-size: 0.84rem;
  color: #0F172A;
  font-weight: 600;
}
.reconciliation-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
  text-align: left;
}
.reconciliation-table th {
  padding: 8px 12px;
  background: #F8FAFC;
  border-bottom: 2px solid var(--primary, #161057);
  font-weight: 700;
  color: var(--primary, #161057);
}
.reconciliation-table td {
  padding: 8px 12px;
  border-bottom: 1px solid #F1F5F9;
  color: #1E293B;
}
.reconciliation-table tfoot th {
  padding: 10px 12px;
  background: #FAF9F5;
  border-top: 2px solid var(--primary, #161057);
  color: var(--primary, #161057);
  font-weight: 800;
}
.reconciliation-table tr:hover td {
  background: #F8FAFC;
}

/* Pillar Card Actions & Inspection Drawer */
.pc-card-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 10px;
  margin-top: 10px;
  border-top: 1px solid #F1F5F9;
}
.btn-inspect-pillar {
  background: transparent;
  border: 1px solid #CBD5E1;
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--primary, #161057);
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-inspect-pillar:hover {
  background: #F1F5F9;
  border-color: var(--primary, #161057);
}
.pc-expanded-questions {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1.5px dashed #E2E8F0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.pc-question-mini-card {
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  padding: 8px 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.pc-qmini-left {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex: 1;
  min-width: 0;
}
.pc-qmini-badge {
  font-size: 0.68rem;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--primary, #161057);
  color: #FFFFFF;
  flex-shrink: 0;
}
.pc-qmini-text {
  font-size: 0.78rem;
  color: #334155;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.pc-qmini-right {
  display: flex;
  align-items: baseline;
  gap: 6px;
  flex-shrink: 0;
}
.pc-qmini-score {
  font-weight: 700;
  font-size: 0.85rem;
  color: var(--primary, #161057);
}
.pc-qmini-raw {
  font-size: 0.7rem;
  color: #64748B;
}

/* Tab 3: Granular Input Analysis Scoring Transparency */
.inputs-filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 12px;
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.08);
  padding: 12px 16px;
  margin-bottom: 14px;
}
.ifb-control-group {
  display: flex;
  align-items: center;
  gap: 6px;
}
.ifb-control-group label {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--primary, #161057);
  white-space: nowrap;
}
.ifb-control-group select {
  font-size: 0.82rem;
  padding: 6px 10px;
  border: 1.5px solid #CBD5E1;
  border-radius: 8px;
  background: #FFFFFF;
  color: #1E293B;
  outline: none;
  cursor: pointer;
}
.ifb-control-group select:focus {
  border-color: var(--primary, #161057);
}
.ifb-search-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #F8FAFC;
  border: 1.5px solid #CBD5E1;
  border-radius: 8px;
  padding: 4px 10px;
  flex: 1;
  min-width: 220px;
}
.ifb-search-wrap:focus-within {
  border-color: var(--primary, #161057);
  background: #FFFFFF;
}
.ifb-search-icon {
  color: #64748B;
}
.ifb-search-wrap input {
  border: none;
  outline: none;
  background: transparent;
  width: 100%;
  font-size: 0.82rem;
  color: #1E293B;
}
.ifb-clear-btn {
  background: transparent;
  border: none;
  color: #94A3B8;
  font-size: 0.8rem;
  cursor: pointer;
}

.inputs-transparency-banner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  background: #EFF6FF;
  border: 1.5px solid #93C5FD;
  border-radius: 10px;
  margin-bottom: 16px;
}
.itb-icon {
  font-size: 1.1rem;
  flex-shrink: 0;
}
.itb-text {
  font-size: 0.82rem;
  color: #1E3A8A;
  line-height: 1.5;
}

.qac-right-metrics {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.qac-score-pill {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 8px;
  padding: 4px 10px;
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
}
.qac-score-val {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--primary, #161057);
}
.qac-score-max {
  font-size: 0.72rem;
  color: #64748B;
  font-weight: 600;
}
.qac-score-pct {
  font-size: 0.74rem;
  color: var(--accent, #04907C);
  font-weight: 700;
}

.qac-scoring-transparency-box {
  margin-top: 14px;
  background: #F8FAFC;
  border: 1.5px dashed #CBD5E1;
  border-radius: 10px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.qstb-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.qstb-title {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--primary, #161057);
}
.qstb-toggle-btn {
  background: #FFFFFF;
  border: 1px solid var(--primary, #161057);
  border-radius: 6px;
  padding: 3px 10px;
  font-size: 0.74rem;
  font-weight: 600;
  color: var(--primary, #161057);
  cursor: pointer;
  transition: all 0.15s ease;
}
.qstb-toggle-btn:hover {
  background: var(--primary, #161057);
  color: #FFFFFF;
}
.qstb-formula code {
  display: block;
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 6px;
  padding: 6px 10px;
  font-family: monospace;
  font-size: 0.78rem;
  color: #1E293B;
  overflow-x: auto;
}
.qstb-meta-row {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  font-size: 0.76rem;
  color: #475569;
}

.qstb-table-wrap {
  margin-top: 6px;
  overflow-x: auto;
}
.q-breakdown-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.78rem;
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  overflow: hidden;
}
.q-breakdown-table th {
  background: #F1F5F9;
  padding: 6px 10px;
  font-weight: 700;
  color: var(--primary, #161057);
  border-bottom: 1.5px solid #CBD5E1;
}
.q-breakdown-table td {
  padding: 6px 10px;
  border-bottom: 1px solid #F1F5F9;
  color: #334155;
}
.q-breakdown-table tfoot th {
  background: #F8FAFC;
  border-top: 1.5px solid var(--primary, #161057);
  color: var(--primary, #161057);
  font-weight: 700;
}
.opt-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
}
.dot-yes { background: #04907C; }
.dot-partially { background: #F59E0B; }
.dot-no { background: #EF4444; }
.dot-notsure { background: #94A3B8; }

/* Tab 4 Table Overflow & Actions column visibility fix */
.table-container {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 12px;
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.08);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  width: 100%;
  padding-bottom: 2px;
}
.modern-resp-table {
  width: 100%;
  min-width: 780px;
  border-collapse: collapse;
  text-align: left;
}
.btn-icon-direct {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1.5px solid #CBD5E1;
  border-radius: 6px;
  background: #FFFFFF;
  color: var(--primary, #161057);
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-icon-direct:hover {
  background: var(--primary, #161057);
  color: #FFFFFF;
  border-color: var(--primary, #161057);
}

/* =====================================================================
   CORE PILLARS REDESIGN & VIBRANT RESPONSE DISTRIBUTION BARS
   ===================================================================== */

/* 2-Column Responsive Layout for 8 Core Pillars on Desktop */
.pillars-cards-grid {
  display: grid !important;
  grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  gap: 22px !important;
  align-items: start !important;
}

@media (max-width: 1024px) {
  .pillars-cards-grid {
    grid-template-columns: 1fr !important;
  }
}

.pillar-card {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 14px;
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.08);
  padding: 22px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  transition: all 0.2s ease;
}

.pillar-card.card-expanded {
  box-shadow: 3px 3px 0px rgba(22, 16, 87, 0.12);
  border-color: var(--primary, #161057);
}

/* Pillar Aggregated Responses Card Box */
.pillar-agg-box {
  background: #F8FAFC;
  border: 1.5px solid #CBD5E1;
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 4px;
}

.pab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.pab-title {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--primary, #161057);
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.pab-count-badge {
  font-size: 0.74rem;
  font-weight: 600;
  color: #334155;
  background: #FFFFFF;
  border: 1px solid #CBD5E1;
  border-radius: 99px;
  padding: 2px 10px;
}

/* Horizontally Stacked Distribution Bars with NIWI Colors */
.pab-distribution-bar,
.qac-distribution-bar {
  display: flex !important;
  width: 100% !important;
  height: 12px !important;
  border-radius: 999px !important;
  overflow: hidden !important;
  background: #E2E8F0 !important;
  border: 1px solid #CBD5E1 !important;
}

.pab-seg,
.bar-seg {
  height: 100% !important;
  transition: width 0.3s ease;
}

.pab-seg-empty,
.bar-seg-empty {
  height: 100%;
  width: 100%;
  background: #E2E8F0;
}

/* Strict Color Mapping: Teal, Amber, Coral, Grey */
.pab-yes,
.bar-seg.bar-yes {
  background-color: #04907C !important;
}

.pab-partially,
.bar-seg.bar-partially {
  background-color: #F59E0B !important;
}

.pab-no,
.bar-seg.bar-no {
  background-color: #E05A47 !important;
}

.pab-notsure,
.bar-seg.bar-notsure {
  background-color: #94A3B8 !important;
}

/* Legends */
.pab-legend,
.qac-bar-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 0.76rem;
  color: #334155;
}

.pab-leg-item,
.leg-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.leg-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* Marks Breakdown Summary Box */
.pab-marks-summary {
  margin-top: 4px;
  padding-top: 10px;
  border-top: 1px dashed #CBD5E1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pms-formula code {
  display: block;
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 6px;
  padding: 6px 10px;
  font-family: monospace;
  font-size: 0.76rem;
  color: #0F172A;
  overflow-x: auto;
}

.pms-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

@media (max-width: 640px) {
  .pms-stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.pms-stat-col {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.pms-lbl {
  font-size: 0.68rem;
  color: #64748B;
  font-weight: 600;
  text-transform: uppercase;
}

.pms-val {
  font-size: 0.82rem;
  color: #1E293B;
}

.pms-badge {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  display: inline-block;
  width: fit-content;
}

/* Accordion Expand/Collapse Trigger */
.pc-accordion-action {
  margin-top: 4px;
}

.btn-pillar-accordion {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 10px 16px;
  background: #FAF9F5;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 8px;
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--primary, #161057);
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-pillar-accordion:hover {
  background: #EEF2FF;
  border-color: var(--primary, #161057);
}

.btn-pillar-accordion.expanded {
  background: var(--primary, #161057);
  color: #FFFFFF;
}

/* Expanded 5 Questions Drawer & Question Cards */
.pc-expanded-questions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 10px;
  padding-top: 14px;
  border-top: 1.5px dashed #CBD5E1;
}

.peq-intro-banner {
  font-size: 0.78rem;
  color: #475569;
  background: #EFF6FF;
  border: 1px solid #BFDBFE;
  border-radius: 6px;
  padding: 6px 10px;
}

.pillar-question-card {
  background: #FFFFFF;
  border: 1.5px solid #CBD5E1;
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.pqc-top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.pqc-left-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pqc-num-badge {
  background: var(--primary, #161057);
  color: #FFFFFF;
  font-size: 0.72rem;
  font-weight: 800;
  padding: 2px 7px;
  border-radius: 5px;
}

.pqc-short-title {
  font-size: 0.84rem;
  font-weight: 700;
  color: var(--primary, #161057);
}

.pqc-right-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pqc-score-pill {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 0.95rem;
  font-weight: 800;
  color: var(--primary, #161057);
  background: #F1F5F9;
  border: 1px solid #CBD5E1;
  border-radius: 6px;
  padding: 2px 8px;
}

.pqc-question-text {
  display: block !important;
  width: 100% !important;
  font-size: 0.86rem;
  color: #1E293B;
  line-height: 1.55;
  margin: 4px 0 6px 0;
  word-break: normal;
  white-space: normal;
}

.pqc-bar-wrap {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.pqc-calc-footnote {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  background: #F8FAFC;
  border: 1px dashed #E2E8F0;
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 0.74rem;
  color: #475569;
  font-family: monospace;
  margin-top: 4px;
}
</style>
