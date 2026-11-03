// Global JavaScript Helpers for AI UPI Fraud Detection System

const API_BASE = '/api';

function getCookie(name) {
    let cookieValue = null;

    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

window.apiCall = async function(endpoint, method = 'GET', data = null) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    };
    const csrftoken = getCookie('csrftoken');
    if (csrftoken) {
        headers['X-CSRFToken'] = csrftoken;
    }
    const options = {
        method,
        headers
    };
    if (data) {
        options.body = JSON.stringify(data);
    }
    const res = await fetch(url, options);
    const contentType = res.headers.get('content-type');
    let responseData = null;
    if (contentType && contentType.includes('application/json')) {
        responseData = await res.json();
    } else {
        responseData = await res.text();
    }
    if (!res.ok) {
        let msg = 'Request Failed';
        if (responseData) {
            if (typeof responseData === 'string') {
                msg = responseData;
            } else if (responseData.error) {
                msg = responseData.error;
            } else if (responseData.detail) {
                msg = responseData.detail;
            } else if (responseData.non_field_errors) {
                msg = Array.isArray(responseData.non_field_errors) 
                    ? responseData.non_field_errors.join(', ') 
                    : responseData.non_field_errors;
            } else if (typeof responseData === 'object') {
                const errors = [];
                for (const key in responseData) {
                    if (Array.isArray(responseData[key])) {
                        errors.push(responseData[key].join(', '));
                    } else if (typeof responseData[key] === 'string') {
                        errors.push(responseData[key]);
                    }
                }
                if (errors.length > 0) {
                    msg = errors.join('; ');
                }
            }
        }
        throw new Error(msg);
    }
    return responseData;
};


window.showToast = function(message, type = 'info', title = '') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'pointer-events-auto p-4 rounded-xl shadow-lg transition-all duration-300 transform translate-y-2 opacity-0 flex items-start gap-3 bg-white border border-slate-200 text-slate-900';

    let iconName = 'info';
    let borderColor = 'border-blue-200';
    let iconBg = 'bg-blue-50 text-blue-600';

    if (type === 'success') {
        iconName = 'check-circle';
        borderColor = 'border-emerald-200';
        iconBg = 'bg-emerald-50 text-emerald-600';
    } else if (type === 'warning') {
        iconName = 'alert-triangle';
        borderColor = 'border-amber-200';
        iconBg = 'bg-amber-50 text-amber-600';
    } else if (type === 'error' || type === 'danger') {
        iconName = 'alert-octagon';
        borderColor = 'border-rose-200';
        iconBg = 'bg-rose-50 text-rose-600';
    }

    toast.classList.add(borderColor);
    toast.innerHTML = `
        <div class="p-2 rounded-lg ${iconBg} shrink-0">
            <i data-lucide="${iconName}" class="w-5 h-5"></i>
        </div>
        <div class="flex-1 text-sm">
            ${title ? `<div class="font-semibold text-slate-900 mb-0.5">${title}</div>` : ''}
            <div class="text-slate-600 leading-snug">${message}</div>
        </div>
        <button class="text-slate-400 hover:text-slate-600 transition-colors p-1" onclick="this.parentElement.remove()">
            <i data-lucide="x" class="w-4 h-4"></i>
        </button>
    `;

    container.appendChild(toast);
    if (window.lucide) window.lucide.createIcons();

    setTimeout(() => {
        toast.classList.remove('translate-y-2', 'opacity-0');
    }, 10);

    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
};

window.showModal = function({ title, bodyHTML, primaryText = 'Confirm', onPrimary = null, secondaryText = 'Cancel', onSecondary = null }) {
    const container = document.getElementById('modal-container');
    if (!container) return;

    container.innerHTML = `
        <div class="bg-white max-w-lg w-full rounded-xl border border-slate-200 overflow-hidden shadow-xl animate-fade-in">
            <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
                <h3 class="text-lg font-bold text-slate-900 flex items-center gap-2">
                    ${title}
                </h3>
                <button id="modal-close-btn" class="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors">
                    <i data-lucide="x" class="w-5 h-5"></i>
                </button>
            </div>
            <div class="p-6 space-y-4 max-h-[75vh] overflow-y-auto text-slate-700 text-sm">
                ${bodyHTML}
            </div>
            <div class="px-6 py-4 border-t border-slate-100 bg-slate-50 flex justify-end gap-3">
                ${secondaryText ? `<button id="modal-secondary-btn" class="px-4 py-2 text-sm font-medium text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-300 rounded-lg transition-all">${secondaryText}</button>` : ''}
                ${primaryText ? `<button id="modal-primary-btn" class="px-5 py-2 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-all shadow-sm">${primaryText}</button>` : ''}
            </div>
        </div>
    `;

    container.classList.remove('hidden');
    container.classList.add('flex');
    if (window.lucide) window.lucide.createIcons();

    const closeModal = () => {
        container.classList.add('hidden');
        container.classList.remove('flex');
        container.innerHTML = '';
    };

    document.getElementById('modal-close-btn')?.addEventListener('click', () => {
        closeModal();
        if (onSecondary) onSecondary();
    });

    document.getElementById('modal-secondary-btn')?.addEventListener('click', () => {
        closeModal();
        if (onSecondary) onSecondary();
    });

    document.getElementById('modal-primary-btn')?.addEventListener('click', async () => {
        if (onPrimary) {
            const shouldClose = await onPrimary();
            if (shouldClose !== false) closeModal();
        } else {
            closeModal();
        }
    });
};

window.closeModal = function() {
    const container = document.getElementById('modal-container');
    if (container) {
        container.classList.add('hidden');
        container.classList.remove('flex');
        container.innerHTML = '';
    }
};

document.addEventListener('DOMContentLoaded', async () => {
    if (window.lucide) window.lucide.createIcons();

    // Dynamically fetch and update header user details if header elements exist
    const headerAvatar = document.getElementById('header-user-avatar');
    const headerName = document.getElementById('header-user-name');
    if (headerAvatar || headerName) {
        try {
            const userData = await apiCall('/auth/profile/');
            if (userData && userData.username) {
                const displayName = userData.full_name || userData.username;
                const initial = displayName.charAt(0).toUpperCase();
                if (headerName) headerName.textContent = displayName;
                if (headerAvatar) headerAvatar.textContent = initial;
            }
        } catch (e) {
            // Unauthenticated or guest mode, default template values remain
        }
    }
});

