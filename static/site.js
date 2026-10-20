/* 글자 크기 버튼, 링크 복사, 유튜브 영상 클릭 재생 */
(function () {
  var KEY = 'sb-font-scale';
  var SIZES = [1, 1.15, 1.3];
  var level = 0;
  try { level = parseInt(localStorage.getItem(KEY), 10) || 0; } catch (e) {}
  if (!(level >= 0 && level < SIZES.length)) level = 0;

  function apply() {
    document.documentElement.style.setProperty('--scale', SIZES[level]);
    var btns = document.querySelectorAll('[data-fontsize]');
    for (var i = 0; i < btns.length; i++) btns[i].setAttribute('data-level', level + 1);
  }
  apply();

  document.addEventListener('click', function (e) {
    var t = e.target;
    var fs = t.closest && t.closest('[data-fontsize]');
    if (fs) {
      level = (level + 1) % SIZES.length;
      apply();
      try { localStorage.setItem(KEY, level); } catch (err) {}
      return;
    }

    var copy = t.closest && t.closest('[data-copy]');
    if (copy) {
      var link = copy.getAttribute('data-copy') || location.href;
      var done = function () { copy.textContent = copy.getAttribute('data-done'); };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(link).then(done, function () { copy.textContent = link; });
      } else {
        copy.textContent = link;
      }
      return;
    }

    var yt = t.closest && t.closest('[data-yt]');
    if (yt) {
      e.preventDefault();
      var id = yt.getAttribute('data-yt');
      var frame = document.createElement('iframe');
      frame.src = 'https://www.youtube-nocookie.com/embed/' + encodeURIComponent(id) + '?autoplay=1';
      frame.title = yt.textContent.trim();
      frame.allow = 'autoplay; encrypted-media; picture-in-picture';
      frame.allowFullscreen = true;
      yt.replaceChildren(frame);
      yt.removeAttribute('href');
      yt.removeAttribute('data-yt');
    }
  });
})();
