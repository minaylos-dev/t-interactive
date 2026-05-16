// Simple pass-through mover for trackball data
// Always returns the latest sample without filtering, cooldowns or gesture detection
export default class TrackballMove {
  constructor() {
    this.last = null
  }

  // Accepts sample {rx, ry, rz, wx, wy, wz, ts}
  // Returns the same sample immediately for direct consumption
  process(sample) {
    if (!sample) return null
    this.last = sample
    return sample
  }
}
