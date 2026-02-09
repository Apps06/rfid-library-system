// ========================================
// Library Logger - Main JavaScript
// ========================================

// Update datetime display
function updateDateTime() {
    const now = new Date();
    const options = {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    const datetimeEl = document.getElementById('datetime');
    if (datetimeEl) {
        datetimeEl.textContent = now.toLocaleDateString('en-US', options);
    }
}

// Run on load and every minute
updateDateTime();
setInterval(updateDateTime, 60000);

// ========== Toast Notifications ==========
function showToast(title, message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const icons = {
        success: '✅',
        error: '❌',
        info: 'ℹ️',
        entry: '🟢',
        exit: '🟡'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
    `;

    container.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// ========== API Helper ==========
const API = {
    async get(endpoint) {
        try {
            const response = await fetch(`/api${endpoint}`);
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            showToast('Error', 'Failed to fetch data', 'error');
            return null;
        }
    },

    async post(endpoint, data) {
        try {
            const response = await fetch(`/api${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            showToast('Error', 'Failed to send data', 'error');
            return null;
        }
    },

    async put(endpoint, data) {
        try {
            const response = await fetch(`/api${endpoint}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            showToast('Error', 'Failed to update data', 'error');
            return null;
        }
    },

    async delete(endpoint) {
        try {
            const response = await fetch(`/api${endpoint}`, {
                method: 'DELETE'
            });
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            showToast('Error', 'Failed to delete', 'error');
            return null;
        }
    }
};

// ========== Format Helpers ==========
function formatTime(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatDate(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}

function formatDateTime(isoString) {
    if (!isoString) return '';
    return `${formatDate(isoString)} ${formatTime(isoString)}`;
}

// ========== Modal Helpers ==========
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

// Close modal on overlay click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('active');
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.active').forEach(modal => {
            modal.classList.remove('active');
        });
    }
});

// ========== Dashboard Auto-Refresh ==========
let dashboardInterval = null;

function startDashboardRefresh() {
    // Refresh every 5 seconds
    dashboardInterval = setInterval(() => {
        if (typeof loadDashboardData === 'function') {
            loadDashboardData();
        }
    }, 5000);
}

function stopDashboardRefresh() {
    if (dashboardInterval) {
        clearInterval(dashboardInterval);
        dashboardInterval = null;
    }
}

// Start refresh if on dashboard page
if (window.location.pathname === '/' || window.location.pathname === '/dashboard') {
    startDashboardRefresh();
}

// ========== Form Validation ==========
function validateForm(formId, rules) {
    const form = document.getElementById(formId);
    if (!form) return false;

    let isValid = true;

    for (const [fieldName, fieldRules] of Object.entries(rules)) {
        const field = form.querySelector(`[name="${fieldName}"]`);
        if (!field) continue;

        const value = field.value.trim();

        if (fieldRules.required && !value) {
            showFieldError(field, `${fieldName} is required`);
            isValid = false;
        } else if (fieldRules.minLength && value.length < fieldRules.minLength) {
            showFieldError(field, `Minimum ${fieldRules.minLength} characters required`);
            isValid = false;
        } else {
            clearFieldError(field);
        }
    }

    return isValid;
}

function showFieldError(field, message) {
    field.style.borderColor = 'var(--danger)';

    let errorEl = field.parentNode.querySelector('.field-error');
    if (!errorEl) {
        errorEl = document.createElement('div');
        errorEl.className = 'field-error';
        errorEl.style.color = 'var(--danger)';
        errorEl.style.fontSize = '12px';
        errorEl.style.marginTop = '4px';
        field.parentNode.appendChild(errorEl);
    }
    errorEl.textContent = message;
}

function clearFieldError(field) {
    field.style.borderColor = '';
    const errorEl = field.parentNode.querySelector('.field-error');
    if (errorEl) errorEl.remove();
}

// ========== Utility ==========
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

console.log('📚 Library Logger initialized');
