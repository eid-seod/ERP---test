'use strict';

const menuButton = document.querySelector('.menu-toggle');
const nav = document.querySelector('.main-nav');

function closeMenu() {
  nav.classList.remove('is-open');
  menuButton.setAttribute('aria-expanded', 'false');
}

menuButton.addEventListener('click', () => {
  const isOpen = nav.classList.toggle('is-open');
  menuButton.setAttribute('aria-expanded', String(isOpen));
});

nav.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', closeMenu);
});

document.addEventListener('keydown', event => {
  if (event.key === 'Escape') closeMenu();
});

if ('IntersectionObserver' in window) {
  const sectionObserver = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      nav.querySelectorAll('a').forEach(link => {
        link.classList.toggle('active', link.getAttribute('href') === '#' + entry.target.id);
      });
    }
  }, {rootMargin: '-15% 0px -55% 0px', threshold: 0});
  document.querySelectorAll('main > section[id]').forEach(section => sectionObserver.observe(section));
}

const screenshotDialog = document.getElementById('screenshot-dialog');
const screenshotImage = document.getElementById('screenshot-image');
const screenshotCaption = document.getElementById('screenshot-caption');
let screenshotTrigger = null;

document.querySelectorAll('[data-image]').forEach(button => {
  button.addEventListener('click', () => {
    screenshotTrigger = button;
    screenshotImage.src = button.dataset.image;
    screenshotImage.alt = button.dataset.caption;
    screenshotCaption.textContent = button.dataset.caption;
    screenshotDialog.showModal();
  });
});

screenshotDialog.querySelector('.dialog-close').addEventListener('click', () => screenshotDialog.close());
screenshotDialog.addEventListener('click', event => {
  const rect = screenshotDialog.getBoundingClientRect();
  if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) screenshotDialog.close();
});
screenshotDialog.addEventListener('close', () => {
  if (screenshotTrigger) screenshotTrigger.focus();
});

const inquiryForm = document.getElementById('inquiry-form');
const inquiryDraft = document.getElementById('inquiry-draft');
const inquiryFeedback = document.getElementById('inquiry-feedback');

inquiryForm.addEventListener('submit', event => {
  event.preventDefault();
  if (!inquiryForm.reportValidity()) return;
  const service = document.getElementById('inquiry-service').value;
  const message = document.getElementById('inquiry-message').value.trim();
  if (!message) {
    inquiryFeedback.textContent = 'Please describe the support you need.';
    return;
  }
  inquiryDraft.value = 'Hello Eid Saeed Mahmoud,\n\nI am interested in ' + service + '.\n\n' + message + '\n\nPlease let me know how we can discuss this further.';
  document.getElementById('inquiry-result').hidden = false;
  inquiryFeedback.textContent = 'Your inquiry is ready. Nothing has been sent or stored.';
  inquiryDraft.focus();
});

document.getElementById('copy-inquiry').addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(inquiryDraft.value);
    inquiryFeedback.textContent = 'Message copied. Contact Eid directly to share it.';
  } catch (error) {
    inquiryDraft.focus();
    inquiryDraft.select();
    inquiryFeedback.textContent = 'Select and copy the message manually. Nothing has been sent.';
  }
});
