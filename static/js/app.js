/**
 * Free Fire BattleX Points Table Studio
 * High-performance client-side interactive logic & poster exporter
 */

// Application State
const state = {
  standings: [],
  highlights: null,
  currentTheme: "inferno",
  tournamentTitle: "FREE FIRE BATTLEGROUNDS CHAMPIONSHIP",
  matchInfo: "GRAND FINALS • MATCH 01 • BERMUDA",
  footerNote: "OFFICIAL RESULTS • VERIFIED BY BATTLEX ESPORTS",
  showPlayerTags: true,
  aspectRatio: "16:9"
};

// DOM Elements
const dom = {
  dropzone: document.getElementById("dropzone"),
  fileInput: document.getElementById("csvFileInput"),
  btnSample: document.getElementById("btnLoadSample"),
  btnDownloadHd: document.getElementById("btnDownloadHd"),
  btnServerExport: document.getElementById("btnServerExport"),
  btnCopyImage: document.getElementById("btnCopyImage"),
  
  // Inputs
  inputTitle: document.getElementById("inputTitle"),
  inputMatch: document.getElementById("inputMatch"),
  inputFooter: document.getElementById("inputFooter"),
  togglePlayerTags: document.getElementById("togglePlayerTags"),
  
  // Poster Elements
  posterNode: document.getElementById("esportsPoster"),
  posterTitle: document.getElementById("posterTitle"),
  posterSubtitle: document.getElementById("posterSubtitle"),
  posterFooterNote: document.getElementById("posterFooterNote"),
  posterTableBody: document.getElementById("tableBody"),
  emptyState: document.getElementById("emptyState"),
  tableContainer: document.getElementById("tableContainer"),
  
  // Highlight Badges
  statWinnerTeam: document.getElementById("statWinnerTeam"),
  statWinnerPoints: document.getElementById("statWinnerPoints"),
  statMvpTeam: document.getElementById("statMvpTeam"),
  statMvpKills: document.getElementById("statMvpKills"),
  statTotalKills: document.getElementById("statTotalKills"),
  statTotalTeams: document.getElementById("statTotalTeams"),
  
  // Toast & Loader
  toast: document.getElementById("toast"),
  toastMessage: document.getElementById("toastMessage"),
  loadingOverlay: document.getElementById("loadingOverlay"),
  loadingText: document.getElementById("loadingText")
};

// ==========================================================================
// 1. FLOATING EMBER CANVAS PARTICLES (Free Fire Lobby Effect)
// ==========================================================================
function initEmberCanvas() {
  const canvas = document.getElementById("ember-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  let width, height;
  let particles = [];

  function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  }
  window.addEventListener("resize", resize);
  resize();

  const themeColors = {
    inferno: ["rgba(255, 106, 0, ", "rgba(255, 183, 3, ", "rgba(255, 42, 0, "],
    chrono: ["rgba(0, 242, 254, ", "rgba(157, 0, 255, ", "rgba(0, 119, 254, "],
    crimson: ["rgba(255, 0, 85, ", "rgba(255, 85, 0, ", "rgba(255, 20, 100, "],
    gold: ["rgba(255, 215, 0, ", "rgba(255, 153, 0, ", "rgba(255, 230, 120, "]
  };

  class Ember {
    constructor() {
      this.reset();
    }
    reset() {
      this.x = Math.random() * width;
      this.y = height + Math.random() * 50;
      this.size = Math.random() * 2.8 + 0.8;
      this.speedY = Math.random() * 1.5 + 0.6;
      this.speedX = (Math.random() - 0.5) * 0.8;
      this.opacity = Math.random() * 0.7 + 0.2;
      this.fadeSpeed = Math.random() * 0.006 + 0.002;
      this.colorBase = themeColors[state.currentTheme] || themeColors.inferno;
      this.color = this.colorBase[Math.floor(Math.random() * this.colorBase.length)];
    }
    update() {
      this.y -= this.speedY;
      this.x += this.speedX + Math.sin(this.y * 0.02) * 0.3;
      this.opacity -= this.fadeSpeed;
      if (this.y < -20 || this.opacity <= 0) {
        this.reset();
      }
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fillStyle = this.color + this.opacity + ")";
      ctx.shadowBlur = this.size * 4;
      ctx.shadowColor = this.color + "0.8)";
      ctx.fill();
    }
  }

  const particleCount = Math.min(45, Math.floor(window.innerWidth / 35));
  for (let i = 0; i < particleCount; i++) {
    particles.push(new Ember());
  }

  function loop() {
    ctx.clearRect(0, 0, width, height);
    for (let p of particles) {
      p.update();
      p.draw();
    }
    requestAnimationFrame(loop);
  }
  loop();
}

// ==========================================================================
// 2. CSV PARSING & DATA INGESTION
// ==========================================================================
async function handleFileUpload(file) {
  if (!file) return;
  showLoading("Parsing CSV Tournament Data...");

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/api/upload-csv", {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || "Failed to parse CSV file");
    }

    state.standings = data.standings;
    state.highlights = data.highlights;
    renderLeaderboard();
    showToast(`Loaded ${data.count} squads from ${file.name}!`);
  } catch (err) {
    console.error(err);
    showToast("Error: " + err.message, true);
  } finally {
    hideLoading();
  }
}

