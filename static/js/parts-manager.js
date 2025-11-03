// Управление запчастями и категориями - Felix Hub
let allParts = [];
let allCategories = [];

// Переключение вкладок
function switchTab(tab, event) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    
    if (tab === 'parts') {
        document.getElementById('partsTab').style.display = 'block';
        document.getElementById('categoriesTab').style.display = 'none';
        loadParts();
    } else {
        document.getElementById('partsTab').style.display = 'none';
        document.getElementById('categoriesTab').style.display = 'block';
        loadCategories();
    }
}

// Загрузка категорий
async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        if (!response.ok) throw new Error('Ошибка загрузки категорий');
        
        allCategories = await response.json();
        updateStats();
        renderCategories();
        updateCategoryFilters();
    } catch (error) {
        console.error(error);
        showAlert('Ошибка загрузки категорий: ' + error.message, 'error');
    }
}

// Отображение категорий
function renderCategories() {
    const container = document.getElementById('categoriesContainer');
    
    if (allCategories.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div style="font-size: 64px;">📁</div>
                <h3>Категорий нет</h3>
                <p>Добавьте первую категорию или импортируйте каталог</p>
            </div>
        `;
        return;
    }
    
    let html = `
        <table>
            <thead>
                <tr>
                    <th style="width: 60px;">ID</th>
                    <th>Название</th>
                    <th style="width: 100px;">Запчастей</th>
                    <th style="width: 100px;">Активных</th>
                    <th style="width: 100px;">Порядок</th>
                    <th style="width: 120px;">Статус</th>
                    <th style="width: 300px;">Действия</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    allCategories.forEach(cat => {
        html += `
            <tr class="${!cat.is_active ? 'inactive' : ''}">
                <td><strong>#${cat.id}</strong></td>
                <td><strong>${cat.name}</strong></td>
                <td>${cat.parts_count || 0}</td>
                <td>${cat.active_parts_count || 0}</td>
                <td>${cat.sort_order}</td>
                <td>
                    <span class="status-badge ${cat.is_active ? 'status-active' : 'status-inactive'}">
                        ${cat.is_active ? 'Активна' : 'Неактивна'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-primary btn-sm" onclick="editCategory(${cat.id})">
                        ✏️ Редактировать
                    </button>
                    <button class="btn btn-warning btn-sm" onclick="toggleCategoryActive(${cat.id})">
                        ${cat.is_active ? '🔒' : '🔓'}
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="deleteCategory(${cat.id})">
                        🗑️
                    </button>
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

// Загрузка запчастей
async function loadParts() {
    try {
        const statusFilter = document.getElementById('statusFilter').value;
        const activeOnly = statusFilter === 'active' ? 'true' : 'false';
        
        const response = await fetch(`/api/parts?active_only=${activeOnly}`);
        if (!response.ok) throw new Error('Ошибка загрузки запчастей');
        
        allParts = await response.json();
        
        if (statusFilter === 'inactive') {
            const allResponse = await fetch('/api/parts?active_only=false');
            const allData = await allResponse.json();
            allParts = allData.filter(p => !p.is_active);
        }
        
        updateStats();
        renderParts();
    } catch (error) {
        console.error(error);
        showAlert('Ошибка загрузки запчастей: ' + error.message, 'error');
    }
}

// Отображение запчастей
function renderParts() {
    const container = document.getElementById('partsContainer');
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const categoryFilter = document.getElementById('categoryFilter').value;
    
    let filteredParts = allParts;
    
    if (categoryFilter !== 'all') {
        filteredParts = filteredParts.filter(p => p.category === categoryFilter);
    }
    
    if (searchTerm) {
        filteredParts = filteredParts.filter(p => 
            p.name.toLowerCase().includes(searchTerm) ||
            p.category.toLowerCase().includes(searchTerm)
        );
    }
    
    if (filteredParts.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div style="font-size: 64px;">📦</div>
                <h3>Запчасти не найдены</h3>
                <p>Попробуйте изменить фильтры</p>
            </div>
        `;
        return;
    }
    
    let html = `
        <table>
            <thead>
                <tr>
                    <th style="width: 60px;">ID</th>
                    <th>Название</th>
                    <th style="width: 200px;">Категория</th>
                    <th style="width: 100px;">Порядок</th>
                    <th style="width: 120px;">Статус</th>
                    <th style="width: 300px;">Действия</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    filteredParts.forEach(part => {
        html += `
            <tr class="${!part.is_active ? 'inactive' : ''}">
                <td><strong>#${part.id}</strong></td>
                <td>${part.name}</td>
                <td>📁 ${part.category}</td>
                <td>${part.sort_order}</td>
                <td>
                    <span class="status-badge ${part.is_active ? 'status-active' : 'status-inactive'}">
                        ${part.is_active ? 'Активна' : 'Неактивна'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-primary btn-sm" onclick="editPart(${part.id})">
                        ✏️ Редактировать
                    </button>
                    <button class="btn btn-warning btn-sm" onclick="togglePartActive(${part.id})">
                        ${part.is_active ? '🔒' : '🔓'}
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="deletePart(${part.id})">
                        🗑️
                    </button>
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

// Обновление фильтров категорий
function updateCategoryFilters() {
    const categoryFilter = document.getElementById('categoryFilter');
    const partCategory = document.getElementById('partCategory');
    
    const currentValue = categoryFilter.value;
    categoryFilter.innerHTML = '<option value="all">Все категории</option>';
    
    allCategories
        .filter(c => c.is_active)
        .forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.name;
            option.textContent = cat.name;
            if (cat.name === currentValue) option.selected = true;
            categoryFilter.appendChild(option);
        });
    
    partCategory.innerHTML = '<option value="">Выберите категорию</option>';
    allCategories
        .filter(c => c.is_active)
        .forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.name;
            option.textContent = cat.name;
            partCategory.appendChild(option);
        });
}

