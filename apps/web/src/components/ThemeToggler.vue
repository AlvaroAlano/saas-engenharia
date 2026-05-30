<script setup lang="ts">
import { isDark, toggleTheme } from '../composables/useTheme'

const maskId = `tm-${Math.random().toString(36).slice(2, 8)}`

const props = withDefaults(defineProps<{ sound?: boolean }>(), { sound: false })

let _ctx: AudioContext | null = null
let _buf: AudioBuffer | null = null
let _lastSnd = 0

function playClick() {
  const now = performance.now()
  if (now - _lastSnd < 80) return
  _lastSnd = now
  try {
    if (!_ctx) _ctx = new AudioContext()
    if (_ctx.state === 'suspended') _ctx.resume()
    if (!_buf || _buf.sampleRate !== _ctx.sampleRate) {
      const rate = _ctx.sampleRate
      const len = Math.floor(rate * 0.006)
      _buf = _ctx.createBuffer(1, len, rate)
      const ch = _buf.getChannelData(0)
      for (let i = 0; i < len; i++) {
        const t = i / len
        ch[i] = (Math.sin(2 * Math.PI * 3400 * t) * 0.6 + (Math.random() * 2 - 1) * 0.4) * (1 - t) ** 3
      }
    }
    const src = _ctx.createBufferSource()
    const gain = _ctx.createGain()
    src.buffer = _buf
    gain.gain.value = 0.08
    src.connect(gain)
    gain.connect(_ctx.destination)
    src.start()
  } catch { /* silent */ }
}

function handleToggle() {
  toggleTheme()
  if (props.sound) playClick()
}
</script>

<template>
  <button
    @click="handleToggle"
    class="p-2 flex items-center justify-center rounded-md cursor-pointer focus:outline-none text-ink-muted hover:text-ink hover:bg-surface-hover tog-btn"
    :aria-label="isDark ? 'Ativar modo claro' : 'Ativar modo escuro'"
  >
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      :class="['tog-svg', { 'is-dark': isDark }]"
      style="overflow: visible"
    >
      <defs>
        <mask :id="maskId">
          <rect x="0" y="0" width="100%" height="100%" fill="white" />
          <!-- Hole moves far away (no crescent) → overlaps center (carves crescent) -->
          <circle r="9" fill="black" :class="['tog-mask', { 'is-dark': isDark }]" />
        </mask>
      </defs>

      <!-- Sun core (r=5) morphs into moon body (r=9) -->
      <circle
        cx="12"
        cy="12"
        fill="currentColor"
        stroke="none"
        :mask="`url(#${maskId})`"
        :class="['tog-body', { 'is-dark': isDark }]"
      />

      <!-- Rays: shrink + rotate away when going dark -->
      <g :class="['tog-rays', { 'is-dark': isDark }]" style="transform-origin: 12px 12px">
        <line x1="12"   y1="1"     x2="12"   y2="3"    />
        <line x1="12"   y1="21"    x2="12"   y2="23"   />
        <line x1="1"    y1="12"    x2="3"    y2="12"   />
        <line x1="21"   y1="12"    x2="23"   y2="12"   />
        <line x1="5.64" y1="5.64"  x2="4.22" y2="4.22" />
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        <line x1="5.64" y1="18.36" x2="4.22" y2="19.78" />
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
      </g>
    </svg>
  </button>
</template>

<style scoped>
/* Spring easing — approximates stiffness:380 damping:30 from motion/react */

.tog-btn {
  -webkit-tap-highlight-color: transparent;
  transition: transform 0.15s cubic-bezier(0.34, 1.56, 0.64, 1),
              background-color 0.15s ease;
}
.tog-btn:hover  { transform: scale(1.08); }
.tog-btn:active { transform: scale(0.86); }

/* Whole SVG rotates 270° on dark, back to 0° on light */
.tog-svg {
  transform: rotate(0deg);
  transition: transform 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.tog-svg.is-dark { transform: rotate(270deg); }

/* Mask hole: cx=33 cy=0 (far, no crescent) → cx=17 cy=8 (overlapping, crescent) */
.tog-mask {
  cx: 33px;
  cy: 0px;
  transition: cx 0.45s cubic-bezier(0.34, 1.56, 0.64, 1),
              cy 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.tog-mask.is-dark { cx: 17px; cy: 8px; }

/* Center circle: r=5 (sun) → r=9 (full moon body) */
.tog-body {
  r: 5px;
  transition: r 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.tog-body.is-dark { r: 9px; }

/* Rays: visible+full → invisible+shrunk+rotated */
.tog-rays {
  opacity: 1;
  transform: scale(1) rotate(0deg);
  transition: opacity  0.3s cubic-bezier(0.34, 1.56, 0.64, 1),
              transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.tog-rays.is-dark {
  opacity: 0;
  transform: scale(0) rotate(-30deg);
}
</style>
