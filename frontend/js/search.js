/* ============================================
   AI NAVIGATOR — Backend API Integration
   ============================================ */

const API_BASE_URL = typeof API_ROOT !== "undefined" ? API_ROOT : "/api";

/**
 * Helper to get authorization headers if a user is logged in
 */
function getAuthHeaders() {
    const token = localStorage.getItem("token");
    return token ? { "Authorization": `Bearer ${token}` } : {};
}

// ============================================
// CORE API CALLS
// ============================================

/**
 * Sends a natural language query to the backend recommendation engine
 */
async function apiSearch(query) {
    try {
        const response = await fetch(`${API_BASE_URL}/search`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...getAuthHeaders()
            },
            body: JSON.stringify({ query: query })
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Search failed");
        }

        return await response.json();
    } catch (error) {
        console.error("API Search Error:", error);
        throw error;
    }
}

/**
 * Requests side-by-side comparison metadata from the backend
 */
async function apiCompare(toolIds) {
    try {
        const response = await fetch(`${API_BASE_URL}/compare`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...getAuthHeaders()
            },
            body: JSON.stringify({ tool_ids: toolIds })
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Comparison failed");
        }

        return await response.json();
    } catch (error) {
        console.error("API Compare Error:", error);
        throw error;
    }
}

// ============================================
// RENDERING FUNCTIONS
// ============================================

/**
 * Configure buttons depending on API availability
 */
function setActionButtons(bestMatch) {
    const useBtn = document.getElementById("btn-use-ai");
    const visitBtn = document.getElementById("btn-visit-official");

    if (useBtn) {
        if (bestMatch.tool.api_available === "yes") {
            useBtn.textContent = "Interact Inside Platform";
            useBtn.className = "btn btn-primary btn-lg";
            useBtn.onclick = (e) => {
                if (e) e.preventDefault();
                sessionStorage.setItem("active_chat_tool", JSON.stringify(bestMatch.tool));
                navigateTo("chat");
            };
        } else {
            useBtn.textContent = "Open Official Website";
            useBtn.className = "btn btn-outline btn-lg";
            useBtn.onclick = (e) => {
                if (e) e.preventDefault();
                window.open(bestMatch.tool.website, "_blank", "noopener,noreferrer");
            };
        }
    }

    if (visitBtn) {
        visitBtn.onclick = (e) => {
            if (e) e.preventDefault();
            window.open(bestMatch.tool.website, "_blank", "noopener,noreferrer");
        };
    }
}

/**
 * Render the dashboard page with backend results
 */
function renderDashboard(query, results) {
    const { intent, best_match, alternatives } = results;
    const tool = best_match.tool;

    // Set query snapshot
    const queryText = document.getElementById("dash-query-text");
    if (queryText) queryText.textContent = `"${query}"`;

    // Render parsed intent values
    setText("intent-category", formatLabel(intent.category));
    setText("intent-purpose", formatLabel(intent.purpose));
    setText("intent-skill", formatLabel(intent.skill_level));
    setText("intent-budget", formatLabel(intent.budget));
    setText("intent-output", formatLabel(intent.output_type));
    setText("intent-priority", formatLabel(intent.priority));

    // Render best match details
    setText("best-match-name", tool.name);
    setText("best-match-tagline", tool.description);
    setText("best-match-score", best_match.overall_score + "%");
    setText("best-match-category-tag", formatLabel(tool.category));

    const pricingTag = document.getElementById("best-match-pricing-tag");
    if (pricingTag) {
        pricingTag.textContent = formatLabel(tool.pricing);
        pricingTag.className = tool.pricing === "free" || tool.pricing === "freemium" ? "tag tag-free" : "tag tag-paid";
    }

    // Match score bar animation
    const bar = document.getElementById("best-match-bar");
    if (bar) {
        bar.style.width = "0%";
        setTimeout(() => { bar.style.width = best_match.overall_score + "%"; }, 100);
    }

    // Score breakdown rows
    setText("score-task", best_match.scores.task_score + "%");
    setText("score-capability", best_match.scores.capability_score + "%");
    setText("score-skill", best_match.scores.skill_score + "%");
    setText("score-budget", best_match.scores.budget_score + "%");
    setText("score-ease", best_match.scores.ease_score + "%");

    // Score explanation lists
    const reasonsContainer = document.getElementById("best-match-reasons");
    if (reasonsContainer) {
        reasonsContainer.innerHTML = best_match.reasons.map(r =>
            `<div class="reason-item positive">${r}</div>`
        ).join("");
    }

    const limitationsContainer = document.getElementById("best-match-limitations");
    if (limitationsContainer) {
        limitationsContainer.innerHTML = best_match.limitations.map(l =>
            `<div class="reason-item warning">${l}</div>`
        ).join("");
    }

    // Set action buttons state
    setActionButtons(best_match);

    // Alternatives Grid
    const altContainer = document.getElementById("dash-alternatives");
    if (altContainer) {
        altContainer.innerHTML = alternatives.map((alt, i) => `
            <div class="alt-card" data-tool-id="${alt.tool.id}">
                <div class="alt-card-rank">Alternative ${i + 1}</div>
                <div class="alt-card-name">${alt.tool.name}</div>
                <div class="alt-card-score">${alt.overall_score}% match</div>
                <p class="text-muted mt-sm" style="font-size: var(--font-size-xs);">${alt.tool.description.substring(0, 80)}...</p>
            </div>
        `).join("");

        // Attach click listeners to alternative cards
        altContainer.querySelectorAll(".alt-card").forEach(card => {
            card.addEventListener("click", () => {
                const altId = parseInt(card.dataset.toolId);
                const selectedAlt = alternatives.find(a => a.tool.id === altId);
                if (selectedAlt) {
                    const modifiedResults = {
                        intent: intent,
                        best_match: selectedAlt,
                        alternatives: [best_match, ...alternatives.filter(a => a.tool.id !== altId)]
                    };
                    renderDashboard(query, modifiedResults);
                }
            });
        });
    }

    // Keep state available globally for compare page transitions
    window.currentResults = results;
}

