const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

const messageBox = document.getElementById("message");
const categorySelect = document.getElementById("category");
const form = document.getElementById("ticket-form");
const titleInput = document.getElementById("title");
const descriptionInput = document.getElementById("description");

const listBody = document.getElementById("tickets-list");
const loadingBox = document.getElementById("loading");
const filterSelect = document.getElementById("status-filter");
const searchInput = document.getElementById("search-input");

const statTotal = document.getElementById("stat-total");
const statProgress = document.getElementById("stat-progress");
const statDone = document.getElementById("stat-done");

// Элементы модальных окон Tabler
const editModalEl = document.getElementById("edit-ticket-modal");
const editForm = document.getElementById("edit-ticket-form");
const editTicketId = document.getElementById("edit-ticket-id");
const editTicketIdLabel = document.getElementById("edit-ticket-id-label");
const editTitle = document.getElementById("edit-title");
const editCategory = document.getElementById("edit-category");
const editDescription = document.getElementById("edit-description");
const editStatus = document.getElementById("edit-status");

const deleteModalEl = document.getElementById("delete-ticket-modal");
const deleteTicketTitle = document.getElementById("delete-ticket-title");
const confirmDeleteBtn = document.getElementById("confirm-delete-btn");

let pendingDeleteId = null;
let cachedCategories = [];
let searchTimer = null;

const STATUS_META = {
    new: { label: "Новая", badgeClass: "bg-secondary-lt" },
    progress: { label: "В работе", badgeClass: "bg-blue-lt" },
    done: { label: "Выполнена", badgeClass: "bg-green-lt" }
};

const ALLOWED_TRANSITIONS = {
    new: ["new", "progress"],
    progress: ["progress", "done"],
    done: ["done"]
};

// Превращаем ответ с ошибкой DRF в понятную строку без сырого JSON
function formatApiError(data) {
    if (!data) {
        return "Не удалось выполнить запрос к серверу.";
    }
    if (typeof data === "string") {
        return data;
    }
    if (data.detail) {
        return data.detail;
    }
    const fieldNames = {
        title: "Название",
        category: "Категория",
        status: "Статус",
        description: "Описание",
        non_field_errors: "Ошибка"
    };
    const parts = [];
    for (const [key, value] of Object.entries(data)) {
        const label = fieldNames[key] || key;
        const text = Array.isArray(value) ? value.join(" ") : String(value);
        parts.push(`${label}: ${text}`);
    }
    return parts.join(" | ") || "Ошибка проверки данных.";
}

function showMessage(text, isError = false) {
    messageBox.textContent = text;
    messageBox.className = "alert mb-3 " + (isError ? "alert-danger" : "alert-success");
}

async function apiRequest(url, options = {}) {
    let response;
    try {
        response = await fetch(url, {
            ...options,
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken,
                ...(options.headers || {})
            },
            credentials: "same-origin"
        });
    } catch (_networkError) {
        throw new Error("Сервис API временно недоступен. Проверьте подключение к сети или попробуйте обновить страницу позже.");
    }

    let data = null;
    if (response.status !== 204) {
        data = await response.json().catch(() => null);
    }

    if (!response.ok) {
        if (response.status >= 500 && !data) {
            throw new Error("Сервис API временно недоступен (ошибка сервера). Попробуйте повторить запрос позже.");
        }
        throw new Error(formatApiError(data));
    }
    return data;
}

function populateCategorySelect(selectEl, categories) {
    selectEl.replaceChildren();
    for (const cat of categories) {
        const option = document.createElement("option");
        option.value = cat.id;
        option.textContent = cat.name;
        selectEl.append(option);
    }
}

async function loadCategories() {
    cachedCategories = await apiRequest("/api/categories/");
    populateCategorySelect(categorySelect, cachedCategories);
    populateCategorySelect(editCategory, cachedCategories);
}

// Обновляем карточки сводной статистики по всем заявкам пользователя
async function refreshStats() {
    const allTickets = await apiRequest("/api/tickets/");
    statTotal.textContent = allTickets.length;
    statProgress.textContent = allTickets.filter((t) => t.status === "progress").length;
    statDone.textContent = allTickets.filter((t) => t.status === "done").length;
}

function getModal(el) {
    const bs = window.bootstrap || (window.tabler && window.tabler.bootstrap);
    return bs.Modal.getOrCreateInstance(el);
}

function openEditModal(ticket) {
    editTicketId.value = ticket.id;
    editTicketIdLabel.textContent = String(ticket.id).padStart(3, "0");
    editTitle.value = ticket.title;
    editDescription.value = ticket.description || "";
    editCategory.value = ticket.category;

    // В выпадающем списке оставляем доступными только текущий и следующий допустимый статус
    const allowed = ALLOWED_TRANSITIONS[ticket.status] || [ticket.status];
    editStatus.replaceChildren();
    for (const [code, meta] of Object.entries(STATUS_META)) {
        const opt = document.createElement("option");
        opt.value = code;
        opt.textContent = meta.label;
        opt.disabled = !allowed.includes(code);
        if (code === ticket.status) {
            opt.selected = true;
        }
        editStatus.append(opt);
    }

    getModal(editModalEl).show();
}

