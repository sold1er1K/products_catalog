const App = {
    user: null, // { username, role }
    categories: [],
    currentView: 'catalog',
    catalog: {
        page: 0,
        limit: 10,
        total: 0,
        search: '',
        categoryId: null,
        searchTimer: null,
    },
};

async function api(method, path, body = null) {
    const opts = {
        method,
        credentials: 'same-origin',
        headers: {},
    };
    if (body) {
        opts.headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(body);
    }
    const resp = await fetch(path, opts);
    if (resp.status === 401) {
        localStorage.removeItem('user');
        window.location.replace('/login');
        return null;
    }
    if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: 'Ошибка сервера' }));
        throw new Error(err.detail || 'Ошибка сервера');
    }
    if (resp.status === 204) return null;
    return resp.json();
}

const GET    = (p)    => api('GET',    p);
const POST   = (p, b) => api('POST',   p, b);
const PATCH  = (p, b) => api('PATCH',  p, b);
const DELETE = (p)    => api('DELETE', p);




function fmt(date) {
    return new Date(date).toLocaleString('ru-RU', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}
function fmtPrice(n) {
    return Number(n).toLocaleString('ru-RU', { minimumFractionDigits: 2 });
}
function esc(str) {
    return String(str ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function $(id) { return document.getElementById(id); }

function toast(msg, type = 'success') {
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => el.classList.add('toast-show'), 10);
    setTimeout(() => { el.classList.remove('toast-show'); setTimeout(() => el.remove(), 300); }, 3000);
}



function openModal(id)  { $(id).classList.remove('hidden'); document.body.style.overflow = 'hidden'; }
function closeModal(id) { $(id).classList.add('hidden');    document.body.style.overflow = ''; }

document.addEventListener('click', e => {
    const btn = e.target.closest('[data-close]');
    if (btn) closeModal(btn.dataset.close);
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.add('hidden');
        document.body.style.overflow = '';
    }
});



function confirm(text) {
    return new Promise(resolve => {
        $('confirmText').textContent = text;
        openModal('confirmModal');
        const ok     = $('confirmOk');
        const cancel = $('confirmCancel');
        function cleanup(val) {
            closeModal('confirmModal');
            ok.replaceWith(ok.cloneNode(true));
            cancel.replaceWith(cancel.cloneNode(true));
            resolve(val);
        }
        $('confirmOk').addEventListener('click',     () => cleanup(true),  { once: true });
        $('confirmCancel').addEventListener('click', () => cleanup(false), { once: true });
    });
}


function showView(name) {
    App.currentView = name;
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    $(`view${name.charAt(0).toUpperCase() + name.slice(1)}`)?.classList.add('active');
    document.querySelector(`.nav-btn[data-view="${name}"]`)?.classList.add('active');

    if (name === 'catalog')    loadProducts();
    if (name === 'categories') loadCategories();
    if (name === 'users')      loadUsers();
    if (name === 'logs')       loadLogs();
}


async function init() {
    try {
        const resp = await fetch('/api/auth/me', { credentials: 'same-origin' });
        if (!resp.ok) { window.location.replace('/login'); return; }
        App.user = await resp.json();
    } catch { window.location.replace('/login'); return; }

    const role = App.user.role;

    $('userBadge').textContent = `${App.user.username} · ${roleLabel(role)}`;
    $('userBadge').className = `user-badge badge-${role}`;

    if (role === 'admin') {
        $('navUsers').classList.remove('hidden');
        $('navLogs').classList.remove('hidden');
    }
    if (role === 'advanced' || role === 'admin') {
        $('addCategoryBtn')?.classList.remove('hidden');
    }

    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => showView(btn.dataset.view));
    });

    $('logoutBtn').addEventListener('click', async () => {
        await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' });
        localStorage.removeItem('user');
        window.location.replace('/login');
    });

    $('searchInput').addEventListener('input', e => {
        clearTimeout(App.catalog.searchTimer);
        App.catalog.searchTimer = setTimeout(() => {
            App.catalog.search = e.target.value.trim();
            App.catalog.page = 0;
            loadProducts();
        }, 350);
    });

    $('categoryFilter').addEventListener('change', e => {
        App.catalog.categoryId = e.target.value || null;
        App.catalog.page = 0;
        loadProducts();
    });

    $('addProductBtn').addEventListener('click', () => openProductModal(null));
    $('addCategoryBtn')?.addEventListener('click', () => openCategoryModal(null));
    $('addUserBtn')?.addEventListener('click', () => openUserModal(null));
    $('refreshLogsBtn')?.addEventListener('click', loadLogs);

    $('productForm').addEventListener('submit',  saveProduct);
    $('categoryForm').addEventListener('submit', saveCategory);
    $('userForm').addEventListener('submit',     saveUser);

    await loadCategoryOptions();

    if (role === 'advanced' || role === 'admin') {
        $('thSpecial')?.classList.remove('hidden');
    }

    showView('catalog');
    document.getElementById('appShell').style.display = '';
}