/**
 * Render comparison data dynamically
 */
function renderComparison(tools, summaryText) {
    const tableHead = document.getElementById("compare-table-head");
    const tableBody = document.getElementById("compare-table-body");
    const detailCards = document.getElementById("compare-detail-cards");
    const summary = document.getElementById("compare-summary");
    const results = document.getElementById("compare-results");

    if (!tableHead || !tableBody) return;

    if (results) results.classList.remove("hidden");

    // Table Headers
    tableHead.innerHTML = "<th>Feature</th>";
    tools.forEach(t => {
        tableHead.innerHTML += `<th>${t.name}</th>`;
    });

    // Comparison Rows
    const features = [
        { label: "Category", key: "category", format: formatLabel },
        { label: "Pricing Model", key: "pricing", format: formatLabel },
        { label: "Skill Level", key: "skill_level", format: formatLabel },
        { label: "API Available", key: "api_available", format: formatApiCheck },
        { label: "Platform", key: "platform", format: v => v },
        { label: "Quality Rating", key: "quality_rating", format: formatStars },
        { label: "Ease of Use", key: "ease_rating", format: formatStars },
        { label: "Processing Speed", key: "speed_rating", format: formatStars }
    ];

    tableBody.innerHTML = features.map(f => {
        let row = `<td><strong>${f.label}</strong></td>`;
        tools.forEach(t => {
            row += `<td>${f.format(t[f.key])}</td>`;
        });
        return `<tr>${row}</tr>`;
    }).join("");

    // Details Cards
    if (detailCards) {
        detailCards.innerHTML = tools.map(t => `
            <div class="card">
                <h3 class="card-title">${t.name}</h3>
                <p class="card-subtitle">${t.description}</p>
                <h4 class="card-section-title">Strengths</h4>
                <div class="reason-list">
                    ${t.strengths.map(s => `<div class="reason-item positive">${formatLabel(s)}</div>`).join("")}
                </div>
                <h4 class="card-section-title">Weaknesses</h4>
                <div class="reason-list">
                    ${t.weaknesses.map(w => `<div class="reason-item warning">${formatLabel(w)}</div>`).join("")}
                </div>
                <div class="card-actions">
                    <a href="${t.website}" target="_blank" rel="noopener noreferrer" class="btn btn-outline btn-sm">Visit Website</a>
                </div>
            </div>
        `).join("");
    }

    if (summary) {
        summary.innerHTML = (summaryText || "").replace(/\n/g, "<br>");
    }

    const resetBtn = document.getElementById("btn-reset-compare");
    if (resetBtn) {
        resetBtn.onclick = () => {
            if (results) results.classList.add("hidden");
            window.scrollTo({ top: 0, behavior: "smooth" });
        };
    }

    const backBtn = document.getElementById("btn-back-dashboard");
    if (backBtn) {
        backBtn.onclick = () => {
            if (window.currentResults) {
                navigateTo("dashboard");
            } else {
                navigateTo("home");
            }
        };
    }
}

