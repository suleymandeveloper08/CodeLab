
  
  // Burger menu açyp ýapmak we accessibility
  const navToggle = document.getElementById('navToggle');
  const navLinks = document.getElementById('navLinks');

  navToggle.addEventListener('click', () => {
    const expanded = navToggle.getAttribute('aria-expanded') === 'true' || false;
    navToggle.setAttribute('aria-expanded', !expanded);
    navToggle.classList.toggle('active');
    navLinks.classList.toggle('active');
  });

  function filterCategories() {
    const input = document.getElementById('searchInput');
    const filter = input.value.toLowerCase();
    const items = document.querySelectorAll('.category-grid .category-item');
    items.forEach(item => {
      const text = item.textContent.toLowerCase();
      item.style.display = text.includes(filter) ? '' : 'none';
    });
  }

const darkModeToggle = document.getElementById('darkModeToggle');

function applyTheme(theme) {
  if (theme === 'dark') {
    document.body.classList.add('dark-mode');
    darkModeToggle.textContent = '☀️'; // Light mode icon
    darkModeToggle.setAttribute('aria-pressed', 'true');
  } else {
    document.body.classList.remove('dark-mode');
    darkModeToggle.textContent = '🌙'; // Dark mode icon
    darkModeToggle.setAttribute('aria-pressed', 'false');
  }
  localStorage.setItem('theme', theme);
}

function loadTheme() {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) {
    applyTheme(savedTheme);
  } else {
    // Sistem temasy boýunça avtomat sazla
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    applyTheme(prefersDark ? 'dark' : 'light');
  }
}

darkModeToggle.addEventListener('click', () => {
  const isDark = document.body.classList.contains('dark-mode');
  applyTheme(isDark ? 'light' : 'dark');
});

window.addEventListener('load', loadTheme);
