const AUTH_ENDPOINTS = {
    login: '/api/auth/login',
    register: '/api/auth/register'
};

const AUTH_STORAGE_KEY = 'authToken';
const AUTH_USER_KEY = 'authUser';

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('authForm');
    const messageBox = document.getElementById('authMessage');
    const page = document.body.dataset.authPage;

    if (!form || !page) {
        attachNavLoginHandler();
        return;
    }

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(form);
        const payload = Object.fromEntries(formData.entries());

        clearMessage(messageBox);
        setFormDisabled(form, true);

        try {
            const endpoint = page === 'login' ? AUTH_ENDPOINTS.login : AUTH_ENDPOINTS.register;
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Authentication failed');
            }

            setAuthState(data.token, data.user);
            showMessage(messageBox, 'success', data.message || 'Success! Redirecting...');

            setTimeout(() => {
                window.location.href = '/';
            }, 900);
        } catch (error) {
            console.error('Auth error:', error);
            showMessage(messageBox, 'error', error.message || 'Something went wrong');
        } finally {
            setFormDisabled(form, false);
        }
    });
});

function attachNavLoginHandler() {
    const loginBtn = document.getElementById('loginBtn');
    if (!loginBtn) return;

    loginBtn.addEventListener('click', () => {
        const token = localStorage.getItem(AUTH_STORAGE_KEY);
        if (token) {
            window.location.href = '/';
        } else {
            window.location.href = '/login';
        }
    });
}

function setFormDisabled(form, disabled) {
    Array.from(form.elements).forEach((element) => {
        element.disabled = disabled;
    });
}

function showMessage(box, type, text) {
    if (!box) return;

    box.textContent = text;
    box.className = `auth-message ${type}`;
    box.style.display = 'block';
}

function clearMessage(box) {
    if (!box) return;
    box.textContent = '';
    box.className = 'auth-message';
    box.style.display = 'none';
}

function setAuthState(token, user) {
    if (token) {
        localStorage.setItem(AUTH_STORAGE_KEY, token);
    }
    if (user) {
        localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
    }
}