async function loadSampleData() {
  showLoading("Loading Free Fire Sample Standings...");
  try {
    const res = await fetch("/api/sample-csv");
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || "Failed to load sample CSV");
    }

    state.standings = data.standings;
    state.highlights = data.highlights;
    renderLeaderboard();
    showToast("Loaded official Free Fire sample points table!");
  } catch (err) {
    console.error(err);
    showToast("Error: " + err.message, true);
  } finally {
    hideLoading();
  }
}

// ==========================================================================
// 3. TABLE RENDERING & UI SYNC
// ==========================================================================
function renderLeaderboard() {
  if (!state.standings || state.standings.length === 0) {
    dom.emptyState.style.display = "flex";
    dom.tableContainer.style.display = "none";
    return;
  }

  dom.emptyState.style.display = "none";
  dom.tableContainer.style.display = "block";

  // Render Stats
  const hl = state.highlights;
  if (hl) {
    dom.statWinnerTeam.textContent = hl.booyah ? (hl.booyah.team.split(",")[0] || "Squad #1") : "-";
    dom.statWinnerPoints.textContent = hl.booyah ? `${hl.booyah.points} PTS` : "-";
    
    dom.statMvpTeam.textContent = hl.top_fragger ? (hl.top_fragger.team.split(",")[0] || "Squad") : "-";
    dom.statMvpKills.textContent = hl.top_fragger ? `${hl.top_fragger.kills} KILLS` : "-";
    
    dom.statTotalKills.textContent = hl.total_kills || "0";
    dom.statTotalTeams.textContent = hl.total_teams || state.standings.length;
  }

  // Render Rows
  dom.posterTableBody.innerHTML = "";
  state.standings.forEach((row, index) => {
    const tr = document.createElement("tr");
    const rank = row.rank || index + 1;

    let rankClass = "";
    if (rank === 1) rankClass = "row-rank-1";
    else if (rank === 2) rankClass = "row-rank-2";
    else if (rank === 3) rankClass = "row-rank-3";
    if (rankClass) tr.className = rankClass;

    // Squad and Player Tags
    const players = row.players || [];
    let playerHtml = "";
    if (state.showPlayerTags && players.length > 0) {
      playerHtml = `
        <div class="player-tags">
          ${players.map(p => `<span class="player-tag ${rank === 1 ? 'highlight' : ''}">${escapeHtml(p)}</span>`).join("")}
        </div>
      `;
    }

    const teamDisplayName = players.length > 1 ? `SQUAD #${rank}` : (row.team_name || row.team_raw);

    tr.innerHTML = `
      <td class="col-rank">
        <div class="rank-badge-wrap">
          <div class="rank-badge">${rank}</div>
        </div>
      </td>
      <td class="col-team">
        <div class="team-cell">
          <div class="team-name-title">
            <span>${escapeHtml(teamDisplayName)}</span>
            ${rank === 1 ? '<span class="booyah-tag">👑 BOOYAH!</span>' : ''}
          </div>
          ${playerHtml}
        </div>
      </td>
      <td class="col-stat stat-num kills">${row.kills}</td>
      <td class="col-stat stat-num placement">${row.placement}</td>
      <td class="col-total">
        <div class="total-pill-wrap">
          <div class="total-pill">${row.total_points}</div>
        </div>
      </td>
    `;
    dom.posterTableBody.appendChild(tr);
  });
}

