const loginForm = document.getElementById('loginForm');
const loginError = document.getElementById('loginError');
const submitBtn = document.getElementById('submitBtn');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');

let isRedirecting = false;

function showError(message) {
    loginError.textContent = message;
    loginError.classList.remove('hidden');
    setTimeout(() => loginError.classList.add('hidden'), 5000);
}

function hideError() {
    loginError.classList.add('hidden');
}

function setLoading(isLoading) {
    submitBtn.disabled = isLoading;
    submitBtn.textContent = isLoading ? 'Вход...' : 'Войти';
    submitBtn.style.opacity = isLoading ? '0.7' : '1';
}

function validateForm() {
    const username = usernameInput.value.trim();
    const password = passwordInput.value.trim();
    if (!username) { showError('Введите имя пользователя'); usernameInput.focus(); return false; }
    if (!password) { showError('Введите пароль'); passwordInput.focus(); return false; }
    return true;
}

async function handleLogin(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData,
            credentials: 'same-origin'
        });

        const data = await response.json();

        if (response.ok) {
            localStorage.setItem('user', JSON.stringify({
                username: data.username,
                role: data.role
            }));
            isRedirecting = true;
            window.location.href = '/';
        } else {
            showError(data.detail || 'Неверное имя пользователя или пароль');
            setLoading(false);
            passwordInput.value = '';
            passwordInput.focus();
        }
    } catch (error) {
        console.error('Network error:', error);
        showError('Ошибка сети. Проверьте подключение к серверу.');
        setLoading(false);
    }
}

async function onSubmit(event) {
    event.preventDefault();
    hideError();
    if (!validateForm()) return;
    setLoading(true);
    await handleLogin(usernameInput.value.trim(), passwordInput.value);
}

async function checkAlreadyLoggedIn() {
    try {
        const response = await fetch('/api/auth/me', { credentials: 'same-origin' });
        if (response.ok && !isRedirecting) {
            const user = await response.json();

            localStorage.setItem('user', JSON.stringify({
                username: user.username,
                role: user.role
            }));
            isRedirecting = true;
            window.location.replace('/');
        }
    } catch (error) {
        // skip
    }
}

function addInputEffects() {
    [usernameInput, passwordInput].forEach(input => {
        input.addEventListener('input', () => {
            hideError();
            input.style.borderColor = '';
        });
        input.addEventListener('focus', () => {
            input.parentElement.style.transform = 'scale(1.02)';
            input.parentElement.style.transition = 'transform 0.2s ease';
        });
        input.addEventListener('blur', () => {
            input.parentElement.style.transform = 'scale(1)';
        });
    });
}

function addAnimationEffect() {
    const card = document.querySelector('.auth-card');
    if (card) {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100);
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    await checkAlreadyLoggedIn();

    if (isRedirecting) return;

    addInputEffects();
    addAnimationEffect();

    loginForm?.addEventListener('submit', onSubmit);
    [usernameInput, passwordInput].forEach(input => {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !submitBtn.disabled) {
                e.preventDefault();
                loginForm.dispatchEvent(new Event('submit'));
            }
        });
    });

    setTimeout(() => usernameInput.focus(), 300);
});
