<template>
  <div class="form-page">

    <!-- Success screen -->
    <div v-if="submitted" class="success-wrap">
      <div class="success-box">
        <div class="success-icon">✓</div>
        <h2>Audit Submitted</h2>
        <p>Thank you for sharing your perspective. Every response helps build a more complete picture.</p>
        <p>Once all NIWI responses have been brought together, the Leadership team will receive a consolidated organizational report. A snapshot of the collective findings and key insights will also be shared with everyone who participated.</p>
      </div>
    </div>
    <div v-else-if="isLoading && currentStep > 0" class="success-wrap">
      <div class="success-box">
        <div class="loader-spinner"></div>
        <h2>Loading...</h2>
      </div>
    </div>

    <div v-else class="form-inner">
      <!-- Transition Wrapper for Smooth Fades -->
      <transition name="page-fade" mode="out-in">
      
      <!-- Full-Page Centered Animated Intro (Step 0) -->
      <div
        v-if="currentStep === 0"
        key="step-0"
        ref="introStageRef"
        :class="['intro-fullpage', { 'anim-ready': isAnimReady, 'anim-done': isAnimDone }]"
      >
        <!-- 2-Column Full Screen Hero Layout -->
        <div class="intro-hero-layout">
          <!-- Top Branding Row - Logo and Orchvate -->
          <div class="hero-top-branding">
            <div class="hero-badge-wrap">
              <img src="/logonew1.png" alt="NIWI Logo" class="niwi-brand-logo anim-hero-niwi" />
            </div>
            <div class="intro-branding">
              <span class="powered-by-text">Powered by</span>
              <img src="/logo_orchvate.png" alt="Orchvate" class="intro-orchvate-logo" />
            </div>
          </div>

          <!-- Content and Image Grid -->
          <div class="hero-content-wrapper">
            <!-- Left Column: Assessment Details -->
            <div class="intro-hero-left">

            <!-- Phase 3: Main Headline -->
            <h1 class="hero-title anim-hero-headline" @click="onLogoClick">
              Neuro-Inclusive Workplace Index (NIWI) Self-Assessment
            </h1>

            <!-- Phase 4: Staggered Descriptions -->
            <p class="hero-desc anim-hero-p1">
              Neuro-inclusion in the workplace is an emerging priority. Approximately 15% of people are neurodivergent (e.g., autistic, dyslexic, ADHD), bringing diverse perspectives and valuable strengths such as creativity, innovation, and attention to detail.
            </p>

            <p class="hero-desc anim-hero-p2">
              The Neuro-Inclusive Workplace Index (NIWI) is a structured self-assessment designed to help C-suite, HR, and DEI leaders understand and strengthen their organisation's approach to neuro-inclusion. It covers key segments across the employee lifecycle, customer experience and wider ecosystem, providing a holistic view of current practices.
            </p>

            <div class="hero-highlight-box anim-hero-p3">
              <p class="hero-desc-boxed">
                <strong>NIWI is not a ranking tool.</strong> It is a reflection-based index designed to help organisations understand where they are today and identify priorities for meaningful action.
              </p>
            </div>

            <!-- Time and perspective badges -->
            <div class="hero-info-badges anim-hero-p4">
              <div class="info-badge badge-time">
                <span class="badge-icon">⏱</span>
                <span class="badge-text">Approximately 20 minutes</span>
              </div>
              <div class="info-badge badge-perspective">
                <span class="badge-icon">👥</span>
                <span class="badge-text">Every perspective adds to the picture</span>
              </div>
            </div>

            <p class="hero-note anim-hero-p5">
              <em>Answer based on your organisation's current reality, not intention.</em>
            </p>

            <!-- Phase 4: Next Button -->
            <div class="hero-btn-row anim-hero-cta">
              <button class="btn-next hero-cta-btn" @click="nextStep" type="button">
                Next &rarr;
              </button>
            </div>
          </div>

          <!-- Right Column: Illustration Image -->
          <div class="intro-hero-right anim-hero-visual">
            <div class="clipart-card">
              <img
                src="/images/AI Brain Hub with Flowing Icon Streams.png"
                alt="Neuro-inclusive workplace illustration showing AI brain hub with diverse organizational elements flowing"
                class="niwi-hero-image"
              />
            </div>
            <div class="perspectives-box">
              <div class="perspectives-label">MULTIPLE PERSPECTIVES</div>
              <div class="perspectives-flow">Understand → Prioritise → Act</div>
            </div>
          </div>
          </div>
        </div>
      </div>

      <!-- Why This Matters Page (Step 1) -->
      <div
        v-else-if="currentStep === 1"
        key="step-1"
        class="why-matters-page"
        ref="whyMattersPageRef"
        @scroll="onPageScroll"
      >
        <!-- Compact Top Header with Logo and Progress -->
        <header class="why-matters-header">
          <div class="why-header-left">
            <img src="/logonew1.png" alt="NIWI" class="why-niwi-logo" />
            <span class="why-niwi-text">Neuro-Inclusive<br/>Workplace Index</span>
          </div>
          <div class="why-header-right">
            <span class="powered-by-label">POWERED BY</span>
            <img src="/logo_orchvate.png" alt="Orchvate" class="orchvate-logo-compact" />
          </div>
        </header>

        <!-- Three Section Layout -->
        <div class="why-matters-content">
          <!-- Section 1: Why This Matters (Full Width) -->
          <div class="why-section-box section-1">
            <div class="flow-header-area">
              <div class="flow-badge-wrapper">
                <span class="flow-category-tag tag-purple">WHY THIS MATTERS</span>
              </div>
              <h2 class="flow-main-heading">Understanding current realities to drive change</h2>
              <p class="flow-subtitle">NIWI helps leaders move beyond isolated initiatives and examine inclusion across the organisation.</p>
            </div>
            <div class="section-1-paragraphs">
              <p class="section-text">
                <strong>Building neuro-inclusive workplaces</strong> is not just about policy, but about how inclusion is experienced every day. Understanding current realities is the first step towards creating meaningful and sustainable change.
              </p>
              <p class="section-text">
                <strong>Designed for C-suite, HR, DEI and business leaders</strong>, NIWI supports structured reflection and practical decision-making across the organisation and its wider ecosystem.
              </p>
            </div>
          </div>

          <!-- Section 2: What NIWI Helps You Do (Full Width Process Flow UI) -->
          <div class="why-section-box section-2">
            <div class="flow-header-area">
              <div class="flow-badge-wrapper">
                <span class="flow-category-tag tag-teal">WHAT NIWI HELPS YOU DO</span>
              </div>
              <h2 class="flow-main-heading">From organisational insight to focused action</h2>
              <p class="flow-subtitle">NIWI turns responses into a clear pathway for reflection, prioritisation and practical next steps.</p>
            </div>

            <div class="process-flow-container">
              <!-- Card 1 (Purple) -->
              <div class="process-flow-card card-purple">
                <div class="flow-card-top">
                  <div class="flow-circle-badge badge-purple">01</div>
                  <h3 class="flow-card-heading">See the<br/>Current State</h3>
                </div>
                <p class="flow-card-body">Create a shared baseline using responses that reflect what happens today.</p>
                <div class="flow-card-accent-bar bar-purple"></div>
              </div>

              <!-- Connector 1 -->
              <div class="flow-connector" aria-hidden="true">
                <div class="connector-line"></div>
                <svg class="connector-arrowhead navy-head" width="18" height="24" viewBox="0 0 18 24" fill="none">
                  <path d="M4 3L13 12L4 21" stroke="#161057" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>

              <!-- Card 2 (Teal) -->
              <div class="process-flow-card card-teal">
                <div class="flow-card-top">
                  <div class="flow-circle-badge badge-teal">02</div>
                  <h3 class="flow-card-heading">Surface<br/>Priorities</h3>
                </div>
                <p class="flow-card-body">Identify strengths, inconsistencies and areas where focused action may be needed.</p>
                <div class="flow-card-accent-bar bar-teal"></div>
              </div>

              <!-- Connector 2 -->
              <div class="flow-connector" aria-hidden="true">
                <div class="connector-line"></div>
                <svg class="connector-arrowhead navy-head" width="18" height="24" viewBox="0 0 18 24" fill="none">
                  <path d="M4 3L13 12L4 21" stroke="#161057" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>

              <!-- Card 3 (Amber) -->
              <div class="process-flow-card card-amber">
                <div class="flow-card-top">
                  <div class="flow-circle-badge badge-amber">03</div>
                  <h3 class="flow-card-heading">Shape the<br/>Roadmap</h3>
                </div>
                <p class="flow-card-body">Use dimension-level insights to guide conversations, ownership and next steps.</p>
                <div class="flow-card-accent-bar bar-amber"></div>
              </div>
            </div>

            <!-- Info Badges Row (Pill Bar) -->
            <div class="info-badges-pill-bar">
              <div class="info-pill-item">
                <span class="pill-badge-circle circle-amber">20</span>
                <span class="pill-badge-label">About 20 minutes</span>
              </div>
              <div class="info-pill-item">
                <span class="pill-badge-circle circle-amber">08</span>
                <span class="pill-badge-label">8 dimensions</span>
              </div>
              <div class="info-pill-item">
                <span class="pill-badge-circle circle-red">01</span>
                <span class="pill-badge-label">One organisational snapshot</span>
              </div>
            </div>
          </div>

          <!-- Section 3: Why Neuro-Inclusion Matters (Full Width) -->
          <div class="why-section-box section-3">
            <div class="flow-header-area">
              <div class="flow-badge-wrapper">
                <span class="flow-category-tag tag-amber">WHY NEURO-INCLUSION MATTERS</span>
              </div>
              <h2 class="flow-main-heading">Creating lasting impact across the organisation</h2>
              <p class="flow-subtitle">Building neuro-inclusive workplaces is not just about policy, but about how inclusion is experienced every day.</p>
            </div>
            <div class="benefits-cards-grid">
              <!-- Benefit 1: Mint -->
              <div class="benefit-card benefit-mint">
                <div class="benefit-icon-badge">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#161057" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="4"/>
                    <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>
                  </svg>
                </div>
                <h4 class="benefit-title">Unlocks Potential</h4>
                <p class="benefit-text">Neuro-inclusion helps organisations tap into diverse talent, ideas, and ways of thinking, driving innovation and better decision-making.</p>
              </div>

              <!-- Benefit 2: Amber -->
              <div class="benefit-card benefit-amber">
                <div class="benefit-icon-badge">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#161057" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                    <circle cx="9" cy="7" r="4"/>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                  </svg>
                </div>
                <h4 class="benefit-title">Stronger Teams</h4>
                <p class="benefit-text">When everyone can participate fully, teams become more collaborative, engaged, and resilient.</p>
              </div>

              <!-- Benefit 3: Blue -->
              <div class="benefit-card benefit-blue">
                <div class="benefit-icon-badge">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#161057" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="20" x2="18" y2="10"/>
                    <line x1="12" y1="20" x2="12" y2="4"/>
                    <line x1="6" y1="20" x2="6" y2="14"/>
                  </svg>
                </div>
                <h4 class="benefit-title">More Equitable Opportunities</h4>
                <p class="benefit-text">It helps identify and remove barriers, ensuring fair access to opportunities across the employee lifecycle.</p>
              </div>

              <!-- Benefit 4: Mint -->
              <div class="benefit-card benefit-mint">
                <div class="benefit-icon-badge">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#161057" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 22v-9"/>
                    <path d="M12 13a5 5 0 0 0 5-5c0-3-5-6-5-6s-5 3-5 6a5 5 0 0 0 5 5z"/>
                    <path d="M12 13a5 5 0 0 1-5-5"/>
                  </svg>
                </div>
                <h4 class="benefit-title">Lasting Impact</h4>
                <p class="benefit-text">Neuro-inclusive practices create workplaces where everyone can thrive, leading to sustainable business growth and positive social impact.</p>
              </div>
            </div>
          </div>



          <!-- Perspective Note (Rounded Pill Banner) -->
          <div class="perspective-note-pill">
            <div class="perspective-eye-icon" aria-hidden="true">
              <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                <circle cx="18" cy="18" r="16.5" stroke="#A5B4FC" stroke-width="2.2" fill="#FFFFFF"/>
                <circle cx="21" cy="14" r="5" fill="#161057"/>
              </svg>
            </div>
            <div class="perspective-pill-content">
              <h4 class="perspective-pill-title">Every perspective adds to the picture</h4>
              <p class="perspective-pill-desc">Views from across the organisation can help create a more complete understanding of current reality.</p>
            </div>
          </div>

          <!-- Inline Navigation Buttons (end of page content) -->
          <div class="inline-nav-bar">
            <button class="btn-back-compact" @click="currentStep = 0" type="button">← Back</button>
            <div></div>
            <button class="btn-next-compact" @click="nextStep" type="button">Let's Begin →</button>
          </div>
        </div>
      </div>

      <!-- Step content (Step 2+) with Consistent Header/Footer -->
      <div
        v-else
        key="step-other"
        class="unified-page"
        ref="unifiedPageRef"
        @scroll="onPageScroll"
      >
        <!-- Top Header -->
        <header class="why-matters-header">
          <div class="why-header-left" @click="onDevModeClick" style="cursor: pointer;" title="Click 5 times for developer mode">
            <img src="/logonew1.png" alt="NIWI" class="why-niwi-logo" />
            <span class="why-niwi-text">Neuro-Inclusive<br/>Workplace Index</span>
          </div>
          <div class="why-header-right">
            <span class="powered-by-label">POWERED BY</span>
            <img src="/logo_orchvate.png" alt="Orchvate" class="orchvate-logo-compact" />
          </div>
        </header>

        <!-- Main Content Area -->
        <div class="unified-content">
          <div class="unified-card">
            <div v-if="currentStep !== 3" class="step-card-head">
              <div class="step-head-meta">
                <div v-if="currentStep === 2" class="step-tag">Getting Started</div>
                <div v-else class="step-tag">Section {{ currentStep - 3 }} of {{ visibleSections.length }}</div>
              </div>
              <div class="step-head-row">
                <h1 class="h1-navy" @click="onLogoClick">{{ currentStep === 2 ? 'Tell Us About You' : (currentSection?.title || '') }}</h1>
                <p v-if="currentStep > 3" class="step-sub step-sub-inline">Select the answer that best reflects your organisation's current position.</p>
              </div>
              <p v-if="currentStep === 2" class="step-sub">
                The following demographic questions help us understand how neuro-inclusion experiences may vary across groups. Your responses will be analyzed in aggregate and treated confidentially.
              </p>
            </div>

            <div ref="questionsScroll" class="questions-scroll">
            <!-- Tell Us About You (Step 2) - Clean Professional Layout -->
            <div v-if="currentStep === 2" class="demographics-form">
              
              <!-- Section 1: About You -->
              <div class="section-card">
                <div class="section-header">
                  <div class="section-number">1</div>
                  <h2 class="section-title">About You</h2>
                </div>
                
                <div class="fields-grid">
                  <!-- Row 1: Name & Organization -->
                  <div class="field-group">
                    <label for="demo_name" class="field-label">Name <span class="optional-label">(Optional)</span></label>
                    <input
                      id="demo_name"
                      v-model="form.name"
                      type="text"
                      class="field-input"
                      placeholder="Enter your name"
                    />
                  </div>

                  <div class="field-group">
                    <label for="demo_company" class="field-label">Organization Name *</label>
                    <input
                      id="demo_company"
                      v-model="form.company_name"
                      type="text"
                      class="field-input"
                      :class="{ 'input-error': errors.company_name }"
                      placeholder="Enter your organization name"
                    />
                    <span v-if="errors.company_name" class="error-message">{{ errors.company_nameMsg || 'Required' }}</span>
                  </div>

                  <!-- Row 2: Email & Function -->
                  <div class="field-group">
                    <label for="demo_email" class="field-label">Email ID *</label>
                    <input
                      id="demo_email"
                      v-model="form.email"
                      type="email"
                      class="field-input"
                      :class="{ 'input-error': errors.email }"
                      placeholder="name@company.com"
                    />
                    <span class="helper-text">Required solely to receive your personalized feedback.</span>
                    <span v-if="errors.email" class="error-message">{{ errors.emailMsg || 'Required' }}</span>
                  </div>

                  <div class="field-group">
                    <label for="demo_function" class="field-label">Which function do you primarily work in? *</label>
                    <AnimatedSelect
                      id="demo_function"
                      v-model="form.function"
                      :options="functionOptions"
                      placeholder="Select your function"
                      :error="!!errors.function"
                      @change="() => {}"
                    />
                    <span v-if="errors.function" class="error-message">{{ errors.functionMsg || 'Please select your function' }}</span>
                  </div>

                  <!-- Conditional: Other Function -->
                  <div v-if="form.function === 'Other'" class="field-group full-width">
                    <label for="demo_function_other" class="field-label">Please specify your function *</label>
                    <input
                      id="demo_function_other"
                      v-model="form.function_other"
                      type="text"
                      class="field-input"
                      :class="{ 'input-error': errors.function_other }"
                      placeholder="Specify your function"
                    />
                    <span v-if="errors.function_other" class="error-message">{{ errors.function_otherMsg }}</span>
                  </div>

                  <!-- Row 3: Country & State -->
                  <div class="field-group">
                    <label for="demo_country" class="field-label">Country of Work Location *</label>
                    <SearchableSelect
                      id="demo_country"
                      v-model="form.country"
                      :options="countryOptions"
                      placeholder="Search and select your country"
                      :error="!!errors.country"
                      @change="onCountryChange"
                    />
                    <span v-if="errors.country" class="error-message">{{ errors.countryMsg }}</span>
                  </div>

                  <div v-if="form.country === 'India'" class="field-group">
                    <label for="demo_state_ut" class="field-label">(If India) Which State or Union Territory are you currently based in? *</label>
                    <AnimatedSelect
                      id="demo_state_ut"
                      v-model="form.state_ut"
                      :options="[...indianStates, ...indianUTs]"
                      placeholder="Select your state / union territory"
                      :error="!!errors.state_ut"
                      @change="() => {}"
                    />
                    <span v-if="errors.state_ut" class="error-message">{{ errors.state_utMsg }}</span>
                  </div>

                  <!-- Row 4: Current Role -->
                  <div class="field-group full-width">
                    <label class="field-label">Which best describes your current role? *</label>
                    <div class="radio-grid" :class="{ 'has-error': errors.role }">
                      <label
                        v-for="r in roleOptions"
                        :key="r"
                        class="radio-option"
                        :class="{ 'radio-selected': form.role === r }"
                      >
                        <input
                          type="radio"
                          name="demo_role"
                          :value="r"
                          v-model="form.role"
                          class="radio-input"
                        />
                        <span class="radio-circle"></span>
                        <span class="radio-text">{{ r }}</span>
                      </label>
                    </div>
                    <span v-if="errors.role" class="error-message">{{ errors.roleMsg }}</span>
                  </div>
                </div>
              </div>

              <!-- Section 2: Inclusion & Identity -->
              <div class="section-card">
                <div class="section-header">
                  <div class="section-number">2</div>
                  <h2 class="section-title">Inclusion & Identity</h2>
                </div>
                
                <p class="section-description">
                  The following questions help us understand representation and identify opportunities to improve accessibility, inclusion, and belonging. Responses will be analyzed in aggregate and treated confidentially.
                </p>

                <div class="questions-container">
                  <!-- Gender Identity -->
                  <div class="question-block">
                    <label class="field-label">How do you describe your gender identity? *</label>
                    <div class="radio-grid" :class="{ 'has-error': errors.gender }">
                      <label
                        v-for="g in genderOptions"
                        :key="g"
                        class="radio-option"
                        :class="{ 'radio-selected': form.gender === g }"
                      >
                        <input
                          type="radio"
                          name="demo_gender"
                          :value="g"
                          v-model="form.gender"
                          class="radio-input"
                        />
                        <span class="radio-circle"></span>
                        <span class="radio-text">{{ g }}</span>
                      </label>
                    </div>
                    <span v-if="errors.gender" class="error-message">{{ errors.genderMsg }}</span>

                    <div v-if="form.gender === 'Other gender identity'" class="field-group mt-3">
                      <input
                        id="demo_gender_other"
                        v-model="form.gender_other"
                        type="text"
                        class="field-input"
                        placeholder="Self-describe (optional)"
                      />
                    </div>
                  </div>

                  <!-- Person with Disability -->
                  <div class="question-block">
                    <label class="field-label">Do you identify as a Person with Disability (PwD)? *</label>
                    <div class="radio-grid radio-grid-compact" :class="{ 'has-error': errors.is_pwd }">
                      <label
                        v-for="opt in pwdOptions"
                        :key="opt"
                        class="radio-option"
                        :class="{ 'radio-selected': form.is_pwd === opt }"
                      >
                        <input
                          type="radio"
                          name="demo_pwd"
                          :value="opt"
                          v-model="form.is_pwd"
                          class="radio-input"
                        />
                        <span class="radio-circle"></span>
                        <span class="radio-text">{{ opt }}</span>
                      </label>
                    </div>
                    <span v-if="errors.is_pwd" class="error-message">{{ errors.is_pwdMsg }}</span>
                  </div>

                  <!-- Neurodivergent -->
                  <div class="question-block">
                    <label class="field-label">Do you identify as neurodivergent? *</label>
                    <p class="question-helper">
                      Neurodivergent may include ADHD, autism, dyslexia, dyspraxia, and other cognitive or neurological differences.
                    </p>
                    <div class="radio-grid" :class="{ 'has-error': errors.is_neurodivergent }">
                      <label
                        v-for="opt in neurodivergentOptions"
                        :key="opt"
                        class="radio-option"
                        :class="{ 'radio-selected': form.is_neurodivergent === opt }"
                      >
                        <input
                          type="radio"
                          name="demo_nd"
                          :value="opt"
                          v-model="form.is_neurodivergent"
                          class="radio-input"
                        />
                        <span class="radio-circle"></span>
                        <span class="radio-text">{{ opt }}</span>
                      </label>
                    </div>
                    <span v-if="errors.is_neurodivergent" class="error-message">{{ errors.is_neurodivergentMsg }}</span>
                  </div>

                  <!-- Underrepresented / Marginalized -->
                  <div class="question-block">
                    <label class="field-label">Do you identify as belonging to an underrepresented or historically marginalized community? *</label>
                    <p class="question-helper">
                      This may include economic, ethnic, religious, caste-based, LGBTQIA+, or other communities that have historically experienced exclusion or underrepresentation.
                    </p>
                    <div class="radio-grid radio-grid-compact" :class="{ 'has-error': errors.is_marginalized }">
                      <label
                        v-for="opt in marginalizedOptions"
                        :key="opt"
                        class="radio-option"
                        :class="{ 'radio-selected': form.is_marginalized === opt }"
                      >
                        <input
                          type="radio"
                          name="demo_marg"
                          :value="opt"
                          v-model="form.is_marginalized"
                          class="radio-input"
                        />
                        <span class="radio-circle"></span>
                        <span class="radio-text">{{ opt }}</span>
                      </label>
                    </div>
                    <span v-if="errors.is_marginalized" class="error-message">{{ errors.is_marginalizedMsg }}</span>
                  </div>

                  <!-- Consent Checkbox -->
                  <div class="consent-block">
                    <label class="consent-label">
                      <input type="checkbox" id="gdpr_consent" v-model="form.consent_given" class="consent-checkbox" />
                      <span class="consent-text">I consent to the collection and processing of my organisational data in accordance with the Privacy Policy. *</span>
                    </label>
                    <span v-if="errors.consent_given" class="error-message">You must provide consent to proceed.</span>
                  </div>
                </div>
              </div>

            </div>

            <!-- Instructions screen (step 3) -->
            <div v-else-if="currentStep === 3" class="instructions-screen">
              <div class="instr-layout">
                <!-- Left: Guide card -->
                <div class="instr-left-card">
                  <h2 class="instr-card-title">Before you begin</h2>
                  <p class="instr-card-subtitle">Here's what to expect before you begin the audit.</p>

                  <div class="instr-points-list">
                    <div class="instr-point-item">
                      <div class="instr-point-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                          <circle cx="12" cy="12" r="10"></circle>
                          <polyline points="12 6 12 12 16 14"></polyline>
                        </svg>
                      </div>
                      <p class="instr-point-text">
                        This should take approximately <strong>20 minutes</strong> to complete.
                      </p>
                    </div>

                    <div class="instr-point-divider"></div>

                    <div class="instr-point-item">
                      <div class="instr-point-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                          <polyline points="14 2 14 8 20 8"></polyline>
                          <line x1="16" y1="13" x2="8" y2="13"></line>
                          <line x1="16" y1="17" x2="8" y2="17"></line>
                          <polyline points="10 9 9 9 8 9"></polyline>
                        </svg>
                      </div>
                      <p class="instr-point-text">
                        The questionnaire covers up to <strong>8 key segments</strong>, each with <strong>5 statements</strong>.
                      </p>
                    </div>

                    <div class="instr-point-divider"></div>

                    <div class="instr-point-item">
                      <div class="instr-point-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                          <circle cx="9" cy="7" r="4"></circle>
                          <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                          <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                        </svg>
                      </div>
                      <p class="instr-point-text">
                        Please read each statement carefully and choose the option that best reflects your <strong>current reality</strong> rather than intention.
                      </p>
                    </div>
                  </div>

                  <!-- Example response options box -->
                  <div class="instr-example-box">
                    <span class="instr-example-label">Example response options</span>
                    <div class="instr-example-options">
                      <span class="instr-example-opt opt-yes">Yes</span>
                      <span class="instr-example-opt opt-partially">Partially</span>
                      <span class="instr-example-opt opt-no">No</span>
                      <span class="instr-example-opt opt-not-sure">Not Sure</span>
                    </div>
                    <div class="instr-privacy-note">
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                      </svg>
                      <span>Your responses will only include details that you choose to share.</span>
                    </div>
                  </div>

                  <!-- Decorative background botanical element -->
                  <div class="instr-botanical-bg" aria-hidden="true">
                    <svg viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M140 200C140 140 180 110 200 100C170 140 180 180 140 200Z" fill="#04907C" fill-opacity="0.12"/>
                      <path d="M110 200C110 130 160 90 190 70C150 120 160 170 110 200Z" fill="#04907C" fill-opacity="0.08"/>
                      <path d="M80 200C80 150 120 120 150 100C120 150 130 180 80 200Z" fill="#04907C" fill-opacity="0.05"/>
                    </svg>
                  </div>
                </div>

                <!-- Right: section descriptions -->
                <div class="instr-right">
                  <div class="instr-right-header">
                    <div class="instr-right-header-left">
                      <span class="instr-right-badge">WHAT EACH SEGMENT COVERS</span>
                      <h3 class="instr-right-title">The Segments Covered</h3>
                      <p class="instr-right-meta">
                        The audit is organised into 8 key segments, each with 5 statements covering different aspects of neuro-inclusion in the workplace.
                      </p>
                    </div>
                  </div>

                  <div class="instr-desc-grid">
                    <div v-for="(s, i) in sections" :key="s.id" class="instr-segment-card">
                      <div class="instr-seg-badge">{{ String(i + 1).padStart(2, '0') }}</div>
                      <div class="instr-seg-content">
                        <h4 class="instr-seg-title">{{ s.title }}</h4>
                        <p class="instr-seg-summary">{{ s.summary }}</p>
                      </div>
                      <div class="instr-seg-arrow">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                          <polyline points="9 18 15 12 9 6"></polyline>
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Section questions (step 3+) -->
            <div v-else class="questions-list">
              <div v-if="currentSection.liner" class="section-liner">
                {{ currentSection.liner }}
              </div>

              <!-- Supplier definition banner for Section 8 -->
              <div v-if="currentSection.id === 'sp'" class="supplier-definition-banner">
                <strong>Suppliers</strong> refer to any external individuals or organisations your organisation engages with, including consultants, freelancers, technology providers, agencies, partners, service providers and contractors.
              </div>

              <!-- Leading gating question (Sections 4 & 8) -->
              <div v-if="currentSection.gatingQuestion && form[currentSection.gatingField] !== 'Yes'" class="q-block gating-block leading-gating-block">
                <div class="gating-eligibility-label">Section Eligibility</div>
                <p class="q-text"><strong>{{ currentSection.gatingQuestion }}</strong></p>
                <div class="options">
                  <button
                    type="button"
                    :class="['opt-btn', form[currentSection.gatingField] === 'Yes' ? 'selected' : '']"
                    @click="form[currentSection.gatingField] = 'Yes'"
                  >Yes</button>
                  <button
                    type="button"
                    :class="['opt-btn', form[currentSection.gatingField] === 'No' ? 'selected' : '']"
                    @click="form[currentSection.gatingField] = 'No'"
                  >No</button>
                </div>
                <p class="gating-guidance">If a context exists—even occasionally—the question is applicable. Please answer based on how these environments are typically experienced, not how often they are used.</p>
                <span v-if="errors[currentSection.gatingField]" class="field-err">Please select an answer</span>
              </div>

              <!-- Gating answered Yes: show compact confirmed badge so user can still change -->
              <div v-if="currentSection.gatingQuestion && form[currentSection.gatingField] === 'Yes'" class="gating-confirmed-badge">
                <span class="gating-confirmed-check">✓</span>
                <span class="gating-confirmed-text">{{ currentSection.gatingQuestion }}</span>
                <button type="button" class="gating-change-btn" @click="form[currentSection.gatingField] = ''">Change</button>
              </div>

              <!-- Section skipped notice -->
              <div v-if="currentSection.gatingQuestion && form[currentSection.gatingField] === 'No'" class="section-skipped-notice">
                <div class="skipped-notice-icon">⊘</div>
                <div>
                  <span class="skipped-heading">This section is not applicable to your organisation.</span>
                  <p>You can safely skip this section. Please click <strong>Next</strong> to continue.</p>
                </div>
              </div>

              <!-- Questions — only shown when gating is passed or section has no gating -->
              <template v-if="!currentSection?.gatingQuestion || form[currentSection.gatingField] === 'Yes'">
                <div v-for="(q, qi) in (currentSection?.questions || [])" :key="q.field" class="q-block" v-show="!q.depends_on_field || form[q.depends_on_field] === q.depends_on_value">
                  <div class="q-header-row">
                    <span class="q-number">Q{{ (currentStep - 4) * 5 + qi + 1 }}</span>
                    <span class="q-short">{{ q.short }}</span>
                  </div>
                  <p class="q-text">{{ q.text }}</p>
                  <div class="options">
                    <button
                      v-for="opt in (q.field === 'q37' ? [...options, 'N/A'] : options)" :key="opt"
                      type="button"
                      :class="['opt-btn', form[q.field] === opt ? 'selected' : '']"
                      @click="form[q.field] = opt"
                    >{{ opt }}</button>
                  </div>
                  <span v-if="errors[q.field]" class="field-err">Please select an answer</span>
                </div>
              </template>
            </div><!-- end questions-list -->

            <!-- Inline Navigation Buttons (at end of question content) -->
            <div class="inline-nav-bar">
              <button v-if="currentStep > 0" class="btn-back-compact" @click="currentStep--" type="button">← Back</button>
              <div v-else></div>

              <div class="step-nav-mid">
                <button v-if="currentStep > 3" class="btn-start-fresh" @click="startFresh" type="button">↺ Start Fresh</button>
              </div>

              <button
                v-if="currentStep < visibleSections.length + 3"
                class="btn-next-compact"
                @click="nextStep"
                type="button"
              >
                {{ currentStep === 3 ? 'Start Audit →' : 'Next →' }}
              </button>
              <button
                v-else
                class="btn-submit"
                @click="submit"
                :disabled="submitting"
                type="button"
              >
                {{ submitting ? 'Submitting…' : 'Submit Audit ✓' }}
              </button>
            </div>
            </div><!-- end questions-scroll -->
          </div><!-- end unified-card -->
        </div><!-- end unified-content -->
      </div><!-- end unified-page -->

      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick, onMounted } from "vue";