function roleLabel(role) {
    return { admin: 'Администратор', advanced: 'Продвинутый', simple: 'Пользователь' }[role] ?? role;
}

async function loadProducts() {
    const body = $('productsBody');
    body.innerHTML = `<tr><td colspan="8" class="loading-cell">Загрузка…</td></tr>`;

    const { page, limit, search, categoryId } = App.catalog;
    const skip = page * limit;
    let url = `/api/products/?skip=${skip}&limit=${limit}`;
    if (search)     url += `&search=${encodeURIComponent(search)}`;
    if (categoryId) url += `&category_id=${categoryId}`;

    try {
        const data = await GET(url);
        if (!data) return;
        App.catalog.total = data.total;
        renderProducts(data.items);
        renderPagination();
    } catch (e) {
        body.innerHTML = `<tr><td colspan="8" class="loading-cell" style="color:var(--danger)">${esc(e.message)}</td></tr>`;
    }
}

function renderProducts(items) {
    const role = App.user.role;
    const showSpecial = role === 'advanced' || role === 'admin';
    const canDelete   = role === 'advanced' || role === 'admin';
    const body = $('productsBody');

    if (!items.length) {
        body.innerHTML = `<tr><td colspan="8" class="loading-cell">Нет товаров</td></tr>`;
        return;
    }

    body.innerHTML = items.map((p, i) => `
        <tr>
            <td>${App.catalog.page * App.catalog.limit + i + 1}</td>
            <td><strong>${esc(p.name)}</strong></td>
            <td><span class="badge badge-cat">${esc(p.category_name ?? '—')}</span></td>
            <td class="truncate">${esc(p.description ?? '—')}</td>
            <td class="price-cell">
                ${fmtPrice(p.price)}
                <span class="price-star" title="Курс USD" data-price="${p.price}">*</span>
            </td>
            <td>${esc(p.note_general ?? '—')}</td>
            ${showSpecial ? `<td>${esc(p.note_special ?? '—')}</td>` : ''}
            <td>
                <div class="actions">
                    <button class="btn-icon" title="Редактировать" onclick="openProductModal(${p.id})">✏️</button>
                    ${canDelete ? `<button class="btn-icon btn-icon-danger" title="Удалить" onclick="deleteProduct(${p.id}, '${esc(p.name)}')">🗑️</button>` : ''}
                </div>
            </td>
        </tr>
    `).join('');

    body.querySelectorAll('.price-star').forEach(star => {
        star.addEventListener('click', () => showCurrencyModal(parseFloat(star.dataset.price)));
    });
}

function renderPagination() {
    const { page, limit, total } = App.catalog;
    const pages = Math.ceil(total / limit);
    const el = $('pagination');
    if (pages <= 1) { el.innerHTML = ''; return; }

    let html = '';
    for (let i = 0; i < pages; i++) {
        html += `<button class="page-btn${i === page ? ' active' : ''}" data-page="${i}">${i + 1}</button>`;
    }
    el.innerHTML = html;
    el.querySelectorAll('.page-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            App.catalog.page = parseInt(btn.dataset.page);
            loadProducts();
        });
    });
}

