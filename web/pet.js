// 小满的「形」：一个小团子。会呼吸、会眨眼。
// 情绪只有 calm / tired 两档，第 1 步够用。

const PET_SVG = `
<svg viewBox="0 0 64 64" role="img" aria-label="小满">
  <defs>
    <radialGradient id="petGrad" cx="34%" cy="26%" r="78%">
      <stop offset="0%" stop-color="#f8dfc0" />
      <stop offset="58%" stop-color="#ecc08d" />
      <stop offset="100%" stop-color="#d99b64" />
    </radialGradient>
  </defs>
  <ellipse cx="32" cy="59" rx="13" ry="2.6" fill="rgba(0,0,0,0.25)" />
  <g class="body">
    <rect class="blob" x="9" y="8" width="46" height="46" rx="19" />
    <g class="eyes">
      <ellipse class="eye" cx="24.5" cy="29" rx="2.7" ry="3.5" />
      <ellipse class="eye" cx="39.5" cy="29" rx="2.7" ry="3.5" />
    </g>
    <path class="mouth" d="M28.5 37.5 q3.5 3 7 0" />
    <circle class="cheek" cx="17.5" cy="35.5" r="2.6" />
    <circle class="cheek" cx="46.5" cy="35.5" r="2.6" />
  </g>
</svg>`;

export function mountPet(host) {
  if (!host) return;
  host.innerHTML = PET_SVG;
}

export function setMood(host, mood) {
  if (!host) return;
  host.dataset.mood = mood === "tired" ? "tired" : "calm";
}
