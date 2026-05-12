import * as THREE from 'three'

function skewMatrixFromVec(v) {
  // returns a Matrix3 representing the skew-symmetric matrix [v]_
  return new THREE.Matrix3().set(
    0, -v.z, v.y,
    v.z, 0, -v.x,
    -v.y, v.x, 0
  )
}

function rowFromSensor(sensor, axis) {
  // -[p]_x * axis projection
  const S = skewMatrixFromVec(sensor.point).multiplyScalar(-1)
  // S is Matrix3; extract columns as vectors to compute dot with axis
  const e = S.elements
  const c0 = new THREE.Vector3(e[0], e[3], e[6])
  const c1 = new THREE.Vector3(e[1], e[4], e[7])
  const c2 = new THREE.Vector3(e[2], e[5], e[8])
  return new THREE.Vector3(axis.dot(c0), axis.dot(c1), axis.dot(c2))
}

export function createProjection(sensors) {
  // M: 6 rows x 3 cols
  const M = sensors.flatMap((s) => [rowFromSensor(s, s.X), rowFromSensor(s, s.Y)])

  // compute MTM (3x3)
  const MTM = new THREE.Matrix3()
  const mtmEls = []
  for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 3; j++) {
      let sum = 0
      for (let k = 0; k < 6; k++) sum += M[k].getComponent(i) * M[k].getComponent(j)
      mtmEls.push(sum)
    }
  }
  MTM.set(...mtmEls)

  const MTM_inv = MTM.clone()
  MTM_inv.invert()

  // M_plus: 3x6 => represented as 6 column Vector3s
  const M_plus = Array.from({ length: 6 }, (_, k) => {
    const row = M[k]
    return new THREE.Vector3(
      MTM_inv.elements[0] * row.x + MTM_inv.elements[1] * row.y + MTM_inv.elements[2] * row.z,
      MTM_inv.elements[3] * row.x + MTM_inv.elements[4] * row.y + MTM_inv.elements[5] * row.z,
      MTM_inv.elements[6] * row.x + MTM_inv.elements[7] * row.y + MTM_inv.elements[8] * row.z
    )
  })

  return (deltas, sensitivity = 1) => {
    const rot = new THREE.Vector3()
    for (let k = 0; k < 6; k++) rot.addScaledVector(M_plus[k], deltas[k] * sensitivity)
    return rot
  }
}
