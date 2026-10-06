// Gourmet Bistro AI Agent Frontend Client
document.addEventListener("DOMContentLoaded", () => {
    let currentConversationId = null;

    // Elements
    const chatWindow = document.getElementById("chat-window");
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const clearChatBtn = document.getElementById("clear-chat-btn");
    const chaosToggle = document.getElementById("chaos-failure-toggle");
    const tracesList = document.getElementById("traces-list");
    const ordersTbody = document.getElementById("orders-tbody");
    const ticketsTbody = document.getElementById("tickets-tbody");
    const workflowForm = document.getElementById("workflow-form");

    // Initialize
    refreshOrders();
    refreshTickets();
    refreshTraces();

    // Tab Navigation
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            const target = document.getElementById(btn.dataset.tab);
            if (target) target.classList.add("active");

            // Auto refresh active tab
            if (btn.dataset.tab === "tab-orders") refreshOrders();
            if (btn.dataset.tab === "tab-tickets") refreshTickets();
            if (btn.dataset.tab === "tab-traces") refreshTraces();
        });
    });

    // Refresh Buttons
    document.getElementById("refresh-traces-btn")?.addEventListener("click", refreshTraces);
    document.getElementById("refresh-orders-btn")?.addEventListener("click", refreshOrders);
    document.getElementById("refresh-tickets-btn")?.addEventListener("click", refreshTickets);

    // Scenario Quick Chips
    document.querySelectorAll(".chip").forEach(chip => {
        chip.addEventListener("click", () => {
            const prompt = chip.dataset.prompt;
            if (prompt) {
                userInput.value = prompt;
                handleChatSubmit();
            }
        });
    });

    // Clear Chat
    clearChatBtn.addEventListener("click", () => {
        currentConversationId = null;
        chatWindow.innerHTML = `
            <div class="message assistant-msg">
                <div class="msg-avatar">🤖</div>
                <div class="msg-content">
                    <p>New conversation started. How may I assist you with orders or restaurant policies?</p>
                </div>
            </div>
        `;
    });

    // Chaos Failure Toggle
    chaosToggle.addEventListener("change", async (e) => {
        const enabled = e.target.checked;
        try {
            const res = await fetch(`/api/orders/simulate-failure?enabled=${enabled}`, { method: "POST" });
            const data = await res.json();
            console.log("Simulate Failure:", data.message);
        } catch (err) {
            console.error("Toggle failed:", err);
        }
    });

    // Chat Submission
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        handleChatSubmit();
    });

    async function handleChatSubmit() {
        const text = userInput.value.trim();
        if (!text) return;

        // Append User Message
        appendUserMessage(text);
        userInput.value = "";
        userInput.disabled = true;
        sendBtn.disabled = true;

        // Placeholder Assistant Message
        const tempMsgEl = document.createElement("div");
        tempMsgEl.className = "message assistant-msg";
        tempMsgEl.innerHTML = `
            <div class="msg-avatar">🤖</div>
            <div class="msg-content">
                <p><em>Reasoning over request and verifying operational tools...</em></p>
            </div>
        `;
        chatWindow.appendChild(tempMsgEl);
        chatWindow.scrollTop = chatWindow.scrollHeight;

        try {
            const response = await fetch("/api/agent/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: text,
                    conversation_id: currentConversationId
                })
            });

            const data = await response.json();
            currentConversationId = data.conversation_id;

            // Render Full Response
            renderAssistantMessage(tempMsgEl, data);
            refreshTraces();
            refreshOrders();
            refreshTickets();
        } catch (err) {
            tempMsgEl.querySelector(".msg-content").innerHTML = `
                <p style="color:var(--danger)">Error contacting agent server: ${err.message}</p>
            `;
        } finally {
            userInput.disabled = false;
            sendBtn.disabled = false;
            userInput.focus();
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }
    }

    function appendUserMessage(text) {
        const msgEl = document.createElement("div");
        msgEl.className = "message user-msg";
        msgEl.innerHTML = `
            <div class="msg-avatar">👤</div>
            <div class="msg-content">
                <p>${escapeHtml(text)}</p>
            </div>
        `;
        chatWindow.appendChild(msgEl);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function renderAssistantMessage(el, data) {
        const contentBox = el.querySelector(".msg-content");
        contentBox.innerHTML = "";

        // Guardrail alert banner
        if (data.guardrail_triggered) {
            contentBox.innerHTML += `
                <div class="guardrail-alert">
                    <strong>🛡️ Guardrail Shield Triggered</strong><br>
                    ${escapeHtml(data.response)}
                </div>
            `;
            return;
        }

        // Natural Language response
        const p = document.createElement("p");
        p.textContent = data.response;
        p.style.whiteSpace = "pre-line";
        contentBox.appendChild(p);

        // Authoritative Data Card (Requirement A & B Separation)
        if (data.authoritative_data) {
            const authCard = document.createElement("div");
            authCard.className = "authoritative-card";
            authCard.innerHTML = `
                <span class="authoritative-badge">Authoritative Operational Data</span>
                <pre style="font-family:var(--font-mono); font-size:0.75rem; color:#bae6fd; overflow-x:auto;">${escapeHtml(JSON.stringify(data.authoritative_data, null, 2))}</pre>
            `;
            contentBox.appendChild(authCard);
        }

        // RAG Source Citations
        if (data.rag_sources && data.rag_sources.length > 0) {
            const sourcesBox = document.createElement("div");
            sourcesBox.className = "sources-box";
            let sourcesHtml = "<strong>📚 Grounded Knowledge Sources:</strong><br>";
            data.rag_sources.forEach(src => {
                sourcesHtml += `• <em>${escapeHtml(src.title)}</em> [Score: ${src.score}]<br>`;
            });
            sourcesBox.innerHTML = sourcesHtml;
            contentBox.appendChild(sourcesBox);
        }
    }

    // Refresh Traces
    async function refreshTraces() {
        try {
            const res = await fetch("/api/agent/traces?limit=15");
            const traces = await res.json();
            if (!traces || traces.length === 0) {
                tracesList.innerHTML = `<div class="empty-state">No traces logged yet.</div>`;
                return;
            }

            tracesList.innerHTML = traces.map(t => {
                const toolsHtml = (t.tools_called || []).map(tool => {
                    const statusClass = tool.status === "success" ? "tool-success" : "tool-failed";
                    return `<span class="tool-chip ${statusClass}">🛠️ ${escapeHtml(tool.tool_name)} (${tool.latency_ms}ms) [${tool.status}]</span>`;
                }).join("");

                return `
                    <div class="trace-item">
                        <div class="trace-top">
                            <span class="trace-id">${t.trace_id}</span>
                            <span class="trace-latency">⏱️ ${t.latency_ms} ms</span>
                        </div>
                        <div class="trace-user-msg"><strong>User:</strong> "${escapeHtml(t.user_message)}"</div>
                        <div style="margin-bottom:6px;">${toolsHtml || '<span style="color:var(--text-muted);font-size:0.75rem;">No tools called</span>'}</div>
                        <div style="font-size:0.75rem; color:var(--text-muted);">
                            Guardrail: <strong>${escapeHtml(t.guardrail_status)}</strong>
                        </div>
                    </div>
                `;
            }).join("");
        } catch (err) {
            console.error("Traces error:", err);
        }
    }

    // Refresh Orders
    async function refreshOrders() {
        try {
            const res = await fetch("/api/orders");
            const orders = await res.json();
            ordersTbody.innerHTML = orders.map(o => {
                let badgeClass = "badge-accent";
                if (o.status === "Delivered") badgeClass = "badge-success";
                if (o.status === "Cancelled") badgeClass = "badge-danger";
                if (o.status === "Preparing") badgeClass = "badge-warning";

                return `
                    <tr>
                        <td><strong>${o.order_id}</strong></td>
                        <td>${escapeHtml(o.customer_name)}</td>
                        <td><span class="badge ${badgeClass}">${o.status}</span></td>
                        <td>$${o.total_amount.toFixed(2)}</td>
                        <td>${escapeHtml(o.driver_name || 'N/A')} (${escapeHtml(o.estimated_delivery_time || 'N/A')})</td>
                    </tr>
                `;
            }).join("");
        } catch (err) {
            console.error("Orders error:", err);
        }
    }

    // Refresh Tickets
    async function refreshTickets() {
        try {
            const res = await fetch("/api/support/tickets");
            const tickets = await res.json();
            ticketsTbody.innerHTML = tickets.map(t => {
                let priorityClass = t.priority === "High" ? "badge-danger" : (t.priority === "Medium" ? "badge-warning" : "badge-accent");
                return `
                    <tr>
                        <td><strong>${t.ticket_id}</strong></td>
                        <td>${t.order_id || 'N/A'}</td>
                        <td>${t.issue_category}</td>
                        <td><span class="badge ${priorityClass}">${t.priority}</span></td>
                        <td>${escapeHtml(t.customer_name)}</td>
                        <td title="${escapeHtml(t.description)}">${escapeHtml(t.description.substring(0, 35))}...</td>
                        <td><span class="badge badge-accent">${t.status}</span></td>
                    </tr>
                `;
            }).join("");
        } catch (err) {
            console.error("Tickets error:", err);
        }
    }

    // Run Automation Workflow
    workflowForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const payload = {
            customer_name: document.getElementById("wf-name").value,
            order_id: document.getElementById("wf-order").value.trim() || null,
            message: document.getElementById("wf-message").value
        };

        try {
            const res = await fetch("/api/automation/complaint", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            document.getElementById("workflow-result").style.display = "block";
            document.getElementById("workflow-result-json").textContent = JSON.stringify(data, null, 2);
            refreshTickets();
        } catch (err) {
            alert("Workflow trigger error: " + err.message);
        }
    });

    function escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});

