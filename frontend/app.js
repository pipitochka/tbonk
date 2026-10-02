const tasksElement = document.querySelector('#tasks');
const dialog = document.querySelector('#task-dialog');
const form = document.querySelector('#task-form');
const filter = document.querySelector('#filter');
const message = document.querySelector('#message');
const labels = { todo: 'К выполнению', in_progress: 'В работе', done: 'Готово' };

async function api(url, options = {}) {
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...options });
  if (!response.ok) throw new Error((await response.json()).error || 'Ошибка запроса');
  return response.status === 204 ? null : response.json();
}

function render(tasks) {
  document.querySelector('#count').textContent = `Задач: ${tasks.length}`;
  tasksElement.innerHTML = tasks.length ? tasks.map(task => `
    <article class="task ${task.status}">
      <div><span class="badge">${labels[task.status]}</span><h3>${escapeHtml(task.title)}</h3>
      <p>${escapeHtml(task.description) || 'Без описания'}</p></div>
      <div class="task-actions"><button data-edit="${task.id}">Изменить</button><button data-delete="${task.id}" class="danger">Удалить</button></div>
    </article>`).join('') : '<div class="empty">Здесь пока нет задач.</div>';
}

function escapeHtml(value) { return value.replace(/[&<>'"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#039;', '"': '&quot;' }[c])); }

async function load() {
  try { render(await api(`/api/tasks${filter.value ? `?status=${filter.value}` : ''}`)); message.textContent = ''; }
  catch (error) { message.textContent = error.message; }
}

function openForm(task = null) {
  document.querySelector('#dialog-title').textContent = task ? 'Изменить задачу' : 'Новая задача';
  document.querySelector('#task-id').value = task?.id || '';
  document.querySelector('#title').value = task?.title || '';
  document.querySelector('#description').value = task?.description || '';
  document.querySelector('#status').value = task?.status || 'todo';
  dialog.showModal();
}

document.querySelector('#new-task').onclick = () => openForm();
document.querySelector('#cancel').onclick = () => dialog.close();
filter.onchange = load;
form.onsubmit = async (event) => {
  event.preventDefault();
  const id = document.querySelector('#task-id').value;
  try {
    await api(id ? `/api/tasks/${id}` : '/api/tasks', { method: id ? 'PUT' : 'POST', body: JSON.stringify({ title: document.querySelector('#title').value, description: document.querySelector('#description').value, status: document.querySelector('#status').value }) });
    dialog.close(); await load();
  } catch (error) { message.textContent = error.message; }
};
tasksElement.onclick = async (event) => {
  const edit = event.target.dataset.edit;
  const remove = event.target.dataset.delete;
  if (edit) openForm(await api(`/api/tasks/${edit}`));
  if (remove && confirm('Удалить задачу?')) { await api(`/api/tasks/${remove}`, { method: 'DELETE' }); await load(); }
};
load();