// Обновление статистики
function updateStats() {
    document.getElementById('totalCategories').textContent = allCategories.length;
    document.getElementById('totalParts').textContent = allParts.length;
    document.getElementById('activeParts').textContent = allParts.filter(p => p.is_active).length;
}

// === КАТЕГОРИИ ===
function openAddCategoryModal() {
    document.getElementById('categoryModalTitle').textContent = 'Добавить категорию';
    document.getElementById('categoryForm').reset();
    document.getElementById('categoryId').value = '';
    document.getElementById('categoryIsActive').checked = true;
    document.getElementById('categoryModal').classList.add('active');
}

async function editCategory(id) {
    try {
        const response = await fetch(`/api/admin/categories/${id}`);
        const category = await response.json();
        
        document.getElementById('categoryModalTitle').textContent = 'Редактировать категорию';
        document.getElementById('categoryId').value = category.id;
        document.getElementById('categoryName').value = category.name;
        document.getElementById('categorySortOrder').value = category.sort_order;
        document.getElementById('categoryIsActive').checked = category.is_active;
        
        document.getElementById('categoryModal').classList.add('active');
    } catch (error) {
        showAlert('Ошибка загрузки категории', 'error');
    }
}

async function saveCategory(event) {
    event.preventDefault();
    
    const id = document.getElementById('categoryId').value;
    const data = {
        name: document.getElementById('categoryName').value,
        sort_order: parseInt(document.getElementById('categorySortOrder').value) || 0,
        is_active: document.getElementById('categoryIsActive').checked
    };
    
    try {
        const url = id ? `/api/admin/categories/${id}` : '/api/admin/categories';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Ошибка сохранения');
        
        showAlert(id ? 'Категория обновлена' : 'Категория добавлена', 'success');
        closeCategoryModal();
        loadCategories();
        loadParts();
    } catch (error) {
        showAlert('Ошибка: ' + error.message, 'error');
    }
}

async function toggleCategoryActive(id) {
    try {
        const response = await fetch(`/api/admin/categories/${id}/toggle-active`, {
            method: 'PUT'
        });
        if (!response.ok) throw new Error('Ошибка');
        
        showAlert('Статус категории изменен', 'success');
        loadCategories();
    } catch (error) {
        showAlert('Ошибка: ' + error.message, 'error');
    }
}

