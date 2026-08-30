(function () {
  'use strict';
  var reduce = matchMedia('(prefers-reduced-motion:reduce)').matches;

  // ---- Apparitions au defilement ----
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
  }, { threshold: 0.12 });
  document.querySelectorAll('.reveal').forEach(function (el, i) { el.style.transitionDelay = ((i % 3) * 80) + 'ms'; io.observe(el); });

  // ---- Menu mobile ----
  var burger = document.getElementById('burger'), mnav = document.getElementById('mobileNav');
  if (burger && mnav) {
    burger.onclick = function () { mnav.classList.add('open'); };
    document.getElementById('closeNav').onclick = function () { mnav.classList.remove('open'); };
    mnav.querySelectorAll('a').forEach(function (a) { a.onclick = function () { mnav.classList.remove('open'); }; });
  }

  // ---- Recherche ----
  var sBtn = document.getElementById('searchBtn'), sOv = document.getElementById('searchOverlay'), sInput = document.getElementById('searchInput');
  if (sBtn && sOv) {
    function openSearch() { sOv.classList.add('open'); setTimeout(function () { sInput.focus(); }, 60); }
    function closeSearch() { sOv.classList.remove('open'); }
    sBtn.onclick = openSearch;
    document.getElementById('searchClose').onclick = closeSearch;
    sOv.addEventListener('click', function (e) { if (e.target === sOv) closeSearch(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeSearch(); });
  }

  // ---- Menus deroulants au clic (support tactile, en plus du survol) ----
  document.querySelectorAll('.navpill .navitem .chev').forEach(function (ch) {
    ch.addEventListener('click', function (e) {
      e.preventDefault(); e.stopPropagation();
      var it = ch.closest('.navitem');
      document.querySelectorAll('.navitem.open').forEach(function (o) { if (o !== it) o.classList.remove('open'); });
      it.classList.toggle('open');
    });
  });
  document.addEventListener('click', function () { document.querySelectorAll('.navitem.open').forEach(function (o) { o.classList.remove('open'); }); });

  // ---- Carrousel "A la Une" + Mur de la presse (dynamiques, rafraichis en direct) ----
  var carousel = document.getElementById('heroCarousel'),
      dotsBox = document.getElementById('heroDots'),
      dmLabel = document.getElementById('dmLabel'),
      track = document.getElementById('track'),
      heroBg = document.getElementById('heroBg');
  var slides = [], dots = [], bgs = [], cur = 0, timer;

  function esc(t) { var d = document.createElement('div'); d.textContent = t || ''; return d.innerHTML; }
  function collect() {
    slides = carousel ? [].slice.call(carousel.querySelectorAll('.hero-slide')) : [];
    dots = dotsBox ? [].slice.call(dotsBox.querySelectorAll('button')) : [];
    bgs = heroBg ? [].slice.call(heroBg.querySelectorAll('.hbg')) : [];
  }
  function show(n) {
    if (!slides.length) return;
    cur = (n + slides.length) % slides.length;
    slides.forEach(function (s, i) { s.classList.toggle('on', i === cur); });
    bgs.forEach(function (b, i) { b.classList.toggle('on', i === cur); });
    dots.forEach(function (d, i) { d.classList.toggle('on', i === cur); });
  }
  function auto() { if (reduce || slides.length < 2) return; clearInterval(timer); timer = setInterval(function () { show(cur + 1); }, 5000); }
  function bindDots() { dots.forEach(function (d) { d.onclick = function () { show(+d.dataset.i); auto(); }; }); }

  function buildHero(items) {
    if (!carousel || !items.length) return;
    carousel.innerHTML = items.map(function (it, i) {
      return '<div class="hero-slide' + (i === 0 ? ' on' : '') + '"><a href="' + it.url + '" target="_blank" rel="noopener" style="color:#fff"><h1>' + esc(it.titre) + '</h1></a><span class="src"><span class="tag">' + esc(it.source) + '</span> ' + esc(it.time) + '</span></div>';
    }).join('');
    if (heroBg) heroBg.innerHTML = items.map(function (it, i) { return '<div class="hbg' + (i === 0 ? ' on' : '') + '"' + (it.image ? ' style="background-image:url(\'' + it.image + '\')"' : '') + '></div>'; }).join('');
    dotsBox.innerHTML = items.map(function (it, i) { return '<button' + (i === 0 ? ' class="on"' : '') + ' data-i="' + i + '"></button>'; }).join('');
    if (dmLabel && items[0]) dmLabel.textContent = 'Dernière minute · ' + items[0].datetime;
    cur = 0; collect(); bindDots(); auto();
  }
  function buildWall(items) {
    if (!track || !items.length) return;
    var one = items.map(function (it) {
      return '<a class="une" href="' + it.url + '" target="_blank" rel="noopener"><div class="thumb">' + (it.image ? '<img src="' + it.image + '" alt="" loading="lazy" onerror="this.remove()">' : '') + '</div><div class="body"><div class="src">' + esc(it.source) + '<span class="cat">' + esc(it.datetime) + '</span></div><div class="hl">' + esc(it.titre) + '</div></div></a>';
    }).join('');
    track.innerHTML = one + one;
  }

  // Initialisation : les slides sont rendus cote serveur, on branche la rotation.
  collect(); bindDots(); auto();
  if (track && track.children.length) { track.innerHTML = track.innerHTML + track.innerHTML; }

  // ---- Mur de la presse : defilement auto (rAF) + fleches gauche/droite ----
  var marquee = document.querySelector('.marquee');
  var wallPaused = false, wallResumeTimer, wallLast = 0;
  function wallLoop(ts) {
    var dt = wallLast ? ts - wallLast : 0;
    wallLast = ts;
    if (marquee && track && !wallPaused && !reduce && dt > 0 && dt < 120) {
      marquee.scrollLeft += 0.055 * dt;                 // ~55 px/s, vitesse constante
      var moitie = track.scrollWidth / 2;               // contenu duplique : boucle a la moitie
      if (moitie > 0 && marquee.scrollLeft >= moitie) marquee.scrollLeft -= moitie;
    }
    requestAnimationFrame(wallLoop);
  }
  function wallPause() { wallPaused = true; clearTimeout(wallResumeTimer); }
  function wallResume(delai) { clearTimeout(wallResumeTimer); wallResumeTimer = setTimeout(function () { wallPaused = false; }, delai || 0); }
  if (marquee && track) {
    // Pause au survol UNIQUEMENT avec une vraie souris : sur ecran tactile,
    // mouseenter se declenche au toucher mais mouseleave jamais -> resterait bloque.
    if (window.matchMedia && window.matchMedia('(hover:hover)').matches) {
      marquee.addEventListener('mouseenter', wallPause);
      marquee.addEventListener('mouseleave', function () { wallResume(300); });
    }
    marquee.addEventListener('touchstart', wallPause, { passive: true });
    marquee.addEventListener('touchend', function () { wallResume(2000); });
    marquee.addEventListener('wheel', function () { wallPause(); wallResume(2000); }, { passive: true });
    requestAnimationFrame(wallLoop);
    var pas = function () { var c = marquee.querySelector('.une'); return c ? c.offsetWidth + 16 : 240; };
    // Defilement fluide fait main (scrollBy 'smooth' n'est pas fiable partout).
    function wallVers(cible) {
      wallPause();
      var depart = marquee.scrollLeft, dist = cible - depart, t0 = null, duree = 380;
      function anim(ts) {
        if (t0 === null) t0 = ts;
        var p = Math.min(1, (ts - t0) / duree);
        marquee.scrollLeft = depart + dist * (0.5 - 0.5 * Math.cos(Math.PI * p));
        if (p < 1) requestAnimationFrame(anim); else wallResume(3500);
      }
      requestAnimationFrame(anim);
    }
    var prev = document.getElementById('wallPrev'), next = document.getElementById('wallNext');
    if (prev) prev.onclick = function () { wallVers(marquee.scrollLeft - pas() * 2); };
    if (next) next.onclick = function () { wallVers(marquee.scrollLeft + pas() * 2); };
  }

  // Rafraichissement en direct toutes les 45 s.
  function poll() {
    fetch('/api/latest/').then(function (r) { return r.json(); }).then(function (d) {
      if (d.items && d.items.length) { buildHero(d.items); buildWall(d.items); }
    }).catch(function () {});
  }
  if (carousel || track) { setInterval(poll, 30000); }

  // ---- Editeur de texte enrichi (page Publier) ----
  (function () {
    var editor = document.getElementById('richEditor');
    var toolbar = document.getElementById('richToolbar');
    var source = document.querySelector('.rich-source');
    if (!editor || !source || !toolbar) return;
    // Amelioration progressive : sans JS, le textarea reste utilisable.
    source.style.display = 'none';
    if (source.value.trim()) editor.innerHTML = source.value;
    try { document.execCommand('styleWithCSS', false, false); } catch (e) {}
    try { document.execCommand('defaultParagraphSeparator', false, 'p'); } catch (e) {}

    function sync() { source.value = editor.innerHTML === '<br>' ? '' : editor.innerHTML; }
    editor.addEventListener('input', sync);
    editor.addEventListener('blur', sync);

    toolbar.addEventListener('click', function (e) {
      var btn = e.target.closest('button'); if (!btn) return;
      e.preventDefault(); editor.focus();
      if (btn.dataset.cmd) {
        document.execCommand(btn.dataset.cmd, false, null);
      } else if (btn.dataset.block) {
        // Bascule le bloc (titre/citation) ou revient au paragraphe.
        var tag = btn.dataset.block;
        var cur = (document.queryCommandValue('formatBlock') || '').toLowerCase();
        document.execCommand('formatBlock', false, (cur === tag) ? 'p' : tag);
      } else if (btn.dataset.link) {
        var url = window.prompt('Adresse du lien (https://...)', 'https://');
        if (url) { document.execCommand('createLink', false, url); }
      }
      sync();
    });
    // Securite : synchronise une derniere fois avant l'envoi du formulaire.
    var form = editor.closest('form');
    if (form) form.addEventListener('submit', sync);
  })();

  // ---- Bascule thème clair / sombre ----
  (function () {
    var t = document.getElementById('themeToggle');
    if (!t) return;
    t.addEventListener('click', function () {
      var dark = document.documentElement.getAttribute('data-theme') === 'dark';
      var next = dark ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem('xamsa-theme', next); } catch (e) {}
    });
  })();

  // ---- Commentaires & reactions (page publication) ----
  (function () {
    function csrf() { var m = document.cookie.match(/csrftoken=([^;]+)/); return m ? m[1] : ''; }
    var jaime = document.getElementById('jaimeBtn');
    if (jaime) {
      jaime.addEventListener('click', function () {
        if (jaime.dataset.login) { window.location = jaime.dataset.login; return; }
        fetch(jaime.dataset.url, { method: 'POST', headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' } })
          .then(function (r) { return r.json(); })
          .then(function (d) { jaime.classList.toggle('on', d.a_aime); var c = document.getElementById('jaimeCount'); if (c) c.textContent = d.total; })
          .catch(function () {});
      });
    }
    var fav = document.getElementById('favBtn');
    if (fav) {
      fav.addEventListener('click', function () {
        if (fav.dataset.login) { window.location = fav.dataset.login; return; }
        fetch(fav.dataset.url, { method: 'POST', headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' } })
          .then(function (r) { return r.json(); })
          .then(function (d) {
            fav.classList.toggle('on', d.favori);
            var l = fav.querySelector('.fav-lbl'); if (l) l.textContent = d.favori ? 'Enregistré' : 'Lire plus tard';
          })
          .catch(function () {});
      });
    }
    document.querySelectorAll('.comm-reply-btn').forEach(function (b) {
      b.addEventListener('click', function () {
        var f = document.getElementById(b.dataset.target);
        if (f) { f.hidden = !f.hidden; if (!f.hidden) { var t = f.querySelector('textarea'); if (t) t.focus(); } }
      });
    });
    // Copier le lien de la publication
    document.querySelectorAll('.share-copy').forEach(function (b) {
      b.addEventListener('click', function () {
        var url = b.dataset.url || window.location.href;
        var done = function () { b.classList.add('ok'); setTimeout(function () { b.classList.remove('ok'); }, 1500); };
        if (navigator.clipboard) { navigator.clipboard.writeText(url).then(done).catch(done); }
        else { var t = document.createElement('textarea'); t.value = url; document.body.appendChild(t); t.select(); try { document.execCommand('copy'); } catch (e) {} t.remove(); done(); }
      });
    });
  })();

  // ---- Chatbot "Looy laaj ?" ----
  var panel = document.getElementById('chatPanel');
  if (!panel) return;
  var ov = document.getElementById('chatOverlay'), cbody = document.getElementById('chatBody'), input = document.getElementById('chatText');
  function openChat() { panel.classList.add('open'); ov.classList.add('open'); panel.setAttribute('aria-hidden', 'false'); input.focus(); }
  function closeChat() { panel.classList.remove('open'); ov.classList.remove('open'); panel.setAttribute('aria-hidden', 'true'); }
  document.getElementById('fab').onclick = openChat;
  document.getElementById('chatClose').onclick = closeChat;
  ov.onclick = closeChat;
  // Lecture vocale de la reponse (synthese vocale du navigateur).
  function speak(text) {
    if (!window.speechSynthesis || !text) return;
    window.speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(text); u.lang = 'fr-FR'; u.rate = 1;
    window.speechSynthesis.speak(u);
  }
  function iconBtn(cls, label, svg) {
    var b = document.createElement('button'); b.type = 'button';
    b.className = 'msg-btn ' + cls; b.setAttribute('aria-label', label); b.innerHTML = svg; return b;
  }
  var ICON_EDIT = '<svg class="icon" viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>';
  var ICON_LISTEN = '<svg class="icon" viewBox="0 0 24 24"><path d="M11 5 6 9H2v6h4l5 4V5Z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M19 5a9 9 0 0 1 0 14"/></svg>';

  // turns = source de verite (DOM + historique synchronises).
  var turns = [];
  function addMessage(text, who) {
    var d = document.createElement('div'); d.className = 'msg ' + who;
    var p = document.createElement('p'); p.style.whiteSpace = 'pre-wrap'; p.textContent = text;
    d.appendChild(p);
    var act = document.createElement('div'); act.className = 'msg-actions';
    var turn = { role: who, texte: text, el: d };
    if (who === 'me') {
      var edit = iconBtn('edit', 'Modifier ce message', ICON_EDIT);
      edit.onclick = function () { editFrom(turn); };
      act.appendChild(edit);
    } else {
      var listen = iconBtn('listen', 'Ecouter la reponse', ICON_LISTEN);
      listen.onclick = function () { speak(text); };
      act.appendChild(listen);
    }
    d.appendChild(act);
    cbody.appendChild(d); cbody.scrollTop = cbody.scrollHeight;
    turns.push(turn);
    return d;
  }
  // Modifier un message deja envoye : on le remet dans le champ et on retire
  // ce message ainsi que tout ce qui suit (question + reponses), pour regenerer.
  function editFrom(turn) {
    var i = turns.indexOf(turn); if (i < 0) return;
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    input.value = turn.texte;
    while (turns.length > i) { var last = turns.pop(); if (last.el) last.el.remove(); }
    input.focus();
  }
  function historique() {
    return turns.map(function (t) { return { role: t.role === 'me' ? 'user' : 'bot', texte: t.texte }; });
  }
  // ---- Intentions : rechercher / retrouver / comparer / expliquer ----
  var currentMode = 'rechercher';
  document.querySelectorAll('#chatModes .chat-mode').forEach(function (b) {
    b.onclick = function () {
      document.querySelectorAll('#chatModes .chat-mode').forEach(function (x) { x.classList.remove('active'); });
      b.classList.add('active'); currentMode = b.dataset.mode; input.focus();
    };
  });
  function esc(s) { var d = document.createElement('div'); d.textContent = s == null ? '' : s; return d.innerHTML; }
  // Bloc « Sources -> dates -> liens -> niveau de confiance » sous une reponse.
  function renderSources(el, data) {
    var sources = data.sources || [], conf = data.confiance;
    if ((!sources.length) && !conf) return;
    var box = document.createElement('div'); box.className = 'msg-sources';
    if (sources.length) {
      var h = document.createElement('div'); h.className = 'src-title'; h.textContent = 'Sources'; box.appendChild(h);
      var ul = document.createElement('ul'); ul.className = 'src-list';
      sources.forEach(function (s) {
        var li = document.createElement('li');
        var meta = s.origine ? esc(s.origine) : '';
        if (s.date) meta += (meta ? ' &middot; ' : '') + esc(s.date);
        li.innerHTML = (meta ? '<span class="src-meta">' + meta + '</span>' : '') +
          '<a href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(s.titre || s.url) + '</a>';
        ul.appendChild(li);
      });
      box.appendChild(ul);
    }
    if (conf && conf.niveau) {
      var lvl = conf.niveau.toLowerCase();
      var cls = lvl.indexOf('lev') >= 0 ? 'high' : (lvl.indexOf('oy') >= 0 ? 'mid' : 'low');
      var c = document.createElement('div'); c.className = 'conf-badge ' + cls;
      c.innerHTML = '<b>Niveau de confiance : ' + esc(conf.niveau) + '</b>' +
        (conf.note ? '<span>' + esc(conf.note) + '</span>' : '');
      box.appendChild(c);
    }
    el.appendChild(box); cbody.scrollTop = cbody.scrollHeight;
  }
  function ask(q) {
    var prev = historique().slice(-8);   // historique anterieur (avant cette question)
    addMessage(q, 'me');
    var t = document.createElement('div'); t.className = 'msg bot typing'; t.innerHTML = '<span></span><span></span><span></span>';
    cbody.appendChild(t); cbody.scrollTop = cbody.scrollHeight;
    fetch('/assistant/ask/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: q, historique: prev, mode: currentMode }) })
      .then(function (r) { return r.json(); }).then(function (data) { t.remove(); var el = addMessage(data.texte || '', 'bot'); renderSources(el, data); })
      .catch(function () { t.remove(); addMessage('Une erreur est survenue. Reessayez.', 'bot'); });
  }
  document.querySelectorAll('.chip').forEach(function (c) { c.onclick = function () { ask(c.textContent.trim()); }; });
  function send() { var v = input.value.trim(); if (v) { ask(v); input.value = ''; } }
  document.getElementById('chatSend').onclick = send;
  input.addEventListener('keydown', function (e) { if (e.key === 'Enter') send(); });

  // ---- Message vocal (reconnaissance vocale du navigateur) ----
  var micBtn = document.getElementById('chatMic');
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (micBtn && SR) {
    var recog = new SR(); recog.lang = 'fr-FR'; recog.interimResults = false; recog.maxAlternatives = 1;
    var recording = false;
    recog.onresult = function (e) { input.value = e.results[0][0].transcript; };
    recog.onend = function () { recording = false; micBtn.classList.remove('rec'); var v = input.value.trim(); if (v) { ask(v); input.value = ''; } };
    recog.onerror = function () { recording = false; micBtn.classList.remove('rec'); };
    micBtn.onclick = function () {
      if (recording) { recog.stop(); return; }
      input.value = '';
      try { recog.start(); recording = true; micBtn.classList.add('rec'); } catch (e) { recording = false; }
    };
  } else if (micBtn) {
    micBtn.title = "La saisie vocale n'est pas prise en charge par ce navigateur.";
    micBtn.disabled = true; micBtn.style.opacity = '.45'; micBtn.style.cursor = 'not-allowed';
  }
})();
