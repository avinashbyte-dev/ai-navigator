/* ============================================
   AI NAVIGATOR — Main Application & System Router
   ============================================ */

const API_ROOT = "http://127.0.0.1:8000/api";

// Available page fragments
const PAGES = {
    home: null,
    dashboard: "pages/dashboard.html",
    compare: "pages/compare.html",
    chat: "pages/chat.html",
    history: "pages/history.html",
    login: "pages/login.html",
    signup: "pages/signup.html",
    admin: "pages/admin.html"
};

// Global User State
let currentUser = null;
let chatMessagesHistory = [];
let editingToolId = null;
let allAdminTools = [];

// ============================================
// ROUTING & PAGE LOADER
// ============================================

async function navigateTo(pageName) {
    if (!PAGES.hasOwnProperty(pageName)) {
        console.warn(`Unknown page route: ${pageName}`);
        return;
    }

    if (window.location.hash !== `#${pageName}`) {
        history.pushState({ page: pageName }, '', `#${pageName}`);
    }

    updateActiveNavLink(pageName);
    closeMobileMenu();

    const heroSection = document.getElementById("hero");
    const pageContent = document.getElementById("page-content");

    if (pageName === "home") {
        if (heroSection) heroSection.classList.remove("hidden");
        if (pageContent) {
            pageContent.classList.add("hidden");
            pageContent.innerHTML = "";
        }
        window.scrollTo({ top: 0, behavior: "smooth" });
        return;
    }

    if (heroSection) heroSection.classList.add("hidden");
    if (pageContent) {
        pageContent.classList.remove("hidden");
        pageContent.innerHTML = '<div class="spinner"></div>';
    }

    try {
        const response = await fetch(PAGES[pageName]);
        if (!response.ok) throw new Error(`HTTP ${response.status}: Failed to load fragment`);
        
        const html = await response.text();
        if (pageContent) {
            pageContent.innerHTML = html;
            window.scrollTo({ top: 0, behavior: "smooth" });
        }

        // Initialize page-specific logic
        initPageLogic(pageName);
    } catch (err) {
        if (pageContent) {
            pageContent.innerHTML = `
                <div class="empty-state">
                    <h3>Page Loading Failed</h3>
                    <p class="text-danger">${err.message}</p>
                    <button class="btn btn-primary mt-md" onclick="navigateTo('home')">Return Home</button>
                </div>
            `;
        }
    }
}

function updateActiveNavLink(pageName) {
    document.querySelectorAll(".nav-link").forEach(link => {
        if (link.dataset.page === pageName) {
            link.classList.add("active");
        } else {
            link.classList.remove("active");
        }
    });
}

function initPageLogic(pageName) {
    if (pageName === "dashboard") initDashboardPage();
    if (pageName === "login") initLoginPage();
    if (pageName === "signup") initSignupPage();
    if (pageName === "chat") initChatPage();
    if (pageName === "history") initHistoryPage();
    if (pageName === "admin") initAdminPage();
    if (pageName === "compare") {
        if (typeof populateCompareOptions === "function") populateCompareOptions();
    }
}

/**
 * Handles live recommendation fetches when navigating to the dashboard
 */
async function initDashboardPage() {
    const query = sessionStorage.getItem("pending_search_query");
    if (!query) {
        // No search was executed (user just clicked "Dashboard" link directly)
        const queryText = document.getElementById("dash-query-text");
        if (queryText) {
            queryText.textContent = "Please enter a search query on the Home page to generate recommendations.";
        }
        return;
    }

    // Clear the pending query so it doesn't run repeatedly
    sessionStorage.removeItem("pending_search_query");

    try {
        const results = await apiSearch(query);
        renderDashboard(query, results);
    } catch (err) {
        const pageContent = document.getElementById("page-content");
        if (pageContent) {
            pageContent.innerHTML = `
                <div class="empty-state">
                    <h3>Search Recommendation Failed</h3>
                    <p class="text-danger">${err.message}</p>
                    <button class="btn btn-primary mt-md" onclick="navigateTo('home')">Return Home</button>
                </div>
            `;
        }
    }
}

// ============================================
// AUTHENTICATION (Login, Signup, User Session)
// ============================================

