// Scan page: poll status until done or failed. Findings page: toggle explanation rows.
(function () {
  var el = document.querySelector('script[data-scan]');
  if (el) {
    var id = el.dataset.scan;
    var timer = setInterval(function () {
      fetch('/api/scans/' + id, { credentials: 'same-origin' }).then(function (r) { return r.json(); })
        .then(function (s) {
          document.getElementById('status').textContent = s.status;
          document.getElementById('err').textContent = s.error || '';
          if (s.status === 'done') { document.getElementById('done').hidden = false; clearInterval(timer); }
          if (s.status === 'failed') { clearInterval(timer); }
        });
    }, 5000);
  }
  document.querySelectorAll('tr.row').forEach(function (tr) {
    tr.addEventListener('click', function () {
      var d = document.getElementById(tr.dataset.toggle);
      d.hidden = !d.hidden;
    });
  });
})();
