/**
 * Autonomous YouTube Shorts Studio Frontend Controller.
 * Handles live telemetry, project list rendering, video preview,
 * Content Brain visualization, and autonomous agent triggers.
 */

let activeProjectId = null;
let allProjectsData = [];
let activeProjectFilter = "all";

document.addEventListener("DOMContentLoaded", () => {
  initTelemetry();
  loadProjects();
  loadJobs();
  loadBrainData();
  setupEventListeners();

  // Handle URL hash changes
  window.addEventListener("hashchange", handleRouting);
  handleRouting();

  // Periodic telemetry refresh
  setInterval(() => {
    loadProjects();
    loadJobs();
  }, 6000);
});

function handleRouting() {
  const hash = window.location.hash || "#dashboard";
  document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active"));
  
  const projectsSection = document.getElementById("section-projects") || document.querySelector(".content-section:not(#section-brain)");
  const brainSection = document.getElementById("section-brain");

  if (hash === "#brain") {
    document.getElementById("nav-brain")?.classList.add("active");
    projectsSection?.classList.add("hidden");
    brainSection?.classList.remove("hidden");
    loadBrainData();
  } else if (hash === "#projects") {
    document.getElementById("nav-projects")?.classList.add("active");
    projectsSection?.classList.remove("hidden");
    brainSection?.classList.add("hidden");
    setFilter("produced");
  } else if (hash === "#jobs") {
    document.getElementById("nav-jobs")?.classList.add("active");
    projectsSection?.classList.remove("hidden");
    brainSection?.classList.add("hidden");
  } else {
    document.getElementById("nav-dashboard")?.classList.add("active");
    projectsSection?.classList.remove("hidden");
    brainSection?.classList.add("hidden");
  }
}

function setFilter(filterType) {
  activeProjectFilter = filterType;
  document.querySelectorAll(".filter-controls .tab-btn").forEach(btn => {
    if (btn.getAttribute("data-filter") === filterType) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });
  renderProjects(allProjectsData);
}

async function initTelemetry() {
  try {
    const res = await fetch("/api/status");
    if (!res.ok) return;
    const data = await res.json();

    // FFmpeg
    const ffmpegEl = document.getElementById("tele-ffmpeg");
    if (data.ffmpeg.available) {
      ffmpegEl.textContent = "7.1 Active";
      ffmpegEl.className = "tele-val text-success";
    } else {
      ffmpegEl.textContent = "Missing";
      ffmpegEl.className = "tele-val text-danger";
    }

    // Ollama
    const ollamaEl = document.getElementById("tele-ollama");
    if (data.ollama.connected) {
      ollamaEl.textContent = data.ollama.active_model;
      ollamaEl.className = "tele-val text-success";
    } else {
      ollamaEl.textContent = "Fallback Mode";
      ollamaEl.className = "tele-val text-warning";
    }

    // YouTube
    const ytEl = document.getElementById("tele-yt");
    if (data.youtube.authenticated) {
      ytEl.textContent = "OAuth Connected";
      ytEl.className = "tele-val text-success";
    } else {
      ytEl.textContent = data.demo_mode ? "Demo Active" : "Private Test Mode";
      ytEl.className = "tele-val text-warning";
    }
  } catch (err) {
    console.error("Telemetry error:", err);
  }
}

async function loadProjects() {
  try {
    const res = await fetch("/api/projects");
    if (!res.ok) return;
    const projects = await res.json();
    allProjectsData = projects;
    renderProjects(projects);
    updateStats(projects);
  } catch (err) {
    console.error("Load projects error:", err);
  }
}

function updateStats(projects) {
  document.getElementById("stat-topics").textContent = projects.length;
  const rendered = projects.filter(p => p.video_path || p.stream_url || p.state === "RENDERED" || p.state === "QC_PASSED" || p.state === "APPROVED" || p.state === "PUBLISHED").length;
  document.getElementById("stat-rendered").textContent = rendered;
  const qcPassed = projects.filter(p => p.quality_score && p.quality_score >= 75).length;
  document.getElementById("stat-qc-passed").textContent = qcPassed;
  const published = projects.filter(p => p.state === "PUBLISHED").length;
  document.getElementById("stat-published").textContent = published;
}