import { useRouter } from "vue-router";
import { submitAudit } from "../api";
import { useDraftSaving } from "../composables/useDraftSaving";
import SaveContinueButton from "../components/SaveContinueButton.vue";
import SearchableSelect from "../components/SearchableSelect.vue";
import AnimatedSelect from "../components/AnimatedSelect.vue";
import { COUNTRIES, INDIAN_STATES, INDIAN_UTS } from "../utils/geoData";
import { DEFAULT_SECTIONS } from "../utils/defaultSections";

const router = useRouter();

// ── Developer mode: click NIWI logo 5 times within 3 seconds to auto-fill ──
const devClickCount = ref(0);
let devClickTimer = null;
function onDevModeClick() {
  devClickCount.value++;
  clearTimeout(devClickTimer);
  if (devClickCount.value >= 5) {
    devClickCount.value = 0;
    autoFillTestData();
    alert('✅ Developer Mode: All fields auto-filled!');
    return;
  }
  devClickTimer = setTimeout(() => { devClickCount.value = 0; }, 3000);
}

// ── Secret admin access: click logo 10 times within 4 seconds ──
const logoClickCount = ref(0);
let logoClickTimer = null;
function onLogoClick() {
  logoClickCount.value++;
  clearTimeout(logoClickTimer);
  if (logoClickCount.value >= 10) {
    logoClickCount.value = 0;
    router.push("/GPadmin");
    return;
  }
  logoClickTimer = setTimeout(() => { logoClickCount.value = 0; }, 4000);
}

