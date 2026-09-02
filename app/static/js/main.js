// Utilitarios de Cliente para GTR Logistics

function showNotification(message, type = 'success') {
  let container = document.getElementById('notification-toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'notification-toast-container';
    container.className = 'fixed bottom-5 right-5 z-50 flex flex-col gap-3 max-w-sm w-full';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  const isError = type === 'error';
  const bgColor = isError ? 'bg-red-600 text-white' : 'bg-slate-900 text-white border border-slate-700';
  const icon = isError ? 'error' : 'check_circle';

  toast.className = `${bgColor} p-4 rounded-xl shadow-2xl flex items-center gap-3 transition-all duration-300 transform translate-y-4 opacity-0`;
  toast.innerHTML = `
    <span class="material-symbols-outlined text-${isError ? 'white' : 'sky-400'}">${icon}</span>
    <p class="text-sm font-medium flex-1">${message}</p>
    <button onclick="this.parentElement.remove()" class="text-slate-400 hover:text-white">
      <span class="material-symbols-outlined text-sm">close</span>
    </button>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.remove('translate-y-4', 'opacity-0');
  }, 10);

  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-2');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Formateador de moneda / distancia / tiempo
function formatDuration(minutes) {
  const hrs = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hrs > 0) return `${hrs}h ${mins}m`;
  return `${mins} min`;
}
