/* The Android shell's side of the page. scripts/build-www.mjs puts this first
   in <head> of the APK's copy of index.html; the web build never sees it.
   It adapts the page to a Capacitor WebView and changes nothing in the game. */
(function () {
  'use strict';
  var W = window, D = document;
  W.DGH_NATIVE = 'android';
  W.DGH_BUILD = __DGH_BUILD__;

  /* 1. FULLSCREEN AND ORIENTATION ARE THE ACTIVITY'S JOB HERE.
     MainActivity is locked to landscape and runs immersive, so the page's own
     goImmersive() must find nothing to call. In a WebView the Fullscreen API
     hands the whole page to onShowCustomView, and orientation.lock() rejects.
     With requestFullscreen gone, goImmersive() falls through to lock(), which
     now resolves and does nothing. */
  try {
    D.documentElement.requestFullscreen = undefined;
    D.documentElement.webkitRequestFullscreen = undefined;
  } catch (e) {}
  try {
    if (screen.orientation && screen.orientation.lock)
      screen.orientation.lock = function () { return Promise.resolve(); };
  } catch (e) {}

  /* 2. SOUND STOPS WHEN THE APP LEAVES THE SCREEN, AND ONLY THEN.
     The game suspends its AudioContext on visibilitychange, but the music is
     <audio>, and a WebView keeps <audio> playing behind the home screen. Every
     media element and AudioContext that is ever used is remembered; whatever
     was running when the app went is stopped, and exactly that comes back.
     A play() asked for while away is deferred rather than refused, so a track
     change that lands in the background still happens -- on return.
     MainActivity also fires dgh:pause / dgh:resume, because visibilitychange
     is the page's view of the lifecycle and the activity's is the one that is
     always right. Both paths are idempotent.
     resume() is held too: the game's actx() resumes a suspended context on
     every sound it plays, so while frames still run -- the moment between
     dgh:pause and the page going hidden, or a device that keeps ticking a
     background WebView -- the next footstep would undo the suspend. */
  var media = new Set(), ctxs = [], held = null;
  var play = HTMLMediaElement.prototype.play;
  HTMLMediaElement.prototype.play = function () {
    media.add(this);
    if (held) { if (held.indexOf(this) < 0) held.push(this); return Promise.resolve(); }
    return play.apply(this, arguments);
  };
  var AC = W.AudioContext || W.webkitAudioContext;
  var resume = AC && AC.prototype.resume;
  if (resume) AC.prototype.resume = function () {
    if (held) { this.__dghHeld = true; return Promise.resolve(); }
    return resume.apply(this, arguments);
  };
  ['AudioContext', 'webkitAudioContext'].forEach(function (k) {
    var C = W[k];
    if (!C) return;
    var Wrapped = function (opts) {
      var c = arguments.length ? new C(opts) : new C();
      ctxs.push(c);
      return c;
    };
    Wrapped.prototype = C.prototype;         // instanceof still answers true
    W[k] = Wrapped;
  });
  function away() {
    if (held) return;
    held = [];
    media.forEach(function (m) {
      if (!m.paused) { held.push(m); try { m.pause(); } catch (e) {} }
    });
    ctxs.forEach(function (c) {
      if (c.state === 'running') { c.__dghHeld = true; try { c.suspend(); } catch (e) {} }
    });
  }
  function back() {
    if (!held) return;
    var list = held;
    held = null;
    ctxs.forEach(function (c) {
      if (c.__dghHeld) { c.__dghHeld = false; try { resume.call(c); } catch (e) {} }
    });
    list.forEach(function (m) {
      try { var p = play.call(m); if (p && p.catch) p.catch(function () {}); } catch (e) {}
    });
  }
  D.addEventListener('visibilitychange', function () { D.hidden ? away() : back(); });
  W.addEventListener('dgh:pause', away);
  W.addEventListener('dgh:resume', back);

  /* 3. THE BACK BUTTON. MainActivity asks this first and minimises the app
     when it answers false. An open panel is closed with its OWN close button,
     never with a synthetic Escape: the game's Escape handler only knows the
     shop, and fired at the options panel it redraws the menu underneath it.
     The death card is deliberately not here -- back must never spend or
     refuse a revive on the player's behalf. */
  var CLOSERS = [['dailyM', 'dayX'], ['opts', 'optX'], ['shop', 'shopBack']];
  W.__dghBack = function () {
    for (var i = 0; i < CLOSERS.length; i++) {
      var panel = D.getElementById(CLOSERS[i][0]);
      var btn = D.getElementById(CLOSERS[i][1]);
      if (panel && btn && panel.classList.contains('show')) { btn.click(); return true; }
    }
    return false;
  };
})();
