/* ===================================================================
   Task Manager Frontend - app.js
   Vanilla JavaScript ES6+ module pattern
   =================================================================== */

const API_BASE = '/api/v1';
let authToken = null;
let currentUser = null;
let currentPage = 1;
let currentFilters = {};
let editingTaskId = null;

// ===================================================================
// DOM Elements
// ===================================================================
const elements = {
  // Auth
  authModal: document.getElementById('authModal'),
  authForm: document.getElementById('authForm'),
  authTitle: document.getElementById('authTitle'),
  authError: document.getElementById('authError'),
  switchAuth: document.getElementById('switchAuth'),
  switchText: document.getElementById('switchText'),
  usernameGroup: document.getElementById('usernameGroup'),
  emailGroup: document.getElementById('emailGroup'),
  modalCloseBtns: document.querySelectorAll('.modal-close'),
  
  // App
  app: document.getElementById('app'),
  userInitial: document.getElementById('userInitial'),
  userName: document.getElementById('userName'),
  userEmail: document.getElementById('userEmail'),
  userAvatar: document.querySelector('.user-avatar'),
  userDropdown: document.querySelector('.user-dropdown'),
  logoutBtn: document.getElementById('logoutBtn'),
  
  // Stats
  statTotal: document.getElementById('statTotal'),
  statPending: document.getElementById('statPending'),
  statInProgress: document.getElementById('statInProgress'),
  statDone: document.getElementById('statDone'),
  
  // Toolbar
  newTaskBtn: document.getElementById('newTaskBtn'),
  firstTaskBtn: document.getElementById('firstTaskBtn'),
  filterStatus: document.getElementById('filterStatus'),
  filterPriority: document.getElementById('filterPriority'),
  filterCategory: document.getElementById('filterCategory'),
  searchInput: document.getElementById('searchInput'),
  
  // Task List
  taskList: document.getElementById('taskList'),
  emptyState: document.getElementById('emptyState'),
  loadingState: document.getElementById('loadingState'),
  
  // Pagination
  pagination: document.getElementById('pagination'),
  prevPage: document.getElementById('prevPage'),
  nextPage: document.getElementById('nextPage'),
  pageInfo: document.getElementById('pageInfo'),
  
  // Task Modal
  taskModal: document.getElementById('taskModal'),
  taskForm: document.getElementById('taskForm'),
  taskModalTitle: document.getElementById('taskModalTitle'),
  taskId: document.getElementById('taskId'),
  taskTitle: document.getElementById('taskTitle'),
  taskDescription: document.getElementById('taskDescription'),
  taskStatus: document.getElementById('taskStatus'),
  taskPriority: document.getElementById('taskPriority'),
  taskCategory: document.getElementById('taskCategory'),
  taskDueDate: document.getElementById('taskDueDate'),
  cancelTaskBtn: document.getElementById('cancelTaskBtn'),
  saveTaskBtn: document.getElementById('saveTaskBtn'),
  categoriesDatalist: document.getElementById('categories'),
  
  // Toast
  toastContainer: document.getElementById('toastContainer'),
};

// ===================================================================
// State Management
// ===================================================================
let isLoginMode = true;
let debounceTimer = null;