async function showCurrencyModal(price) {
    const body = $('currencyModalBody');
    body.innerHTML = '<div class="loading-cell">Загрузка курса…</div>';
    openModal('currencyModal');
    try {
        const data = await GET(`/api/currency/usd-rate?price=${price}`);
        body.innerHTML = `
            <div class="currency-info">
                <div class="currency-row">
                    <span class="currency-label">Курс НБ РБ (BYN за 1 USD)</span>
                    <span class="currency-value">${data.rate.toFixed(4)}</span>
                </div>
                <div class="currency-row">
                    <span class="currency-label">Стоимость товара (BYN)</span>
                    <span class="currency-value">${fmtPrice(price)}</span>
                </div>
                <div class="currency-row">
                    <span class="currency-label">Стоимость в USD</span>
                    <span class="currency-value" style="color:var(--success)">$ ${data.price_usd.toFixed(2)}</span>
                </div>
            </div>`;
    } catch (e) {
        body.innerHTML = `<div class="loading-cell" style="color:var(--danger)">Ошибка: ${esc(e.message)}</div>`;
    }
}

async function openProductModal(id) {
    const role = App.user.role;
    $('productModalTitle').textContent = id ? 'Редактировать товар' : 'Добавить товар';
    $('productId').value = id ?? '';
    $('productFormError').classList.add('hidden');

    const nsGroup = $('noteSpecialGroup');
    if (role === 'advanced' || role === 'admin') {
        nsGroup.classList.remove('hidden');
    } else {
        nsGroup.classList.add('hidden');
    }

    const sel = $('pCategory');
    sel.innerHTML = App.categories.map(c => `<option value="${c.id}">${esc(c.name)}</option>`).join('');

    if (id) {
        try {
            const p = await GET(`/api/products/${id}`);
            $('pName').value        = p.name ?? '';
            $('pDescription').value = p.description ?? '';
            $('pPrice').value       = p.price ?? '';
            $('pNoteGeneral').value = p.note_general ?? '';
            $('pNoteSpecial').value = p.note_special ?? '';
            sel.value = p.category_id;
        } catch (e) { toast(e.message, 'error'); return; }
    } else {
        $('productForm').reset();
    }
    openModal('productModal');
}

async function saveProduct(e) {
    e.preventDefault();
    const errEl = $('productFormError');
    errEl.classList.add('hidden');
    const btn = $('productSaveBtn');
    btn.disabled = true;

    const id   = $('productId').value;
    const role = App.user.role;
    const body = {
        name:         $('pName').value.trim(),
        category_id:  parseInt($('pCategory').value),
        description:  $('pDescription').value.trim() || null,
        price:        parseFloat($('pPrice').value),
        note_general: $('pNoteGeneral').value.trim() || null,
    };
    if (role === 'advanced' || role === 'admin') {
        body.note_special = $('pNoteSpecial').value.trim() || null;
    }

    try {
        if (id) {
            await PATCH(`/api/products/${id}`, body);
            toast('Товар обновлён');
        } else {
            await POST('/api/products/', body);
            toast('Товар добавлен');
        }
        closeModal('productModal');
        loadProducts();
    } catch (e) {
        errEl.textContent = e.message;
        errEl.classList.remove('hidden');
    } finally {
        btn.disabled = false;
    }
}

async function deleteProduct(id, name) {
    if (!await confirm(`Удалить товар «${name}»?`)) return;
    try {
        await DELETE(`/api/products/${id}`);
        toast('Товар удалён');
        loadProducts();
    } catch (e) { toast(e.message, 'error'); }
}

async function loadCategoryOptions() {
    try {
        App.categories = await GET('/api/categories/') ?? [];
        const sel = $('categoryFilter');
        sel.innerHTML = '<option value="">Все категории</option>' +
            App.categories.map(c => `<option value="${c.id}">${esc(c.name)}</option>`).join('');
    } catch { /* skip */ }
}