// ============================================
// EVENT HANDLERS
// ============================================

/**
 * Handle Search Input Submission (Race-Free routing)
 */
async function handleSearch(event) {
    // Prevent browser's default form submission behavior
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    const input = document.getElementById("search-input");
    if (!input) return;

    const query = input.value.trim();
    if (!query) {
        input.focus();
        return;
    }

    // Save the query in temporary session storage
    sessionStorage.setItem("pending_search_query", query);

    // Let the central router handle navigation cleanly
    navigateTo("dashboard");
}

// ============================================
// FORMATTING HELPERS
// ============================================

function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function formatLabel(str) {
    if (!str) return "--";
    return str
        .replace(/-/g, " ")
        .replace(/\b\w/g, c => c.toUpperCase());
}

function formatStars(rating) {
    const full = Math.round((rating || 0) / 2);
    const empty = 5 - full;
    return `<span class="star-rating">${"\u2605".repeat(full)}${"\u2606".repeat(empty)}</span>`;
}

function formatApiCheck(value) {
    if (value === "yes") return '<span class="check-yes">Yes</span>';
    if (value === "no") return '<span class="check-no">No</span>';
    return '<span class="check-limited">Limited</span>';
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener("DOMContentLoaded", () => {
    const searchBtn = document.getElementById("search-btn");
    if (searchBtn) {
        searchBtn.addEventListener("click", (e) => {
            e.preventDefault();
            handleSearch(e);
        });
    }

    const searchInput = document.getElementById("search-input");
    if (searchInput) {
        searchInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                e.stopPropagation();
                handleSearch(e);
            }
        });
    }

    document.querySelectorAll(".prompt-chip").forEach(chip => {
        chip.addEventListener("click", (e) => {
            e.preventDefault();
            if (searchInput) {
                searchInput.value = chip.dataset.prompt;
                handleSearch(e);
            }
        });
    });
});

/**
 * Handle populate logic for comparison cards
 */
async function populateCompareOptions() {
    const container = document.getElementById("compare-tool-options");
    const countLabel = document.getElementById("compare-count-label");
    const runBtn = document.getElementById("btn-run-compare");
    
    if (!container) return;

    let toolCards = [];
    if (window.currentResults && window.currentResults.best_match) {
        const all = [
            window.currentResults.best_match,
            ...window.currentResults.alternatives
        ];
        toolCards = all.map(item => ({
            id: item.tool.id,
            name: item.tool.name,
            sub: `${item.overall_score}% match`
        }));
    } else {
        container.innerHTML = '<div class="spinner"></div>';
        try {
            const res = await fetch(`${API_BASE_URL}/tools`);
            if (res.ok) {
                const tools = await res.json();
                toolCards = tools.map(t => ({
                    id: t.id,
                    name: t.name,
                    sub: `${formatLabel(t.category)} • ${formatLabel(t.pricing)}`
                }));
            }
        } catch (e) {
            console.error("Error loading tools for comparison:", e);
        }
    }

    if (!toolCards.length) {
        container.innerHTML = `
            <div class="empty-state">
                <h3>No tools available for comparison</h3>
                <p>Run a search first or make sure active AI tools are registered in the database.</p>
            </div>
        `;
        return;
    }

    let selectedIds = new Set();

    container.innerHTML = toolCards.map(item => `
        <div class="compare-tool-option" data-tool-id="${item.id}">
            <h4>${item.name}</h4>
            <p>${item.sub}</p>
        </div>
    `).join("");

    container.querySelectorAll(".compare-tool-option").forEach(option => {
        option.addEventListener("click", () => {
            const id = parseInt(option.dataset.toolId);
            if (selectedIds.has(id)) {
                selectedIds.delete(id);
                option.classList.remove("selected");
            } else if (selectedIds.size < 4) {
                selectedIds.add(id);
                option.classList.add("selected");
            }
            if (countLabel) countLabel.textContent = `${selectedIds.size} of 4 selected`;
        });
    });

    if (runBtn) {
        const newRunBtn = runBtn.cloneNode(true);
        runBtn.parentNode.replaceChild(newRunBtn, runBtn);
        
        newRunBtn.addEventListener("click", async () => {
            if (selectedIds.size < 2) {
                alert("Please select at least 2 tools to compare.");
                return;
            }
            
            try {
                const comparisonData = await apiCompare(Array.from(selectedIds));
                renderComparison(comparisonData.tools, comparisonData.summary);
            } catch (err) {
                alert("Failed to fetch comparison data: " + err.message);
            }
        });
    }
}