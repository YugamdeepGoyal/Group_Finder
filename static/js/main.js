// Auto-submit the directory search box after the user pauses typing,
// so search feels live without needing a full JS framework.
document.addEventListener('DOMContentLoaded', function () {
  var searchInput = document.getElementById('search-input');
  if (searchInput) {
    var debounceTimer;
    searchInput.addEventListener('input', function () {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(function () {
        searchInput.form.submit();
      }, 450);
    });
  }

  // Auto-dismiss flash messages after a few seconds.
  document.querySelectorAll('.flash').forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity 0.4s ease';
      el.style.opacity = '0';
      setTimeout(function () { el.remove(); }, 400);
    }, 4500);
  });
});
