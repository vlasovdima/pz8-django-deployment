// Переключение светлой и темной темы с сохранением в localStorage
document.addEventListener('DOMContentLoaded', function () {
  var themeToggleBtn = document.getElementById('theme-toggle-btn');
  var themeIcon = document.getElementById('theme-toggle-icon');

  function updateThemeIcon(theme) {
    if (!themeIcon) return;
    if (theme === 'dark') {
      themeIcon.className = 'ti ti-sun icon';
    } else {
      themeIcon.className = 'ti ti-moon icon';
    }
  }

  var currentTheme = document.documentElement.getAttribute('data-bs-theme') || 'light';
  updateThemeIcon(currentTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', function (e) {
      e.preventDefault();
      var now = document.documentElement.getAttribute('data-bs-theme') || 'light';
      var next = now === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-bs-theme', next);
      localStorage.setItem('pz5-tabler-theme', next);
      updateThemeIcon(next);
    });
  }

  // Переключатель видимости пароля на странице входа
  var togglePwd = document.getElementById('toggle-password-btn');
  var pwdInput = document.getElementById('id_password');
  if (togglePwd && pwdInput) {
    togglePwd.addEventListener('click', function (e) {
      e.preventDefault();
      var isPass = pwdInput.getAttribute('type') === 'password';
      pwdInput.setAttribute('type', isPass ? 'text' : 'password');
      var icon = togglePwd.querySelector('i');
      if (icon) {
        icon.className = isPass ? 'ti ti-eye-off icon' : 'ti ti-eye icon';
      }
    });
  }
});