function openDeleteModal(ticket) {
    pendingDeleteId = ticket.id;
    deleteTicketTitle.textContent = ticket.title;
    getModal(deleteModalEl).show();
}

function renderTickets(tickets) {
    listBody.replaceChildren();

    if (tickets.length === 0) {
        const tr = document.createElement("tr");
        const td = document.createElement("td");
        td.colSpan = 5;
        td.className = "text-center text-secondary py-4";
        td.textContent = "Заявки не найдены";
        tr.append(td);
        listBody.append(tr);
        return;
    }

    for (const ticket of tickets) {
        const tr = document.createElement("tr");

        const tdId = document.createElement("td");
        tdId.className = "text-secondary";
        tdId.textContent = String(ticket.id).padStart(3, "0");

        const tdTitle = document.createElement("td");
        const titleEl = document.createElement("div");
        titleEl.className = "fw-medium";
        titleEl.textContent = ticket.title;
        tdTitle.append(titleEl);
        if (ticket.description) {
            const descEl = document.createElement("div");
            descEl.className = "text-secondary small";
            descEl.textContent = ticket.description;
            tdTitle.append(descEl);
        }

        const tdCategory = document.createElement("td");
        tdCategory.textContent = ticket.category_name;

        const tdStatus = document.createElement("td");
        const badge = document.createElement("span");
        const meta = STATUS_META[ticket.status] || { label: ticket.status, badgeClass: "bg-secondary-lt" };
        badge.className = "badge " + meta.badgeClass;
        badge.textContent = meta.label;
        tdStatus.append(badge);

        const tdActions = document.createElement("td");
        tdActions.className = "text-end";
        const btnGroup = document.createElement("div");
        btnGroup.className = "btn-list justify-content-end";

        const editBtn = document.createElement("button");
        editBtn.type = "button";
        editBtn.className = "btn btn-sm btn-outline-primary";
        editBtn.textContent = "Изменить статус";
        editBtn.addEventListener("click", () => openEditModal(ticket));

        const delBtn = document.createElement("button");
        delBtn.type = "button";
        delBtn.className = "btn btn-sm btn-outline-danger";
        delBtn.textContent = "Удалить";
        delBtn.addEventListener("click", () => openDeleteModal(ticket));

        btnGroup.append(editBtn, delBtn);
        tdActions.append(btnGroup);

        tr.append(tdId, tdTitle, tdCategory, tdStatus, tdActions);
        listBody.append(tr);
    }
}

async function loadTickets() {
    loadingBox.hidden = false;
    const params = new URLSearchParams();
    if (filterSelect.value) {
        params.set("status", filterSelect.value);
    }
    const queryText = searchInput.value.trim();
    if (queryText) {
        params.set("search", queryText);
    }

    const query = params.toString();
    const url = "/api/tickets/" + (query ? "?" + query : "");

    try {
        const tickets = await apiRequest(url);
        renderTickets(tickets);
        await refreshStats();
    } catch (error) {
        showMessage("Не удалось загрузить заявки: " + error.message, true);
    } finally {
        loadingBox.hidden = true;
    }
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        await apiRequest("/api/tickets/", {
            method: "POST",
            body: JSON.stringify({
                title: titleInput.value,
                description: descriptionInput.value,
                category: Number(categorySelect.value)
            })
        });
        titleInput.value = "";
        descriptionInput.value = "";
        showMessage("Заявка успешно создана.");
        await loadTickets();
    } catch (error) {
        showMessage("Не удалось создать заявку: " + error.message, true);
    }
});

editForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const id = editTicketId.value;
    try {
        await apiRequest(`/api/tickets/${id}/`, {
            method: "PATCH",
            body: JSON.stringify({
                title: editTitle.value,
                description: editDescription.value,
                category: Number(editCategory.value),
                status: editStatus.value
            })
        });
        getModal(editModalEl).hide();
        showMessage("Изменения по заявке сохранены.");
        await loadTickets();
    } catch (error) {
        getModal(editModalEl).hide();
        showMessage("Не удалось обновить заявку: " + error.message, true);
    }
});

confirmDeleteBtn.addEventListener("click", async () => {
    if (!pendingDeleteId) {
        return;
    }
    const id = pendingDeleteId;
    pendingDeleteId = null;
    try {
        await apiRequest(`/api/tickets/${id}/`, { method: "DELETE" });
        getModal(deleteModalEl).hide();
        showMessage("Заявка удалена.");
        await loadTickets();
    } catch (error) {
        getModal(deleteModalEl).hide();
        showMessage("Не удалось удалить заявку: " + error.message, true);
    }
});

filterSelect.addEventListener("change", loadTickets);
searchInput.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(loadTickets, 250);
});

async function initialize() {
    try {
        await loadCategories();
        await loadTickets();
    } catch (error) {
        showMessage("Ошибка инициализации: " + error.message, true);
    }
}

initialize();
