// Video background fade system
(function () {
  const video = document.getElementById('bg-video');
  if (!video) return;

  let rafId = null;
  let fadingOutRef = false;

  function cancelAnim() {
    if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
  }

  function fadeIn(from) {
    cancelAnim();
    let opacity = from;
    function step() {
      opacity = Math.min(1, opacity + 0.033);
      video.style.opacity = opacity;
      if (opacity < 1) rafId = requestAnimationFrame(step);
    }
    rafId = requestAnimationFrame(step);
  }

  function fadeOut() {
    cancelAnim();
    let opacity = parseFloat(video.style.opacity) || 1;
    function step() {
      opacity = Math.max(0, opacity - 0.033);
      video.style.opacity = opacity;
      if (opacity > 0) rafId = requestAnimationFrame(step);
    }
    rafId = requestAnimationFrame(step);
  }

  video.addEventListener('canplay', function onReady() {
    video.removeEventListener('canplay', onReady);
    video.play().catch(() => {});
    fadeIn(0);
  });

  video.addEventListener('timeupdate', function () {
    if (!fadingOutRef && video.duration - video.currentTime <= 0.55) {
      fadingOutRef = true;
      fadeOut();
    }
  });

  video.addEventListener('ended', function () {
    cancelAnim();
    video.style.opacity = 0;
    setTimeout(function () {
      fadingOutRef = false;
      video.currentTime = 0;
      video.play().catch(() => {});
      fadeIn(0);
    }, 100);
  });
})();

// Filter pills (category page)
document.querySelectorAll('.filter-pill').forEach(function (pill) {
  pill.addEventListener('click', function () {
    document.querySelectorAll('.filter-pill').forEach(function (p) { p.classList.remove('active'); });
    pill.classList.add('active');
  });
});

// Email subscribe
document.querySelectorAll('.email-bar button').forEach(function (btn) {
  btn.addEventListener('click', function () {
    const input = btn.previousElementSibling;
    if (input && input.value.includes('@')) {
      input.value = '';
      input.placeholder = 'You\'re subscribed ✓';
    }
  });
});
