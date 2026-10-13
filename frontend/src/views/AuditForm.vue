<template>
  <div class="form-page">

    <!-- Success screen -->
    <div v-if="submitted" class="success-wrap">
      <div class="success-box">
        <div class="success-icon">✓</div>
        <h2>Audit Submitted</h2>
        <p>Thank you for completing the Neuro-Inclusive Workplace Index <strong>{{ form.company_name }}</strong>.<br/>You will receive your results by email shortly.</p>
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
        <!-- Discreet Orchvate Top Header -->
        <header class="intro-topbar">
          <div class="intro-branding">
            <span class="powered-by-text">Powered by</span>
            <img src="/logo_orchvate.png" alt="Orchvate" class="intro-orchvate-logo" />
          </div>
        </header>

        <!-- 2-Column Full Screen Hero Layout -->
        <div class="intro-hero-layout">
          <!-- Left Column: Welcome & Assessment Details -->
          <div class="intro-hero-left">
            <!-- Phase 1 & 2: Welcome Pill + NIWI Brand -->
            <div class="hero-badge-wrap">
              <img src="/logonew1.png" alt="NIWI Logo" class="niwi-brand-logo anim-hero-niwi" />
              <span ref="welcomePillRef" class="welcome-pill">WELCOME TO</span>
            </div>

            <!-- Phase 3: Main Headline -->
            <h1 class="hero-title anim-hero-headline" @click="onLogoClick">
              Neuro-Inclusive Workplace Index (NIWI) Self-Assessment
            </h1>

            <!-- Phase 4: Staggered Descriptions -->
            <p class="hero-desc anim-hero-p1">
              Neuro-inclusion in the workplace is an emerging priority, with ~15% of people being neurodivergent (e.g., autistic, dyslexic, ADHD) and bringing valuable strengths such as creativity, innovation, and attention to detail.
            </p>

            <p class="hero-desc anim-hero-p2">
              The Neuro-Inclusive Workplace Index (NIWI) is a structured self-assessment designed to help C-suite, HR, and DEI leaders understand and strengthen their organisation's approach to neuro-inclusion. It covers key segments across the employee lifecycle and customer experience, providing a holistic view of current practices.
            </p>

            <p class="hero-desc anim-hero-p3">
              NIWI is not a ranking tool, but a reflection-based index to help organisations understand where they are in their neuro-inclusion journey.
            </p>

            <!-- Phase 4: Next Button -->
            <div class="hero-btn-row anim-hero-cta">
              <button class="btn-next hero-cta-btn" @click="nextStep" type="button">
                Next &rarr;
              </button>
            </div>
          </div>

          <!-- Right Column: Animated Clipart Video -->
          <div class="intro-hero-right anim-hero-visual">
            <div class="clipart-card">
              <video
                ref="heroVideoRef"
                autoplay
                muted
                loop
                playsinline
                :autoplay="true"
                :muted="true"
                :loop="true"
                :playsinline="true"
                preload="auto"
                poster="/niwi_video_preview.png"
                src="/niwi_clipart_staggered_animation.mp4"
                class="niwi-hero-animation hero-clipart-video"
                aria-label="Animated hand-drawn illustration representing neuro-inclusion"
                @loadedmetadata="playHeroVideo"
                @canplay="playHeroVideo"
                @ended="onVideoEnded"
                @timeupdate="onVideoTimeUpdate"
              >
                <source src="/niwi_clipart_staggered_animation.mp4" type="video/mp4" />
                <source src="/images/niwi_clipart_staggered_animation.mp4" type="video/mp4" />
                Your browser does not support the video tag.
              </video>
            </div>
          </div>
        </div>
      </div>

      <!-- Why This Matters Page (Step 1) -->
      <div
        v-else-if="currentStep === 1"
        key="step-1"
        class="why-matters-page"
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

        <!-- Compact 2-Column Content -->
        <div class="why-matters-content">
          <!-- Left Column: Text & Benefits -->
          <div class="why-content-left">
            <!-- Badge -->
            <div class="why-badge-compact">WHY THIS MATTERS</div>

            <!-- Headline -->
            <h1 class="why-title-compact">Why This Matters</h1>

            <!-- Description -->
            <p class="why-desc-compact">
              Building neuro-inclusive workplaces is not just about policy, but about how inclusion is experienced every day. Understanding current realities is the first step towards creating meaningful and sustainable change.
            </p>

            <!-- 2x2 Benefits Grid with Pastel Colors -->
            <div class="benefits-grid-compact">
              <!-- Card 1: Unlocks Potential - Pale Mint -->
              <div class="benefit-card-compact benefit-mint">
                <div class="benefit-icon-compact">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="5"></circle>
                    <line x1="12" y1="1" x2="12" y2="3"></line>
                    <line x1="12" y1="21" x2="12" y2="23"></line>
                    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                    <line x1="1" y1="12" x2="3" y2="12"></line>
                    <line x1="21" y1="12" x2="23" y2="12"></line>
                    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
                  </svg>
                </div>
                <h3 class="benefit-title-compact">Unlocks Potential</h3>
                <p class="benefit-text-compact">
                  Neuro-inclusion helps organisations tap into diverse talent, ideas, and ways of thinking, driving innovation and better decision-making.
                </p>
              </div>

              <!-- Card 2: Stronger Teams - Pale Cream/Yellow -->
              <div class="benefit-card-compact benefit-cream">
                <div class="benefit-icon-compact">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                  </svg>
                </div>
                <h3 class="benefit-title-compact">Stronger Teams</h3>
                <p class="benefit-text-compact">
                  When everyone can participate fully, teams become more collaborative, engaged, and resilient.
                </p>
              </div>

              <!-- Card 3: More Equitable Opportunities - Pale Blue -->
              <div class="benefit-card-compact benefit-blue">
                <div class="benefit-icon-compact">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="12" y1="20" x2="12" y2="10"></line>
                    <line x1="18" y1="20" x2="18" y2="4"></line>
                    <line x1="6" y1="20" x2="6" y2="16"></line>
                  </svg>
                </div>
                <h3 class="benefit-title-compact">More Equitable Opportunities</h3>
                <p class="benefit-text-compact">
                  It helps identify and remove barriers, ensuring fair access to opportunities across the employee lifecycle.
                </p>
              </div>

              <!-- Card 4: Lasting Impact - Pale Mint -->
              <div class="benefit-card-compact benefit-mint">
                <div class="benefit-icon-compact">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                    <line x1="12" y1="19" x2="12" y2="22"></line>
                  </svg>
                </div>
                <h3 class="benefit-title-compact">Lasting Impact</h3>
                <p class="benefit-text-compact">
                  Neuro-inclusive practices create workplaces where everyone can thrive, leading to sustainable business growth and positive social impact.
                </p>
              </div>
            </div>
          </div>

          <!-- Right Column: Illustration -->
          <div class="why-content-right">
            <img 
              src="/why-matters-illustration.png" 
              alt="Team collaboration illustration" 
              class="why-illustration-compact"
            />
          </div>
        </div>

        <!-- Bottom Navigation -->
        <div class="why-matters-footer">
          <button class="btn-back-compact" @click="currentStep = 0" type="button">← Back</button>
          <button class="btn-next-compact" @click="nextStep" type="button">Next →</button>
        </div>
      </div>

      <!-- Step content (Step 2+) with Consistent Header/Footer -->
      <div v-else key="step-other" class="unified-page">
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
            <div class="step-card-head">
              <div class="step-head-meta">
                <div v-if="currentStep === 2" class="step-tag">Getting Started</div>
                <div v-else-if="currentStep === 3"></div>
                <div v-else class="step-tag">Section {{ currentStep - 3 }} of {{ visibleSections.length }}</div>
              </div>
              <div class="step-head-row">
                <h1 :class="currentStep === 2 ? 'h1-navy' : currentStep === 3 ? 'h1-navy' : 'h1-green'" @click="onLogoClick">{{ currentStep === 2 ? 'Tell Us About You' : currentStep === 3 ? 'Before you begin' : (currentSection?.title || '') }}</h1>
                <p v-if="currentStep > 3" class="step-sub step-sub-inline">Select the answer that best reflects your organisation's current position.</p>
              </div>
              <p v-if="currentStep === 2" class="step-sub">
                The following demographic questions help us understand how neuro-inclusion experiences may vary across groups. Your responses will be analyzed in aggregate and treated confidentially.
              </p>
              <p v-if="currentStep === 3" class="step-sub">Here's what to expect before you begin the audit.</p>
            </div>

            <div ref="questionsScroll" class="questions-scroll">
            <!-- Tell Us About You (Step 2) - Paginated -->
            <div v-if="currentStep === 2" class="demographics-form">
              
              <!-- Page 1: Basic Info + Role & Location -->
              <div v-if="demoPage === 1" class="demo-page">
                <div class="fields-grid">
                  <!-- A. Name (Half width) -->
                  <div class="field half-width">
                    <label for="demo_name">Name <span class="label-opt">(Optional)</span></label>
                    <input
                      id="demo_name"
                      v-model="form.name"
                      type="text"
                      placeholder="Enter your name (optional)"
                    />
                  </div>

                  <!-- B. Organization Name (Half width) -->
                  <div class="field half-width">
                    <label for="demo_company">Organization Name *</label>
                    <input
                      id="demo_company"
                      v-model="form.company_name"
                      type="text"
                      placeholder="Enter your organization name"
                      :class="{ error: errors.company_name }"
                    />
                    <span v-if="errors.company_name" class="field-err">{{ errors.company_nameMsg || 'Required' }}</span>
                  </div>

                  <!-- C. Email ID -->
                  <div class="field full-width">
                    <label for="demo_email">Email ID *</label>
                    <input
                      id="demo_email"
                      v-model="form.email"
                      type="email"
                      placeholder="Enter your email (e.g. name@company.com)"
                      :class="{ error: errors.email }"
                    />
                    <span class="field-helper">Required solely to receive your personalized feedback.</span>
                    <span v-if="errors.email" class="field-err">{{ errors.emailMsg || 'Required' }}</span>
                  </div>

                  <!-- D. Function -->
                  <div class="field full-width">
                    <label for="demo_function">Which function do you primarily work in? *</label>
                    <AnimatedSelect
                      id="demo_function"
                      v-model="form.function"
                      :options="functionOptions"
                      placeholder="Select your function"
                      :error="!!errors.function"
                      @change="() => {}"
                    />
                    <span v-if="errors.function" class="field-err">{{ errors.functionMsg || 'Please select your function' }}</span>

                    <!-- Conditional field if Other -->
                    <div v-if="form.function === 'Other'" class="conditional-field mt-2">
                      <label for="demo_function_other">Please specify your function *</label>
                      <input
                        id="demo_function_other"
                        v-model="form.function_other"
                        type="text"
                        placeholder="Specify your function"
                        :class="{ error: errors.function_other }"
                      />
                      <span v-if="errors.function_other" class="field-err">{{ errors.function_otherMsg || 'Please specify your function' }}</span>
                    </div>
                  </div>

                  <!-- E. Current Role -->
                  <div class="field full-width">
                    <label class="group-label">Which best describes your current role? *</label>
                    <div class="radio-card-grid" :class="{ 'has-error': errors.role }">
                      <label
                        v-for="r in roleOptions"
                        :key="r"
                        class="radio-card"
                        :class="{ selected: form.role === r }"
                      >
                        <input
                          type="radio"
                          name="demo_role"
                          :value="r"
                          v-model="form.role"
                          class="sr-only"
                        />
                        <span class="radio-dot"></span>
                        <span class="radio-label">{{ r }}</span>
                      </label>
                    </div>
                    <span v-if="errors.role" class="field-err">{{ errors.roleMsg || 'Please select your current role' }}</span>
                  </div>

                  <!-- F. Country of Work Location -->
                  <div class="field full-width">
                    <label for="demo_country">Country of Work Location *</label>
                    <SearchableSelect
                      id="demo_country"
                      v-model="form.country"
                      :options="countryOptions"
                      placeholder="Search and select your country"
                      :error="!!errors.country"
                      @change="onCountryChange"
                    />
                    <span v-if="errors.country" class="field-err">{{ errors.countryMsg || 'Please select your country of work location' }}</span>

                    <!-- Conditionally display State or UT if India -->
                    <div v-if="form.country === 'India'" class="conditional-field mt-3">
                      <label for="demo_state_ut">Which State or Union Territory are you currently based in? *</label>
                      <AnimatedSelect
                        id="demo_state_ut"
                        v-model="form.state_ut"
                        :options="[...indianStates, ...indianUTs]"
                        placeholder="Select State or Union Territory"
                        :error="!!errors.state_ut"
                        @change="() => {}"
                      />
                      <span v-if="errors.state_ut" class="field-err">{{ errors.state_utMsg || 'Please select your State or Union Territory' }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Page 2: Gender Identity & PwD -->
              <div v-else-if="demoPage === 2" class="demo-page">
                <div class="identity-questions-list">
                  <!-- A. Gender Identity -->
                  <div class="demo-q-block">
                    <label class="group-label">How do you describe your gender identity? *</label>
                    <div class="radio-card-grid" :class="{ 'has-error': errors.gender }">
                      <label
                        v-for="g in genderOptions"
                        :key="g"
                        class="radio-card"
                        :class="{ selected: form.gender === g }"
                      >
                        <input
                          type="radio"
                          name="demo_gender"
                          :value="g"
                          v-model="form.gender"
                          class="sr-only"
                        />
                        <span class="radio-dot"></span>
                        <span class="radio-label">{{ g }}</span>
                      </label>
                    </div>
                    <span v-if="errors.gender" class="field-err">{{ errors.genderMsg || 'Please select your gender identity' }}</span>

                    <!-- Optional self-describe text field if Other gender identity -->
                    <div v-if="form.gender === 'Other gender identity'" class="conditional-field mt-2">
                      <label for="demo_gender_other">Self-describe <span class="label-opt">(Optional)</span></label>
                      <input
                        id="demo_gender_other"
                        v-model="form.gender_other"
                        type="text"
                        placeholder="Self-describe (optional)"
                      />
                    </div>
                  </div>

                  <!-- B. Person with Disability -->
                  <div class="demo-q-block">
                    <label class="group-label">Do you identify as a Person with Disability (PwD)? *</label>
                    <div class="radio-card-grid radio-card-grid--compact" :class="{ 'has-error': errors.is_pwd }">
                      <label
                        v-for="opt in pwdOptions"
                        :key="opt"
                        class="radio-card"
                        :class="{ selected: form.is_pwd === opt }"
                      >
                        <input
                          type="radio"
                          name="demo_pwd"
                          :value="opt"
                          v-model="form.is_pwd"
                          class="sr-only"
                        />
                        <span class="radio-dot"></span>
                        <span class="radio-label">{{ opt }}</span>
                      </label>
                    </div>
                    <span v-if="errors.is_pwd" class="field-err">{{ errors.is_pwdMsg || 'Please select an option' }}</span>
                  </div>
                </div>
              </div>

              <!-- Page 3: Neurodivergent & Marginalized + Consent -->
              <div v-else-if="demoPage === 3" class="demo-page">
                <div class="identity-questions-list">
                  <div class="demo-q-block">
                    <label class="group-label">Do you identify as neurodivergent? *</label>
                    <p class="field-helper-block">
                      Neurodivergent may include ADHD, autism, dyslexia, dyspraxia, and other cognitive or neurological differences.
                    </p>
                    <div class="radio-card-grid" :class="{ 'has-error': errors.is_neurodivergent }">
                      <label
                        v-for="opt in neurodivergentOptions"
                        :key="opt"
                        class="radio-card"
                        :class="{ selected: form.is_neurodivergent === opt }"
                      >
                        <input
                          type="radio"
                          name="demo_nd"
                          :value="opt"
                          v-model="form.is_neurodivergent"
                          class="sr-only"
                        />
                        <span class="radio-dot"></span>
                        <span class="radio-label">{{ opt }}</span>
                      </label>
                    </div>
                    <span v-if="errors.is_neurodivergent" class="field-err">{{ errors.is_neurodivergentMsg || 'Please select an option' }}</span>
                  </div>

                  <!-- D. Underrepresented / Historically Marginalized -->
                  <div class="demo-q-block">
                    <label class="group-label">Do you identify as belonging to an underrepresented or historically marginalized community? *</label>
                    <p class="field-helper-block">
                      This may include economic, ethnic, religious, caste-based, LGBTQIA+, or other communities that have historically experienced exclusion or underrepresentation.
                    </p>
                    <div class="radio-card-grid radio-card-grid--compact" :class="{ 'has-error': errors.is_marginalized }">
                      <label
                        v-for="opt in marginalizedOptions"
                        :key="opt"
                        class="radio-card"
                        :class="{ selected: form.is_marginalized === opt }"
                      >
                        <input
                          type="radio"
                          name="demo_marg"
                          :value="opt"
                          v-model="form.is_marginalized"
                          class="sr-only"
                        />
                        <span class="radio-dot"></span>
                        <span class="radio-label">{{ opt }}</span>
                      </label>
                    </div>
                    <span v-if="errors.is_marginalized" class="field-err">{{ errors.is_marginalizedMsg || 'Please select an option' }}</span>
                  </div>
                </div>

                <!-- Confidentiality Statement & Consent -->
              <div class="confidentiality-card mt-4">
                <div class="confidentiality-header">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#009070" stroke-width="2">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                  </svg>
                  <span>Confidentiality & Data Privacy</span>
                </div>
                <p class="confidentiality-text">
                  The demographic questions above help us understand how neuro-inclusion experiences vary across groups. Your responses will be analyzed in aggregate and treated confidentially. Individual demographic responses are never disclosed publicly or used to identify participants.
                </p>

                <div class="field full-width consent-wrapper">
                  <label for="gdpr_consent" class="consent-label">
                    <input type="checkbox" id="gdpr_consent" v-model="form.consent_given" class="consent-checkbox" />
                    <span>I consent to the collection and processing of my organisational data in accordance with the Privacy Policy. *</span>
                  </label>
                  <span v-if="errors.consent_given" class="field-err" style="margin-left: 2rem;">You must provide consent to proceed.</span>
                </div>
              </div>
              </div>

            </div>

            <!-- Instructions screen (step 3) -->
            <div v-else-if="currentStep === 3" class="instructions-screen">
              <div class="instr-layout">
                <!-- Left: how to complete -->
                <div class="instr-left">
                  <p class="instr-body">This should take approximately <strong>10 minutes</strong> to complete. The questionnaire covers up to <strong>8 key segments</strong>, each with <strong>5 statements</strong>.</p>
                  <p class="instr-body">Please read each statement carefully and choose the option that best reflects your <strong>current reality</strong> (rather than intention).</p>
                  <div class="instr-options">
                    <span class="instr-opt">Yes</span>
                    <span class="instr-opt">Partially</span>
                    <span class="instr-opt">No</span>
                    <span class="instr-opt">Not Sure</span>
                  </div>
                  <p class="instr-note">Your responses will only include details that you choose to share.</p>
                  <div class="instr-divider"></div>
                  <p class="instr-segments-label">The segments covered:</p>
                  <div class="instr-segments-list">
                    <div v-for="(s, i) in sections" :key="s.id" class="instr-segment-row">
                      <span class="instr-seg-num">{{ i + 1 }}</span>
                      <span class="instr-seg-name">{{ s.title }}</span>
                    </div>
                  </div>
                </div>
                <!-- Right: section descriptions -->
                <div class="instr-right">
                  <p class="instr-right-label">What each segment covers</p>
                  <div class="instr-desc-list">
                    <div v-for="(s, i) in sections" :key="s.id" class="instr-desc-row">
                      <div class="instr-desc-num">{{ i + 1 }}</div>
                      <div>
                        <span class="instr-desc-title">{{ s.title }}</span>
                        <p class="instr-desc-body">{{ s.summary }}</p>
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
            </div>
          </div>
          </div>

          <!-- Bottom Navigation -->
          <div class="why-matters-footer">
            <button v-if="currentStep === 2 && demoPage > 1" class="btn-back-compact" @click="demoPage--" type="button">← Back</button>
            <button v-else-if="currentStep > 0" class="btn-back-compact" @click="currentStep--; demoPage = 1;" type="button">← Back</button>
            <div v-else></div>

            <div class="step-nav-mid">
              <button v-if="currentStep > 3" class="btn-start-fresh" @click="startFresh" type="button">↺ Start Fresh</button>
              <SaveContinueButton v-if="currentStep > 3" :onSave="syncToBackend" />
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
        </div>
      </div>

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
const demoPage        = ref(1); // Pagination for demographics (step 2)
const showMobileInfo  = ref(false);
const questionsScroll = ref(null);
const errors      = reactive({});
const options     = ["Yes", "Partially", "No", "Not Sure"];

// ── Cinematic Welcome Animation ──
const welcomePillRef = ref(null);
const introStageRef = ref(null);
const heroVideoRef = ref(null);
const isAnimReady = ref(false);
const isAnimDone = ref(false);

function playHeroVideo() {
  if (heroVideoRef.value) {
    heroVideoRef.value.muted = true;
    heroVideoRef.value.defaultMuted = true;
    heroVideoRef.value.playsInline = true;
    heroVideoRef.value.loop = true;
    heroVideoRef.value.play().catch(() => {});
  }
}

function onVideoEnded() {
  if (heroVideoRef.value) {
    heroVideoRef.value.currentTime = 0;
    heroVideoRef.value.play().catch(() => {});
  }
}

function onVideoTimeUpdate() {
  if (heroVideoRef.value && heroVideoRef.value.duration) {
    if (heroVideoRef.value.currentTime >= heroVideoRef.value.duration - 0.1) {
      heroVideoRef.value.currentTime = 0;
      heroVideoRef.value.play().catch(() => {});
    }
  }
}

function setupWelcomeAnimation() {
  playHeroVideo();
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
  tip: "This should take approximately 10 minutes to complete. The questionnaire is organised into 8 key segments, each with 5 statements. Please read each statement carefully and choose the option that best reflects your current reality (rather than intention). Your responses will only include details that you choose to share.",
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

watch(currentStep, async () => {
  showMobileInfo.value = false;
  await nextTick();
  questionsScroll.value?.scrollTo({ top: 0, behavior: "smooth" });
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
  playHeroVideo();
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
  }
});

watch(() => form, (newForm) => {
  Object.keys(newForm).forEach(k => {
    if (newForm[k] && errors[k]) {
      delete errors[k];
    }
  });
}, { deep: true });

function validateDemoPage() {
  Object.keys(errors).forEach(k => delete errors[k]);
  
  if (demoPage.value === 1) {
    // Page 1: Name (optional), Company, Email, Function, Role, Country
    const comp = (form.company_name || "").trim();
    if (!comp) {
      errors.company_name = true;
      errors.company_nameMsg = "Organization name is required";
    }

    const em = (form.email || "").trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!em) {
      errors.email = true;
      errors.emailMsg = "Email ID is required solely to receive your personalized feedback";
    } else if (!emailRegex.test(em)) {
      errors.email = true;
      errors.emailMsg = "Please enter a valid email address (e.g. name@company.com)";
    }

    if (!form.function) {
      errors.function = true;
      errors.functionMsg = "Please select your primary function";
    } else if (form.function === "Other" && !(form.function_other || "").trim()) {
      errors.function_other = true;
      errors.function_otherMsg = "Please specify your function";
    }

    if (!form.role) {
      errors.role = true;
      errors.roleMsg = "Please select your current role";
    }

    if (!form.country) {
      errors.country = true;
      errors.countryMsg = "Please select your country of work location";
    } else if (form.country === "India" && !form.state_ut) {
      errors.state_ut = true;
      errors.state_utMsg = "Please select your State or Union Territory";
    }
  } else if (demoPage.value === 2) {
    // Page 2: Gender, PwD
    if (!form.gender) {
      errors.gender = true;
      errors.genderMsg = "Please select your gender identity";
    }

    if (!form.is_pwd) {
      errors.is_pwd = true;
      errors.is_pwdMsg = "Please select an answer";
    }
  } else if (demoPage.value === 3) {
    // Page 3: Neurodivergent, Marginalized, Consent
    if (!form.is_neurodivergent) {
      errors.is_neurodivergent = true;
      errors.is_neurodivergentMsg = "Please select an answer";
    }

    if (!form.is_marginalized) {
      errors.is_marginalized = true;
      errors.is_marginalizedMsg = "Please select an answer";
    }

    if (!form.consent_given) {
      errors.consent_given = true;
    }
  }
  
  return Object.keys(errors).length === 0;
}

