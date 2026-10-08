document.querySelectorAll('.sa-confirm').forEach(form => {
  form.addEventListener('submit', event => {
    if (!window.confirm('هل تريد تنفيذ هذا الإجراء؟ سيُسجل في سجل التدقيق.')) event.preventDefault();
  });
});
const logoutButton = document.getElementById('logout');
if (logoutButton) {
  logoutButton.addEventListener('click', async () => {
    const script = document.querySelector('script[data-csrf]');
    const response = await fetch('/logout', {method: 'POST', headers: {'X-CSRF-Token': script.dataset.csrf}});
    if (response.ok) {
      const data = await response.json();
      window.location.assign(data.redirect_url === '/super-admin/login' ? '/super-admin/login' : '/login');
    }
  });
}