async function checkAuthSession() {
    const token = localStorage.getItem("token");
    if (!token) {
        updateAuthUI(null);
        return;
    }

    try {
        const res = await fetch(`${API_ROOT}/auth/me`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (res.ok) {
            currentUser = await res.json();
            updateAuthUI(currentUser);
        } else {
            logoutUser();
        }
    } catch (e) {
        console.error("Auth check failed:", e);
        updateAuthUI(null);
    }
}

function updateAuthUI(user) {
    const navActions = document.querySelector(".nav-actions");
    if (!navActions) return;

    if (user) {
        navActions.innerHTML = `
            <span class="text-secondary" style="font-size: var(--font-size-sm); font-weight: 600;">
                ${user.name} ${user.is_admin ? '<span class="tag">Admin</span>' : ''}
            </span>
            ${user.is_admin ? '<button class="btn btn-outline btn-sm" onclick="navigateTo(\'admin\')">Admin Panel</button>' : ''}
            <button class="btn btn-ghost btn-sm" onclick="logoutUser()">Log Out</button>
        `;
    } else {
        navActions.innerHTML = `
            <a href="#login" data-page="login" class="btn btn-ghost">Log In</a>
            <a href="#signup" data-page="signup" class="btn btn-primary">Sign Up</a>
        `;
        attachNavDelegation();
    }
}

function logoutUser() {
    localStorage.removeItem("token");
    currentUser = null;
    updateAuthUI(null);
    navigateTo("home");
}

function initLoginPage() {
    const form = document.getElementById("login-form");
    const guestBtn = document.getElementById("login-guest");

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const email = document.getElementById("login-email").value.trim();
            const password = document.getElementById("login-password").value;
            const submitBtn = document.getElementById("login-submit");

            if (submitBtn) submitBtn.textContent = "Authenticating...";

            try {
                const res = await fetch(`${API_ROOT}/auth/login`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password })
                });

                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || "Login failed");

                localStorage.setItem("token", data.access_token);
                currentUser = data.user;
                updateAuthUI(currentUser);
                navigateTo("home");
            } catch (err) {
                alert(err.message);
            } finally {
                if (submitBtn) submitBtn.textContent = "Log In";
            }
        });
    }

    if (guestBtn) {
        guestBtn.addEventListener("click", () => navigateTo("home"));
    }
}

function initSignupPage() {
    const form = document.getElementById("signup-form");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = document.getElementById("signup-name").value.trim();
        const email = document.getElementById("signup-email").value.trim();
        const password = document.getElementById("signup-password").value;
        const confirm = document.getElementById("signup-confirm").value;

        if (password !== confirm) {
            alert("Passwords do not match.");
            return;
        }

        const submitBtn = document.getElementById("signup-submit");
        if (submitBtn) submitBtn.textContent = "Creating Account...";

        try {
            const res = await fetch(`${API_ROOT}/auth/signup`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, email, password })
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Registration failed");

            localStorage.setItem("token", data.access_token);
            currentUser = data.user;
            updateAuthUI(currentUser);
            navigateTo("home");
        } catch (err) {
            alert(err.message);
        } finally {
            if (submitBtn) submitBtn.textContent = "Create Account";
        }
    });
}

// ============================================
// INTERACTIVE AI CHAT PROXY
// ============================================

function initChatPage() {
    const storedTool = sessionStorage.getItem("active_chat_tool");
    const tool = storedTool ? JSON.parse(storedTool) : null;

    const noticeAvailable = document.getElementById("chat-availability-notice");
    const noticeOffline = document.getElementById("chat-offline-notice");
    const chatLayout = document.getElementById("chat-layout");
    const officialLink = document.getElementById("chat-official-link");

    if (!tool) {
        // Fallback default tool if opened directly
        setupChatHeader({ id: 1, name: "ChatGPT", api_available: "yes", platform: "OpenAI API" });
    } else if (tool.api_available === "no") {
        if (noticeAvailable) noticeAvailable.classList.add("hidden");
        if (chatLayout) chatLayout.classList.add("hidden");
        if (noticeOffline) noticeOffline.classList.remove("hidden");
        if (officialLink) officialLink.href = tool.website;
        return;
    } else {
        setupChatHeader(tool);
    }

    chatMessagesHistory = [];
    
    const sendBtn = document.getElementById("chat-send-btn");
    const input = document.getElementById("chat-input");
    const clearBtn = document.getElementById("btn-clear-chat");

    if (sendBtn) sendBtn.onclick = () => handleSendChatMessage(tool ? tool.id : 1);
    if (input) {
        input.onkeydown = (e) => {
            if (e.key === "Enter") handleSendChatMessage(tool ? tool.id : 1);
        };
    }
    if (clearBtn) {
        clearBtn.onclick = () => {
            chatMessagesHistory = [];
            const msgBox = document.getElementById("chat-messages");
            if (msgBox) {
                msgBox.innerHTML = `
                    <div class="chat-msg ai">
                        <p>Chat cleared. How can I assist you next?</p>
                    </div>
                `;
            }
        };
    }
}

