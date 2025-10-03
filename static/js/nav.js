const AUTH_TOKEN_KEY = 'authToken';
const AUTH_USER_KEY = 'authUser';

document.addEventListener('DOMContentLoaded', () => {
    const loginBtn = document.getElementById('loginBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const historyBtn = document.getElementById('historyBtn');
    const navHomeLinks = document.querySelectorAll('[data-nav="home"]');
    const navAboutLinks = document.querySelectorAll('[data-nav="about"]');

    const token = getToken();
    toggleAuthControls(token);

    if (loginBtn) {
        loginBtn.addEventListener('click', (event) => {
            event.preventDefault();
            window.location.href = '/login';
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            clearAuthState();
            window.location.href = '/login';
        });
    }

    if (historyBtn) {
        historyBtn.addEventListener('click', () => {
            const currentToken = getToken();
            if (!currentToken) {
                window.location.href = '/login';
                return;
            }

            window.location.href = '/account';
        });
    }

    navHomeLinks.forEach((link) => {
        if (window.location.pathname === '/') {
            link.classList.add('active');
        }
    });

    navAboutLinks.forEach((link) => {
        link.addEventListener('click', (event) => {
            const aboutSection = document.getElementById('about');
            if (aboutSection) {
                event.preventDefault();
                aboutSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});

function toggleAuthControls(token) {
    const loginBtn = document.getElementById('loginBtn');
    const logoutBtn = document.getElementById('logoutBtn');

    if (token) {
        if (loginBtn) {
            loginBtn.style.display = 'none';
        }
        if (logoutBtn) {
            logoutBtn.style.display = 'inline-flex';
        }
    } else {
        if (loginBtn) {
            loginBtn.style.display = 'inline-flex';
        }
        if (logoutBtn) {
            logoutBtn.style.display = 'none';
        }
    }
}

function getToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
}

function clearAuthState() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
}
