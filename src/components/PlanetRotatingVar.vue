<template>
  <div ref="container" class="planet-scene w-full h-full"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'
import { MTLLoader } from 'three/examples/jsm/loaders/MTLLoader'
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader'

const container = ref(null)

let renderer, scene, camera, animationId, planet, pivot
let targetRotationX = 0
let targetRotationY = 0

function onMouseMove(e) {
  const el = container.value
  if (!el) return
  const rect = el.getBoundingClientRect()
  const nx = (e.clientX - rect.left) / rect.width // 0..1
  const ny = (e.clientY - rect.top) / rect.height
  // map to -1..1
  const mx = nx * 2 - 1
  const my = ny * 2 - 1
  // increase range so mouse produces stronger rotation around planet center
  targetRotationY = mx * Math.PI * 0.6
  targetRotationX = my * Math.PI * 0.45
}

onMounted(() => {
  const el = container.value
  if (!el) return

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x000000)

  const width = el.clientWidth || 800
  const height = el.clientHeight || 600

  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000)
  camera.position.set(0, 0, 3.5)
  camera.lookAt(0, 0, 0)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setPixelRatio(window.devicePixelRatio || 1)
  renderer.setSize(width, height)
  renderer.outputEncoding = THREE.sRGBEncoding
  el.appendChild(renderer.domElement)

  // lights
  const ambient = new THREE.AmbientLight(0xffffff, 0.05)
  scene.add(ambient)
  const hemi = new THREE.HemisphereLight(0xffffff, 0.4)
//   scene.add(hemi)
  const dir = new THREE.DirectionalLight(0xffffff, 2)
  dir.position.set(5, 5, 5)
  scene.add(dir)

  // Load model (MTL then OBJ)
  const mtlLoader = new MTLLoader()
  const objLoader = new OBJLoader()

  const resourcePath = new URL('../assets/planet/', import.meta.url).href
  const mtlUrl = new URL('../assets/planet/output.mtl', import.meta.url).href
  const objUrl = new URL('../assets/planet/output.obj', import.meta.url).href

  // ensure loader resolves texture paths relative to the assets folder
  if (mtlLoader.setResourcePath) mtlLoader.setResourcePath(resourcePath)

  mtlLoader.load(
    mtlUrl,
    (materials) => {
      materials.preload()
      objLoader.setMaterials(materials)
      objLoader.load(
        objUrl,
        (object) => {
          planet = object
          // compute model center and recenter geometry vertices so each mesh is truly centered
          const box = new THREE.Box3().setFromObject(planet)
          const center = box.getCenter(new THREE.Vector3())

          planet.traverse((c) => {
            if (c.isMesh && c.geometry && c.geometry.isBufferGeometry) {
              // translate geometry vertices to remove local offsets
              c.geometry.translate(-center.x, -center.y, -center.z)
              c.geometry.computeBoundingBox()
              c.geometry.computeBoundingSphere()
            }
          })

          // recompute bounds after centering and scale
          const box2 = new THREE.Box3().setFromObject(planet)
          const size = new THREE.Vector3()
          box2.getSize(size)
          const maxDim = Math.max(size.x, size.y, size.z)
          const scale = 1.5 / (maxDim || 1)
          planet.scale.setScalar(scale)
          planet.position.set(0, 0, 0)

          // Load and apply PBR textures (color, normal, metallic-roughness)
          const texLoader = new THREE.TextureLoader()
          const colorUrl = new URL('../assets/planet/texture_pbr_20250901.png', import.meta.url).href
          const normalUrl = new URL('../assets/planet/texture_pbr_20250901_normal.png', import.meta.url).href
          const metalRoughUrl = new URL('../assets/planet/texture_pbr_20250901_metallic-texture_pbr_20250901_roughness.png', import.meta.url).href

          const colorMap = texLoader.load(colorUrl)
          const normalMap = texLoader.load(normalUrl)
          const metalRoughMap = texLoader.load(metalRoughUrl)

          colorMap.encoding = THREE.sRGBEncoding
          normalMap.encoding = THREE.LinearEncoding
          metalRoughMap.encoding = THREE.LinearEncoding

          planet.traverse((c) => {
            if (c.isMesh) {
              const mats = Array.isArray(c.material) ? c.material : [c.material]
              mats.forEach((mat) => {
                if (!mat) return
                // force material base color to white for consistent tint
                if (mat.color && typeof mat.color.set === 'function') {
                  mat.color.set(0xffffff)
                } else {
                  mat.color = new THREE.Color(0xffffff)
                }
                mat.map = colorMap
                mat.normalMap = normalMap
                mat.metalnessMap = metalRoughMap
                mat.roughnessMap = metalRoughMap
                mat.metalness = 1.0
                mat.roughness = 1.0
                mat.needsUpdate = true
              })
            }
          })

          // initial orientation
          planet.rotation.set(0, 0, 0)
          // create a pivot at origin and attach planet so rotations occur around planet center
          pivot = new THREE.Object3D()
          pivot.add(planet)
          scene.add(pivot)
        },
        undefined,
        (err) => {
          // ignore load errors in UI
        }
      )
    },
    undefined,
    (err) => {
      // ignore mtl errors
    }
  )

  function onResize() {
    if (!el) return
    const w = el.clientWidth
    const h = el.clientHeight
    camera.aspect = w / h
    camera.updateProjectionMatrix()
    renderer.setSize(w, h)
  }

  window.addEventListener('resize', onResize)
  window.addEventListener('mousemove', onMouseMove)

  function animate() {
    animationId = requestAnimationFrame(animate)
    if (pivot) {
      // rotation only on the pivot so planet rotates around its true center
      pivot.rotation.y += (targetRotationY - pivot.rotation.y) * 0.14
      pivot.rotation.x += (targetRotationX - pivot.rotation.x) * 0.14
    }
    renderer.render(scene, camera)
  }

  animate()

  onUnmounted(() => {
    window.removeEventListener('resize', onResize)
    window.removeEventListener('mousemove', onMouseMove)
    if (animationId) cancelAnimationFrame(animationId)
    if (renderer) {
      renderer.dispose()
      if (renderer.domElement && renderer.domElement.parentNode) renderer.domElement.parentNode.removeChild(renderer.domElement)
    }
    if (pivot && pivot.parent) pivot.parent.remove(pivot)
    scene = null
    camera = null
    planet = null
    pivot = null
  })
})
</script>

<style scoped>
.planet-scene {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
</style>
