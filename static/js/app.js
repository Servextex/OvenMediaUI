/**
 * OvenMediaEngine Web UI - Main JavaScript Application
 * Handles API communication, authentication, and UI interactions
 */

// ===== Configuration =====
const API_BASE_URL = '/api';

// ===== Authentication =====
function getAuthToken() {
    return localStorage.getItem('access_token');
}

function getUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}

function isAuthenticated() {
    return !!getAuthToken();
}

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        // Call logout API
        apiRequest('/auth/logout', { method: 'POST' })
            .finally(() => {
                localStorage.removeItem('access_token');
                localStorage.removeItem('user');
                window.location.href = '/login';
            });
    }
}

// ===== API Request Helper =====
async function apiRequest(endpoint, options = {}) {
    const token = getAuthToken();

    const defaultHeaders = {
        'Content-Type': 'application/json'
    };

    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }

    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...(options.headers || {})
        }
    };

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

        // Handle authentication errors
        if (response.status === 401) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            window.location.href = '/login';
            throw new Error('Unauthorized');
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }

        return data;
    } catch (error) {
        console.error('API Request Error:', error);
        throw error;
    }
}

// ===== Toast Notifications =====
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast';

    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };

    const colors = {
        success: 'var(--color-accent-success)',
        error: 'var(--color-accent-error)',
        warning: 'var(--color-accent-warning)',
        info: 'var(--color-accent-primary)'
    };

    toast.innerHTML = `
        <div style="display: flex; align-items: center; gap: var(--space-md);">
            <i class="fas ${icons[type]}" style="color: ${colors[type]}; font-size: 1.25rem;"></i>
            <div style="flex: 1;">${message}</div>
            <button onclick="this.parentElement.parentElement.remove()" 
                    style="background: none; border: none; color: var(--color-text-tertiary); cursor: pointer;">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;

    container.appendChild(toast);

    // Auto remove
    setTimeout(() => {
        toast.remove();
    }, duration);
}

// ===== Modal Helper =====
function showModal(title, content, buttons = []) {
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        backdrop-filter: blur(4px);
    `;

    // Create modal
    const modal = document.createElement('div');
    modal.className = 'card';
    modal.style.cssText = `
        max-width: 500px;
        width: 90%;
        max-height: 90vh;
        overflow: auto;
        margin: var(--space-lg);
    `;

    // Modal header
    const header = document.createElement('div');
    header.className = 'card-header';
    header.innerHTML = `
        <h3 class="card-title">${title}</h3>
        <button onclick="this.closest('.card').parentElement.remove()" 
                class="btn btn-sm btn-secondary">
            <i class="fas fa-times"></i>
        </button>
    `;

    // Modal body
    const body = document.createElement('div');
    body.className = 'card-body';
    body.innerHTML = content;

    // Modal footer (if buttons provided)
    const footer = document.createElement('div');
    if (buttons.length > 0) {
        footer.style.cssText = 'display: flex; gap: var(--space-md); justify-content: flex-end; margin-top: var(--space-lg);';
        buttons.forEach(btn => {
            const button = document.createElement('button');
            button.className = `btn ${btn.class || 'btn-secondary'}`;
            button.textContent = btn.text;
            button.onclick = () => {
                if (btn.onClick) btn.onClick();
                overlay.remove();
            };
            footer.appendChild(button);
        });
    }

    modal.appendChild(header);
    modal.appendChild(body);
    if (buttons.length > 0) modal.appendChild(footer);

    overlay.appendChild(modal);
    document.body.appendChild(overlay);

    // Close on overlay click
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.remove();
        }
    });
}

// ===== Form Helper =====
function serializeForm(form) {
    const formData = new FormData(form);
    const data = {};

    for (const [key, value] of formData.entries()) {
        data[key] = value;
    }

    return data;
}

// ===== Confirmation Dialog =====
function confirmAction(message, onConfirm) {
    showModal(
        'Confirm Action',
        `<p>${message}</p>`,
        [
            { text: 'Cancel', class: 'btn-secondary' },
            {
                text: 'Confirm',
                class: 'btn-primary',
                onClick: onConfirm
            }
        ]
    );
}

// ===== Loading Indicator =====
function showLoading(element) {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    if (element) {
        element.innerHTML = '<div style="display: flex; justify-content: center; padding: var(--space-xl);"><div class="spinner"></div></div>';
    }
}

// ===== Format Helpers =====
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// ===== Page Initialization =====
document.addEventListener('DOMContentLoaded', function () {
    // Check authentication on protected pages
    const isLoginPage = window.location.pathname === '/login';

    if (!isLoginPage && !isAuthenticated()) {
        window.location.href = '/login';
        return;
    }

    // Redirect to dashboard if on login page but already authenticated
    if (isLoginPage && isAuthenticated()) {
        window.location.href = '/';
        return;
    }

    // Display user info in sidebar if exists
    const user = getUser();
    if (user) {
        const userInfo = document.getElementById('userInfo');
        if (userInfo) {
            userInfo.innerHTML = `
                <div style="padding: var(--space-md); color: var(--color-text-secondary);">
                    <i class="fas fa-user"></i> ${user.username}
                    <div style="font-size: 0.75rem; margin-top: var(--space-xs);">
                        Role: ${user.role}
                    </div>
                </div>
            `;
        }
    }
});

// ===== Global Error Handler =====
window.addEventListener('unhandledrejection', function (event) {
    console.error('Unhandled promise rejection:', event.reason);
    showToast('An unexpected error occurred', 'error');
});

// Export for use in inline scripts
window.apiRequest = apiRequest;
window.showToast = showToast;
window.showModal = showModal;
window.confirmAction = confirmAction;
window.showLoading = showLoading;
window.formatDate = formatDate;
window.formatBytes = formatBytes;
window.logout = logout;