function setupChatHeader(tool) {
    const nameLabel = document.getElementById("chat-ai-display-name");
    const badgeLabel = document.getElementById("chat-ai-provider-badge");
    const toolInfo = document.getElementById("chat-info-tool");
    const providerInfo = document.getElementById("chat-info-provider");

    if (nameLabel) nameLabel.textContent = tool.name;
    if (badgeLabel) badgeLabel.textContent = tool.platform || "API Connected";
    if (toolInfo) toolInfo.textContent = tool.name;
    if (providerInfo) providerInfo.textContent = tool.platform || "Official API";
}

async function handleSendChatMessage(toolId) {
    const input = document.getElementById("chat-input");
    const msgContainer = document.getElementById("chat-messages");
    const typing = document.getElementById("chat-typing-indicator");
    const msgCount = document.getElementById("chat-info-msg-count");

    if (!input || !msgContainer) return;
    const text = input.value.trim();
    if (!text) return;

    const userBubble = document.createElement("div");
    userBubble.className = "chat-msg user";
    userBubble.innerHTML = `<p>${escapeHTML(text)}</p>`;
    msgContainer.appendChild(userBubble);

    input.value = "";
    msgContainer.scrollTop = msgContainer.scrollHeight;

    chatMessagesHistory.push({ role: "user", content: text });
    if (msgCount) msgCount.textContent = chatMessagesHistory.length;

    if (typing) typing.classList.remove("hidden");

    try {
        const token = localStorage.getItem("token");
        const res = await fetch(`${API_ROOT}/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...(token ? { "Authorization": `Bearer ${token}` } : {})
            },
            body: JSON.stringify({
                tool_id: toolId,
                messages: chatMessagesHistory
            })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "AI response failed");

        chatMessagesHistory.push({ role: "assistant", content: data.reply });

        const aiBubble = document.createElement("div");
        aiBubble.className = "chat-msg ai";
        aiBubble.innerHTML = `<p>${data.reply.replace(/\n/g, "<br>")}</p>`;
        msgContainer.appendChild(aiBubble);

    } catch (err) {
        const errBubble = document.createElement("div");
        errBubble.className = "chat-msg ai";
        errBubble.innerHTML = `<p class="text-danger">Error: ${escapeHTML(err.message)}</p>`;
        msgContainer.appendChild(errBubble);
    } finally {
        if (typing) typing.classList.add("hidden");
        msgContainer.scrollTop = msgContainer.scrollHeight;
    }
}

// ============================================
// SEARCH HISTORY (Database Connected)
// ============================================

async function initHistoryPage() {
    const list = document.getElementById("history-list");
    const empty = document.getElementById("history-empty");
    const countLabel = document.getElementById("history-count-label");
    const clearBtn = document.getElementById("btn-clear-history");
    const startBtn = document.getElementById("btn-history-start");

    if (startBtn) startBtn.onclick = () => navigateTo("home");

    const token = localStorage.getItem("token");
    if (!token) {
        if (empty) {
            empty.innerHTML = `
                <h3>Login Required</h3>
                <p>Log in or create an account to view and save your search recommendations.</p>
                <button class="btn btn-primary mt-md" onclick="navigateTo('login')">Log In</button>
            `;
            empty.classList.remove("hidden");
        }
        return;
    }

    try {
        const res = await fetch(`${API_ROOT}/history`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!res.ok) throw new Error("Could not load history");
        const historyData = await res.json();

        if (countLabel) countLabel.textContent = `${historyData.length} searches recorded`;

        if (historyData.length === 0) {
            if (empty) empty.classList.remove("hidden");
            return;
        }

        if (empty) empty.classList.add("hidden");
        if (list) {
            list.querySelectorAll(".history-item").forEach(el => el.remove());
            
            historyData.forEach(item => {
                const row = document.createElement("div");
                row.className = "history-item";
                row.innerHTML = `
                    <div>
                        <div class="history-query">${escapeHTML(item.query)}</div>
                        <div class="history-meta">${formatLabel(item.detected_category)} • Top Match: ${item.best_tool_name} • ${new Date(item.created_at).toLocaleDateString()}</div>
                    </div>
                    <span class="tag">${item.match_score}% match</span>
                `;
                row.onclick = () => {
                    sessionStorage.setItem("pending_search_query", item.query);
                    navigateTo("dashboard");
                };
                list.appendChild(row);
            });
        }

        if (clearBtn) {
            clearBtn.onclick = async () => {
                if (!confirm("Are you sure you want to clear your search history?")) return;
                await fetch(`${API_ROOT}/history`, {
                    method: "DELETE",
                    headers: { "Authorization": `Bearer ${token}` }
                });
                initHistoryPage();
            };
        }
    } catch (err) {
        console.error("History fetch error:", err);
    }
}

// ============================================
// ADMIN PANEL (Tool Management & CRUD)
// ============================================

async function initAdminPage() {
    if (!currentUser || !currentUser.is_admin) {
        const pageContent = document.getElementById("page-content");
        if (pageContent) {
            pageContent.innerHTML = `
                <div class="empty-state">
                    <h3>Access Denied</h3>
                    <p>Administrative privileges are required to access this dashboard.</p>
                    <button class="btn btn-primary mt-md" onclick="navigateTo('login')">Admin Log In</button>
                </div>
            `;
        }
        return;
    }

    loadAdminStatsAndTools();

    const addBtn = document.getElementById("btn-add-tool");
    const cancelBtn = document.getElementById("btn-cancel-form");
    const searchInput = document.getElementById("admin-search-input");
    const catFilter = document.getElementById("admin-category-filter");
    const form = document.getElementById("admin-tool-form");

    if (addBtn) addBtn.onclick = () => openAdminForm(null);
    if (cancelBtn) cancelBtn.onclick = () => closeAdminForm();
    if (searchInput) searchInput.oninput = () => filterAdminTools();
    if (catFilter) catFilter.onchange = () => filterAdminTools();
    if (form) form.onsubmit = handleAdminFormSubmit;
}

async function loadAdminStatsAndTools() {
    try {
        const res = await fetch(`${API_ROOT}/tools?active_only=false`);
        allAdminTools = await res.json();

        const total = allAdminTools.length;
        const categories = new Set(allAdminTools.map(t => t.category)).size;
        const apiCount = allAdminTools.filter(t => t.api_available === "yes").length;
        const activeCount = allAdminTools.filter(t => t.active).length;

        setText("admin-total-tools", total);
        setText("admin-total-categories", categories);
        setText("admin-api-available", apiCount);
        setText("admin-active-tools", activeCount);

        renderAdminToolList(allAdminTools);
    } catch (e) {
        console.error("Failed to load admin tool list:", e);
    }
}

function renderAdminToolList(tools) {
    const list = document.getElementById("admin-tools-list");
    if (!list) return;

    if (tools.length === 0) {
        list.innerHTML = '<div class="empty-state"><p>No tools matched your filter.</p></div>';
        return;
    }

    list.innerHTML = tools.map(t => `
        <div class="admin-tool-card">
            <div class="admin-tool-info">
                <h4>${t.name} ${!t.active ? '<span class="tag tag-paid">Disabled</span>' : ''}</h4>
                <p>${formatLabel(t.category)} • ${formatLabel(t.pricing)} • Quality: ${t.quality_rating}/10</p>
            </div>
            <div class="admin-actions">
                <button class="btn btn-sm btn-ghost" onclick="openAdminForm(${t.id})">Edit</button>
                <button class="btn btn-sm btn-danger" onclick="deleteAdminTool(${t.id}, '${escapeHTML(t.name)}')">Delete</button>
            </div>
        </div>
    `).join("");
}

function filterAdminTools() {
    const query = (document.getElementById("admin-search-input")?.value || "").toLowerCase();
    const cat = document.getElementById("admin-category-filter")?.value || "all";

    const filtered = allAdminTools.filter(t => {
        const matchesQuery = t.name.toLowerCase().includes(query) || t.description.toLowerCase().includes(query);
        const matchesCat = cat === "all" || t.category === cat;
        return matchesQuery && matchesCat;
    });

    renderAdminToolList(filtered);
}

function openAdminForm(toolId) {
    const formCard = document.getElementById("admin-tool-form-card");
    const formTitle = document.getElementById("admin-form-title");
    const deleteBtn = document.getElementById("btn-delete-tool");
    if (!formCard) return;

    editingToolId = toolId;
    formCard.classList.remove("hidden");
    formCard.scrollIntoView({ behavior: "smooth" });

    if (toolId) {
        const tool = allAdminTools.find(t => t.id === toolId);
        if (!tool) return;
        if (formTitle) formTitle.textContent = `Edit Tool: ${tool.name}`;
        if (deleteBtn) {
            deleteBtn.classList.remove("hidden");
            deleteBtn.onclick = () => deleteAdminTool(tool.id, tool.name);
        }

        setValue("tool-name", tool.name);
        setValue("tool-category", tool.category);
        setValue("tool-description", tool.description);
        setValue("tool-website", tool.website);
        setValue("tool-pricing", tool.pricing);
        setValue("tool-skill-level", tool.skill_level);
        setValue("tool-api", tool.api_available);
        setValue("tool-platform", tool.platform);
        setValue("tool-capabilities", (tool.capabilities || []).join(", "));
        setValue("tool-strengths", (tool.strengths || []).join(", "));
        setValue("tool-weaknesses", (tool.weaknesses || []).join(", "));
        setValue("tool-quality", tool.quality_rating);
        setValue("tool-ease", tool.ease_rating);
        setValue("tool-speed", tool.speed_rating);
        
        const activeCheckbox = document.getElementById("tool-active");
        if (activeCheckbox) activeCheckbox.checked = tool.active;
    } else {
        if (formTitle) formTitle.textContent = "Add New AI Tool";
        if (deleteBtn) deleteBtn.classList.add("hidden");
        document.getElementById("admin-tool-form")?.reset();
    }
}

function closeAdminForm() {
    const formCard = document.getElementById("admin-tool-form-card");
    if (formCard) formCard.classList.add("hidden");
    editingToolId = null;
}

async function handleAdminFormSubmit(e) {
    e.preventDefault();
    const token = localStorage.getItem("token");
    if (!token) return;

    const payload = {
        name: document.getElementById("tool-name").value.trim(),
        category: document.getElementById("tool-category").value,
        description: document.getElementById("tool-description").value.trim(),
        website: document.getElementById("tool-website").value.trim(),
        pricing: document.getElementById("tool-pricing").value,
        skill_level: document.getElementById("tool-skill-level").value,
        api_available: document.getElementById("tool-api").value,
        platform: document.getElementById("tool-platform").value.trim() || "Web",
        capabilities: parseList(document.getElementById("tool-capabilities").value),
        strengths: parseList(document.getElementById("tool-strengths").value),
        weaknesses: parseList(document.getElementById("tool-weaknesses").value),
        quality_rating: parseInt(document.getElementById("tool-quality").value) || 7,
        ease_rating: parseInt(document.getElementById("tool-ease").value) || 7,
        speed_rating: parseInt(document.getElementById("tool-speed").value) || 7,
        active: document.getElementById("tool-active").checked
    };

    try {
        const url = editingToolId ? `${API_ROOT}/tools/${editingToolId}` : `${API_ROOT}/tools`;
        const method = editingToolId ? "PUT" : "POST";

        const res = await fetch(url, {
            method: method,
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Operation failed");

        closeAdminForm();
        loadAdminStatsAndTools();
    } catch (err) {
        alert("Admin Save Error: " + err.message);
    }
}

async function deleteAdminTool(toolId, toolName) {
    if (!confirm(`Are you sure you want to permanently delete "${toolName}"?`)) return;
    const token = localStorage.getItem("token");

    try {
        const res = await fetch(`${API_ROOT}/tools/${toolId}`, {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!res.ok) throw new Error("Delete failed");
        closeAdminForm();
        loadAdminStatsAndTools();
    } catch (err) {
        alert(err.message);
    }
}

// ============================================
// HELPER UTILITIES
// ============================================

function setValue(id, val) {
    const el = document.getElementById(id);
    if (el) el.value = val || "";
}

function parseList(str) {
    return (str || "").split(",").map(s => s.trim()).filter(Boolean);
}

function escapeHTML(str) {
    return (str || "").replace(/[&<>'"]/g, tag => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[tag] || tag));
}

function toggleMobileMenu() {
    const navMenu = document.getElementById("nav-menu");
    const navToggle = document.getElementById("nav-toggle");
    if (navMenu) navMenu.classList.toggle("open");
    if (navToggle) navToggle.classList.toggle("active");
}

function closeMobileMenu() {
    const navMenu = document.getElementById("nav-menu");
    const navToggle = document.getElementById("nav-toggle");
    if (navMenu) navMenu.classList.remove("open");
    if (navToggle) navToggle.classList.remove("active");
}

function attachNavDelegation() {
    document.querySelectorAll("[data-page]").forEach(link => {
        link.onclick = (e) => {
            e.preventDefault();
            navigateTo(link.dataset.page);
        };
    });
}

// ============================================
// APP ENTRY POINT
// ============================================

document.addEventListener("DOMContentLoaded", () => {
    attachNavDelegation();

    const navToggle = document.getElementById("nav-toggle");
    if (navToggle) navToggle.addEventListener("click", toggleMobileMenu);

    window.addEventListener("popstate", () => {
        const page = window.location.hash.replace("#", "") || "home";
        navigateTo(page);
    });

    checkAuthSession();

    const initialPage = window.location.hash.replace("#", "") || "home";
    navigateTo(initialPage);
});