async function deleteCategory(id) {
    if (!confirm('Удалить категорию? Это возможно только если в ней нет запчастей.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/categories/${id}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Ошибка удаления');
        
        showAlert('Категория удалена', 'success');
        loadCategories();
    } catch (error) {
        showAlert('Ошибка: ' + error.message, 'error');
    }
}

function closeCategoryModal() {
    document.getElementById('categoryModal').classList.remove('active');
}

// === ЗАПЧАСТИ ===
function openAddPartModal() {
    document.getElementById('partModalTitle').textContent = 'Добавить запчасть';
    document.getElementById('partForm').reset();
    document.getElementById('partId').value = '';
    document.getElementById('partIsActive').checked = true;
    document.getElementById('partModal').classList.add('active');
}

async function editPart(id) {
    try {
        const response = await fetch(`/api/admin/parts/${id}`);
        const part = await response.json();
        
        document.getElementById('partModalTitle').textContent = 'Редактировать запчасть';
        document.getElementById('partId').value = part.id;
        document.getElementById('partName').value = part.name;
        document.getElementById('partCategory').value = part.category;
        document.getElementById('partSortOrder').value = part.sort_order;
        document.getElementById('partIsActive').checked = part.is_active;
        
        document.getElementById('partModal').classList.add('active');
    } catch (error) {
        showAlert('Ошибка загрузки запчасти', 'error');
    }
}

async function savePart(event) {
    event.preventDefault();
    
    const id = document.getElementById('partId').value;
    const data = {
        name: document.getElementById('partName').value,
        category: document.getElementById('partCategory').value,
        sort_order: parseInt(document.getElementById('partSortOrder').value) || 0,
        is_active: document.getElementById('partIsActive').checked
    };
    
    try {
        const url = id ? `/api/admin/parts/${id}` : '/api/admin/parts';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Ошибка сохранения');
        
        showAlert(id ? 'Запчасть обновлена' : 'Запчасть добавлена', 'success');
        closePartModal();
        loadParts();
    } catch (error) {
        showAlert('Ошибка: ' + error.message, 'error');
    }
}

async function togglePartActive(id) {
    try {
        const response = await fetch(`/api/admin/parts/${id}/toggle-active`, {
            method: 'PUT'
        });
        if (!response.ok) throw new Error('Ошибка');
        
        showAlert('Статус запчасти изменен', 'success');
        loadParts();
    } catch (error) {
        showAlert('Ошибка: ' + error.message, 'error');
    }
}

async function deletePart(id) {
    if (!confirm('Удалить запчасть?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/parts/${id}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Ошибка удаления');
        
        showAlert('Запчасть удалена', 'success');
        loadParts();
    } catch (error) {
        showAlert('Ошибка: ' + error.message, 'error');
    }
}

function closePartModal() {
    document.getElementById('partModal').classList.remove('active');
}

// === ИМПОРТ ===
async function importDefaultCatalog() {
    if (!confirm('Импортировать дефолтный каталог? Существующие записи не будут затронуты.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/admin/parts/import-default', {
            method: 'POST'
        });
        
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Ошибка импорта');
        
        showAlert(result.message, 'success');
        loadCategories();
        loadParts();
    } catch (error) {
        showAlert('Ошибка: ' + error.message, 'error');
    }
}

// === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
function showAlert(message, type) {
    const container = document.getElementById('alertContainer');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    
    container.appendChild(alert);
    
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

// Поиск по мере ввода
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', renderParts);
    }
    
    // Закрытие модальных окон по клику вне их
    document.getElementById('categoryModal').addEventListener('click', function(e) {
        if (e.target === this) closeCategoryModal();
    });
    
    document.getElementById('partModal').addEventListener('click', function(e) {
        if (e.target === this) closePartModal();
    });
    
    // Загрузка при старте
    loadCategories();
    loadParts();
});