async function loadCategories() {
    const grid = $('categoriesGrid');
    grid.innerHTML = '<div class="loading-cell">Загрузка…</div>';
    try {
        const cats = await GET('/api/categories/') ?? [];
        App.categories = cats;
        const role = App.user.role;
        const canEdit = role === 'advanced' || role === 'admin';

        if (!cats.length) { grid.innerHTML = '<div class="loading-cell">Нет категорий</div>'; return; }

        grid.innerHTML = cats.map(c => `
            <div class="category-card">
                <div class="category-card-header">
                    <div>
                        <h3>${esc(c.name)}</h3>
                        <p class="cat-desc">${esc(c.description ?? '—')}</p>
                    </div>
                    ${canEdit ? `
                    <div class="cat-actions">
                        <button class="btn-icon" title="Редактировать" onclick="openCategoryModal(${c.id})">✏️</button>
                        <button class="btn-icon btn-icon-danger" title="Удалить" onclick="deleteCategory(${c.id}, '${esc(c.name)}')">🗑️</button>
                    </div>` : ''}
                </div>
                <p class="cat-count">Создана: ${fmt(c.created_at)}</p>
            </div>
        `).join('');
    } catch (e) {
        grid.innerHTML = `<div class="loading-cell" style="color:var(--danger)">${esc(e.message)}</div>`;
    }
}

async function openCategoryModal(id) {
    $('categoryModalTitle').textContent = id ? 'Редактировать категорию' : 'Добавить категорию';
    $('categoryId').value = id ?? '';
    $('categoryFormError').classList.add('hidden');
    $('categoryForm').reset();
    if (id) {
        const cat = App.categories.find(c => c.id === id);
        if (cat) { $('catName').value = cat.name; $('catDescription').value = cat.description ?? ''; }
    }
    openModal('categoryModal');
}

async function saveCategory(e) {
    e.preventDefault();
    const errEl = $('categoryFormError');
    errEl.classList.add('hidden');
    const id   = $('categoryId').value;
    const body = { name: $('catName').value.trim(), description: $('catDescription').value.trim() || null };
    try {
        if (id) { await PATCH(`/api/categories/${id}`, body); toast('Категория обновлена'); }
        else    { await POST('/api/categories/', body);        toast('Категория добавлена'); }
        closeModal('categoryModal');
        await loadCategoryOptions();
        loadCategories();
    } catch (e) { errEl.textContent = e.message; errEl.classList.remove('hidden'); }
}

async function deleteCategory(id, name) {
    if (!await confirm(`Удалить категорию «${name}»?\nВсе товары этой категории будут удалены.`)) return;
    try {
        await DELETE(`/api/categories/${id}`);
        toast('Категория удалена');
        await loadCategoryOptions();
        loadCategories();
    } catch (e) { toast(e.message, 'error'); }
}

async function loadUsers() {
    const body = $('usersBody');
    body.innerHTML = `<tr><td colspan="7" class="loading-cell">Загрузка…</td></tr>`;
    try {
        const users = await GET('/api/users/') ?? [];
        if (!users.length) { body.innerHTML = `<tr><td colspan="7" class="loading-cell">Нет пользователей</td></tr>`; return; }
        body.innerHTML = users.map(u => `
            <tr>
                <td>${u.id}</td>
                <td><strong>${esc(u.username)}</strong></td>
                <td>${esc(u.email)}</td>
                <td><span class="badge badge-${u.role}">${roleLabel(u.role)}</span></td>
                <td><span class="badge ${u.is_active ? 'badge-active' : 'badge-blocked'}">${u.is_active ? 'Активен' : 'Заблокирован'}</span></td>
                <td>${fmt(u.created_at)}</td>
                <td>
                    <div class="actions">
                        <button class="btn-icon" title="Редактировать" onclick="openUserModal(${u.id})">✏️</button>
                        <button class="btn-icon" title="Сменить пароль" onclick="openPasswordModal(${u.id})">🔑</button>
                        <button class="btn-icon btn-icon-danger" title="Удалить" onclick="deleteUser(${u.id}, '${esc(u.username)}')">🗑️</button>
                    </div>
                </td>
            </tr>
        `).join('');
    } catch (e) {
        body.innerHTML = `<tr><td colspan="7" class="loading-cell" style="color:var(--danger)">${esc(e.message)}</td></tr>`;
    }
}