function validateStep() {
  Object.keys(errors).forEach(k => delete errors[k]);
  if (currentStep.value === 0) {
    // Intro screen — no validation needed
  } else if (currentStep.value === 1) {
    // Why This Matters — no validation needed
  } else if (currentStep.value === 2) {
    // Tell Us About You validation
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
    const firstError = document.querySelector('.field-err');
    if (firstError) {
      const block = firstError.closest('.q-block') || firstError.closest('.demo-q-block') || firstError.closest('.field') || firstError.closest('.confidentiality-card');
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
  if (currentStep.value === 2 && demoPage.value < 3) {
    // Demographics pagination - advance to next page within step 2 (3 pages total)
    if (validateDemoPage()) {
      demoPage.value++;
    } else {
      scrollToError();
    }
  } else if (validateStep()) {
    // Move to next step and reset demo page
    if (currentStep.value === 2) {
      demoPage.value = 1;
    }
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
  padding: 1rem 4rem 0;
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
  max-width: 1600px;
  margin: 0 auto;
  padding: 0.5rem 4rem 2rem;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: center;
  box-sizing: border-box;
  min-height: 0;
}

.intro-hero-left {
  display: flex;
  flex-direction: column;
  justify-content: center;
  max-width: 100%;
  padding-right: 1rem;
}

.hero-badge-wrap {
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.niwi-brand-logo {
  height: 36px;
  width: auto;
  border-radius: 7px;
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
  font-size: clamp(2.1rem, 3vw, 3rem);
  font-weight: 800;
  color: var(--c-primary-dark, #161057);
  letter-spacing: -0.025em;
  line-height: 1.18;
  margin: 0 0 1.25rem 0;
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
  font-size: 1.02rem;
  line-height: 1.7;
  color: #374151;
  margin: 0 0 0.85rem 0;
  font-family: var(--font-body);
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
  margin-top: 1.25rem;
  padding-top: 0;
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
  justify-content: center;
  align-items: center;
  position: relative;
  padding-top: 0;
  height: 100%;
}

.clipart-card {
  width: 100%;
  max-width: 680px;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
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

.intro-fullpage.anim-ready:not(.anim-done) .anim-hero-cta {
  opacity: 0;
  animation: contentGentleFadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) 2.45s forwards;
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
@media (max-width: 1080px) {
  .intro-topbar {
    padding: 0.75rem 2rem 0.25rem;
  }
  .intro-hero-layout {
    grid-template-columns: 1fr;
    gap: 2.5rem;
    padding: 1rem 2rem 2.5rem;
    align-items: flex-start;
  }
  .intro-hero-left {
    padding-right: 0;
  }
  .intro-hero-right {
    order: 2;
    padding-top: 0;
    justify-content: center;
  }
  .clipart-card {
    max-width: 480px;
    margin: 0 auto;
  }
}

@media (max-width: 640px) {
  .intro-topbar {
    padding: 0.75rem 1.25rem 0.25rem;
    justify-content: flex-end;
  }
  .intro-hero-layout {
    padding: 0.75rem 1.25rem 2rem;
    gap: 1.75rem;
  }
  .hero-title {
    font-size: 1.75rem;
  }
  .hero-desc {
    font-size: 0.95rem;
  }
  .clipart-card {
    max-width: 100%;
  }
  .hero-clipart-video {
    max-height: 350px;
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
  overflow: hidden;
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

/* ── Compact Content Area ── */
.why-matters-content {
  flex: 1;
  display: grid;
  grid-template-columns: 55fr 45fr;
  gap: 3rem;
  padding: 1.5rem 2.5rem;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  overflow-y: auto;
  min-height: 0;
}

.why-content-left {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  min-height: 0;
}

.why-badge-compact {
  display: inline-flex;
  align-items: center;
  background: transparent;
  color: var(--c-accent, #04907C);
  border: 1.5px solid var(--c-accent, #04907C);
  border-radius: 99px;
  padding: 0.25rem 0.75rem;
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-family: var(--font-body);
  width: fit-content;
}

.why-title-compact {
  font-size: 1.65rem;
  font-weight: 800;
  color: var(--c-primary-dark, #161057);
  letter-spacing: -0.02em;
  line-height: 1.2;
  margin: 0;
  font-family: 'Fraunces', serif;
}

.why-desc-compact {
  font-size: 0.875rem;
  line-height: 1.6;
  color: #374151;
  margin: 0 0 0.5rem 0;
  font-family: var(--font-body);
}

/* ── 2x2 Benefits Grid with Pastel Colors ── */
.benefits-grid-compact {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
  margin-top: 0.25rem;
}

.benefit-card-compact {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  border-radius: 10px;
  border: none;
  box-shadow: none;
}

.benefit-card-compact:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* Pastel Background Colors */
.benefit-mint {
  background: #EAF7F1;
}

.benefit-cream {
  background: #FFF5D9;
}

.benefit-blue {
  background: #EDF5FC;
}

.benefit-icon-compact {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 8px;
  color: var(--c-primary-dark, #161057);
  flex-shrink: 0;
}

.benefit-title-compact {
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--c-primary-dark, #161057);
  font-family: 'Fraunces', serif;
  line-height: 1.3;
  margin: 0;
}

.benefit-text-compact {
  font-size: 0.75rem;
  line-height: 1.5;
  color: #4B5563;
  margin: 0;
  font-family: var(--font-body);
}

/* ── Right Column: Compact Illustration ── */
.why-content-right {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem 0;
}

.why-illustration-compact {
  width: 100%;
  max-width: 450px;
  height: auto;
  max-height: 500px;
  object-fit: contain;
  display: block;
}

/* ── Footer Navigation ── */
.why-matters-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 3rem;
  border-top: 1px solid rgba(22, 16, 87, 0.08);
  flex-shrink: 0;
  background: var(--bg, #FAFAF8);
  gap: 1rem;
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

/* ── Responsive Design ── */
@media (max-width: 1080px) {
  .why-matters-header {
    padding: 0.75rem 2rem;
  }
  
  .why-matters-content {
    grid-template-columns: 1fr;
    gap: 2rem;
    padding: 1.25rem 2rem;
  }
  
  .why-content-right {
    order: -1;
  }
  
  .why-illustration-compact {
    max-width: 350px;
    max-height: 350px;
  }
}

@media (max-width: 640px) {
  .why-matters-header {
    padding: 0.75rem 1rem;
  }
  
  .why-niwi-text {
    font-size: 0.65rem;
  }
  
  .why-matters-content {
    padding: 1rem;
    gap: 1.5rem;
  }
  
  .why-title-compact {
    font-size: 1.5rem;
  }
  
  .why-desc-compact {
    font-size: 0.8rem;
  }
  
  .benefits-grid-compact {
    grid-template-columns: 1fr;
    gap: 0.65rem;
  }
  
  .benefit-card-compact {
    padding: 0.875rem;
  }
  
  .benefit-title-compact {
    font-size: 0.8rem;
  }
  
  .benefit-text-compact {
    font-size: 0.7rem;
  }
  
  .why-illustration-compact {
    max-width: 280px;
    max-height: 280px;
  }
  
  .why-matters-footer {
    padding: 0.875rem 1rem;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .btn-back-compact,
  .btn-next-compact {
    width: 100%;
    justify-content: center;
    display: flex;
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
  overflow-y: auto;
  overflow-x: hidden;
  overscroll-behavior: contain;
  padding: 0.75rem 3.5rem 2rem;
  scrollbar-width: thin;
  scrollbar-color: rgba(4, 144, 124, 0.3) rgba(4, 144, 124, 0.08);
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

.step-tag { display: inline-flex; align-items: center; background: transparent; color: var(--c-accent); font-size: 0.68rem; font-weight: 800; padding: 0.25rem 0.75rem; border-radius: 99px; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.75rem; border: 1.5px solid var(--c-accent); font-family: var(--font-body); }
.step-head-row { display: flex; align-items: baseline; gap: 1rem; flex-wrap: wrap; }
.h1-green { font-size: 1.65rem; font-weight: 800; color: var(--c-accent); letter-spacing: -0.025em; line-height: 1.2; margin-bottom: 0.65rem; font-family: 'Fraunces', serif; }
.h1-navy { font-size: 1.75rem; font-weight: 800; color: var(--c-primary-dark); letter-spacing: -0.025em; line-height: 1.2; margin-bottom: 0.65rem; font-family: 'Fraunces', serif; cursor: pointer; }
.step-sub { color: #64748B; font-size: 0.85rem; margin-bottom: 0; line-height: 1.45; }
.step-sub-inline { color: #64748B; font-size: 0.8rem; white-space: nowrap; margin-bottom: 0; align-self: flex-end; padding-bottom: 0.35rem; }

/* Demographics Form Styles */
.demographics-form {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
  padding-bottom: 1.5rem;
}

/* Demographics Form - No Background Boxes, Paginated Content */
.demographics-form {
  width: 100%;
}

.demo-page {
  width: 100%;
  padding: 0;
}

/* Hide section styling - no boxes or headers */
.demo-section {
  background: transparent;
  border: none;
  border-radius: 0;
  padding: 0;
  box-shadow: none;
}

.demo-section:focus-within {
  border-color: transparent;
}

.demo-section-header {
  display: none;
}

.demo-section-badge {
  display: none;
}

.demo-section-badge.demo-badge-teal {
  display: none;
}

.demo-section-title {
  display: none;
}

.demo-section-desc {
  display: none;
}

.label-opt {
  color: #8C827A;
  font-weight: 400;
  font-size: 0.82em;
  text-transform: none;
}

.field-helper {
  display: block;
  font-size: 0.75rem;
  color: #007057;
  margin-top: 0.25rem;
  font-weight: 500;
}

.field-helper-block {
  font-size: 0.78rem;
  color: #4A5568;
  margin: 0 0 0.6rem 0;
  line-height: 1.45;
  background: #FAF8F5;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  border-left: 2.5px solid #009070;
}

.select-wrapper {
  position: relative;
  width: 100%;
}

.select-wrapper::after {
  content: '';
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23555555' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: center;
  background-size: contain;
  pointer-events: none;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.select-wrapper:has(.custom-select:focus)::after {
  transform: translateY(-50%) rotate(180deg);
}

.custom-select {
  width: 100%;
  padding: 0.55rem 2.25rem 0.55rem 0.75rem;
  background-color: #FFFFFF;
  border: 1.5px solid var(--c-border);
  border-radius: 8px;
  font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 0.85rem;
  color: #120050;
  appearance: none;
  -webkit-appearance: none;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  min-height: 38px;
  box-sizing: border-box;
}

.custom-select:hover {
  border-color: #009070;
}

.custom-select:focus {
  outline: none;
  border-color: #009070;
  box-shadow: 0 0 0 2px rgba(0, 144, 112, 0.12);
}

.custom-select.error {
  border-color: #ff4444;
  background-color: #FFF5F5;
}

.custom-select option {
  padding: 0.6rem 0.75rem;
  background: #FFFFFF;
  color: #120050;
  font-size: 0.85rem;
}

.custom-select option:hover,
.custom-select option:checked {
  background: #E6F4F1;
  color: #007057;
}

.group-label {
  display: block;
  font-size: 0.68rem;
  font-weight: 800;
  color: var(--c-primary-dark);
  margin-bottom: 0.45rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-family: 'Fraunces', serif;
}

.radio-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(165px, 1fr));
  gap: 0.5rem;
  row-gap: 0.5rem;
}

.radio-card-grid--compact {
  grid-template-columns: repeat(auto-fit, minmax(105px, 1fr));
}

.radio-card-grid.has-error .radio-card {
  border-color: rgba(255, 68, 68, 0.5);
}

.radio-card {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.6rem 0.75rem;
  background: #FFFFFF;
  border: 1.5px solid var(--c-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  user-select: none;
  position: relative;
  overflow: hidden;
  min-height: 36px;
}

.radio-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.05), rgba(59, 130, 246, 0.02));
  opacity: 0;
  transition: opacity 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.radio-card:hover {
  border-color: #3B82F6;
  background: #FAF8F5;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.radio-card:hover::before {
  opacity: 1;
}

.radio-card.selected {
  border-color: #3B82F6;
  background: #EFF6FF;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.2);
  transform: translateY(-1px);
}

.radio-card.selected::before {
  opacity: 1;
}

.radio-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 1.5px solid #8C827A;
  background: #FFFFFF;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  z-index: 1;
}

.radio-card:hover .radio-dot {
  border-color: #3B82F6;
  transform: scale(1.1);
}

.radio-card.selected .radio-dot {
  border-color: #3B82F6;
  background: #3B82F6;
  box-shadow: inset 0 0 0 2.5px #FFFFFF, 0 0 0 1.5px rgba(59, 130, 246, 0.2);
  transform: scale(1.15);
}

.radio-label {
  font-size: 0.84rem;
  font-weight: 500;
  color: #120050;
  line-height: 1.3;
  position: relative;
  z-index: 1;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.radio-card:hover .radio-label {
  color: #2563EB;
}

.radio-card.selected .radio-label {
  font-weight: 600;
  color: #2563EB;
}

.identity-questions-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.demo-q-block {
  padding-bottom: 0.85rem;
  border-bottom: 1px solid #F0ECE4;
}

.demo-q-block:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.conditional-field {
  background: #FAF8F5;
  padding: 1rem;
  border-radius: 8px;
  border: 1px dashed #009070;
  margin-top: 0.75rem;
  animation: fadeIn 0.2s ease-out;
}

.confidentiality-card {
  background: #FAF8F5;
  border: 1.5px solid #009070;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0, 144, 112, 0.08);
}

.confidentiality-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-family: 'Playfair Display', serif;
  font-size: 1.1rem;
  font-weight: 700;
  color: #120050;
  margin-bottom: 0.5rem;
}

.confidentiality-text {
  font-size: 0.88rem;
  color: #555;
  line-height: 1.6;
  margin: 0 0 1rem 0;
}

.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 0.75rem; }
.mt-4 { margin-top: 1.25rem; }
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

/* Details fields - Compact sizing with blue focus */
.fields-grid { 
  display: grid; 
  grid-template-columns: 1fr 1fr; 
  gap: 0.75rem;
  row-gap: 0.85rem;
}

.field.half-width {
  grid-column: span 1;
}

.field label { 
  display: block; 
  font-size: 0.68rem; 
  font-weight: 800; 
  color: var(--c-primary-dark); 
  margin-bottom: 0.3rem; 
  text-transform: uppercase; 
  letter-spacing: 0.05em; 
  font-family: 'Fraunces', serif; 
}

.field input:not([type="checkbox"]) {
  width: 100%; 
  max-width: 420px;
  padding: 0.55rem 0.75rem;
  border: 1.5px solid #3B82F6; 
  border-radius: 8px;
  font-size: 0.85rem; 
  background: var(--c-white); 
  color: var(--c-primary-dark);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); 
  font-family: inherit;
  min-height: 38px;
}
.field input:not([type="checkbox"]):hover {
  border-color: #2563EB;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.1);
}
.field input:not([type="checkbox"]):focus { 
  outline: none; 
  border-color: #2563EB; 
  background: var(--c-white);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  transform: translateY(-1px);
}
.field input:not([type="checkbox"]).error { 
  border-color: #ff4444; 
  background-color: #FFF5F5;
}
.field-err { color: #ff4444; font-size: 0.72rem; margin-top: 0.2rem; display: block; }

/* Consent Checkbox Styling */
.consent-wrapper {
  grid-column: 1 / -1;
  margin-top: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.field label.consent-label {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  cursor: pointer;
  font-size: 0.75rem;
  line-height: 1.5;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--c-accent);
  user-select: none;
  margin-bottom: 0;
}
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

/* Questions */
.questions-list { display: flex; flex-direction: column; gap: 1rem; padding-bottom: 0.5rem; }
.section-liner { font-size: 0.9rem; color: #444; background: rgba(4, 144, 124, 0.05); padding: 1rem 1.25rem; border-radius: 8px; border-left: 3px solid var(--c-accent); font-style: italic; }
.supplier-definition-banner { 
  font-size: 0.85rem; 
  color: #555; 
  background: #F4F2F0; 
  padding: 0.875rem 1.25rem; 
  border-radius: 8px; 
  border: 1px solid #E2DDD4; 
  font-style: italic;
  line-height: 1.5;
  margin-bottom: 0.5rem;
}
.supplier-definition-banner strong {
  color: var(--c-primary-dark);
  font-weight: 700;
  font-style: normal;
}
.gating-block { background: #F9F8FF; padding: 1.25rem; border-radius: 12px; border: 1px solid #E2DDD4; }
.leading-gating-block { border-color: var(--c-accent); border-width: 1.5px; background: rgba(4, 144, 124, 0.04); }
.gating-eligibility-label {
  font-size: 0.65rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--c-accent); font-family: 'Fraunces', serif;
  margin-bottom: 0.5rem;
}
.gating-guidance {
  font-size: 0.8rem;
  color: #777;
  line-height: 1.55;
  margin: 0.75rem 0 0;
  font-style: italic;
  border-top: 1px solid rgba(4, 144, 124, 0.15);
  padding-top: 0.65rem;
}
.gating-confirmed-badge {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  background: rgba(4, 144, 124, 0.06);
  border: 1.5px solid rgba(4, 144, 124, 0.25);
  border-radius: 10px;
  padding: 0.6rem 1rem;
}
.gating-confirmed-check {
  font-size: 0.75rem;
  font-weight: 800;
  color: var(--c-white);
  background: var(--c-accent);
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}
.gating-confirmed-text {
  font-size: 0.8rem;
  color: var(--c-primary-dark);
  font-weight: 600;
  flex: 1;
  line-height: 1.4;
}
.gating-change-btn {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--c-accent);
  background: none;
  border: 1.5px solid var(--c-accent);
  border-radius: 99px;
  padding: 0.2rem 0.65rem;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s;
}
.gating-change-btn:hover {
  background: var(--c-accent);
  color: var(--c-white);
}
.section-skipped-notice {
  display: flex; align-items: flex-start; gap: 1rem;
  background: #F4F2F0; border: 1.5px solid #E2DDD4; border-radius: 12px;
  padding: 1.25rem 1.5rem; color: #555;
}
.section-skipped-notice .skipped-heading { font-weight: 800; color: var(--c-primary-dark); display: block; margin-bottom: 0.25rem; }
.section-skipped-notice p { margin: 0; font-size: 0.875rem; line-height: 1.55; color: #666; }
.section-skipped-notice strong { color: var(--c-primary-dark); font-weight: 700; }
.skipped-notice-icon { font-size: 1.5rem; color: #aaa; flex-shrink: 0; line-height: 1; margin-top: 0.1rem; }
.how-to-intro {
  background: var(--c-white);
  border: 2px solid var(--c-border);
  border-left: 4px solid var(--c-accent);
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 0.5rem;
}
.how-to-intro h3 {
  font-size: 0.85rem; font-weight: 800; color: var(--c-accent);
  text-transform: uppercase; letter-spacing: 0.06em;
  margin-bottom: 0.5rem; font-family: 'Fraunces', serif;
}
.how-to-intro p {
  font-size: 0.9rem; line-height: 1.6; color: #444;
}
.q-block:last-child { padding-bottom: 0.25rem; }
.q-header-row { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.4rem; }
.q-number { font-size: 0.68rem; font-weight: 800; color: var(--c-primary-dark); background: var(--c-bg); border: 1.5px solid var(--c-primary-dark); display: inline-block; padding: 0.15rem 0.55rem; border-radius: 5px; letter-spacing: 0.06em; font-family: 'Fraunces', serif; }
.q-short { font-size: 0.78rem; font-weight: 700; color: var(--c-primary-dark); font-family: 'Fraunces', serif; letter-spacing: -0.01em; }
.q-text { font-size: 0.95rem; font-weight: 500; color: var(--c-primary-dark); line-height: 1.55; margin-bottom: 0.75rem; }
.options { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.opt-btn {
  padding: 0.45rem 1rem; border-radius: 99px;
  border: 1.5px solid #E2DDD4; background: var(--c-bg);
  font-size: 0.85rem; font-weight: 500; cursor: pointer; color: #555;
  transition: all 0.15s;
}
.opt-btn:hover { border-color: var(--c-primary-dark); color: var(--c-primary-dark); }
.opt-btn.selected { background: var(--c-primary-dark); color: var(--c-white); border-color: var(--c-primary-dark); font-weight: 700; }

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
.success-wrap { flex: 1; display: flex; align-items: center; justify-content: center; padding: 2rem; }
.success-box { background: var(--c-white); border-radius: 16px; padding: 3rem 2.5rem; text-align: center; border: 1px solid #E2DDD4; max-width: 440px; width: 100%; }
.success-icon { width: 64px; height: 64px; background: var(--c-accent-secondary); border-radius: 50%; display: inline-grid; place-items: center; font-size: 1.8rem; margin-bottom: 1.25rem; }
.success-box h2 { font-size: 1.5rem; font-weight: 800; color: var(--c-primary-dark); margin-bottom: 0.75rem; }
.success-box p  { color: #666; line-height: 1.6; font-size: 0.9rem; margin-bottom: 1.5rem; }

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
}
.instr-layout {
  display: grid;
  grid-template-columns: minmax(320px, 480px) 1fr;
  gap: 2rem;
  align-items: start;
}
.instr-left {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  padding: 1.5rem;
  background: rgba(4, 144, 124, 0.04);
  border-radius: 12px;
}
.instr-right {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.instr-right-label {
  font-size: 0.68rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--c-accent);
  font-family: 'Fraunces', serif;
  margin: 0 0 0.25rem;
}
.instr-desc-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.instr-desc-row {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  padding: 0.65rem 0.85rem;
  background: var(--c-white);
  border: 1.5px solid #E2DDD4;
  border-radius: 10px;
}
.instr-desc-num {
  font-size: 0.7rem;
  font-weight: 800;
  color: var(--c-white);
  background: var(--c-accent);
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  margin-top: 1px;
  font-family: 'Fraunces', serif;
}
.instr-desc-title {
  font-size: 0.8rem;
  font-weight: 800;
  color: var(--c-primary-dark);
  display: block;
  margin-bottom: 0.2rem;
  font-family: 'Fraunces', serif;
}
.instr-desc-body {
  font-size: 0.78rem;
  color: #666;
  line-height: 1.5;
  margin: 0;
}
.instr-body {
  font-size: 0.95rem;
  line-height: 1.7;
  color: #444;
  margin: 0;
}
.instr-options {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin: 0.1rem 0;
}
.instr-opt {
  padding: 0.3rem 1rem;
  border-radius: 99px;
  border: 1.5px solid #C8C3BA;
  background: var(--c-white);
  font-size: 0.85rem;
  font-weight: 500;
  color: #555;
}
.instr-note {
  font-size: 0.8rem;
  color: #aaa;
  margin: 0;
  font-style: italic;
}
.instr-divider {
  height: 1px;
  background: #E2DDD4;
  margin: 0.4rem 0;
}
.instr-segments-label {
  font-size: 0.68rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--c-accent);
  font-family: 'Fraunces', serif;
  margin: 0;
}
.instr-segments-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.instr-segment-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.instr-seg-num {
  font-size: 0.7rem;
  font-weight: 800;
  color: var(--c-accent);
  font-family: 'Fraunces', serif;
  min-width: 1rem;
}
.instr-seg-name {
  font-size: 0.875rem;
  color: var(--c-primary-dark);
  font-weight: 500;
  line-height: 1.35;
}
@media (max-width: 600px) {
  .instr-segments-list { grid-template-columns: 1fr; }
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
  overflow: hidden;
}

.unified-content {
  flex: 1;
  padding: 0;
  max-width: 100%;
  margin: 0;
  width: 100%;
  overflow-y: auto;
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
  padding: 2rem 3rem 1.5rem;
  background: var(--bg, #FAFAF8);
}

.questions-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 0 3rem 2rem;
  background: var(--bg, #FAFAF8);
  min-height: 0;
}

/* Responsive for unified layout */
@media (max-width: 1080px) {
  .step-card-head {
    padding: 1.5rem 2rem 1rem;
  }
  
  .questions-scroll {
    padding: 0 2rem 1.5rem;
  }
}

@media (max-width: 640px) {
  .step-card-head {
    padding: 1.25rem 1.5rem 1rem;
  }
  
  .questions-scroll {
    padding: 0 1.5rem 1.25rem;
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