const submitted       = ref(false);
const submitting      = ref(false);
const submitError     = ref("");
const currentStep     = ref(0);
const showMobileInfo  = ref(false);
const questionsScroll = ref(null);
const errors      = reactive({});
const options     = ["Yes", "Partially", "No", "Not Sure"];

// ── Universal Scroll-Activated Bottom Navigation Drawer ──
const isDrawerVisible = ref(false);
const whyMattersPageRef = ref(null);
const unifiedPageRef = ref(null);

function checkScrollBottom(el) {
  if (!el) return;
  const { scrollTop, scrollHeight, clientHeight } = el;
  // If the page content is not tall enough to require scrolling (fits within viewport)
  if (scrollHeight <= clientHeight + 40) {
    isDrawerVisible.value = true;
    return;
  }
  // Reveal drawer as soon as user scrolls down (> 40px) or reaches the bottom area
  isDrawerVisible.value = (scrollTop > 40 || scrollTop + clientHeight >= scrollHeight - 200);
}

function onPageScroll(e) {
  checkScrollBottom(e.target);
}

let scrollResizeObserver = null;
function attachScrollObserver(el) {
  if (scrollResizeObserver) {
    scrollResizeObserver.disconnect();
    scrollResizeObserver = null;
  }
  if (!el || typeof ResizeObserver === 'undefined') return;
  scrollResizeObserver = new ResizeObserver(() => {
    checkScrollBottom(el);
  });
  scrollResizeObserver.observe(el);
  const content = el.querySelector('.why-matters-content, .unified-content');
  if (content) {
    scrollResizeObserver.observe(content);
  }
}

// ── Cinematic Welcome Animation ──
const welcomePillRef = ref(null);
const introStageRef = ref(null);
const isAnimReady = ref(false);
const isAnimDone = ref(false);

function setupWelcomeAnimation() {
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const alreadyPlayed = sessionStorage.getItem('niwi_welcome_animated') === '1';

  if (prefersReduced || alreadyPlayed) {
    isAnimDone.value = true;
    return;
  }

  nextTick(() => {
    if (!welcomePillRef.value || !introStageRef.value) {
      isAnimDone.value = true;
      return;
    }

    const rect = welcomePillRef.value.getBoundingClientRect();
    const cx = window.innerWidth / 2;
    const cy = window.innerHeight / 2;
    const px = rect.left + rect.width / 2;
    const py = rect.top + rect.height / 2;
    const deltaX = cx - px;
    const deltaY = cy - py;

    introStageRef.value.style.setProperty('--start-x', `${deltaX}px`);
    introStageRef.value.style.setProperty('--start-y', `${deltaY}px`);

    isAnimReady.value = true;
    sessionStorage.setItem('niwi_welcome_animated', '1');

    setTimeout(() => {
      isAnimDone.value = true;
    }, 3200);
  });
}

const step0Panel = {
  icon: "✦",
  tag: "Welcome",
  title: "Neuro-Inclusive Workplace Index (NIWI) Self-Assessment",
  summary: "Neuro-inclusion in the workplace is an emerging priority, with ~15% of people being neurodivergent (e.g., autistic, dyslexic, ADHD) and bringing valuable strengths such as creativity, innovation, and attention to detail.",
  why: "The Neuro-Inclusive Workplace Index (NIWI) is a structured self-assessment designed to help C-suite, HR, and DEI leaders understand and strengthen their organisation's approach to neuro-inclusion. It covers key segments across the employee lifecycle and customer experience, providing a holistic view of current practices.\n\nNIWI is not a ranking tool, but a reflection-based index to help organisations understand where they are in their neuro-inclusion journey.",
  points: [
    "Building neuro-inclusive workplaces is not just about policy, but about how inclusion is experienced every day. Understanding current realities is the first step towards creating meaningful and sustainable change.",
  ],
  tip: "This should take approximately 20 minutes to complete. The questionnaire is organised into 8 key segments, each with 5 statements. Please read each statement carefully and choose the option that best reflects your current reality (rather than intention). Your responses will only include details that you choose to share.",
};

const sections = ref(DEFAULT_SECTIONS);
const isLoading = ref(false);

const visibleSections = computed(() => sections.value);

const totalSteps = computed(() => visibleSections.value.length + 4);
const currentSection = computed(() => visibleSections.value[currentStep.value - 4]);
const progressPct    = computed(() => ((currentStep.value) / (totalSteps.value - 1)) * 100);

const progressSteps = computed(() => [
  { id: "welcome", short: "Welcome",          label: "What is NIWI?" },
  { id: "why",     short: "Why This Matters", label: "Why This Matters" },
  { id: "start",   short: "About You",        label: "Tell Us About You" },
  { id: "intro",   short: "Before You Begin", label: "Before You Begin" },
  ...visibleSections.value.map((s) => ({
    id: s.id,
    short: s.title,
    label: s.title,
  })),
]);

const progressPhase = computed(() => {
  if (currentStep.value === 0) return "What is NIWI?";
  if (currentStep.value === 1) return "Why This Matters";
  if (currentStep.value === 2) return "Tell Us About You";
  if (currentStep.value === 3) return "Before You Begin";
  if (!currentSection.value) return "";
  return `Section ${currentStep.value - 3} — ${currentSection.value.title}`;
});

const currentPanel = computed(() => {
  if (currentStep.value === 0) return step0Panel;
  if (currentStep.value === 1) return step0Panel; // why this matters reuses welcome panel
  if (currentStep.value === 2) return step0Panel;
  if (currentStep.value === 3) return step0Panel; // reuse welcome panel on instructions screen
  const s = currentSection.value;
  if (!s) return {};
  return {
    icon: s.icon,
    tag: `Section ${currentStep.value - 3} of ${visibleSections.value.length}`,
    title: s.title,
    summary: s.summary,
    why: s.why,
    points: s.points,
    tip: s.tip,
  };
});

const activeQuestions = computed(() => {
  if (!currentSection.value) return [];
  return currentSection.value.questions.filter(q => !q.depends_on_field || form[q.depends_on_field] === q.depends_on_value);
});

const sectionAnsweredCount = computed(() => {
  if (currentStep.value <= 2 || !currentSection.value) return 0;
  return activeQuestions.value.filter(q => form[q.field]).length;
});

const sectionProgressPct = computed(() => {
  if (currentStep.value <= 2 || !currentSection.value) return 0;
  const total = activeQuestions.value.length;
  if (total === 0) return 0;
  return (sectionAnsweredCount.value / total) * 100;
});

function goToStep(i) {
  if (i <= currentStep.value) currentStep.value = i;
}

watch(currentStep, async (step) => {
  showMobileInfo.value = false;
  isDrawerVisible.value = false;
  await nextTick();
  questionsScroll.value?.scrollTo({ top: 0, behavior: "smooth" });

  const el = step === 1 ? whyMattersPageRef.value : unifiedPageRef.value;
  if (el) {
    el.scrollTop = 0;
    attachScrollObserver(el);
    checkScrollBottom(el);
    setTimeout(() => {
      if (el) checkScrollBottom(el);
    }, 120);
  }
});

const form = reactive({
  name: "",
  company_name: "",
  email: "",
  contact_number: "",
  consent_given: false,
  // Section One: About You
  function: "",
  function_other: "",
  role: "",
  country: "",
  state_ut: "",
  // Section Two: Inclusion & Identity
  gender: "",
  gender_other: "",
  is_pwd: "",
  is_neurodivergent: "",
  is_marginalized: "",
  // Legacy / DB compatibility
  designation: "",
  has_physical_workspace: "",
  has_suppliers: "",
  ...Object.fromEntries(DEFAULT_SECTIONS.flatMap(s => s.questions.map(q => [q.field, ""])))
});

const countryOptions = COUNTRIES;
const indianStates = INDIAN_STATES;
const indianUTs = INDIAN_UTS;

const functionOptions = [
  "Administration",
  "Engineering",
  "ESG / Sustainability",
  "Finance",
  "HR / People",
  "Legal & Compliance",
  "Manufacturing / Production",
  "Marketing & Communications",
  "Operations",
  "Project Management",
  "Quality Assurance / Quality Control",
  "Research & Development (R&D)",
  "Sales & Business Development",
  "Supply Chain / Procurement / Logistics",
  "Technology / IT / Product Management",
  "Other"
];

const roleOptions = [
  "Individual Contributor / Team Member",
  "People Manager/Supervisor",
  "Head of Function/Director",
  "Executive / Senior Leadership (C-Suite, Business Unit Head, VP)"
];

const genderOptions = [
  "Woman",
  "Man",
  "Non-binary",
  "Other gender identity",
  "Prefer not to say"
];

const pwdOptions = [
  "Yes",
  "No",
  "Prefer not to say"
];

const neurodivergentOptions = [
  "Yes",
  "No",
  "Don't know / Not sure",
  "Prefer not to say"
];

const marginalizedOptions = [
  "Yes",
  "No",
  "Prefer not to say"
];

function onCountryChange(val) {
  if (val !== "India" && form.state_ut) {
    form.state_ut = "";
    if (errors.state_ut) delete errors.state_ut;
  }
}

watch(() => form.country, (newVal, oldVal) => {
  if (oldVal === "India" && newVal !== "India") {
    form.state_ut = "";
    if (errors.state_ut) delete errors.state_ut;
  }
});

watch(() => form.function, (newVal) => {
  if (newVal !== "Other") {
    form.function_other = "";
    if (errors.function_other) delete errors.function_other;
  }
});

watch(() => form.gender, (newVal) => {
  if (newVal !== "Other gender identity") {
    form.gender_other = "";
  }
});

watch([() => form.role, () => form.function], () => {
  form.designation = form.role ? `${form.role}${form.function ? ` - ${form.function}` : ''}` : (form.function || '');
});

const allQuestionFields = computed(() => sections.value.flatMap(s => s.questions.map(q => q.field)));

const { isSaving, syncToBackend, restoreLocalDraft, clearDraft, draftId } = useDraftSaving(form, currentStep);

onMounted(async () => {
  setupWelcomeAnimation();
  try {
    const res = await fetch("/api/form/sections");
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        sections.value = data.map(sec => ({
          id: sec.section_code,
          title: sec.title,
          icon: sec.icon || "◆",
          summary: sec.summary || "",
          why: sec.why_it_matters || "",
          points: [],
          tip: sec.tip || "",
          gatingQuestion: sec.gating_question,
          gatingField: sec.gating_field,
          naAllowed: !!sec.gating_question,
          questions: sec.questions.map(q => ({
            field: q.field_name,
            short: q.short_title,
            text: q.question_text,
            depends_on_field: q.depends_on_field,
            depends_on_value: q.depends_on_value,
            allowNA: q.field_name === 'q37' || q.allow_na
          }))
        }));
        // Initialise dynamic fields
        allQuestionFields.value.forEach(f => {
          if (form[f] === undefined) form[f] = "";
        });
        sections.value.forEach(s => {
          if (s.gatingField && form[s.gatingField] === undefined) {
            form[s.gatingField] = "";
          }
        });
      }
    } else {
      console.warn("Could not fetch sections from API, using default sections");
    }
  } catch (e) {
    console.warn("Error loading sections from API, using default sections", e);
  } finally {
    isLoading.value = false;
    restoreLocalDraft();
    nextTick(() => {
      const el = currentStep.value === 1 ? whyMattersPageRef.value : unifiedPageRef.value;
      if (el) {
        attachScrollObserver(el);
        checkScrollBottom(el);
      }
    });
  }
});

watch(() => form, (newForm) => {
  Object.keys(newForm).forEach(k => {
    if (newForm[k] && errors[k]) {
      delete errors[k];
    }
  });
}, { deep: true });

function validateStep() {
  Object.keys(errors).forEach(k => delete errors[k]);
  if (currentStep.value === 0) {
    // Intro screen — no validation needed
  } else if (currentStep.value === 1) {
    // Why This Matters — no validation needed
  } else if (currentStep.value === 2) {
    // Tell Us About You validation - all fields on one page
    // A. Name is optional

    // B. Organization Name (reject empty or whitespace-only)
    const comp = (form.company_name || "").trim();
    if (!comp) {
      errors.company_name = true;
      errors.company_nameMsg = "Organization name is required";
    }

    // C. Email ID (required, format validated)
    const em = (form.email || "").trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!em) {
      errors.email = true;
      errors.emailMsg = "Email ID is required solely to receive your personalized feedback";
    } else if (!emailRegex.test(em)) {
      errors.email = true;
      errors.emailMsg = "Please enter a valid email address (e.g. name@company.com)";
    }

    // D. Function
    if (!form.function) {
      errors.function = true;
      errors.functionMsg = "Please select your primary function";
    } else if (form.function === "Other" && !(form.function_other || "").trim()) {
      errors.function_other = true;
      errors.function_otherMsg = "Please specify your function";
    }

    // E. Current Role
    if (!form.role) {
      errors.role = true;
      errors.roleMsg = "Please select your current role";
    }

    // F. Country of Work Location
    if (!form.country) {
      errors.country = true;
      errors.countryMsg = "Please select your country of work location";
    } else if (form.country === "India" && !form.state_ut) {
      errors.state_ut = true;
      errors.state_utMsg = "Please select your State or Union Territory";
    }

    // Section Two: Inclusion & Identity
    // A. Gender Identity
    if (!form.gender) {
      errors.gender = true;
      errors.genderMsg = "Please select your gender identity";
    }

    // B. PwD
    if (!form.is_pwd) {
      errors.is_pwd = true;
      errors.is_pwdMsg = "Please select an answer";
    }

    // C. Neurodivergent
    if (!form.is_neurodivergent) {
      errors.is_neurodivergent = true;
      errors.is_neurodivergentMsg = "Please select an answer";
    }

    // D. Historically Marginalized
    if (!form.is_marginalized) {
      errors.is_marginalized = true;
      errors.is_marginalizedMsg = "Please select an answer";
    }

    // Consent
    if (!form.consent_given) {
      errors.consent_given = true;
    }
  } else if (currentStep.value === 3) {
    // Instructions screen ("Before you begin") — no validation needed
  } else {
    const section = currentSection.value;

    // Leading gating question — must be answered before anything else
    if (section && section.gatingQuestion) {
      if (!form[section.gatingField]) {
        errors[section.gatingField] = true;
        return Object.keys(errors).length === 0;
      }
      if (form[section.gatingField] === 'No') {
        return true;
      }
    }

    // Validate active questions (NA is a valid answer)
    if (section && section.questions) {
      section.questions.forEach(q => { 
        if (q.depends_on_field && form[q.depends_on_field] !== q.depends_on_value) return;
        if (!form[q.field]) errors[q.field] = true; 
      });
    }
  }
  return Object.keys(errors).length === 0;
}

