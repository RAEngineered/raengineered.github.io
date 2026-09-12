document.querySelectorAll('.tabs').forEach(function (group) {
  var buttons = group.querySelectorAll('.tablist button');
  var panels = group.querySelectorAll('.tabpanel');
  buttons.forEach(function (btn, i) {
    btn.addEventListener('click', function () {
      buttons.forEach(function (b) { b.setAttribute('aria-selected', 'false'); });
      panels.forEach(function (p) { p.hidden = true; });
      btn.setAttribute('aria-selected', 'true');
      panels[i].hidden = false;
    });
  });
});
