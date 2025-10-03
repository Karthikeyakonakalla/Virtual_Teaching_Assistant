(() => {
const API_BASE = '/api';
const AUTH_TOKEN_KEY = 'authToken';
const AUTH_USER_KEY = 'authUser';

const toast = document.getElementById('toast');
const userNameEl = document.getElementById('userName');
const historyList = document.getElementById('historyList');
const historyPlaceholder = document.getElementById('historyPlaceholder');
const refreshBtn = document.getElementById('refreshHistoryBtn');

initAccountPage();

function initAccountPage() {
    if (!ensureAuthenticated()) {
        window.location.href = '/login';
        return;
    }

    const storedUser = localStorage.getItem(AUTH_USER_KEY);
    if (storedUser) {
        try {
            const parsed = JSON.parse(storedUser);
            if (parsed?.name) {
                userNameEl.textContent = parsed.name.split(' ')[0];
            }
        } catch (error) {
            console.warn('Failed to parse stored user', error);
        }
    }

    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => fetchHistory(true));
    }

    fetchHistory();
}

function ensureAuthenticated() {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (!token) {
        return false;
    }
    return true;
}

async function fetchHistory(manual = false) {
    if (!historyList || !historyPlaceholder) return;

    setPlaceholder('Loading your history...');

    try {
        if (refreshBtn) {
            refreshBtn.disabled = true;
            const icon = refreshBtn.querySelector('i');
            if (icon) icon.classList.add('fa-spin');
        }

        const response = await fetch(`${API_BASE}/history`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem(AUTH_TOKEN_KEY)}`
            }
        });

        if (response.status === 401) {
            handleUnauthenticated();
            return;
        }

        if (!response.ok) {
            throw new Error(`History request failed (${response.status})`);
        }

        const data = await response.json();
        if (data.success && Array.isArray(data.history) && data.history.length > 0) {
            renderHistory(data.history);
        } else {
            showEmptyState();
        }

        if (manual) {
            showToast('History refreshed');
        }
    } catch (error) {
        console.error('Error fetching history:', error);
        setPlaceholder('Unable to load history right now.');
        historyList.innerHTML = '';
        if (manual) {
            showToast('Failed to refresh history', true);
        }
    } finally {
        if (refreshBtn) {
            refreshBtn.disabled = false;
            const icon = refreshBtn.querySelector('i');
            if (icon) icon.classList.remove('fa-spin');
        }
    }
}

function renderHistory(records) {
    historyPlaceholder.style.display = 'none';
    historyList.innerHTML = records.map(createHistoryItem).join('');
}

function createHistoryItem(item) {
    const subject = capitalize(item.subject) || 'General';
    const queryType = item.query_type ? item.query_type.replace(/_/g, ' ') : 'general';
    const created = formatDate(item.created_at);
    const finalAnswer = item.final_answer ? `<div class="history-item-answer"><strong>Final answer:</strong> ${escapeHtml(item.final_answer)}</div>` : '';

    const metaParts = [];
    if (created) metaParts.push(`<span><i class="fas fa-clock"></i> ${escapeHtml(created)}</span>`);
    if (item.processing_time !== undefined && item.processing_time !== null) {
        metaParts.push(`<span><i class="fas fa-stopwatch"></i> ${item.processing_time.toFixed(2)}s</span>`);
    }
    if (item.confidence_score !== undefined && item.confidence_score !== null) {
        metaParts.push(`<span><i class="fas fa-signal"></i> ${Math.round(item.confidence_score * 100)}% confidence</span>`);
    }

    return `
        <li class="history-item">
            <div class="history-item-header">
                <span class="history-item-subject"><i class="fas fa-book"></i> ${escapeHtml(subject)}</span>
                <span class="history-item-type">${escapeHtml(queryType)}</span>
            </div>
            <div class="history-item-query">${escapeHtml(truncate(item.query_text || ''))}</div>
            <div class="history-item-meta">${metaParts.join('')}</div>
            ${finalAnswer}
        </li>
    `;
}

function showEmptyState() {
    setPlaceholder('You haven’t asked any questions yet. Start learning now!');
    historyList.innerHTML = '';
}

function setPlaceholder(message) {
    historyPlaceholder.textContent = message;
    historyPlaceholder.style.display = 'block';
}

function handleUnauthenticated() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
    window.location.href = '/login';
}

function showToast(message, isError = false) {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.toggle('error', isError);
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2000);
}

function formatDate(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    if (Number.isNaN(date.getTime())) return '';
    return date.toLocaleString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function truncate(text, max = 200) {
    if (!text || typeof text !== 'string') return '';
    return text.length > max ? `${text.slice(0, max)}…` : text;
}

function capitalize(value) {
    if (!value || typeof value !== 'string') return '';
    return value.charAt(0).toUpperCase() + value.slice(1);
}

function escapeHtml(value) {
    if (value === undefined || value === null) return '';
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

})();