function scrollToError() {
  nextTick(() => {
    const firstError = document.querySelector('.field-err, .error-message');
    if (firstError) {
      const block = firstError.closest('.q-block') || firstError.closest('.question-block') || firstError.closest('.demo-q-block') || firstError.closest('.field') || firstError.closest('.confidentiality-card');
      if (block) {
        block.scrollIntoView({ behavior: 'smooth', block: 'center' });
        block.classList.remove('shake-animation');
        void block.offsetWidth; // trigger reflow
        block.classList.add('shake-animation');
      }
    }
  });
}

function nextStep() {
  if (validateStep()) {
    currentStep.value++;
  } else {
    scrollToError();
  }
}

function resetForm() {
  form.name = "";
  form.company_name = "";
  form.email = "";
  form.contact_number = "";
  form.function = "";
  form.function_other = "";
  form.role = "";
  form.country = "";
  form.state_ut = "";
  form.gender = "";
  form.gender_other = "";
  form.is_pwd = "";
  form.is_neurodivergent = "";
  form.is_marginalized = "";
  form.designation = "";
  form.consent_given = false;
  form.has_physical_workspace = "";
  form.has_suppliers = "";
  allQuestionFields.value.forEach(f => {
    form[f] = "";
  });
}

function autoFillTestData() {
  const rand = (arr) => arr[Math.floor(Math.random() * arr.length)];
  const answers = ["Yes", "Partially", "No", "Not Sure"];
  const names = ["Alex Johnson", "Priya Sharma", "Jordan Lee", "Sam Clarke", "Morgan Davis"];
  const companies = ["Acme Corp", "BluePeak Ltd", "Nexgen Solutions", "Vertex Group", "Orbis Technologies"];

  // Fill person details with valid demographic values
  form.name = rand(names);
  form.company_name = rand(companies);
  form.email = "test@orchvate.com";
  form.contact_number = "+44 7700 900000";
  form.function = "HR / People";
  form.function_other = "";
  form.role = "People Manager/Supervisor";
  form.country = "India";
  form.state_ut = "Maharashtra";
  form.gender = "Woman";
  form.gender_other = "";
  form.is_pwd = "No";
  form.is_neurodivergent = "Yes";
  form.is_marginalized = "No";
  form.consent_given = true;
  form.designation = "People Manager/Supervisor - HR / People";

  // Gating questions — randomly Yes or No
  form.has_physical_workspace = rand(["Yes", "No"]);
  form.has_suppliers = rand(["Yes", "No"]);

  // Fill all questions with a random answer
  allQuestionFields.value.forEach(f => {
    form[f] = rand(answers);
  });

  // Q37 randomly gets N/A sometimes
  if (Math.random() > 0.5) form.q37 = "N/A";

  console.log("✅ Test data auto-filled with demographic and assessment answers");
}

function startFresh() {
  resetForm();
  clearDraft();
  currentStep.value = 0;
  Object.keys(errors).forEach(k => delete errors[k]);
}