// ===================================================================
// Utility Functions
// ===================================================================

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span class="toast-message">${escapeHtml(message)}</span>
    <button class="toast-close" aria-label="Dismiss">&times;</button>
  `;
  
  toast.querySelector('.toast-close').addEventListener('click', () => {
    toast.style.animation = 'slideIn 0.2s ease reverse';
    setTimeout(() => toast.remove(), 200);
  });
  
  elements.toastContainer.appendChild(toast);
  
  // Auto remove after 5 seconds
  setTimeout(() => {
    if (toast.parentNode) {
      toast.style.animation = 'slideIn 0.2s ease reverse';
      setTimeout(() => toast.remove(), 200);
    }
  }, 5000);
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function formatDate(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function isOverdue(dueDate, status) {
  if (!dueDate || status === 'done') return false;
  return new Date(dueDate) < new Date();
}

function getInitials(name) {
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

// ===================================================================
// API Functions
// ===================================================================

async function apiRequest(endpoint, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });
  
  const data = await response.json().catch(() => ({}));
  
  if (!response.ok) {
    const error = new Error(extractErrorMessage(data) || 'Request failed');
    error.status = response.status;
    error.data = data;
    throw error;
  }
  
  return data;
}

// Turn FastAPI error payloads (string OR 422 array) into a readable message
function extractErrorMessage(data) {
  const detail = data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const field = Array.isArray(item.loc) ? item.loc.slice(1).join('.') : '';
        return field ? `${field}: ${item.msg}` : item.msg;
      })
      .join(' | ');
  }
  return '';
}

// Auth API
async function registerUser(email, username, password) {
  return apiRequest('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, username, password }),
  });
}

async function loginUser(email, password) {
  return apiRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

async function refreshAuthToken(refreshToken) {
  return apiRequest('/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

async function getCurrentUser() {
  return apiRequest('/auth/me');
}

// Task API
async function fetchTasks(params = {}) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, value);
    }
  });
  return apiRequest(`/tasks/?${searchParams.toString()}`);
}

async function fetchTaskStats() {
  return apiRequest('/tasks/stats/summary');
}

async function createTask(taskData) {
  return apiRequest('/tasks/', {
    method: 'POST',
    body: JSON.stringify(taskData),
  });
}

async function updateTask(taskId, taskData) {
  return apiRequest(`/tasks/${taskId}`, {
    method: 'PATCH',
    body: JSON.stringify(taskData),
  });
}

async function deleteTask(taskId) {
  return apiRequest(`/tasks/${taskId}`, {
    method: 'DELETE',
  });
}

// ===================================================================
// Auth Flow
// ===================================================================

function setAuthMode(login) {
  isLoginMode = login;
  
  if (isLoginMode) {
    elements.authTitle.textContent = 'Welcome Back';
    elements.switchText.textContent = "Don't have an account?";
    elements.switchAuth.textContent = 'Sign Up';
    elements.usernameGroup.style.display = 'none';
    elements.authForm.querySelector('button[type="submit"]').textContent = 'Sign In';
  } else {
    elements.authTitle.textContent = 'Create Account';
    elements.switchText.textContent = 'Already have an account?';
    elements.switchAuth.textContent = 'Sign In';
    elements.usernameGroup.style.display = 'block';
    elements.authForm.querySelector('button[type="submit"]').textContent = 'Create Account';
  }
  
  elements.authError.textContent = '';
  elements.authForm.reset();
}

function switchAuthMode() {
  setAuthMode(!isLoginMode);
}

async function handleAuthSubmit(e) {
  e.preventDefault();
  elements.authError.textContent = '';
  
  const formData = new FormData(elements.authForm);
  const email = formData.get('email');
  const username = formData.get('username');
  const password = formData.get('password');
  
  // The form uses novalidate, so mirror the API rules here for instant feedback
  const problems = [];
  if (!email || !String(email).includes('@')) problems.push('Enter a valid email address.');
  if (!password || String(password).length < 8) problems.push('Password must be at least 8 characters.');
  if (!isLoginMode && (!username || String(username).length < 3)) {
    problems.push('Username must be at least 3 characters.');
  }
  if (problems.length) {
    elements.authError.textContent = problems.join(' ');
    return;
  }
  
  const submitBtn = elements.authForm.querySelector('button[type="submit"]');
  const originalText = submitBtn.textContent;
  submitBtn.disabled = true;
  submitBtn.textContent = isLoginMode ? 'Signing in...' : 'Creating account...';
  
  try {
    let data;
    if (isLoginMode) {
      data = await loginUser(email, password);
    } else {
      data = await registerUser(email, username, password);
      // Auto-login after registration
      data = await loginUser(email, password);
    }
    
    authToken = data.access_token;
    localStorage.setItem('authToken', authToken);
    localStorage.setItem('refreshToken', data.refresh_token);
    
    await initApp();
    if (!elements.app.hidden) {
      showToast(isLoginMode ? 'Welcome back!' : 'Account created successfully!', 'success');
    }
  } catch (error) {
    elements.authError.textContent = error.message;
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = originalText;
  }
}

async function initApp() {
  try {
    currentUser = await getCurrentUser();
    updateUserUI();
    elements.app.hidden = false;
    closeModal(elements.authModal);
    loadTasks();
    loadStats();
  } catch (error) {
    logout();
  }
}

function updateUserUI() {
  if (currentUser) {
    elements.userInitial.textContent = getInitials(currentUser.username);
    elements.userName.textContent = currentUser.username;
    elements.userEmail.textContent = currentUser.email;
  }
}

function logout() {
  authToken = null;
  currentUser = null;
  localStorage.removeItem('authToken');
  localStorage.removeItem('refreshToken');
  elements.app.hidden = true;
  closeModal(elements.taskModal);
  setAuthMode(true);
  openModal(elements.authModal);
}

// ===================================================================
// Modal Management
// ===================================================================

function openModal(modal) {
  modal.hidden = false;
  requestAnimationFrame(() => modal.classList.add('show'));
  document.body.style.overflow = 'hidden';
  
  // Focus the first visible input (skip fields hidden by the current mode)
  const firstInput = Array.from(modal.querySelectorAll('input, select, textarea')).find(
    (el) => el.offsetParent !== null
  );
  if (firstInput) firstInput.focus();
}

function closeModal(modal) {
  modal.classList.remove('show');
  setTimeout(() => {
    modal.hidden = true;
    // Only unlock page scroll when no other modal is still open
    if (!document.querySelector('.modal.show')) {
      document.body.style.overflow = '';
    }
  }, 200);
}

function setupModalClose(modal, locked = false) {
  // A locked modal (the login screen) must not be dismissed — otherwise the
  // user is left staring at an empty page with no way back.
  if (locked) {
    modal.querySelectorAll('.modal-close').forEach((btn) => {
      btn.style.display = 'none';
    });
    return;
  }

  modal.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => closeModal(modal));
  });
  
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal(modal);
  });
  
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !modal.hidden) closeModal(modal);
  });
}

// ===================================================================
// Task Rendering
// ===================================================================

function renderTasks(tasks) {
  if (tasks.length === 0) {
    elements.taskList.innerHTML = '';
    elements.emptyState.hidden = false;
    elements.pagination.hidden = true;
    return;
  }
  
  elements.emptyState.hidden = true;
  elements.pagination.hidden = false;
  
  elements.taskList.innerHTML = tasks.map(task => `
    <article class="task-card ${task.status === 'done' ? 'completed' : ''}" data-task-id="${task.id}">
      <div class="task-checkbox">
        <input type="checkbox" ${task.status === 'done' ? 'checked' : ''} 
               onchange="toggleTaskStatus('${task.id}', this.checked)">
      </div>
      <div class="task-content">
        <div class="task-header">
          <h3 class="task-title">${escapeHtml(task.title)}</h3>
          <div class="task-meta">
            <span class="badge badge-status-${task.status}">${formatStatus(task.status)}</span>
            <span class="badge badge-priority-${task.priority}">${task.priority}</span>
            ${task.category ? `<span class="badge badge-category">${escapeHtml(task.category)}</span>` : ''}
          </div>
        </div>
        ${task.description ? `<p class="task-description">${escapeHtml(task.description)}</p>` : ''}
        <div class="task-footer">
          <span class="task-due-date ${isOverdue(task.due_date, task.status) ? 'overdue' : ''}">
            ${task.due_date ? `📅 ${formatDate(task.due_date)}` : 'No due date'}
          </span>
          <div class="task-actions">
            <button class="task-action-btn" onclick="openEditTask('${task.id}')" aria-label="Edit task">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            </button>
            <button class="task-action-btn delete" onclick="confirmDeleteTask('${task.id}')" aria-label="Delete task">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </article>
  `).join('');
  
  // Update categories datalist
  updateCategoriesDatalist(tasks);
}

function formatStatus(status) {
  return status.split('_').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ');
}

function updateCategoriesDatalist(tasks) {
  const categories = [...new Set(tasks.map(t => t.category).filter(Boolean))];
  elements.categoriesDatalist.innerHTML = categories
    .map(cat => `<option value="${escapeHtml(cat)}">`)
    .join('');
}

function renderPagination(page, totalPages) {
  elements.pageInfo.textContent = `Page ${page} of ${totalPages || 1}`;
  elements.prevPage.disabled = page <= 1;
  elements.nextPage.disabled = page >= totalPages;
}

function setLoading(loading) {
  elements.loadingState.hidden = !loading;
  elements.taskList.style.opacity = loading ? '0.5' : '1';
}

// ===================================================================
// Task Operations
// ===================================================================

async function loadTasks() {
  setLoading(true);
  
  try {
    const params = {
      page: currentPage,
      page_size: 20,
      ...currentFilters,
    };
    
    // Remove empty filters
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null) delete params[key];
    });
    
    const data = await fetchTasks(params);
    renderTasks(data.items);
    renderPagination(data.page, data.total_pages);
  } catch (error) {
    showToast('Failed to load tasks: ' + error.message, 'error');
  } finally {
    setLoading(false);
  }
}

async function loadStats() {
  try {
    const stats = await fetchTaskStats();
    elements.statTotal.textContent = stats.total;
    elements.statPending.textContent = stats.by_status?.pending || 0;
    elements.statInProgress.textContent = stats.by_status?.in_progress || 0;
    elements.statDone.textContent = stats.by_status?.done || 0;
  } catch (error) {
    console.error('Failed to load stats:', error);
  }
}

function openNewTask() {
  editingTaskId = null;
  elements.taskModalTitle.textContent = 'New Task';
  elements.taskForm.reset();
  elements.taskId.value = '';
  elements.taskStatus.value = 'pending';
  elements.taskPriority.value = 'medium';
  openModal(elements.taskModal);
}

async function openEditTask(taskId) {
  try {
    const data = await fetchTasks({ page: 1, page_size: 1 }); // We need to fetch the specific task
    // Better: fetch single task
    const taskData = await apiRequest(`/tasks/${taskId}`);
    
    editingTaskId = taskId;
    elements.taskModalTitle.textContent = 'Edit Task';
    elements.taskId.value = taskData.id;
    elements.taskTitle.value = taskData.title;
    elements.taskDescription.value = taskData.description || '';
    elements.taskStatus.value = taskData.status;
    elements.taskPriority.value = taskData.priority;
    elements.taskCategory.value = taskData.category || '';
    elements.taskDueDate.value = taskData.due_date ? taskData.due_date.slice(0, 16) : '';
    
    openModal(elements.taskModal);
  } catch (error) {
    showToast('Failed to load task: ' + error.message, 'error');
  }
}

async function handleTaskSubmit(e) {
  e.preventDefault();
  
  const formData = new FormData(elements.taskForm);
  const taskData = {
    title: formData.get('title'),
    description: formData.get('description') || null,
    status: formData.get('status'),
    priority: formData.get('priority'),
    category: formData.get('category') || null,
    due_date: formData.get('due_date') || null,
  };
  
  // Remove null values
  Object.keys(taskData).forEach(key => {
    if (taskData[key] === null || taskData[key] === '') delete taskData[key];
  });
  
  const submitBtn = elements.saveTaskBtn;
  const originalText = submitBtn.textContent;
  submitBtn.disabled = true;
  submitBtn.textContent = editingTaskId ? 'Saving...' : 'Creating...';
  
  try {
    if (editingTaskId) {
      await updateTask(editingTaskId, taskData);
      showToast('Task updated successfully', 'success');
    } else {
      await createTask(taskData);
      showToast('Task created successfully', 'success');
    }
    
    closeModal(elements.taskModal);
    loadTasks();
    loadStats();
  } catch (error) {
    showToast('Failed to save task: ' + error.message, 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = originalText;
  }
}

async function toggleTaskStatus(taskId, completed) {
  try {
    await updateTask(taskId, { status: completed ? 'done' : 'pending' });
    loadTasks();
    loadStats();
  } catch (error) {
    showToast('Failed to update task: ' + error.message, 'error');
    // Revert checkbox
    const checkbox = document.querySelector(`[data-task-id="${taskId}"] input[type="checkbox"]`);
    if (checkbox) checkbox.checked = !completed;
  }
}

function confirmDeleteTask(taskId) {
  if (confirm('Are you sure you want to delete this task?')) {
    deleteTaskConfirmed(taskId);
  }
}

async function deleteTaskConfirmed(taskId) {
  try {
    await deleteTask(taskId);
    showToast('Task deleted', 'success');
    loadTasks();
    loadStats();
  } catch (error) {
    showToast('Failed to delete task: ' + error.message, 'error');
  }
}

// ===================================================================
// Filter & Search
// ===================================================================

function handleFilterChange() {
  currentFilters = {
    status: elements.filterStatus.value || undefined,
    priority: elements.filterPriority.value || undefined,
    category: elements.filterCategory.value || undefined,
  };
  currentPage = 1;
  loadTasks();
}

function handleSearch() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    currentFilters.search = elements.searchInput.value || undefined;
    currentPage = 1;
    loadTasks();
  }, 300);
}

// ===================================================================
// Pagination
// ===================================================================

function goToPage(page) {
  currentPage = page;
  loadTasks();
}

// ===================================================================
// Event Listeners Setup
// ===================================================================

function setupEventListeners() {
  // Auth
  elements.authForm.addEventListener('submit', handleAuthSubmit);
  elements.switchAuth.addEventListener('click', switchAuthMode);
  
  // Modals
  setupModalClose(elements.authModal, true); // login screen: must not be dismissed
  setupModalClose(elements.taskModal);
  
  // User menu
  const closeUserMenu = () => {
    document.querySelectorAll('.user-menu.open').forEach((m) => m.classList.remove('open'));
    elements.userAvatar.setAttribute('aria-expanded', 'false');
  };

  elements.userAvatar.addEventListener('click', () => {
    const menu = document.querySelector('.user-menu');
    const isOpen = menu.classList.toggle('open');
    elements.userAvatar.setAttribute('aria-expanded', String(isOpen));
  });

  document.addEventListener('click', (e) => {
    if (!e.target.closest('.user-menu')) closeUserMenu();
  });

  elements.logoutBtn.addEventListener('click', () => {
    closeUserMenu();
    logout();
  });
  
  // Task actions
  elements.newTaskBtn.addEventListener('click', openNewTask);
  elements.firstTaskBtn.addEventListener('click', openNewTask);
  elements.taskForm.addEventListener('submit', handleTaskSubmit);
  elements.cancelTaskBtn.addEventListener('click', () => closeModal(elements.taskModal));
  
  // Filters
  elements.filterStatus.addEventListener('change', handleFilterChange);
  elements.filterPriority.addEventListener('change', handleFilterChange);
  elements.filterCategory.addEventListener('change', handleFilterChange);
  elements.searchInput.addEventListener('input', handleSearch);
  
  // Pagination
  elements.prevPage.addEventListener('click', () => goToPage(currentPage - 1));
  elements.nextPage.addEventListener('click', () => goToPage(currentPage + 1));
}

// ===================================================================
// Initialize
// ===================================================================

async function init() {
  setupEventListeners();
  
  // Check for stored token
  const storedToken = localStorage.getItem('authToken');
  if (storedToken) {
    authToken = storedToken;
    try {
      await initApp();
    } catch (error) {
      // Token expired or invalid
      logout();
    }
  } else {
    setAuthMode(true);
    openModal(elements.authModal);
  }
}

// Make functions globally accessible for inline handlers
window.toggleTaskStatus = toggleTaskStatus;
window.openEditTask = openEditTask;
window.confirmDeleteTask = confirmDeleteTask;

// Start app
document.addEventListener('DOMContentLoaded', init);