function renderProjects(projects) {
  const container = document.getElementById("projects-container");
  let filteredList = projects || [];

  const producedCount = filteredList.filter(p => p.video_path || p.stream_url || p.state === "RENDERED" || p.state === "QC_PASSED" || p.state === "APPROVED" || p.state === "PUBLISHED").length;
  const producedBtn = document.getElementById("filter-produced");
  if (producedBtn) {
    producedBtn.textContent = `Produced Videos (${producedCount})`;
  }

  if (activeProjectFilter === "produced") {
    filteredList = filteredList.filter(p => p.video_path || p.stream_url || p.state === "RENDERED" || p.state === "QC_PASSED" || p.state === "APPROVED" || p.state === "PUBLISHED");
  } else if (activeProjectFilter === "failed") {
    filteredList = filteredList.filter(p => p.state === "FAILED");
  }

  if (!filteredList || filteredList.length === 0) {
    container.innerHTML = `
      <div class="empty-state glass-panel">
        <div class="empty-icon">🎬</div>
        <h4>No ${activeProjectFilter === "produced" ? "Produced Videos" : "Projects"} found</h4>
        <p>${activeProjectFilter === "produced" ? "Rendered video shorts will appear here once ready." : "Click <strong>Generate Short Now</strong> to start your first autonomous production cycle."}</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filteredList.map(p => {
    let badgeClass = "badge-rendered";
    if (p.state === "QC_PASSED" || p.state === "APPROVED") badgeClass = "badge-qc-passed";
    if (p.state === "PUBLISHED") badgeClass = "badge-published";
    if (p.state === "NEEDS_REVIEW") badgeClass = "badge-needs-review";
    if (p.state === "FAILED") badgeClass = "badge-failed";

    const duration = p.duration_sec ? `${p.duration_sec.toFixed(0)}s` : "Processing";
    const score = p.quality_score ? `QC: ${p.quality_score}/100` : "QC Pending";

    return `
      <div class="project-card glass-panel" onclick="openProjectDetail('${p.id}')">
        <div class="project-card-header">
          <span class="badge ${badgeClass}">${p.state}</span>
          <span style="font-size: 11px; color: var(--text-muted);">${new Date(p.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
        </div>
        <div class="project-title">${escapeHtml(p.title)}</div>
        <div class="project-meta-row">
          <span>⏱ ${duration}</span>
          <span>⭐ ${score}</span>
          <span style="text-transform: capitalize;">📁 ${p.category}</span>
        </div>
      </div>
    `;
  }).join("");
}

// -------------------------------------------------------------
// Content Brain Data Loading & Rendering
// -------------------------------------------------------------

async function loadBrainData() {
  try {
    const res = await fetch("/api/brain");
    if (!res.ok) return;
    const brain = await res.json();

    // 1. Dynamic Portfolio Mix
    renderPortfolioBars(brain.dynamic_portfolio_mix);

    // 2. Characters Roster
    renderCharacters(brain.characters);

    // 3. Category Leaderboard
    renderCategoryTable(brain.category_leaderboard);

    // 4. Latest Review
    renderLatestReview(brain.latest_review);

    // 5. Blacklists
    loadBlacklists();
  } catch (err) {
    console.error("Load brain error:", err);
  }
}

function renderPortfolioBars(mix) {
  const container = document.getElementById("portfolio-bars-container");
  if (!mix || Object.keys(mix).length === 0) {
    container.innerHTML = "<p>No allocation data.</p>";
    return;
  }

  const entries = Object.entries(mix).sort((a, b) => b[1] - a[1]);
  container.innerHTML = entries.map(([cat, weight]) => {
    const pct = (weight * 100).toFixed(1);
    const isExp = weight < 0.08;
    return `
      <div class="portfolio-bar-row">
        <div class="portfolio-meta">
          <span style="text-transform: capitalize; font-weight: 500;">${escapeHtml(cat)}</span>
          <span style="color: var(--text-muted);">${pct}% ${isExp ? '(Experiment)' : ''}</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill ${isExp ? 'experiment' : ''}" style="width: ${pct}%;"></div>
        </div>
      </div>
    `;
  }).join("");
}

function renderCharacters(characters) {
  const container = document.getElementById("characters-container");
  if (!characters || characters.length === 0) {
    container.innerHTML = "<p>No characters created yet.</p>";
    return;
  }

  container.innerHTML = characters.map(c => {
    const isByte = c.name.toLowerCase().includes("byte");
    const avatar = isByte ? "🤖" : "🧭";
    const avatarClass = isByte ? "byte" : "sam";

    return `
      <div class="character-card">
        <div class="character-avatar ${avatarClass}">${avatar}</div>
        <div class="character-info">
          <h4>${escapeHtml(c.name)} <span style="font-size: 11px; color: var(--accent); margin-left: 8px;">${c.appearances || 0} Shorts</span></h4>
          <p>${escapeHtml(c.persona)}</p>
          <p style="font-style: italic; color: #94a3b8; margin-top: 2px;">"${escapeHtml(c.catchphrase || 'Channel Duo')}"</p>
        </div>
      </div>
    `;
  }).join("");
}

function renderCategoryTable(categories) {
  const tbody = document.getElementById("category-table-body");
  if (!categories || categories.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4">No category data recorded.</td></tr>`;
    return;
  }

  tbody.innerHTML = categories.map(c => `
    <tr>
      <td style="text-transform: capitalize; font-weight: 600;">${escapeHtml(c.category)}</td>
      <td><span class="badge ${c.score >= 80 ? 'badge-qc-passed' : 'badge-rendered'}">${c.score.toFixed(1)}</span></td>
      <td>${c.lifetime_videos || 0}</td>
      <td>${(c.avg_retention || 70).toFixed(0)}%</td>
    </tr>
  `).join("");
}

function renderLatestReview(review) {
  const container = document.getElementById("latest-review-container");
  if (!review) {
    container.innerHTML = `
      <div class="review-item">
        <strong>Initial State:</strong> The agent is currently accumulating viewer telemetry across all 17 categories.
        Click <em>"Run Daily Review Now"</em> to compute the first learning cycle.
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="review-item">
      <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 4px;">REVIEW DATE: ${escapeHtml(review.review_date)}</div>
      <strong class="text-success">What Worked:</strong>
      <p style="margin: 3px 0 8px;">${escapeHtml(review.successes)}</p>
      <strong class="text-warning">What Surprised Us:</strong>
      <p style="margin: 3px 0 8px;">${escapeHtml(review.what_surprised || review.failures)}</p>
      <strong class="text-accent">Strategy Tomorrow:</strong>
      <p style="margin: 3px 0 0;">${escapeHtml(review.strategy_changes || review.lessons)}</p>
    </div>
  `;
}

async function loadBlacklists() {
  try {
    const res = await fetch("/api/brain/blacklists");
    if (!res.ok) return;
    const list = await res.json();
    const container = document.getElementById("blacklists-container");

    if (!list || list.length === 0) {
      container.innerHTML = "<span style='font-size: 12px; color: var(--text-muted);'>No active blacklists. Add safety rules above.</span>";
      return;
    }

    container.innerHTML = list.map(b => `
      <span class="blacklist-pill">
        <strong>${escapeHtml(b.list_type)}:</strong> ${escapeHtml(b.value)}
      </span>
    `).join("");
  } catch (err) {
    console.error(err);
  }
}

// -------------------------------------------------------------
// Project Inspection & Interaction
// -------------------------------------------------------------

async function openProjectDetail(projectId) {
  activeProjectId = projectId;
  try {
    const res = await fetch(`/api/projects/${projectId}`);
    if (!res.ok) return;
    const data = await res.json();
    const p = data.project;

    document.getElementById("detail-title").textContent = p.title;
    const badge = document.getElementById("detail-state-badge");
    badge.textContent = p.state;
    badge.className = `badge badge-${p.state.toLowerCase().replace('_', '-')}`;

    // Video Player
    const player = document.getElementById("detail-video-player");
    if (data.stream_url) {
      player.src = data.stream_url;
      player.load();
    } else {
      player.removeAttribute("src");
    }

    // Script tab
    if (data.script) {
      document.getElementById("script-word-count").textContent = `Words: ${data.script.word_count}`;
      document.getElementById("script-duration").textContent = `Duration: ~${data.script.estimated_duration_sec}s`;
      document.getElementById("script-full-text").textContent = data.script.full_narration;

      const scenesEl = document.getElementById("scenes-container");
      scenesEl.innerHTML = data.script.scenes.map(s => `
        <div class="scene-item">
          <strong>Scene ${s.scene_index} (~${s.duration_est}s):</strong> ${escapeHtml(s.narration)}
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Visual: ${escapeHtml(s.visual_description)}</div>
        </div>
      `).join("");
    } else {
      document.getElementById("script-full-text").textContent = "Script generation in progress...";
      document.getElementById("scenes-container").innerHTML = "";
    }

    // Facts tab
    const claimsEl = document.getElementById("claims-container");
    if (data.claims && data.claims.length > 0) {
      claimsEl.innerHTML = data.claims.map(c => `
        <div class="claim-item">
          <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
            <strong class="text-${c.status === 'VERIFIED' ? 'success' : 'warning'}">${c.status}</strong>
            <span>Confidence: ${(c.confidence * 100).toFixed(0)}%</span>
          </div>
          <div>${escapeHtml(c.claim_text)}</div>
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Evidence: ${escapeHtml(c.evidence)}</div>
        </div>
      `).join("");
    } else {
      claimsEl.innerHTML = "<p>Fact check claims pending.</p>";
    }

    // Sources tab
    document.getElementById("sources-container").innerHTML = 
      `<pre style="white-space: pre-wrap; font-family: inherit;">${escapeHtml(data.sources_markdown || "No source report available.")}</pre>`;

    // QC tab
    if (data.qc) {
      document.getElementById("qc-score-display").textContent = `${data.qc.quality_score}/100`;
      const verdictEl = document.getElementById("qc-verdict-display");
      verdictEl.textContent = data.qc.passed ? "QC PASSED - READY TO PUBLISH" : "FLAGGED FOR REVIEW";
      verdictEl.className = data.qc.passed ? "qc-verdict text-success" : "qc-verdict text-warning";

      const issuesEl = document.getElementById("qc-issues-container");
      if (data.qc.issues.length > 0) {
        issuesEl.innerHTML = data.qc.issues.map(iss => `<li style="color: #ef4444; margin-left: 20px;">${escapeHtml(iss)}</li>`).join("");
      } else {
        issuesEl.innerHTML = "<li style=\"color: #10b981; margin-left: 20px;\">All technical, audio, caption, and factual checks passed.</li>";
      }
    }

    // Metadata tab
    if (data.metadata) {
      document.getElementById("meta-title-view").value = data.metadata.selected_title || "";
      document.getElementById("meta-desc-view").value = data.metadata.description || "";
      document.getElementById("meta-tags-view").value = (data.metadata.hashtags || []).join(" ");
    }

    document.getElementById("detail-modal").classList.remove("hidden");
  } catch (err) {
    console.error("Open project detail error:", err);
  }
}

async function loadJobs() {
  try {
    const res = await fetch("/api/jobs");
    if (!res.ok) return;
    const jobs = await res.json();
    const runningJobs = jobs.filter(j => j.status === "RUNNING" || j.status === "PENDING");
    document.getElementById("active-jobs-count").textContent = runningJobs.length;
  } catch (e) {}
}

function setupEventListeners() {
  // Modal toggle
  document.getElementById("btn-open-generate").onclick = () => {
    document.getElementById("generate-modal").classList.remove("hidden");
  };
  document.getElementById("modal-close").onclick = () => {
    document.getElementById("generate-modal").classList.add("hidden");
  };
  document.getElementById("btn-cancel-gen").onclick = () => {
    document.getElementById("generate-modal").classList.add("hidden");
  };
  document.getElementById("detail-close").onclick = () => {
    document.getElementById("detail-modal").classList.add("hidden");
    const player = document.getElementById("detail-video-player");
    player.pause();
  };

  // Trigger generation
  document.getElementById("btn-start-gen").onclick = async () => {
    const topic = document.getElementById("gen-topic").value.trim();
    const category = document.getElementById("gen-category").value;
    const format = document.getElementById("gen-format").value;
    const character = document.getElementById("gen-character").value;
    const autoPublish = document.getElementById("gen-autopublish").checked;

    document.getElementById("generate-modal").classList.add("hidden");

    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: topic || null,
          category: category === "autonomous" ? null : category,
          character: character === "auto" ? null : character,
          format: format === "auto" ? null : format,
          auto_publish: autoPublish,
        }),
      });
      if (res.ok) {
        loadProjects();
        loadJobs();
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Filter tabs
  document.getElementById("filter-all")?.addEventListener("click", () => setFilter("all"));
  document.getElementById("filter-produced")?.addEventListener("click", () => setFilter("produced"));
  document.getElementById("filter-failed")?.addEventListener("click", () => setFilter("failed"));

  // Refresh
  document.getElementById("btn-refresh").onclick = loadProjects;
  document.getElementById("btn-refresh-brain")?.addEventListener("click", loadBrainData);

  // Run Daily Review button
  document.getElementById("btn-run-review")?.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/brain/reviews/run", { method: "POST" });
      if (res.ok) {
        const rev = await res.json();
        alert(`Daily Review Run Complete! Recorded insights for ${rev.review_date}.`);
        loadBrainData();
      }
    } catch (e) {
      alert("Error triggering daily review: " + e);
    }
  });

  // Blacklist addition
  document.getElementById("btn-add-blacklist")?.addEventListener("click", async () => {
    const type = document.getElementById("bl-type").value;
    const val = document.getElementById("bl-value").value.trim();
    const reason = document.getElementById("bl-reason").value.trim();

    if (!val) {
      alert("Please enter a value to blacklist.");
      return;
    }

    try {
      const res = await fetch("/api/brain/blacklists", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          list_type: type,
          value: val,
          reason: reason,
        }),
      });
      if (res.ok) {
        document.getElementById("bl-value").value = "";
        document.getElementById("bl-reason").value = "";
        loadBlacklists();
      }
    } catch (e) {
      console.error(e);
    }
  });

  // Detail Modal Actions
  document.getElementById("btn-action-approve").onclick = async () => {
    if (!activeProjectId) return;
    await fetch(`/api/projects/${activeProjectId}/approve`, { method: "POST" });
    openProjectDetail(activeProjectId);
    loadProjects();
  };

  document.getElementById("btn-action-publish").onclick = async () => {
    if (!activeProjectId) return;
    const res = await fetch(`/api/projects/${activeProjectId}/publish`, { method: "POST" });
    const data = await res.json();
    alert(data.message || "Publish request sent!");
    openProjectDetail(activeProjectId);
    loadProjects();
  };

  document.getElementById("btn-action-delete").onclick = async () => {
    if (!activeProjectId || !confirm("Delete this project?")) return;
    await fetch(`/api/projects/${activeProjectId}`, { method: "DELETE" });
    document.getElementById("detail-modal").classList.add("hidden");
    loadProjects();
  };

  // Tabs navigation
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      const tabId = btn.getAttribute("data-tab");
      document.getElementById(tabId).classList.add("active");
    };
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