async function openUserModal(id) {
    $('userModalTitle').textContent = id ? 'Редактировать пользователя' : 'Добавить пользователя';
    $('userId').value = id ?? '';
    $('userFormError').classList.add('hidden');
    $('userForm').reset();

    const isNew = !id;
    $('usernameGroup').style.display = isNew ? '' : 'none';
    $('emailGroup').style.display    = isNew ? '' : 'none';
    $('passwordGroup').style.display = isNew ? '' : 'none';
    $('activeGroup').style.display   = isNew ? 'none' : '';

    if (id) {
        try {
            const users = await GET('/api/users/');
            const u = users?.find(u => u.id === id);
            if (u) {
                $('uRole').value   = u.role;
                $('uActive').checked = u.is_active;
            }
        } catch (e) { toast(e.message, 'error'); return; }
    }
    openModal('userModal');
}

async function saveUser(e) {
    e.preventDefault();
    const errEl = $('userFormError');
    errEl.classList.add('hidden');
    const id = $('userId').value;

    try {
        if (id) {
            await PATCH(`/api/users/${id}`, {
                role:      $('uRole').value,
                is_active: $('uActive').checked,
            });
            toast('Пользователь обновлён');
        } else {
            await POST('/api/users/', {
                username: $('uUsername').value.trim(),
                email:    $('uEmail').value.trim(),
                password: $('uPassword').value,
                role:     $('uRole').value,
            });
            toast('Пользователь создан');
        }
        closeModal('userModal');
        loadUsers();
    } catch (e) { errEl.textContent = e.message; errEl.classList.remove('hidden'); }
}

async function openPasswordModal(userId) {
    const pwd = window.prompt('Введите новый пароль (минимум 6 символов):');
    if (!pwd) return;
    if (pwd.length < 6) { toast('Пароль слишком короткий', 'error'); return; }
    try {
        await POST(`/api/users/${userId}/change-password`, { new_password: pwd });
        toast('Пароль изменён');
    } catch (e) { toast(e.message, 'error'); }
}

async function deleteUser(id, username) {
    if (!await confirm(`Удалить пользователя «${username}»?`)) return;
    try {
        await DELETE(`/api/users/${id}`);
        toast('Пользователь удалён');
        loadUsers();
    } catch (e) { toast(e.message, 'error'); }
}

async function loadLogs() {
    const body = $('logsBody');
    body.innerHTML = `<tr><td colspan="7" class="loading-cell">Загрузка…</td></tr>`;
    try {
        const logs = await GET('/api/logs/?limit=200') ?? [];
        if (!logs.length) { body.innerHTML = `<tr><td colspan="7" class="loading-cell">Логов нет</td></tr>`; return; }
        body.innerHTML = logs.map(l => `
            <tr>
                <td style="white-space:nowrap;font-size:.8rem">${fmt(l.created_at)}</td>
                <td>${esc(l.username ?? '—')}</td>
                <td><span class="log-action log-${l.action}">${l.action}</span></td>
                <td>${esc(l.entity)}</td>
                <td>${l.entity_id ?? '—'}</td>
                <td class="truncate">${esc(l.detail ?? '—')}</td>
                <td>${esc(l.ip_address ?? '—')}</td>
            </tr>
        `).join('');
    } catch (e) {
        body.innerHTML = `<tr><td colspan="7" class="loading-cell" style="color:var(--danger)">${esc(e.message)}</td></tr>`;
    }
}

// script start
document.addEventListener('DOMContentLoaded', init);