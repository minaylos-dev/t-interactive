import * as THREE from 'three'

const WORLD_Y = new THREE.Vector3(0, 1, 0)

export function createSensorGeometry(theta = (135 * Math.PI) / 180) {
  const phis = [0, (2 * Math.PI) / 3, (4 * Math.PI) / 3]

  const points = phis.map((phi) =>
    new THREE.Vector3(
      Math.sin(theta) * Math.cos(phi),
      Math.cos(theta),
      Math.sin(theta) * Math.sin(phi)
    ).normalize()
  )

  const sensors = points.map((p) => {
    const Z = p.clone().negate() // optical axis: from sensor toward centre
    const Y_temp = WORLD_Y.clone().sub(Z.clone().multiplyScalar(WORLD_Y.dot(Z))).normalize()
    const X = new THREE.Vector3().crossVectors(Y_temp, Z).normalize()
    const Y = Y_temp
    return { point: p, X, Y, Z }
  })

  return sensors
}