function escapeHtml(text) {
  if (!text) return "";
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ==========================================================================
// 4. POSTER EXPORT (High-Res Client Canvas & Server Pillow)
// ==========================================================================
async function downloadPosterImage() {
  if (!state.standings || state.standings.length === 0) {
    showToast("Please upload a CSV or load sample data first!", true);
    return;
  }

  showLoading("Rendering 4K Esports Poster...");

  try {
    const posterEl = dom.posterNode;
    
    // Check if html2canvas is ready
    if (typeof html2canvas === "undefined") {
      throw new Error("html2canvas library is not loaded");
    }

    // High DPI scaling (scale: 2 for super crisp typography and borders)
    const canvas = await html2canvas(posterEl, {
      scale: 2,
      useCORS: true,
      allowTaint: true,
      backgroundColor: "#07090e",
      logging: false,
      scrollX: 0,
      scrollY: -window.scrollY
    });

    // Create download link
    const imageUri = canvas.toDataURL("image/png");
    const link = document.createElement("a");
    const cleanName = (state.tournamentTitle || "free_fire")
      .toLowerCase()
      .replace(/[^a-z0-9]/g, "_")
      .replace(/_+/g, "_");
      
    link.download = `${cleanName}_points_table.png`;
    link.href = imageUri;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showToast("High-Res Poster downloaded successfully! 🎮");
  } catch (err) {
    console.error("Client canvas render error, falling back to server render:", err);
    // Automatic fallback to backend Pillow generator!
    await exportViaServer();
  } finally {
    hideLoading();
  }
}

async function exportViaServer() {
  if (!state.standings || state.standings.length === 0) {
    showToast("Please upload a CSV first!", true);
    return;
  }

  showLoading("Generating Server-side Esports PNG...");

  try {
    const payload = {
      standings: state.standings,
      tournament_title: state.tournamentTitle,
      match_info: state.matchInfo,
      theme: state.currentTheme,
      width: 1920,
      height: 1080
    };

    const res = await fetch("/api/export-image", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error("Server image generation failed");

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "free_fire_points_table_hd.png";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    showToast("Downloaded Server HD Poster! 🔥");
  } catch (err) {
    console.error(err);
    showToast("Export error: " + err.message, true);
  } finally {
    hideLoading();
  }
}

async function copyImageToClipboard() {
  if (!state.standings || state.standings.length === 0) {
    showToast("Please load data before copying!", true);
    return;
  }

  showLoading("Copying poster to clipboard...");

  try {
    const canvas = await html2canvas(dom.posterNode, {
      scale: 1.5,
      useCORS: true,
      backgroundColor: "#07090e",
      logging: false
    });

    canvas.toBlob(async (blob) => {
      if (!blob) throw new Error("Could not create image blob");
      try {
        await navigator.clipboard.write([
          new ClipboardItem({ "image/png": blob })
        ]);
        showToast("Poster copied! Paste into WhatsApp or Discord (Ctrl+V)");
      } catch (clipErr) {
        // If Clipboard API is restricted by browser permissions, fallback to download
        console.warn("Direct clipboard write failed, downloading instead", clipErr);
        downloadPosterImage();
      } finally {
        hideLoading();
      }
    }, "image/png");
  } catch (err) {
    console.error(err);
    hideLoading();
    showToast("Could not copy directly. Downloading instead...");
    downloadPosterImage();
  }
}

// ==========================================================================
// 5. TOAST & NOTIFICATIONS
// ==========================================================================
let toastTimer = null;
function showToast(msg, isError = false) {
  if (toastTimer) clearTimeout(toastTimer);
  dom.toastMessage.textContent = msg;
  if (isError) {
    dom.toast.style.borderColor = "#ff3300";
    dom.toast.style.boxShadow = "0 10px 30px rgba(0,0,0,0.6), 0 0 20px rgba(255, 50, 0, 0.4)";
  } else {
    dom.toast.style.borderColor = "var(--theme-primary)";
    dom.toast.style.boxShadow = "0 10px 30px rgba(0,0,0,0.6), 0 0 20px var(--theme-glow)";
  }
  dom.toast.classList.add("show");
  toastTimer = setTimeout(() => {
    dom.toast.classList.remove("show");
  }, 3500);
}

function showLoading(text = "Processing...") {
  dom.loadingText.textContent = text;
  dom.loadingOverlay.classList.add("active");
}

function hideLoading() {
  dom.loadingOverlay.classList.remove("active");
}

// ==========================================================================
// 6. EVENT LISTENERS SETUP
// ==========================================================================
function setupEventListeners() {
  // Drag and Drop
  dom.dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dom.dropzone.classList.add("dragover");
  });

  dom.dropzone.addEventListener("dragleave", () => {
    dom.dropzone.classList.remove("dragover");
  });

  dom.dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dom.dropzone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  dom.fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files[0]);
    }
  });

  dom.btnSample.addEventListener("click", loadSampleData);

  // Live Text Inputs
  dom.inputTitle.addEventListener("input", (e) => {
    state.tournamentTitle = e.target.value.trim() || "FREE FIRE CHAMPIONSHIP";
    dom.posterTitle.textContent = state.tournamentTitle;
  });

  dom.inputMatch.addEventListener("input", (e) => {
    state.matchInfo = e.target.value.trim() || "MATCH STANDINGS";
    dom.posterSubtitle.textContent = state.matchInfo;
  });

  dom.inputFooter.addEventListener("input", (e) => {
    state.footerNote = e.target.value.trim() || "BATTLEX ESPORTS";
    dom.posterFooterNote.textContent = state.footerNote;
  });

  // Toggle Player Tags
  dom.togglePlayerTags.addEventListener("change", (e) => {
    state.showPlayerTags = e.target.checked;
    renderLeaderboard();
  });

  // Theme Picker Buttons
  document.querySelectorAll(".theme-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      document.querySelectorAll(".theme-pill").forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      const theme = pill.getAttribute("data-theme");
      state.currentTheme = theme;
      document.body.setAttribute("data-theme", theme);
    });
  });

  // Downloads & Actions
  dom.btnDownloadHd.addEventListener("click", downloadPosterImage);
  dom.btnServerExport.addEventListener("click", exportViaServer);
  dom.btnCopyImage.addEventListener("click", copyImageToClipboard);
}

// Initializer
document.addEventListener("DOMContentLoaded", () => {
  initEmberCanvas();
  setupEventListeners();
  // Auto-load sample data on startup for immediate breathtaking visual impression!
  loadSampleData();
});
