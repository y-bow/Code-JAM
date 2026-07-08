document.addEventListener('DOMContentLoaded', function() {
  // ─── Theme ─────────────────────────────────────────────────────────
  var body = document.body;
  var themeBtn = document.getElementById('themeToggle');
  var themeIcon = themeBtn && themeBtn.querySelector('.material-symbols-rounded');

  var saved = localStorage.getItem('hive-theme');
  if (saved) body.className = saved;
  updateIcon(body.className);

  if (themeBtn) {
    themeBtn.addEventListener('click', function() {
      var next = body.className === 'dark-theme' ? 'light-theme' : 'dark-theme';
      body.className = next;
      localStorage.setItem('hive-theme', next);
      updateIcon(next);
    });
  }

  function updateIcon(theme) {
    if (!themeIcon) return;
    themeIcon.textContent = theme === 'dark-theme' ? 'light_mode' : 'dark_mode';
  }

  // ─── Profile Modal ─────────────────────────────────────────────────
  var profileBtn = document.getElementById('userProfileBtn');
  var profileModal = document.getElementById('profileModal');
  var closeProfile = document.getElementById('closeProfileBtn');

  if (profileBtn && profileModal) {
    profileBtn.addEventListener('click', function(e) {
      e.preventDefault();
      profileModal.classList.add('active');
    });
    if (closeProfile) {
      closeProfile.addEventListener('click', function() { profileModal.classList.remove('active'); });
    }
    profileModal.addEventListener('click', function(e) {
      if (e.target === profileModal) profileModal.classList.remove('active');
    });
  }

  // ─── Notifications Dropdown ────────────────────────────────────────
  var notifBtn = document.getElementById('notificationBtn');
  var notifDrop = document.getElementById('notificationsDropdown');

  if (notifBtn && notifDrop) {
    notifBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      notifDrop.classList.toggle('active');
    });
    document.addEventListener('click', function(e) {
      if (!notifBtn.contains(e.target) && !notifDrop.contains(e.target)) {
        notifDrop.classList.remove('active');
      }
    });
  }

  // ─── Flash message auto-dismiss ────────────────────────────────────
  document.querySelectorAll('.alert').forEach(function(el) {
    if (!el.querySelector('a')) {
      setTimeout(function() {
        el.style.transition = 'opacity 0.3s';
        el.style.opacity = '0';
        setTimeout(function() { el.style.display = 'none'; }, 300);
      }, 5000);
    }
  });
});

function closeModal(id) {
  var el = document.getElementById(id);
  if (el) el.classList.remove('active');
}

function openModal(id) {
  var el = document.getElementById(id);
  if (el) el.classList.add('active');
}