async function submit() {
  if (!validateStep()) {
    scrollToError();
    return;
  }
  submitting.value  = true;
  submitError.value = "";
  try {
    // SCORING NOTES FOR BACKEND:
    // 1. Sections marked as "Not Applicable" (gating question = No) should be excluded from scoring
    //    - Section 4 (Built Environment): if form.has_physical_workspace === "No"
    //    - Section 8 (Suppliers & Procurement): if form.has_suppliers === "No"
    // 2. Section 7 (Products & Customer Experience): if q37 = "N/A", rescale section score from /20 to /16
    //    (since q37 becomes non-applicable, calculate section score based on 4 questions instead of 5)
    
    await submitAudit({ ...form, draft_id: draftId.value });
    clearDraft();
    resetForm();
    submitted.value = true;
    window.scrollTo({ top: 0, behavior: "smooth" });
  } catch (e) {
    submitError.value = e.message;
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.form-page {
  flex: 1;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background: transparent;
  display: flex; flex-direction: column;
}

.loader-spinner {
  border: 4px solid var(--c-border);
  border-top: 4px solid var(--c-accent);
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.form-inner {
  display: flex; flex-direction: column;
  flex: 1; width: 100%;
  min-height: 0;
  overflow: hidden;
}

/* =========================================================
   CINEMATIC WELCOME ENTRANCE ANIMATION (4 PHASES)
   ========================================================= */

.intro-fullpage {
  flex: 1;
  width: 100%;
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  background: var(--bg, #FAFAF8);
  box-sizing: border-box;
  position: relative;
  overflow-y: auto;
  overflow-x: hidden;
}

.intro-fullpage:not(.anim-ready):not(.anim-done) {
  opacity: 0;
}

/* ── Orchvate Top Branding ── */
.intro-topbar {
  width: 100%;
  padding: 1rem 5% 0;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  box-sizing: border-box;
  flex-shrink: 0;
  z-index: 10;
}

.intro-fullpage.anim-ready:not(.anim-done) .intro-topbar {
  opacity: 0;
  animation: contentGentleFadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) 1.8s forwards;
}

.hero-top-branding {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  margin-bottom: 1.5rem;
  gap: 1rem;
}

.intro-branding {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.4rem 1.1rem;
  border-radius: 99px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(22, 16, 87, 0.08);
  box-shadow: 0 2px 12px rgba(22, 16, 87, 0.04);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  flex-shrink: 0;
}

.intro-branding:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(22, 16, 87, 0.07);
}

.powered-by-text {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: #64748B;
  font-family: var(--font-body);
}

.intro-orchvate-logo {
  height: 24px;
  width: auto;
  object-fit: contain;
  display: block;
}

/* ── Full-Screen 2-Column Hero ── */
.intro-hero-layout {
  flex: 1;
  width: 100%;
  max-width: 1440px;
  margin: 0 auto;
  padding: 0.75rem 5% 3rem;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  min-height: 0;
}

.hero-top-branding {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  margin-bottom: 1.25rem;
  gap: 2rem;
}

.hero-content-wrapper {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 3rem;
  align-items: center;
  width: 100%;
}

.intro-hero-left {
  display: flex;
  flex-direction: column;
  justify-content: center;
  max-width: 640px;
  padding-right: 0;
  width: 100%;
}

.hero-badge-wrap {
  margin-bottom: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.niwi-brand-logo {
  height: 40px;
  width: auto;
  border-radius: 8px;
  display: block;
  object-fit: contain;
  box-shadow: 0 2px 8px rgba(22, 16, 87, 0.12);
  user-select: none;
}

.intro-fullpage.anim-ready:not(.anim-done) .anim-hero-niwi {
  opacity: 0;
  animation: headlineGentleFadeUp 0.75s cubic-bezier(0.16, 1, 0.3, 1) 1.4s forwards;
}

.welcome-pill {
  display: inline-flex;
  align-items: center;
  background: transparent;
  color: var(--c-accent, #04907C);
  border: 1.5px solid var(--c-accent, #04907C);
  border-radius: 99px;
  padding: 0.32rem 0.95rem;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-family: var(--font-body);
  box-sizing: border-box;
  will-change: transform, opacity;
}

/* Phase 1 (0–1s) & Phase 2 (1–1.7s) Welcome Pill */
.intro-fullpage.anim-ready:not(.anim-done) .welcome-pill {
  animation: welcomeCinematicSequence 1.7s cubic-bezier(0.65, 0, 0.35, 1) forwards;
}

@keyframes welcomeCinematicSequence {
  0% {
    opacity: 0;
    transform: translate(var(--start-x, 0px), var(--start-y, 0px)) scale(0.95);
  }
  24% {
    opacity: 1;
    transform: translate(var(--start-x, 0px), var(--start-y, 0px)) scale(1);
  }
  58% {
    opacity: 1;
    transform: translate(var(--start-x, 0px), var(--start-y, 0px)) scale(1);
  }
  100% {
    opacity: 1;
    transform: translate(0, 0) scale(1);
  }
}

.hero-title {
  font-size: clamp(2rem, 2.75vw, 2.75rem);
  font-weight: 800;
  color: var(--c-primary-dark, #161057);
  letter-spacing: -0.025em;
  line-height: 1.15;
  margin: 0.5rem 0 1.25rem 0;
  max-width: 560px;
  font-family: 'Fraunces', serif;
  cursor: pointer;
  text-wrap: balance;
}

/* Phase 3: Main Headline Appears (1.4–2.2s) */
.intro-fullpage.anim-ready:not(.anim-done) .anim-hero-headline {
  opacity: 0;
  animation: headlineGentleFadeUp 0.75s cubic-bezier(0.16, 1, 0.3, 1) 1.4s forwards;
}

@keyframes headlineGentleFadeUp {
  0% {
    opacity: 0;
    transform: translateY(24px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

.hero-desc {
  font-size: 1rem;
  line-height: 1.7;
  color: #374151;
  margin: 0 0 0.875rem 0;
  font-family: var(--font-body);
}

.hero-desc:last-of-type {
  margin-bottom: 0;
}

.hero-highlight-box {
  background: rgba(241, 245, 249, 0.8);
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 10px;
  padding: 1rem 1.25rem;
  margin: 1rem 0 0 0;
}

.hero-desc-boxed {
  font-size: 0.9rem;
  line-height: 1.6;
  color: #1e293b;
  margin: 0;
  font-family: var(--font-body);
}

.hero-info-badges {
  display: flex;
  gap: 0.75rem;
  margin: 1.75rem 0 0.625rem 0;
  flex-wrap: wrap;
}

.info-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  font-family: var(--font-body);
  font-weight: 500;
}

.badge-time {
  background: rgba(251, 191, 36, 0.12);
  border: 1px solid rgba(251, 191, 36, 0.3);
  color: #92400e;
}

.badge-perspective {
  background: rgba(139, 92, 246, 0.12);
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: #5b21b6;
}

.badge-icon {
  font-size: 1.1rem;
  line-height: 1;
}

.badge-text {
  line-height: 1.3;
}

.hero-note {
  font-size: 0.9rem;
  line-height: 1.5;
  color: #6b7280;
  margin: 0.5rem 0 0 0;
  font-family: var(--font-body);
  font-style: italic;
}

/* ── Why This Matters Card (Step 1 - Next Page) ── */
.step-why-card {
  background: rgba(4, 144, 124, 0.05);
  border: 1px solid rgba(4, 144, 124, 0.18);
  border-left: 4px solid var(--c-accent, #04907C);
  border-radius: 12px;
  padding: 1.1rem 1.4rem;
  margin-bottom: 1.75rem;
  box-sizing: border-box;
}

.step-why-header {
  margin-bottom: 0.35rem;
}

.step-why-badge {
  font-family: 'Fraunces', serif;
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--c-accent, #04907C);
  letter-spacing: -0.01em;
}

.step-why-text {
  font-size: 0.95rem;
  line-height: 1.62;
  color: #374151;
  margin: 0;
  font-family: var(--font-body);
}

.hero-btn-row {
  display: flex;
  justify-content: flex-start;
  margin-top: 1.75rem;
  padding-top: 0;
  width: 100%;
  align-self: stretch;
}

.hero-cta-btn {
  background: var(--c-primary-dark, #161057);
  color: #ffffff;
  border: none;
  border-radius: 99px;
  padding: 0.8rem 2.4rem;
  font-size: 0.98rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: var(--font-body);
  box-shadow: 0 4px 16px rgba(22, 16, 87, 0.24);
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.hero-cta-btn:hover {
  background: #0f0a42;
  transform: translateY(-2px);
  box-shadow: 0 6px 22px rgba(22, 16, 87, 0.35);
}

/* ── Right Column: Clipart Video Illustration ── */
.intro-hero-right {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: center;
  position: relative;
  padding: 0;
  height: 100%;
  gap: 1.5rem;
  margin-top: 20.5rem;
}

.clipart-card {
  width: 100%;
  max-width: 600px;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
}

.perspectives-box {
  width: 100%;
  max-width: 600px;
  background: #FFFFFF;
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 12px;
  padding: 1.5rem 2rem;
  text-align: center;
  box-shadow: 0 2px 8px rgba(22, 16, 87, 0.04);
  margin-top: 1.5rem;
}

.perspectives-label {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--c-accent, #04907C);
  margin-bottom: 0.5rem;
  font-family: var(--font-body);
}

.perspectives-flow {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--c-primary-dark, #161057);
  font-family: 'Fraunces', serif;
  letter-spacing: -0.01em;
  line-height: 1.3;
}

.hero-clipart-video {
  width: 100%;
  height: auto;
  min-height: 400px;
  max-height: 580px;
  object-fit: contain;
  filter: drop-shadow(0 16px 36px rgba(22, 16, 87, 0.08));
  display: block;
  border: none;
  outline: none;
  background: transparent;
  user-select: none;
  border-radius: 16px;
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  visibility: visible;
  opacity: 1;
}

.hero-clipart-video:hover {
  transform: translateY(-3px) scale(1.01);
}

.hero-clipart-img {
  width: 100%;
  height: auto;
  max-height: 580px;
  object-fit: contain;
  filter: drop-shadow(0 16px 36px rgba(22, 16, 87, 0.08));
  display: block;
  border-radius: 16px;
}

.niwi-hero-image {
  width: 100%;
  height: auto;
  max-height: 520px;
  object-fit: contain;
  filter: drop-shadow(0 12px 32px rgba(22, 16, 87, 0.08));
  display: block;
  border: none;
  outline: none;
  background: transparent;
  user-select: none;
  border-radius: 12px;
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.niwi-hero-image:hover {
  transform: translateY(-2px) scale(1.01);
}

/* Phase 4: Staggered Content Reveal (1.8s–2.8s) */
.intro-fullpage.anim-ready:not(.anim-done) .anim-hero-visual {
  opacity: 0;
  animation: visualGentleFadeIn 0.85s cubic-bezier(0.16, 1, 0.3, 1) 1.8s forwards;
}

@keyframes visualGentleFadeIn {
  0% {
    opacity: 0;
    transform: translateY(24px) scale(0.96);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.intro-fullpage.anim-ready:not(.anim-done) .anim-hero-p1 {
  opacity: 0;
  animation: contentGentleFadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) 1.9s forwards;
}

.intro-fullpage.anim-ready:not(.anim-done) .anim-hero-p2 {
  opacity: 0;
  animation: contentGentleFadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) 2.1s forwards;
}

.intro-fullpage.anim-ready:not(.anim-done) .anim-hero-p3 {
  opacity: 0;
  animation: contentGentleFadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) 2.3s forwards;
}

.intro-fullpage.anim-ready:not(.anim-done) .anim-hero-p4 {
  opacity: 0;
  animation: contentGentleFadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) 2.45s forwards;
}

.intro-fullpage.anim-ready:not(.anim-done) .anim-hero-p5 {
  opacity: 0;
  animation: contentGentleFadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) 2.6s forwards;
}

.intro-fullpage.anim-ready:not(.anim-done) .anim-hero-cta {
  opacity: 0;
  animation: contentGentleFadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) 2.75s forwards;
}

@keyframes contentGentleFadeUp {
  0% {
    opacity: 0;
    transform: translateY(18px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Settled Final State (Phase done & Accessibility) */
.intro-fullpage.anim-done .welcome-pill,
.intro-fullpage.anim-done .anim-hero-niwi,
.intro-fullpage.anim-done .anim-hero-headline,
.intro-fullpage.anim-done .anim-hero-p1,
.intro-fullpage.anim-done .anim-hero-p2,
.intro-fullpage.anim-done .anim-hero-p3,
.intro-fullpage.anim-done .anim-hero-p4,
.intro-fullpage.anim-done .anim-hero-p5,
.intro-fullpage.anim-done .anim-hero-cta,
.intro-fullpage.anim-done .anim-hero-visual,
.intro-fullpage.anim-done .intro-topbar,
.intro-fullpage.anim-done .hero-clipart-video {
  opacity: 1 !important;
  transform: none !important;
  animation: none !important;
  visibility: visible !important;
}

@media (prefers-reduced-motion: reduce) {
  .intro-fullpage,
  .welcome-pill,
  .anim-hero-niwi,
  .anim-hero-headline,
  .anim-hero-p1,
  .anim-hero-p2,
  .anim-hero-p3,
  .anim-hero-p4,
  .anim-hero-p5,
  .anim-hero-cta,
  .anim-hero-visual,
  .intro-topbar,
  .hero-clipart-video {
    opacity: 1 !important;
    transform: none !important;
    animation: none !important;
    transition: none !important;
    visibility: visible !important;
  }
}

/* Responsive adjustments */
@media (max-width: 1200px) {
  .hero-content-wrapper {
    gap: 2rem;
  }
  .hero-title {
    max-width: 100%;
  }
  .clipart-card {
    max-width: 520px;
  }
}

@media (max-width: 1080px) {
  .intro-topbar {
    padding: 1rem 4% 0;
  }
  .intro-hero-layout {
    padding: 1.5rem 4% 3rem;
  }
  .hero-content-wrapper {
    grid-template-columns: 1fr;
    gap: 2.5rem;
    align-items: flex-start;
  }
  .intro-hero-left {
    max-width: 100%;
    padding-right: 0;
  }
  .intro-hero-right {
    order: 2;
    padding: 0;
    justify-content: center;
    gap: 1.5rem;
    margin-top: 0;
  }
  .clipart-card {
    max-width: 480px;
    margin: 0 auto;
  }
  .perspectives-box {
    max-width: 480px;
  }
  .niwi-hero-image {
    max-height: 420px;
  }
  .hero-btn-row {
    justify-content: flex-start;
  }
}

@media (max-width: 640px) {
  .intro-topbar {
    padding: 1rem 5% 0;
    justify-content: flex-end;
  }
  .intro-hero-layout {
    padding: 1.5rem 5% 2.5rem;
  }
  .hero-top-branding {
    flex-direction: column;
    align-items: flex-start;
    margin-bottom: 1.5rem;
    gap: 0.75rem;
  }
  .hero-content-wrapper {
    gap: 2rem;
  }
  .hero-badge-wrap {
    margin-bottom: 0;
  }
  .niwi-brand-logo {
    height: 36px;
  }
  .welcome-pill {
    font-size: 0.7rem;
    padding: 0.3rem 0.85rem;
  }
  .intro-branding {
    align-self: flex-start;
  }
  .hero-title {
    font-size: 1.75rem;
    margin: 1rem 0 1.25rem 0;
  }
  .hero-desc {
    font-size: 0.95rem;
    margin-bottom: 0.875rem;
  }
  .hero-info-badges {
    gap: 0.625rem;
    margin-top: 1.5rem;
  }
  .info-badge {
    font-size: 0.85rem;
    padding: 0.5rem 0.875rem;
  }
  .hero-note {
    font-size: 0.875rem;
  }
  .hero-btn-row {
    margin-top: 1.5rem;
    justify-content: flex-start;
  }
  .hero-cta-btn {
    padding: 0.75rem 2rem;
    font-size: 0.95rem;
  }
  .intro-hero-right {
    gap: 1.25rem;
    margin-top: 0;
  }
  .clipart-card {
    max-width: 100%;
  }
  .perspectives-box {
    max-width: 100%;
    padding: 1.25rem 1.5rem;
  }
  .perspectives-label {
    font-size: 0.7rem;
  }
  .perspectives-flow {
    font-size: 1.1rem;
  }
  .niwi-hero-image {
    max-height: 320px;
  }
}

/* =========================================================
   WHY THIS MATTERS PAGE - COMPACT LAYOUT
   ========================================================= */

.why-matters-page {
  width: 100%;
  height: 100vh;
  max-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg, #FAFAF8);
  overflow-y: auto;
  overflow-x: hidden;
  scroll-behavior: smooth;
}

/* ── Compact Header with Logo, Progress, and Orchvate ── */
.why-matters-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 2.5rem;
  border-bottom: 1px solid rgba(22, 16, 87, 0.08);
  flex-shrink: 0;
  background: #FFFFFF;
}

.why-header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.why-niwi-logo {
  height: 32px;
  width: auto;
  border-radius: 6px;
}

.why-niwi-text {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--c-primary-dark, #161057);
  line-height: 1.2;
  font-family: var(--font-body);
}

.why-header-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.powered-by-label {
  font-size: 0.6rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #9CA3AF;
  font-family: var(--font-body);
}

.orchvate-logo-compact {
  height: 20px;
  width: auto;
}

/* ── Three Horizontal Sections Layout (One after another) ── */
.why-matters-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0.75rem 3rem 2rem;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  overflow: visible;
  min-height: 0;
  gap: 0.875rem;
}

.why-section-box {
  background: #FFFFFF;
  border: 1px solid rgba(22, 16, 87, 0.08);
  border-radius: 14px;
  padding: 1.15rem 1.5rem 1.25rem;
  text-align: left;
  width: 100%;
  box-shadow: 0 2px 8px rgba(22, 16, 87, 0.03);
}

/* Section Card Header Matching Page 1 Typography & Vibe */
.section-card-header {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  margin-bottom: 0.625rem;
}

.section-idx-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: 'Fraunces', serif;
  font-weight: 700;
  font-size: 0.775rem;
  color: var(--c-accent, #04907C);
  background: rgba(4, 144, 124, 0.08);
  border: 1px solid rgba(4, 144, 124, 0.22);
  border-radius: 6px;
  padding: 0.18rem 0.45rem;
  letter-spacing: 0.03em;
  line-height: 1;
}

.section-card-title {
  font-family: 'Fraunces', serif;
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--c-primary-dark, #161057);
  letter-spacing: -0.015em;
  line-height: 1.25;
  margin: 0;
}

/* ── Section 1: Why This Matters ── */
.section-1 {
  background: #FFFFFF;
}

.section-1-paragraphs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.75rem;
}

.section-text {
  font-size: 0.825rem;
  line-height: 1.6;
  color: #374151;
  margin: 0;
  font-family: var(--font-body);
}

.section-text strong {
  color: var(--c-primary-dark, #161057);
  font-weight: 600;
}

/* ── Section 2: What NIWI Helps You Do (Process Flow UI) ── */
.section-2 {
  background: #FFFFFF;
  border: 1px solid rgba(22, 16, 87, 0.08);
  border-radius: 14px;
  padding: 1.1rem 1.5rem 1.25rem;
}

.flow-header-area {
  margin-bottom: 1.1rem;
  text-align: left;
}

.flow-badge-wrapper {
  margin-bottom: 0.35rem;
}

.flow-category-tag {
  display: inline-block;
  font-size: 0.6875rem;
  font-weight: 700;
  padding: 0.22rem 0.65rem;
  border-radius: 99px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  font-family: var(--font-body);
}

.flow-category-tag.tag-purple {
  background: #EDE9FE;
  color: #6D28D9;
}

.flow-category-tag.tag-teal {
  background: #CCFBF1;
  color: #0F766E;
}

.flow-category-tag.tag-amber {
  background: #FEF3C7;
  color: #B45309;
}

.flow-main-heading {
  font-family: 'Fraunces', serif;
  font-size: 1.35rem;
  font-weight: 800;
  color: var(--c-primary-dark, #161057);
  letter-spacing: -0.02em;
  line-height: 1.2;
  margin: 0 0 0.35rem 0;
}

.flow-subtitle {
  font-size: 0.825rem;
  line-height: 1.45;
  color: #64748B;
  margin: 0;
  font-family: var(--font-body);
}

.process-flow-container {
  display: flex;
  align-items: stretch;
  width: 100%;
  gap: 0;
}

.process-flow-card {
  flex: 1 1 0;
  min-width: 0;
  border-radius: 16px;
  padding: 1.25rem 1.25rem 1.2rem;
  text-align: left;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 2px 6px rgba(22, 16, 87, 0.03);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.process-flow-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 12px rgba(22, 16, 87, 0.07);
}

.card-purple {
  background: #FAF8FF;
  border: 1.5px solid #C4B5FD;
}

.card-teal {
  background: #F0FDFA;
  border: 1.5px solid #5EEAD4;
}

.card-amber {
  background: #FFFDF5;
  border: 1.5px solid #FDE68A;
}

.flow-card-top {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.flow-circle-badge {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: #FFFFFF;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: 'Fraunces', serif;
  font-weight: 700;
  font-size: 0.95rem;
  flex-shrink: 0;
}

.badge-purple {
  border: 1.5px solid #8B5CF6;
  color: #7C3AED;
}

.badge-teal {
  border: 1.5px solid #0D9488;
  color: #0F766E;
}

.badge-amber {
  border: 1.5px solid #D97706;
  color: #B45309;
}

.flow-card-heading {
  font-family: 'Fraunces', serif;
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--c-primary-dark, #161057);
  line-height: 1.15;
  margin: 0;
  letter-spacing: -0.01em;
}

.flow-card-body {
  font-size: 0.775rem;
  line-height: 1.45;
  color: #475569;
  margin: 0;
  font-family: var(--font-body);
  flex-grow: 1;
}

.flow-card-accent-bar {
  height: 2.5px;
  border-radius: 99px;
  width: 100%;
  margin-top: 1.25rem;
}

.bar-purple {
  background: #A78BFA;
}

.bar-teal {
  background: #2DD4BF;
}

.bar-amber {
  background: #FBBF24;
}

/* Arrow Connectors */
.flow-connector {
  display: flex;
  align-items: center;
  align-self: center;
  flex: 0 0 auto;
  width: 50px;
  padding: 0 2px;
}

.connector-line {
  flex: 1;
  height: 5px;
  background: #7FE3D4;
  border-radius: 3px 0 0 3px;
}

.connector-arrowhead {
  flex-shrink: 0;
  margin-left: -3px;
}

.trailing-connector {
  width: 42px;
}

/* ── Section 3: Why Neuro-Inclusion Matters ── */
.section-3 {
  background: #FFFFFF;
}

.section-desc-lead {
  font-size: 0.8125rem;
  line-height: 1.5;
  color: #475569;
  margin: 0.35rem 0 1.1rem 0;
  font-family: var(--font-body);
  text-align: left;
}

.benefits-cards-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.875rem;
  align-items: stretch;
}

.benefit-card {
  border-radius: 14px;
  padding: 1.15rem 1.15rem 1.1rem;
  text-align: left;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 6px rgba(22, 16, 87, 0.02);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.benefit-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 12px rgba(22, 16, 87, 0.06);
}

.benefit-mint {
  background: #EBF8F4;
  border: 1px solid #CCFBF1;
}

.benefit-amber {
  background: #FEF9E7;
  border: 1px solid #FEF3C7;
}

.benefit-blue {
  background: #EEF4FF;
  border: 1px solid #DBEAFE;
}

.benefit-icon-badge {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.85rem;
  box-shadow: 0 1px 4px rgba(22, 16, 87, 0.05);
  flex-shrink: 0;
}

.benefit-title {
  font-family: 'Fraunces', serif;
  font-size: 0.975rem;
  font-weight: 800;
  color: var(--c-primary-dark, #161057);
  line-height: 1.25;
  margin: 0 0 0.45rem 0;
  letter-spacing: -0.01em;
}

.benefit-text {
  font-size: 0.775rem;
  line-height: 1.5;
  color: #475569;
  margin: 0;
  font-family: var(--font-body);
}

/* ── Info Badges Row (Pill Bar) ── */
.info-badges-pill-bar {
  display: flex;
  align-items: center;
  justify-content: space-around;
  background: #FFFDF5;
  border: 1.5px solid #FEF3C7;
  border-radius: 9999px;
  padding: 0.65rem 2rem;
  width: 100%;
  max-width: 820px;
  margin: 0.25rem auto 0;
  box-shadow: 0 1px 3px rgba(217, 119, 6, 0.04);
}

.info-pill-item {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.pill-badge-circle {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #FFFFFF;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: 'Fraunces', serif;
  font-weight: 700;
  font-size: 0.85rem;
  flex-shrink: 0;
}

.circle-amber {
  border: 1.5px solid #F59E0B;
  color: #D97706;
}

.circle-red {
  border: 1.5px solid #EF4444;
  color: #DC2626;
}

.pill-badge-label {
  font-family: 'Fraunces', serif;
  font-weight: 700;
  font-size: 0.925rem;
  color: var(--c-primary-dark, #161057);
}

/* ── Perspective Note (Pill Banner) ── */
.perspective-note-pill {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.65rem 1.5rem;
  background: #F1F4FD;
  border-radius: 14px;
  text-align: left;
  max-width: 720px;
  margin: 0.25rem auto 0;
}

.perspective-eye-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.perspective-pill-content {
  flex: 1;
}

.perspective-pill-title {
  font-family: 'Fraunces', serif;
  font-size: 0.95rem;
  font-weight: 800;
  color: var(--c-primary-dark, #161057);
  margin: 0 0 0.15rem 0;
  letter-spacing: -0.01em;
}

.perspective-pill-desc {
  font-size: 0.735rem;
  line-height: 1.4;
  color: #475569;
  margin: 0;
  font-family: var(--font-body);
}

/* ── Responsive Styles for Step 1 ── */
@media (max-width: 1080px) {
  .why-matters-content {
    padding: 0.75rem 1.75rem 0.5rem;
    gap: 0.75rem;
  }
  .benefits-cards-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.625rem;
  }
  .flow-connector {
    width: 24px;
  }
  .flow-card-heading {
    font-size: 0.95rem;
  }
  .flow-card-body {
    font-size: 0.725rem;
  }
  .info-badges-pill-bar {
    padding: 0.55rem 1.25rem;
  }
  .pill-badge-label {
    font-size: 0.85rem;
  }
}

@media (max-width: 768px) {
  .why-matters-content {
    padding: 0.75rem 1.25rem 0.5rem;
    overflow-y: auto;
  }
  .section-1-paragraphs {
    grid-template-columns: 1fr;
    gap: 0.625rem;
  }
  .process-flow-container {
    flex-direction: column;
    gap: 0.75rem;
  }
  .flow-connector {
    display: none;
  }
  .process-flow-card {
    width: 100%;
  }
  .info-badges-pill-bar {
    flex-direction: column;
    gap: 0.65rem;
    border-radius: 14px;
    align-items: flex-start;
    padding: 0.75rem 1.25rem;
  }
}

@media (max-width: 640px) {
  .why-matters-page {
    height: auto;
    min-height: 100vh;
    overflow-y: auto;
  }
  .why-matters-header {
    padding: 0.625rem 1rem;
  }
  .why-matters-content {
    padding: 0.875rem 1rem;
    gap: 0.75rem;
    overflow: visible;
  }
  .benefits-cards-grid {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
  .perspective-note-pill {
    padding: 0.75rem 1rem;
    max-width: 100%;
  }
}

/* ── Inline Navigation Bar (at end of question content) ── */
.inline-nav-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 1.75rem 0 1.5rem;
  margin-top: 2rem;
  border-top: 1px solid rgba(22, 16, 87, 0.10);
}

.btn-back-compact {
  background: transparent;
  border: 1.5px solid rgba(22, 16, 87, 0.15);
  border-radius: 99px;
  padding: 0.55rem 1.35rem;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  color: var(--c-primary-dark, #161057);
  font-family: var(--font-body);
}

.btn-back-compact:hover {
  background: rgba(22, 16, 87, 0.05);
}

.btn-next-compact {
  background: var(--c-primary-dark, #161057);
  color: #FFFFFF;
  border: none;
  border-radius: 99px;
  padding: 0.55rem 1.5rem;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  font-family: var(--font-body);
  box-shadow: 0 2px 8px rgba(22, 16, 87, 0.2);
}

.btn-next-compact:hover {
  background: #0f0a42;
  transform: translateY(-1px);
}

.step-nav-mid {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.btn-start-fresh {
  background: transparent;
  color: var(--text-muted, #6B7280);
  border: 1.5px solid var(--border, rgba(22, 16, 87, 0.15));
  padding: 0.5rem 1.1rem;
  border-radius: 99px;
  font-weight: 600;
  font-family: var(--font-body);
  cursor: pointer;
  font-size: 0.85rem;
}

.btn-start-fresh:hover {
  background: rgba(22, 16, 87, 0.05);
  color: var(--c-primary-dark, #161057);
}

.btn-back-compact {
  background: transparent;
  border: 1.5px solid var(--border, rgba(22, 16, 87, 0.15));
  border-radius: 99px;
  padding: 0.6rem 1.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  color: var(--c-primary-dark, #161057);
  font-family: var(--font-body);
}

.btn-back-compact:hover {
  background: rgba(22, 16, 87, 0.05);
  transform: translateY(-1px);
}

.btn-next-compact {
  background: var(--c-primary-dark, #161057);
  color: #FFFFFF;
  border: none;
  border-radius: 99px;
  padding: 0.6rem 1.75rem;
  font-size: 0.875rem;
  font-weight: 700;
  cursor: pointer;
  font-family: var(--font-body);
  box-shadow: 0 2px 8px rgba(22, 16, 87, 0.2);
}

.btn-next-compact:hover {
  background: #0f0a42;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(22, 16, 87, 0.3);
}

.btn-submit {
  background: var(--c-primary-dark, #161057);
  color: #FFFFFF;
  border: none;
  border-radius: 99px;
  padding: 0.6rem 1.75rem;
  font-size: 0.875rem;
  font-weight: 700;
  cursor: pointer;
  font-family: var(--font-body);
  box-shadow: 0 2px 8px rgba(22, 16, 87, 0.2);
}

.btn-submit:hover:not(:disabled) {
  background: #0f0a42;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(22, 16, 87, 0.3);
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}

@media (max-width: 1080px) {
  .why-matters-footer {
    padding: 1rem 2rem;
  }
}

@media (max-width: 640px) {
  .why-matters-footer {
    padding: 0.875rem 1.5rem;
    flex-wrap: wrap;
  }
  
  .step-nav-mid {
    order: 3;
    width: 100%;
    justify-content: center;
  }
}


/* Step layout — progress left | form + aside right */
.step-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 0;
  overflow: hidden;
  padding: 1.25rem 2rem 1.25rem;
  width: 100%;
}

.step-layout {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 1.75rem;
  width: 100%;
  max-width: 100%;
  height: 100%;
  min-height: 0;
  margin: 0;
  align-items: stretch;
  transition: grid-template-columns 0.45s cubic-bezier(0.16, 1, 0.3, 1),
              gap 0.45s cubic-bezier(0.16, 1, 0.3, 1);
}
.step-layout--no-sidebar {
  grid-template-columns: minmax(0, 1fr);
  max-width: 100%;
}

.step-center {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: 1.75rem;
  min-width: 0;
  min-height: 0;
  height: 100%;
  transition: grid-template-columns 0.45s cubic-bezier(0.4, 0, 0.2, 1),
              gap 0.45s cubic-bezier(0.4, 0, 0.2, 1);
}
.step-center--full {
  grid-template-columns: minmax(0, 1fr) 0px;
  gap: 0;
}

.step-main {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.step-card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #ffffff;
  border-radius: 24px;
  padding: 0;
  border: 1px solid rgba(22, 16, 87, 0.1);
  box-shadow: 0 4px 24px rgba(22, 16, 87, 0.04);
  width: 100%;
}

.step-card-head {
  flex-shrink: 0;
  padding: 1.5rem 3.5rem 0;
  border-bottom: 1px solid #F0ECE4;
  padding-bottom: 1rem;
  margin-bottom: 1.5rem;
}

.questions-scroll {
  flex: 1;
  min-height: 0;
  overflow: visible;
  padding: 0.75rem 3.5rem 2rem;
}

/* No scrolling for demographics (step 2) - use pagination instead */
.demographics-form .questions-scroll {
  overflow-y: visible;
}

/* Smooth scroll behavior */
html {
  scroll-behavior: smooth;
}

.questions-scroll {
  scroll-behavior: smooth;
}

.questions-scroll::-webkit-scrollbar {
  width: 8px;
}

.questions-scroll::-webkit-scrollbar-track {
  background: rgba(4, 144, 124, 0.08);
  border-radius: 4px;
}

.questions-scroll::-webkit-scrollbar-thumb {
  background: rgba(4, 144, 124, 0.3);
  border-radius: 4px;
  transition: background 0.2s;
}

.questions-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(4, 144, 124, 0.5);
}

.step-actions {
  flex-shrink: 0;
  padding: 1.25rem 3.5rem 1.5rem;
  margin-top: 0;
  border-top: 1px solid rgba(22, 16, 87, 0.08);
  background: #ffffff;
}

/* Progress — left sidebar */
.progress-sidebar {
  min-height: 0;
  height: 100%;
  overflow-y: auto;
  align-self: stretch;
  -ms-overflow-style: none;
  scrollbar-width: none;
  background: var(--c-white);
  border: 1px solid rgba(28, 26, 24, 0.08);
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(28, 26, 24, 0.07);
  animation: sideSlide 0.45s cubic-bezier(0.16, 1, 0.3, 1) both;
}
@keyframes sideSlide {
  from { transform: translateX(-20px); opacity: 0; }
  to   { transform: translateX(0);     opacity: 1; }
}
.progress-sidebar::-webkit-scrollbar { display: none; }
.progress-wrap {
  display: flex;
  flex-direction: column;
  padding: 20px 16px 20px;
  min-height: 100%;
}
.progress-header {
  display: flex; flex-direction: column; gap: 4px;
  margin-bottom: 16px; padding-bottom: 16px;
  border-bottom: 1px solid rgba(28, 26, 24, 0.08);
}
.progress-phase {
  font-size: 10px; font-weight: 600; color: var(--ink2, #4a4540);
  text-transform: uppercase; letter-spacing: 0.1em;
  opacity: 0.5;
  line-height: 1.3;
}
.progress-pct {
  font-size: 28px; font-weight: 700; color: var(--c-accent);
  font-family: 'Fraunces', serif;
  line-height: 1;
}
.progress-count {
  font-size: 12px; font-weight: 500; color: #888;
}
/* thin progress bar under header */
.progress-pct-bar {
  height: 4px; background: rgba(4,144,124,0.12);
  border-radius: 99px; overflow: hidden; margin-top: 4px;
}
.progress-pct-fill {
  height: 100%; background: var(--c-accent);
  border-radius: 99px;
  transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

.progress-track--vertical {
  --progress-dot: 20px;
  --progress-rail: 1.5px;
  --progress-pad: 6px;
  position: relative;
  flex: 1;
}
.progress-track--vertical .progress-rail {
  position: absolute;
  left: calc(var(--progress-dot) / 2 - var(--progress-rail) / 2);
  top: calc(var(--progress-pad) + var(--progress-dot));
  bottom: calc(var(--progress-pad) + var(--progress-dot));
  width: var(--progress-rail);
  background: rgba(28, 26, 24, 0.1);
  border-radius: 99px;
  overflow: hidden;
  z-index: 0;
  pointer-events: none;
}
.progress-track--vertical .progress-fill {
  width: 100%;
  height: 0;
  min-height: 0;
  background: var(--c-accent);
  border-radius: 99px;
  transition: height 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}
.progress-track--vertical .progress-steps {
  display: flex;
  flex-direction: column;
  gap: 2px;
  position: relative;
  z-index: 1;
  list-style: none;
}
.progress-track--vertical .progress-step {
  display: flex;
  align-items: center;
  gap: 10px;
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--progress-pad) 6px;
  text-align: left;
  width: 100%;
  border-radius: 8px;
  transition: background 0.15s ease;
}
.progress-track--vertical .progress-step:hover:not(:disabled) {
  background: rgba(28, 26, 24, 0.04);
}
.progress-step:disabled { cursor: default; }
.progress-step.done:not(:disabled), .progress-step.active { cursor: pointer; }

/* The number dot */
.progress-track--vertical .progress-step-dot {
  width: var(--progress-dot);
  height: var(--progress-dot);
  border-radius: 50%;
  background: rgba(28, 26, 24, 0.06);
  border: 1.5px solid rgba(28, 26, 24, 0.15);
  display: grid;
  place-items: center;
  font-size: 9px;
  font-weight: 700;
  color: rgba(28, 26, 24, 0.5);
  flex-shrink: 0;
  transition: all 0.22s ease;
  position: relative;
  z-index: 1;
  font-family: 'DM Sans', 'Inter', sans-serif;
  letter-spacing: 0;
}
.progress-step.done .progress-step-dot {
  background: var(--c-accent);
  border-color: var(--c-accent);
  color: #FFFFFF;
}
.progress-step.active .progress-step-dot {
  background: #1c1a18;
  border-color: #1c1a18;
  color: #FFFFFF;
  box-shadow: 0 2px 8px rgba(28, 26, 24, 0.25);
}
.step-check { font-size: 9px; line-height: 1; }
.progress-step-label {
  font-size: 11px; font-weight: 500; color: rgba(28, 26, 24, 0.4);
  line-height: 1.35;
  transition: color 0.15s;
}
.progress-step.active .progress-step-label { color: #1c1a18; font-weight: 600; opacity: 1; }
.progress-step.done  .progress-step-label  { color: var(--c-accent); font-weight: 500; opacity: 1; }

/* Aside panel */
.step-aside {
  min-height: 0;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  align-self: stretch;
  -ms-overflow-style: none;
  scrollbar-width: none;
  background: transparent;
  border-radius: 20px;
  border: 2px solid var(--c-border);
  box-shadow: 6px 6px 0 rgba(4, 144, 124, 0.18);
  /* Smooth collapse */
  opacity: 1;
  transform: translateX(0);
  transition: opacity 0.4s ease, transform 0.4s ease, border-width 0.4s ease;
}
.step-aside--hidden {
  opacity: 0;
  transform: translateX(24px);
  pointer-events: none;
  border-width: 0;
  box-shadow: none;
}
.step-aside::-webkit-scrollbar { display: none; }
.aside-card {
  padding: 1.25rem 1.5rem 1.5rem;
  color: var(--c-primary-dark);
  min-height: 100%;
  display: flex;
  flex-direction: column;
  animation: asideIn 0.35s ease;
  background: #ffffff;
  border-radius: 18px;
}
@keyframes asideIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.aside-header {
  display: flex;
  justify-content: flex-end;
  align-items: flex-start;
  margin-bottom: 0.5rem;
  flex-shrink: 0;
}
.aside-logo-img {
  height: 44px;
  width: auto;
  max-width: 100%;
  object-fit: contain;
  display: block;
  border-radius: 6px;
}
.aside-tag {
  display: inline-block; font-size: 0.68rem; font-weight: 800;
  text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--c-accent); margin: 0 0 0.35rem;
  font-family: 'Inter', sans-serif;
}
.aside-title {
  font-size: 1.55rem; font-weight: 800; line-height: 1.2;
  margin: 0 0 0.65rem; color: var(--c-primary-dark);
  font-family: 'Inter', sans-serif; letter-spacing: -0.02em;
}
.aside-summary {
  font-size: 0.9rem; line-height: 1.65; color: #555;
  margin: 0 0 1.25rem;
  font-family: 'Inter', sans-serif;
}
.aside-block h3 {
  font-size: 0.7rem; font-weight: 800; text-transform: uppercase;
  letter-spacing: 0.08em; color: var(--c-accent); margin-bottom: 0.4rem;
  font-family: 'Inter', sans-serif;
}
.aside-block p {
  font-size: 0.85rem; line-height: 1.55; color: #444;
  margin-bottom: 1rem;
  font-family: 'Inter', sans-serif;
}
.aside-points {
  list-style: none; margin: 0 0 1.25rem; padding: 0;
  display: flex; flex-direction: column; gap: 0.5rem;
}
.aside-points li {
  font-size: 0.82rem; color: #333;
  padding-left: 1.1rem; position: relative; line-height: 1.45;
  font-family: 'Inter', sans-serif;
}
.aside-points li::before {
  content: ""; position: absolute; left: 0; top: 0.45em;
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--c-accent);
}
.aside-progress-mini {
  padding-top: 1rem; border-top: 1px solid rgba(4, 144, 124, 0.2);
  margin-top: auto;
}
.aside-progress-mini span {
  font-size: 0.75rem; color: #888;
  display: block; margin-bottom: 0.5rem;
  font-family: 'Inter', sans-serif;
}
.mini-bar {
  height: 6px; background: rgba(4, 144, 124, 0.12);
  border-radius: 99px; overflow: hidden;
}
.mini-fill {
  height: 100%; background: var(--c-accent);
  border-radius: 99px; transition: width 0.3s ease;
}

.step-tag { display: inline-flex; align-items: center; background: transparent; color: var(--c-primary-dark); font-size: 0.68rem; font-weight: 800; padding: 0.25rem 0.75rem; border-radius: 99px; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.6rem; border: 1.5px solid rgba(22, 16, 87, 0.3); font-family: var(--font-body); }
.step-head-row { display: flex; align-items: baseline; gap: 1rem; flex-wrap: wrap; }
.h1-green { font-size: 1.5rem; font-weight: 800; color: var(--c-primary-dark); letter-spacing: -0.025em; line-height: 1.2; margin-bottom: 0.5rem; font-family: 'Fraunces', serif; }
.h1-navy { font-size: 1.65rem; font-weight: 800; color: var(--c-primary-dark); letter-spacing: -0.025em; line-height: 1.2; margin-bottom: 0.5rem; font-family: 'Fraunces', serif; cursor: pointer; }
.step-sub { color: #64748B; font-size: 0.8rem; margin-bottom: 0; line-height: 1.45; }
.step-sub-inline { color: #64748B; font-size: 0.8rem; white-space: nowrap; margin-bottom: 0; align-self: flex-end; padding-bottom: 0.35rem; }

/* =========================================================
   DEMOGRAPHICS FORM - CLEAN PROFESSIONAL DESIGN
   ========================================================= */

.demographics-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 100%;
  width: 100%;
  box-sizing: border-box;
  padding-bottom: 4rem;
}

/* Section Cards with numbered headers */
.section-card {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  padding: 0;
  width: 100%;
  box-sizing: border-box;
  overflow: visible;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, #E8F5F3 0%, #F0F9F7 100%);
  border-bottom: 1px solid #E5E7EB;
}

.section-number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #047C69;
  color: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.875rem;
  flex-shrink: 0;
}

.section-title {
  font-family: 'Fraunces', serif;
  font-weight: 700;
  font-size: 1.05rem;
  color: #1F2937;
  margin: 0;
  letter-spacing: -0.01em;
}

.section-description {
  font-size: 0.8125rem;
  line-height: 1.5;
  color: #6B7280;
  margin: 0 0 1.25rem 0;
  padding: 1.25rem 1.5rem 0 1.5rem;
}

/* Fields Grid - Two columns */
.fields-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  padding: 1.5rem;
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.field-group {
  display: flex;
  flex-direction: column;
  min-width: 0;
  box-sizing: border-box;
}

.field-group.full-width {
  grid-column: 1 / -1;
}

.field-label {
  display: block;
  font-size: 0.8125rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.375rem;
  line-height: 1.4;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.optional-label {
  font-weight: 400;
  color: #6B7280;
  font-style: italic;
}

.field-input,
.field-select {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  padding: 0.5rem 0.75rem;
  border: 1px solid #D1D5DB;
  border-radius: 6px;
  font-size: 0.875rem;
  background: #FFFFFF;
  color: #1F2937;
  transition: all 0.2s ease;
  font-family: inherit;
  min-height: 40px;
  box-sizing: border-box;
}

.field-input:hover,
.field-select:hover {
  border-color: #9CA3AF;
}

.field-input:focus,
.field-select:focus {
  outline: none;
  border-color: #047C69;
  box-shadow: 0 0 0 3px rgba(4, 124, 105, 0.1);
}

.field-input::placeholder {
  color: #9CA3AF;
}

.field-input.input-error,
.field-select.input-error {
  border-color: #DC2626;
  background-color: #FEF2F2;
}

.helper-text {
  display: block;
  font-size: 0.75rem;
  color: #047C69;
  margin-top: 0.25rem;
  line-height: 1.4;
}

.error-message {
  display: block;
  color: #DC2626;
  font-size: 0.75rem;
  margin-top: 0.25rem;
  font-weight: 500;
  line-height: 1.3;
}

/* Radio Options - Clean inline design */
.radio-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.625rem;
  width: 100%;
  margin-top: 0.5rem;
}

.radio-grid-compact {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.radio-grid.has-error .radio-option {
  border-color: #FCA5A5;
}

.radio-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 0.75rem;
  background: #FFFFFF;
  border: 1px solid #D1D5DB;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  min-height: 40px;
  box-sizing: border-box;
}

.radio-option:hover {
  border-color: #047C69;
  background: #F9FAFB;
}

.radio-option.radio-selected {
  border-color: #047C69;
  background: #F0FDF4;
  box-shadow: 0 0 0 1px #047C69;
}

.radio-input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.radio-circle {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid #9CA3AF;
  background: #FFFFFF;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  position: relative;
}

.radio-option:hover .radio-circle {
  border-color: #047C69;
}

.radio-option.radio-selected .radio-circle {
  border-color: #047C69;
  background: #047C69;
}

.radio-option.radio-selected .radio-circle::after {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #FFFFFF;
  position: absolute;
}

.radio-text {
  font-size: 0.8125rem;
  font-weight: 500;
  color: #374151;
  line-height: 1.3;
  flex: 1;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.radio-option.radio-selected .radio-text {
  color: #047C69;
  font-weight: 600;
}

/* Questions Container */
.questions-container {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  padding: 0 1.5rem 1.5rem 1.5rem;
}

.question-block {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.question-helper {
  font-size: 0.75rem;
  color: #6B7280;
  line-height: 1.4;
  margin: 0 0 0.375rem 0;
  font-style: italic;
}

/* Consent Block */
.consent-block {
  margin-top: 0.75rem;
  padding-top: 1.25rem;
  border-top: 1px solid #E5E7EB;
}

.consent-label {
  display: flex;
  align-items: flex-start;
  gap: 0.625rem;
  cursor: pointer;
  font-size: 0.8125rem;
  line-height: 1.5;
  color: #374151;
}

.consent-checkbox {
  margin-top: 0.125rem;
  flex-shrink: 0;
  width: 16px;
  height: 16px;
  cursor: pointer;
  border: 1px solid #D1D5DB;
  border-radius: 4px;
  accent-color: #047C69;
}

.consent-text {
  flex: 1;
}

.mt-3 {
  margin-top: 0.75rem;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Responsive breakpoints */
@media (max-width: 768px) {
  .demographics-form {
    gap: 1.25rem;
  }

  .section-header {
    padding: 0.875rem 1.25rem;
  }

  .fields-grid {
    padding: 1.25rem;
    gap: 0.875rem;
  }

  .radio-grid {
    gap: 0.5rem;
  }

  .questions-container {
    padding: 0 1.25rem 1.25rem 1.25rem;
    gap: 1rem;
  }

  .section-description {
    padding: 1rem 1.25rem 0 1.25rem;
  }
}

@media (max-width: 640px) {
  .demographics-form {
    gap: 1rem;
    padding-bottom: 1.5rem;
  }

  .section-header {
    padding: 0.75rem 1rem;
  }

  .section-number {
    width: 24px;
    height: 24px;
    font-size: 0.8125rem;
  }

  .section-title {
    font-size: 0.9375rem;
  }

  .fields-grid {
    grid-template-columns: minmax(0, 1fr);
    padding: 1rem;
    gap: 0.75rem;
  }

  .field-group.full-width {
    grid-column: 1 / -1;
  }

  .radio-grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 0.5rem;
  }

  .radio-grid-compact {
    grid-template-columns: minmax(0, 1fr);
  }

  .radio-option {
    padding: 0.5rem 0.625rem;
  }

  .questions-container {
    padding: 0 1rem 1rem 1rem;
    gap: 1rem;
  }

  .section-description {
    padding: 1rem;
    margin-bottom: 0;
  }
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

/* Consent Checkbox Styling */
.consent-checkbox {
  appearance: none;
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  border: 2px solid var(--c-border);
  background-color: var(--c-white);
  cursor: pointer;
  margin-top: 2px;
  flex-shrink: 0;
  position: relative;
  transition: all 0.2s ease;
  box-shadow: 2px 2px 0 rgba(0,0,0,0.1);
}
.consent-checkbox:hover {
  border-color: var(--c-border);
  background-color: var(--c-bg);
}
.consent-checkbox:checked {
  background-color: var(--c-accent);
  border-color: var(--c-border);
  box-shadow: 2px 2px 0 var(--c-accent-secondary);
}
.consent-checkbox:checked::after {
  content: "✓";
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: var(--c-accent-retro);
  font-size: 0.85rem;
  font-weight: 900;
}
.consent-checkbox:focus-visible {
  outline: 2px solid var(--c-accent);
  outline-offset: 2px;
}

@keyframes error-shake {
  0% { transform: translateX(0); }
  25% { transform: translateX(-6px); }
  50% { transform: translateX(6px); }
  75% { transform: translateX(-6px); }
  100% { transform: translateX(0); }
}
.shake-animation {
  animation: error-shake 0.4s ease-in-out;
  border-radius: 8px;
  box-shadow: 0 0 0 2px rgba(255, 68, 68, 0.4);
}

/* Mobile progress header */
.mobile-progress-bar {
  display: none;
}
/* Step Head Meta for Mobile Info Toggle */
.step-head-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}
.step-head-meta .step-tag {
  margin-bottom: 0;
}
.mobile-info-toggle {
  display: none;
}

/* Questions List - Clean Card Style */
.questions-list { 
  display: flex; 
  flex-direction: column; 
  gap: 1rem; 
  padding-bottom: 0.5rem; 
}

/* Helper banners and notices - Clean style */
.section-liner { 
  font-size: 0.8125rem; 
  color: #6B7280; 
  background: #F9FAFB; 
  padding: 0.875rem 1.125rem; 
  border-radius: 8px; 
  border-left: 3px solid #047C69; 
  font-style: italic;
  line-height: 1.5;
  margin-bottom: 0.75rem;
}

.supplier-definition-banner { 
  font-size: 0.8125rem; 
  color: #374151; 
  background: #F9FAFB; 
  padding: 0.875rem 1.125rem; 
  border-radius: 8px; 
  border: 1px solid #E5E7EB; 
  font-style: italic;
  line-height: 1.5;
  margin-bottom: 0.875rem;
}

.supplier-definition-banner strong {
  color: #1F2937;
  font-weight: 700;
  font-style: normal;
}

/* Gating blocks - Clean card style */
.gating-block { 
  background: #FFFFFF; 
  padding: 1.25rem 1.5rem; 
  border-radius: 8px; 
  border: 1px solid #E5E7EB;
  margin-bottom: 1rem;
}

.leading-gating-block { 
  border-color: #047C69; 
  border-width: 2px; 
  background: #F0FDF4;
}

.gating-eligibility-label {
  font-size: 0.6875rem; 
  font-weight: 800; 
  text-transform: uppercase; 
  letter-spacing: 0.1em;
  color: #047C69; 
  font-family: 'Fraunces', serif;
  margin-bottom: 0.625rem;
}

.gating-guidance {
  font-size: 0.8125rem;
  color: #6B7280;
  line-height: 1.5;
  margin: 0.875rem 0 0;
  font-style: italic;
  border-top: 1px solid #E5E7EB;
  padding-top: 0.875rem;
}

.gating-confirmed-badge {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: #F0FDF4;
  border: 1.5px solid #86EFAC;
  border-radius: 8px;
  padding: 0.75rem 1rem;
}

.gating-confirmed-check {
  font-size: 0.75rem;
  font-weight: 800;
  color: #FFFFFF;
  background: #047C69;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.gating-confirmed-text {
  font-size: 0.8125rem;
  color: #1F2937;
  font-weight: 600;
  flex: 1;
  line-height: 1.4;
}

.gating-change-btn {
  font-size: 0.75rem;
  font-weight: 700;
  color: #047C69;
  background: #FFFFFF;
  border: 1.5px solid #047C69;
  border-radius: 6px;
  padding: 0.375rem 0.875rem;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.gating-change-btn:hover {
  background: #047C69;
  color: #FFFFFF;
}

.section-skipped-notice {
  display: flex; 
  align-items: flex-start; 
  gap: 1rem;
  background: #F9FAFB; 
  border: 1px solid #E5E7EB; 
  border-radius: 8px;
  padding: 1.25rem 1.5rem; 
  color: #6B7280;
}

.section-skipped-notice .skipped-heading { 
  font-weight: 700; 
  color: #1F2937; 
  display: block; 
  margin-bottom: 0.375rem; 
}

.section-skipped-notice p { 
  margin: 0; 
  font-size: 0.8125rem; 
  line-height: 1.5; 
  color: #6B7280; 
}

.section-skipped-notice strong { 
  color: #1F2937; 
  font-weight: 700; 
}

.skipped-notice-icon { 
  font-size: 1.5rem; 
  color: #9CA3AF; 
  flex-shrink: 0; 
  line-height: 1; 
  margin-top: 0.125rem; 
}

.how-to-intro {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-left: 3px solid #047C69;
  border-radius: 8px;
  padding: 1.125rem 1.375rem;
  margin-bottom: 0.875rem;
}

.how-to-intro h3 {
  font-size: 0.8125rem; 
  font-weight: 800; 
  color: #047C69;
  text-transform: uppercase; 
  letter-spacing: 0.06em;
  margin-bottom: 0.625rem; 
  font-family: 'Fraunces', serif;
}

.how-to-intro p {
  font-size: 0.875rem; 
  line-height: 1.5; 
  color: #374151;
  margin: 0;
}

.q-block {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  padding: 1.25rem 1.5rem;
  box-sizing: border-box;
  transition: box-shadow 0.2s ease;
}

.q-block:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.q-block:last-child { 
  padding-bottom: 1.25rem; 
}

.q-header-row { 
  display: flex; 
  align-items: center; 
  gap: 0.625rem; 
  margin-bottom: 0.625rem; 
}

.q-number { 
  font-size: 0.6875rem; 
  font-weight: 800; 
  color: #047C69; 
  background: #F0FDF4; 
  border: 1.5px solid #047C69; 
  display: inline-block; 
  padding: 0.25rem 0.625rem; 
  border-radius: 6px; 
  letter-spacing: 0.06em; 
  font-family: 'Fraunces', serif; 
}

.q-short { 
  font-size: 0.8125rem; 
  font-weight: 700; 
  color: #1F2937; 
  font-family: 'Fraunces', serif; 
  letter-spacing: -0.01em; 
}

.q-text { 
  font-size: 0.875rem; 
  font-weight: 500; 
  color: #374151; 
  line-height: 1.5; 
  margin-bottom: 0.875rem; 
}

.options { 
  display: flex; 
  gap: 0.625rem; 
  flex-wrap: wrap; 
}

.opt-btn {
  padding: 0.5rem 1rem; 
  border-radius: 6px;
  border: 1px solid #D1D5DB; 
  background: #FFFFFF;
  font-size: 0.8125rem; 
  font-weight: 500; 
  cursor: pointer; 
  color: #374151;
  transition: all 0.2s ease;
  min-height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.opt-btn:hover { 
  border-color: #047C69; 
  color: #047C69;
  background: #F9FAFB;
}

.opt-btn.selected { 
  background: #047C69; 
  color: #FFFFFF; 
  border-color: #047C69; 
  font-weight: 600; 
  box-shadow: 0 0 0 1px #047C69;
}

/* Navigation */
.step-nav { display: flex; align-items: center; justify-content: space-between; width: 100%; gap: 0.5rem; }
.step-nav-mid { display: flex; gap: 0.5rem; align-items: center; }
.btn-back {
  background: transparent; border: 1.5px solid var(--border); border-radius: 99px;
  padding: 0.7rem 1.6rem; font-size: 0.9rem; font-weight: 600;
  cursor: pointer; color: var(--c-primary-dark); transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: var(--font-body);
}
.btn-back:hover { background: rgba(22, 16, 87, 0.05); transform: translateY(-1px); }
.btn-start-fresh {
  background: transparent; color: var(--text-muted); border: 1.5px solid var(--border); 
  padding: 0.5rem 1.1rem; border-radius: 99px; font-weight: 600; font-family: var(--font-body);
  cursor: pointer; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 0.85rem;
}
.btn-start-fresh:hover { background: rgba(22, 16, 87, 0.05); color: var(--c-primary-dark); }
.btn-auto-fill {
  background: #FFA500; color: var(--c-white); border: 1.5px solid #FF8C00; 
  padding: 0.5rem 1.1rem; border-radius: 99px; font-weight: 600; font-family: var(--font-body);
  box-shadow: 0 2px 8px rgba(255, 140, 0, 0.3); cursor: pointer; transition: all 0.15s;
  font-size: 0.85rem;
}
.btn-auto-fill:hover { transform: translateY(-1px); background: #FFB52E; }
.btn-next {
  background: var(--c-primary-dark); color: var(--c-white); border: none; border-radius: 99px;
  padding: 0.75rem 2.25rem; font-size: 0.95rem; font-weight: 700;
  cursor: pointer; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); font-family: var(--font-body);
  box-shadow: 0 4px 14px rgba(22, 16, 87, 0.25);
  display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem;
}
.btn-next:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(22, 16, 87, 0.35); background: #0f0a42; }
.btn-submit {
  background: var(--c-primary-dark); color: var(--c-white); border: none; border-radius: 99px;
  padding: 0.75rem 2.25rem; font-size: 0.95rem; font-weight: 700;
  cursor: pointer; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); font-family: var(--font-body);
  box-shadow: 0 4px 14px rgba(22, 16, 87, 0.25);
  display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem;
}
.btn-submit:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(22, 16, 87, 0.35); background: #0f0a42; }
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; box-shadow: none; }

/* Footer */
.form-footer {
  flex-shrink: 0;
  display: flex; align-items: center; justify-content: flex-end;
  padding: 0.5rem 5.5rem 0.75rem 2rem; /* right padding clears the fixed accessibility button (48px + 20px margin) */
  border-top: 1px solid rgba(0,0,0,0.08);
  gap: 1rem;
}
.admin-link-small { color: #bbb; font-size: 0.8rem; text-decoration: none; }
.admin-link-small:hover { color: var(--c-primary-dark); }

/* Dev toolbar — fixed bottom-left, clear of the accessibility panel (bottom-right) */
.dev-toolbar {
  position: fixed;
  bottom: 16px;
  left: 16px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  z-index: 900;
}
.dev-btn {
  height: 36px;
  padding: 0 1rem;
  border-radius: 99px;
  font-size: 0.78rem;
  font-weight: 700;
  font-family: 'DM Sans', sans-serif;
  cursor: pointer;
  border: 2px solid var(--c-primary-dark);
  transition: transform 0.12s, box-shadow 0.12s;
  white-space: nowrap;
}
.dev-btn--fill {
  background: var(--c-primary-dark);
  color: var(--c-accent);
  box-shadow: 3px 3px 0 var(--c-accent);
}
.dev-btn--fill:hover { transform: translate(-2px,-2px); box-shadow: 5px 5px 0 var(--c-accent); }
.dev-btn--fresh {
  background: #fff;
  color: var(--c-primary-dark);
  box-shadow: 3px 3px 0 var(--c-primary-dark);
}
.dev-btn--fresh:hover { transform: translate(-2px,-2px); box-shadow: 5px 5px 0 var(--c-primary-dark); }

/* Success */
.success-wrap { flex: 1; display: flex; align-items: center; justify-content: center; padding: 2rem; background: var(--bg, #FAFAF8); }
.success-box {
  background: var(--c-white, #FFFFFF);
  border-radius: 16px;
  padding: 3.5rem 3rem;
  text-align: center;
  border: 1px solid rgba(22, 16, 87, 0.08);
  box-shadow: 0 8px 32px rgba(22, 16, 87, 0.05);
  max-width: 580px;
  width: 100%;
}
.success-icon {
  width: 64px;
  height: 64px;
  background: #E6F4F1;
  color: var(--c-accent, #04907C);
  border: 2px solid var(--c-accent, #04907C);
  border-radius: 50%;
  display: inline-grid;
  place-items: center;
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
}
.success-box h2 {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--c-primary-dark, #161057);
  margin-bottom: 0.85rem;
  font-family: 'Fraunces', serif;
  letter-spacing: -0.02em;
}
.success-box p {
  color: #475569;
  line-height: 1.65;
  font-size: 0.95rem;
  margin-bottom: 1.25rem;
  font-family: var(--font-body);
}

.alert { padding: 0.75rem 1rem; border-radius: 8px; font-size: 0.875rem; margin-bottom: 0.75rem; word-break: break-word; }
.alert-error { background: #FFF0F0; color: #C0392B; border: 1px solid #FFCACA; }

@media (max-width: 900px) {
  .instr-layout {
    grid-template-columns: 1fr;
  }
  .instr-right {
    display: none; /* hide section descriptions on small screens to save space */
  }
  .step-wrap { padding: 0.75rem 0.75rem 0.5rem; }
  .step-layout {
    grid-template-columns: 1fr;
    gap: 0;
    max-width: 100%;
  }
  .progress-sidebar {
    display: none;
  }
  .mobile-progress-bar {
    display: block;
    padding: 1.25rem 1.75rem 0.5rem;
    background: var(--c-white);
    border-bottom: 1px solid #E2DDD4;
  }
  .mobile-progress-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.4rem;
  }
  .mobile-phase {
    font-size: 0.78rem;
    font-weight: 800;
    color: var(--c-accent);
    font-family: 'Fraunces', serif;
  }
  .mobile-count {
    font-size: 0.72rem;
    font-weight: 700;
    color: #888;
  }
  .mobile-progress-track {
    height: 6px;
    background: #E2DDD4;
    border-radius: 99px;
    overflow: hidden;
    border: 1.5px solid var(--c-border);
  }
  .mobile-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--c-accent), #20C0B0);
    border-radius: 99px;
    transition: width 0.45s ease;
  }

  .step-center {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto;
    gap: 0.75rem;
  }
  .step-aside {
    display: none;
  }
  /* On steps 0 & 1: show aside panel ABOVE the form card (app info → form) */
  .step-aside:not(.step-aside--hidden) {
    display: block;
    order: -1;         /* ← appears before step-main in visual order */
    height: auto;
    max-height: 420px;
    overflow-y: auto;
    border-radius: 16px;
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
  .step-aside:not(.step-aside--hidden)::-webkit-scrollbar { display: none; }
  .step-aside.mobile-show {
    display: block;
    order: -1;
    height: auto;
    max-height: 38vh;
    overflow-y: auto;
    margin-bottom: 0.5rem;
  }
  .step-aside--hidden {
    display: none !important;
  }
  .step-main {
    min-height: 0;
  }
  .step-card-head { padding: 1.5rem 1.75rem 0; }
  .questions-scroll { padding: 1rem 1.75rem 1.5rem; }
  .aside-title { font-size: 1.2rem; }
  .aside-summary { font-size: 0.85rem; }
  
  .mobile-info-toggle {
    display: inline-flex;
    align-items: center;
    background: transparent;
    color: var(--c-accent);
    border: none;
    box-shadow: none;
    font-size: 0.75rem;
    font-weight: 700;
    cursor: pointer;
    text-decoration: underline;
    text-underline-offset: 3px;
    padding: 0;
    font-family: var(--font-body);
  }
  .mobile-info-toggle:hover {
    color: var(--c-primary-light);
  }
}

@media (max-width: 480px) {
  /* Hide text on tiny screens — keep just the logo image */
  .form-logo-name { display: none; }
}

@media (max-width: 600px) {
  .fields-grid { grid-template-columns: 1fr; }
  .radio-card-grid { grid-template-columns: 1fr; }
  .radio-card-grid--compact { grid-template-columns: 1fr; }
}

/* Tablet breakpoint for better two-column layout */
@media (min-width: 601px) and (max-width: 900px) {
  .fields-grid {
    gap: 0.6rem;
    row-gap: 0.7rem;
  }
  
  .radio-card-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .demo-section { padding: 0; border-radius: 0; border: none; background: transparent; }
  .step-wrap { padding: 0.75rem 0.5rem 0.5rem; }
  .form-header { padding: 0.85rem 1rem; }
  
  .mobile-progress-bar {
    padding: 1.25rem 1.25rem 0.5rem;
  }
  .step-card-head { padding: 1.25rem 1.25rem 0; }
  .step-card-head h1 { font-size: 1.25rem; }
  .questions-scroll { padding: 1rem 1.25rem 1.25rem; }
  .q-text { font-size: 0.88rem; line-height: 1.45; }
  
  .step-tag {
    font-size: 0.65rem;
    padding: 0.15rem 0.55rem;
    border-width: 1px;
    margin-bottom: 0;
  }

  .options {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
    width: 100%;
  }
  .opt-btn {
    width: 100%;
    text-align: center;
    padding: 0.5rem;
    font-size: 0.8rem;
    border-radius: 8px;
  }
  
  .step-actions {
    padding: 0.75rem 1.25rem;
  }
  .step-nav {
    flex-wrap: wrap;
    gap: 0.5rem;
    row-gap: 0.5rem;
  }
  /* On mobile: mid group (Start Fresh + Save) takes full width above back/next */
  .step-nav-mid {
    order: -1;
    width: 100%;
    justify-content: center;
    gap: 0.4rem;
  }
  .btn-back, .btn-next, .btn-submit, .save-continue-container :deep(.btn),
  .save-continue-container :deep(.btn-green) {
    height: 38px;
    padding: 0.4rem 0.7rem;
    font-size: 0.8rem;
    font-weight: 700;
    border-radius: 8px;
    border: 1.5px solid var(--c-border);
    box-shadow: 2px 2px 0 rgba(4, 144, 124, 0.3);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin: 0;
  }
  .btn-back {
    flex: 1;
    min-width: 60px;
    max-width: 75px;
  }
  .btn-start-fresh {
    flex: 1;
    height: 38px;
    padding: 0.4rem 0.7rem;
    font-size: 0.8rem;
    border-radius: 8px;
    border: 1.5px solid var(--c-border);
    box-shadow: 2px 2px 0 rgba(4, 144, 124, 0.3);
  }
  .save-continue-container {
    flex: 1.8;
    display: inline-block;
    width: auto;
  }
  .save-continue-container :deep(.btn) {
    width: 100%;
  }
  .btn-next, .btn-submit {
    flex: 1;
    min-width: 80px;
    box-shadow: 2px 2px 0 rgba(4, 144, 124, 0.3);
  }

  .form-footer {
    padding: 0.4rem 1rem 0.5rem;
    justify-content: flex-end;
    align-items: center;
  }
  .dev-btn {
    height: 32px;
    padding: 0 0.75rem;
    font-size: 0.72rem;
  }
}
/* ── Intro screen (step 0) ─────────────────────────────── */
.intro-screen {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
  padding: 0.25rem 0 0.5rem;
}
.intro-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
  margin-bottom: 0.25rem;
}
.intro-stat {
  background: rgba(4, 144, 124, 0.06);
  border: 1.5px solid rgba(4, 144, 124, 0.18);
  border-radius: 12px;
  padding: 0.85rem 0.65rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.25rem;
}
.intro-stat-num {
  font-size: 1.4rem;
  font-weight: 900;
  color: var(--c-accent);
  font-family: 'Fraunces', serif;
  line-height: 1;
}
.intro-stat-label {
  font-size: 0.7rem;
  font-weight: 600;
  color: #666;
  line-height: 1.3;
}
.intro-body {
  font-size: 1.02rem;
  line-height: 1.7;
  color: #374151;
  margin: 0 0 1.25rem 0;
  font-family: var(--font-body);
}
.intro-points {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  background: rgba(4, 144, 124, 0.04);
  border-left: 3px solid var(--c-accent);
  border-radius: 0 8px 8px 0;
  padding: 0.85rem 1rem;
}
.intro-point {
  display: flex;
  gap: 0.5rem;
  align-items: flex-start;
  font-size: 0.875rem;
  line-height: 1.5;
  color: #444;
}
.intro-point-arrow {
  color: var(--c-accent);
  font-weight: 800;
  flex-shrink: 0;
  margin-top: 0.05rem;
}

/* Instructions screen */

.instructions-screen {
  width: 100%;
  max-width: 1360px;
  margin: 0 auto;
  padding: 1.5rem 0 1.25rem;
}

.instr-layout {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 2.25rem;
  align-items: start;
}

/* Left Guide Card */
.instr-left-card {
  background: linear-gradient(180deg, #F6FAF9 0%, #EDF6F4 100%);
  border: 1.5px solid #DFEDE9;
  border-radius: 18px;
  padding: 2.1rem 1.85rem;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(4, 144, 124, 0.04);
}


.instr-card-title {
  font-family: 'Fraunces', serif;
  font-size: 1.85rem;
  font-weight: 700;
  color: var(--c-primary-dark, #161057);
  margin: 0 0 0.45rem;
  letter-spacing: -0.015em;
  line-height: 1.2;
}

.instr-card-subtitle {
  font-size: 0.92rem;
  color: #64748B;
  margin: 0 0 1.75rem;
  line-height: 1.45;
}

.instr-points-list {
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 2;
}

.instr-point-item {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.instr-point-icon {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: #E6F7F5;
  border: 1.5px solid rgba(4, 144, 124, 0.25);
  color: var(--c-accent, #04907C);
  display: grid;
  place-items: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.instr-point-text {
  font-size: 0.9rem;
  color: #334155;
  line-height: 1.55;
  margin: 0;
  flex: 1;
}

.instr-point-text strong {
  color: #0F172A;
  font-weight: 700;
}

.instr-point-divider {
  height: 1px;
  background: #E1EBE7;
  margin: 1.15rem 0;
}

/* Response options example box */
.instr-example-box {
  margin-top: 1.6rem;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #DCECE7;
  border-radius: 12px;
  padding: 1.15rem 1.15rem;
  position: relative;
  z-index: 2;
  backdrop-filter: blur(8px);
  box-shadow: 0 2px 8px rgba(4, 144, 124, 0.04);
}

.instr-example-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748B;
  margin-bottom: 0.75rem;
  letter-spacing: 0.01em;
}

.instr-example-options {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 0.9rem;
}

.instr-example-opt {
  font-size: 0.8rem;
  font-weight: 600;
  padding: 0.32rem 0.85rem;
  border-radius: 99px;
  border: 1.5px solid;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.instr-example-opt.opt-yes {
  background: #F0FDF4;
  border-color: #86EFAC;
  color: #166534;
}

.instr-example-opt.opt-partially {
  background: #FFFBEB;
  border-color: #FCD34D;
  color: #92400E;
}

.instr-example-opt.opt-no {
  background: #FEF2F2;
  border-color: #FCA5A5;
  color: #991B1B;
}

.instr-example-opt.opt-not-sure {
  background: #F5F3FF;
  border-color: #C4B5FD;
  color: #5B21B6;
}

.instr-privacy-note {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #64748B;
  line-height: 1.4;
}

.instr-privacy-note svg {
  flex-shrink: 0;
  color: #64748B;
}

.instr-botanical-bg {
  position: absolute;
  right: -15px;
  bottom: -20px;
  width: 140px;
  height: 140px;
  pointer-events: none;
  z-index: 1;
}

/* Right Section */
.instr-right {
  display: flex;
  flex-direction: column;
  margin-top: 1.5rem;
}

.instr-right-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 1.35rem;
  gap: 1.5rem;
}

.instr-right-header-left {
  flex: 1;
}

.instr-right-badge {
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: var(--c-accent, #04907C);
  display: block;
  margin-bottom: 0.3rem;
  font-family: 'Fraunces', serif;
}

.instr-right-title {
  font-family: 'Fraunces', serif;
  font-size: 1.85rem;
  font-weight: 700;
  color: var(--c-primary-dark, #161057);
  margin: 0;
  letter-spacing: -0.015em;
  line-height: 1.2;
}

.instr-right-meta {
  font-size: 0.88rem;
  color: #334155;
  line-height: 1.55;
  max-width: 100%;
  text-align: left;
  margin: 0.5rem 0 0 0;
  font-weight: 500;
}

/* 8 Segments 2-Column Grid */
.instr-desc-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem 1.15rem;
}

.instr-segment-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: var(--c-white, #FFFFFF);
  border: 1.5px solid #EDE8E1;
  border-radius: 14px;
  padding: 1.15rem 1.2rem;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
  position: relative;
  cursor: default;
}

.instr-segment-card:hover {
  border-color: var(--c-accent, #04907C);
  box-shadow: 0 4px 14px rgba(4, 144, 124, 0.08);
  transform: translateY(-1px);
}

.instr-seg-badge {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #E8F7F5;
  color: var(--c-accent, #04907C);
  font-family: 'Fraunces', serif;
  font-weight: 800;
  font-size: 0.95rem;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.instr-seg-content {
  flex: 1;
  min-width: 0;
}

.instr-seg-title {
  font-family: 'Fraunces', serif;
  font-size: 0.98rem;
  font-weight: 700;
  color: var(--c-primary-dark, #161057);
  margin: 0 0 0.25rem;
  line-height: 1.3;
}

.instr-seg-summary {
  font-size: 0.78rem;
  color: #64748B;
  margin: 0;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.instr-seg-arrow {
  color: #94A3B8;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  margin-left: 0.25rem;
  transition: transform 0.2s ease, color 0.2s ease;
}

.instr-segment-card:hover .instr-seg-arrow {
  color: var(--c-accent, #04907C);
  transform: translateX(2px);
}

@media (max-width: 1140px) {
  .instr-layout {
    grid-template-columns: 1fr;
    gap: 1.75rem;
  }
  .instr-right-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  .instr-right-meta {
    text-align: left;
    max-width: 100%;
  }
}

@media (max-width: 720px) {
  .instr-desc-grid {
    grid-template-columns: 1fr;
  }
}

/* =========================================================
   UNIFIED PAGE LAYOUT (Steps 2+)
   ========================================================= */

.unified-page {
  width: 100%;
  height: 100vh;
  max-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg, #FAFAF8);
  overflow-y: auto;
  overflow-x: hidden;
  scroll-behavior: smooth;
}

.unified-content {
  flex: 1;
  padding: 0 0 2rem;
  max-width: 100%;
  margin: 0;
  width: 100%;
  overflow: visible;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.unified-card {
  background: transparent;
  border-radius: 0;
  border: none;
  overflow: visible;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.step-card-head {
  flex-shrink: 0;
  padding: 1.5rem 3rem 1rem;
  background: var(--bg, #FAFAF8);
}

.questions-scroll {
  flex: 1;
  overflow: visible !important;
  padding: 0 1.5rem 1.5rem;
  background: var(--bg, #FAFAF8);
  min-height: 0;
}

/* Responsive for unified layout */
@media (max-width: 1080px) {
  .step-card-head {
    padding: 1.25rem 1.5rem 0.75rem;
  }
  
  .questions-scroll {
    padding: 0 1.5rem 1.25rem;
  }
}

@media (max-width: 640px) {
  .step-card-head {
    padding: 1rem 1.25rem 0.75rem;
  }
  
  .questions-scroll {
    padding: 0 1.25rem 1rem;
  }
}

/* =========================================================
   PAGE FADE TRANSITIONS
   ========================================================= */

.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.page-fade-enter-to,
.page-fade-leave-from {
  opacity: 1;
  transform: translateY(0);
}

</style>
