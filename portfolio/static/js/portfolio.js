'use strict';

const menuButton = document.querySelector('.menu-toggle');
const nav = document.querySelector('.main-nav');
function closeMenu() {
  nav.classList.remove('is-open');
  menuButton.setAttribute('aria-expanded', 'false');
}
menuButton.addEventListener('click', () => {
  const open = nav.classList.toggle('is-open');
  menuButton.setAttribute('aria-expanded', String(open));
});
nav.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') closeMenu();
});
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      nav.querySelectorAll('a').forEach(link => link.classList.toggle('active', link.getAttribute('href') === '/#' + entry.target.id));
    }
  }, {rootMargin: '-15% 0px -55% 0px', threshold: 0});
  document.querySelectorAll('main > section[id]').forEach(section => observer.observe(section));
}

const dialog = document.getElementById('screenshot-dialog');
let screenshotTrigger = null;
document.querySelectorAll('[data-image]').forEach(button => {
  button.addEventListener('click', () => {
    screenshotTrigger = button;
    const image = document.getElementById('screenshot-image');
    image.src = button.dataset.image;
    image.alt = button.dataset.caption;
    document.getElementById('screenshot-caption').textContent = button.dataset.caption;
    dialog.showModal();
  });
});
dialog.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => {
  const rect = dialog.getBoundingClientRect();
  if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
});
dialog.addEventListener('close', () => {
  if (screenshotTrigger) screenshotTrigger.focus();
});

const form = document.getElementById('inquiry-form');
if (form) {
  const service = document.getElementById('inquiry-service');
  const message = document.getElementById('inquiry-message');
  const draft = document.getElementById('inquiry-draft');
  const feedback = document.getElementById('inquiry-feedback');
  function validateField(field, text) {
    field.setCustomValidity(field.value.trim() ? '' : text);
  }
  service.addEventListener('change', () => validateField(service, 'يرجى اختيار الخدمة المناسبة.'));
  message.addEventListener('input', () => validateField(message, 'يرجى توضيح نوع الدعم الذي تحتاجه.'));
  service.setCustomValidity('يرجى اختيار الخدمة المناسبة.');
  message.setCustomValidity('يرجى توضيح نوع الدعم الذي تحتاجه.');
  form.addEventListener('submit', event => {
    event.preventDefault();
    validateField(service, 'يرجى اختيار الخدمة المناسبة.');
    validateField(message, 'يرجى توضيح نوع الدعم الذي تحتاجه.');
    if (!form.reportValidity()) return;
    draft.value = 'مرحباً أستاذ عيد سعيد محمود،\n\nأرغب في مناقشة خدمة: ' + service.value + '.\n\n' + message.value.trim() + '\n\nيرجى التواصل لمناقشة نطاق الدعم المناسب.';
    document.getElementById('inquiry-result').hidden = false;
    feedback.textContent = 'رسالتك جاهزة. لم يتم إرسال أو تخزين أي بيانات.';
    draft.focus();
  });
  document.getElementById('copy-inquiry').addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(draft.value);
      feedback.textContent = 'تم نسخ الرسالة. تواصل معي مباشرة لمشاركتها.';
    } catch (error) {
      draft.focus();
      draft.select();
      feedback.textContent = 'يمكنك تحديد الرسالة ونسخها يدوياً. لم يتم إرسال أي بيانات.';
    }
  });
}
