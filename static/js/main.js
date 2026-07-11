/* Travel Pro – main.js */

// Auto-dismiss flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', () => {
  const messages = document.getElementById('messages');
  if (messages) {
    setTimeout(() => {
      messages.style.transition = 'opacity 0.5s';
      messages.style.opacity = '0';
      setTimeout(() => messages.remove(), 500);
    }, 5000);
  }
});
