// Gesture detector for trackball rotation data
export default class TrackballGesture {
  constructor(opts = {}) {
    this.windowSec = opts.windowSec ?? 0.6
    this.xThresh = opts.xThresh ?? 0.5
    this.yThresh = opts.yThresh ?? 0.5
    this.zThresh = opts.zThresh ?? 0.5
    this.cooldownMs = opts.cooldownMs ?? 600
    this.samples = []
    this.lastTrigger = 0
  }

  // push a new sample: {rx, ry, rz, ts}
  process(sample) {
    if (!sample || typeof sample.ts !== 'number') return null

    const now = sample.ts
    // convert ts to seconds if ts looks like epoch seconds or milliseconds
    // assume incoming ts from Python is seconds (time.time())

    // append sample
    this.samples.push({ rx: sample.rx, ry: sample.ry, rz: sample.rz, ts: sample.ts })

    // remove old samples outside the window
    const minTs = now - this.windowSec
    while (this.samples.length > 1 && this.samples[0].ts < minTs) {
      this.samples.shift()
    }

    // need at least two samples to compute delta
    if (this.samples.length < 2) return null

    const first = this.samples[0]
    const last = this.samples[this.samples.length - 1]

    const dx = last.rx - first.rx
    const dy = last.ry - first.ry
    const dz = last.rz - first.rz

    const adx = Math.abs(dx)
    const ady = Math.abs(dy)
    const adz = Math.abs(dz)

    const nowMs = Date.now()
    if (nowMs - this.lastTrigger < this.cooldownMs) return null

    // determine which axis dominates
    if (adx >= this.xThresh && adx > ady && adx > adz) {
      this.lastTrigger = nowMs
      this.samples = []
      return { axis: 'x', dir: Math.sign(dx) || 1, value: dx }
    }

    if (ady >= this.yThresh && ady > adx && ady > adz) {
      this.lastTrigger = nowMs
      this.samples = []
      return { axis: 'y', dir: Math.sign(dy) || 1, value: dy }
    }

    if (adz >= this.zThresh && adz > adx && adz > ady) {
      this.lastTrigger = nowMs
      this.samples = []
      return { axis: 'z', dir: Math.sign(dz) || 1, value: dz }
    }

    return null
  }
}
