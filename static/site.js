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

  // 타임머신 숫자: 지금 연도에서 기사 연도로 한 번만 거꾸로 돌아갑니다
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var counters = document.querySelectorAll('[data-count-to]');
  for (var c = 0; c < counters.length; c++) {
    (function (el) {
      var from = parseInt(el.getAttribute('data-count-from'), 10);
      var to = parseInt(el.getAttribute('data-count-to'), 10);
      if (reduce || !(from > to)) return;
      var start = null, dur = 1600;
      el.textContent = from;
      function step(t) {
        if (start === null) start = t;
        var p = Math.min(1, (t - start) / dur);
        var eased = 1 - Math.pow(1 - p, 3);
        el.textContent = Math.round(from - (from - to) * eased);
        if (p < 1) requestAnimationFrame(step);
      }
      setTimeout(function () { requestAnimationFrame(step); }, 300);
    })(counters[c]);
  }

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
      var box = document.createElement('div');
      box.className = yt.className;
      var tpl = yt.nextElementSibling;
      if (!tpl || !tpl.classList || !tpl.classList.contains('video-end')) tpl = null;
      var end = parseInt(yt.getAttribute('data-end') || '0', 10) || 0;
      var id = yt.getAttribute('data-yt');
      var label = yt.textContent.trim();
      yt.replaceWith(box);
      playVideo(box, id, end, tpl, label);
    }
  });

  // 2026-11-13: 사이트 영상은 맛보기 — 긴 영상은 data-end 초에서 멈추고, 끝나면 <template class="video-end"> 를 보여 줌.
  var apiWait = [];
  function loadApi(cb) {
    if (window.YT && window.YT.Player) { cb(); return; }
    apiWait.push(cb);
    if (apiWait.length > 1) return;
    var prev = window.onYouTubeIframeAPIReady;
    var flush = function (failed) { apiWait.splice(0).forEach(function (f) { f(failed); }); };
    window.onYouTubeIframeAPIReady = function () { if (prev) prev(); flush(false); };
    var s = document.createElement('script');
    s.src = 'https://www.youtube.com/iframe_api';
    s.onerror = function () { flush(true); };
    document.head.appendChild(s);
  }

  function plainFrame(box, id, end, label) {   // API 를 못 받으면 예전처럼(끝 초만 지정)
    var frame = document.createElement('iframe');
    frame.src = 'https://www.youtube-nocookie.com/embed/' + encodeURIComponent(id) + '?autoplay=1&rel=0' + (end ? '&end=' + end : '');
    frame.title = label;
    frame.allow = 'autoplay; encrypted-media; picture-in-picture';
    frame.allowFullscreen = true;
    box.replaceChildren(frame);
  }

  function playVideo(box, id, end, tpl, label) {
    box.classList.remove('video-ended');
    var holder = document.createElement('div');
    box.replaceChildren(holder);
    loadApi(function (failed) {
      if (failed || !window.YT || !window.YT.Player) { plainFrame(box, id, end, label); return; }
      var done = false, timer = null, player;
      var finish = function () {
        if (done) return;
        done = true;
        if (timer) clearInterval(timer);
        try { player.destroy(); } catch (err) {}
        if (!tpl) { plainFrame(box, id, 0, label); return; }
        box.classList.add('video-ended');
        box.replaceChildren(tpl.content.cloneNode(true));
        var again = box.querySelector('[data-replay]');
        if (again) again.addEventListener('click', function () { playVideo(box, id, end, tpl, label); });
      };
      var vars = { autoplay: 1, rel: 0, playsinline: 1 };
      if (end) vars.end = end;
      player = new window.YT.Player(holder, {
        host: 'https://www.youtube-nocookie.com', videoId: id, playerVars: vars,
        events: { onStateChange: function (ev) { if (ev.data === 0) finish(); } }
      });
      if (end) {   // 앞으로 건너뛰어도 맛보기 끝에서 멈춤
        timer = setInterval(function () {
          try { if (player.getCurrentTime && player.getCurrentTime() >= end) finish(); } catch (err) {}
        }, 500);
      }
    });
  }
})();
