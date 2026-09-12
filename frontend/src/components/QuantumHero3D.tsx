import React, { useEffect, useRef } from "react"
import * as THREE from "three"
import s from "./QuantumHero3D.module.css"

interface QuantumHero3DProps {
  onOpenBrain?: () => void
}

export const QuantumHero3D: React.FC<QuantumHero3DProps> = ({ onOpenBrain }) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const container = containerRef.current
    const canvas = canvasRef.current
    if (!container || !canvas) return

    let animId: number
    const width = container.clientWidth || 420
    const height = container.clientHeight || 460

    // 1. Three.js Scene Setup
    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100)
    camera.position.set(0, 0, 8.5)

    const renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))

    // 2. Quantum State Group
    const group = new THREE.Group()
    scene.add(group)

    // Inner pulsating core
    const coreGeo = new THREE.IcosahedronGeometry(1.3, 3)
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      wireframe: true,
      transparent: true,
      opacity: 0.35,
    })
    const coreMesh = new THREE.Mesh(coreGeo, coreMat)
    group.add(coreMesh)

    // Central solid glow sphere
    const glowGeo = new THREE.SphereGeometry(0.75, 24, 24)
    const glowMat = new THREE.MeshBasicMaterial({
      color: 0x60a5fa,
      transparent: true,
      opacity: 0.6,
    })
    const glowMesh = new THREE.Mesh(glowGeo, glowMat)
    group.add(glowMesh)

    // 3. Entangled Qubit Nodes (Superposition Cloud)
    const nodeCount = 36
    const nodeGeo = new THREE.SphereGeometry(0.07, 12, 12)
    const nodeMats = [
      new THREE.MeshBasicMaterial({ color: 0x38bdf8 }), // cyan
      new THREE.MeshBasicMaterial({ color: 0xc084fc }), // purple
      new THREE.MeshBasicMaterial({ color: 0xfbbf24 }), // gold
    ]

    const nodeMeshes: THREE.Mesh[] = []
    const nodePositions: THREE.Vector3[] = []

    for (let i = 0; i < nodeCount; i++) {
      // Distribute points on sphere using Fibonacci spiral
      const phi = Math.acos(1 - (2 * (i + 0.5)) / nodeCount)
      const theta = Math.PI * (1 + 5 ** 0.5) * i
      const r = 2.4 + (Math.random() - 0.5) * 0.4
      const x = r * Math.sin(phi) * Math.cos(theta)
      const y = r * Math.sin(phi) * Math.sin(theta)
      const z = r * Math.cos(phi)

      const pos = new THREE.Vector3(x, y, z)
      nodePositions.push(pos)

      const mat = nodeMats[i % nodeMats.length]
      const mesh = new THREE.Mesh(nodeGeo, mat)
      mesh.position.copy(pos)
      group.add(mesh)
      nodeMeshes.push(mesh)
    }

    // 4. Entanglement Lines (Interference Network)
    const lineIndices: number[] = []
    for (let i = 0; i < nodeCount; i++) {
      for (let j = i + 1; j < nodeCount; j++) {
        if (nodePositions[i].distanceTo(nodePositions[j]) < 1.6) {
          lineIndices.push(i, j)
        }
      }
    }

    const linePositions = new Float32Array(lineIndices.length * 3)
    for (let k = 0; k < lineIndices.length; k++) {
      const p = nodePositions[lineIndices[k]]
      linePositions[k * 3] = p.x
      linePositions[k * 3 + 1] = p.y
      linePositions[k * 3 + 2] = p.z
    }

    const lineGeo = new THREE.BufferGeometry()
    lineGeo.setAttribute("position", new THREE.BufferAttribute(linePositions, 3))
    const lineMat = new THREE.LineBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.25,
      blending: THREE.AdditiveBlending,
    })
    const lines = new THREE.LineSegments(lineGeo, lineMat)
    group.add(lines)

    // 5. Orbital Geodesic Rings (QAOA layers)
    const ringGeo1 = new THREE.TorusGeometry(3.1, 0.02, 16, 100)
    const ringMat1 = new THREE.MeshBasicMaterial({
      color: 0xc084fc,
      transparent: true,
      opacity: 0.4,
    })
    const ring1 = new THREE.Mesh(ringGeo1, ringMat1)
    ring1.rotation.x = Math.PI / 3
    group.add(ring1)

    const ringGeo2 = new THREE.TorusGeometry(3.3, 0.015, 16, 100)
    const ringMat2 = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.35,
    })
    const ring2 = new THREE.Mesh(ringGeo2, ringMat2)
    ring2.rotation.y = Math.PI / 4
    group.add(ring2)

    // 6. Smooth Mouse Parallax
    let targetRotX = 0
    let targetRotY = 0
    let currentRotX = 0
    let currentRotY = 0

    const handlePointerMove = (e: PointerEvent) => {
      const rect = container.getBoundingClientRect()
      const x = ((e.clientX - rect.left) / rect.width) * 2 - 1
      const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1)
      targetRotY = x * 0.4
      targetRotX = -y * 0.4
    }

    container.addEventListener("pointermove", handlePointerMove)

    // 7. Animation Loop
    let clock = new THREE.Clock()

    const animate = () => {
      animId = requestAnimationFrame(animate)
      const t = clock.getElapsedTime()

      // Continuous quantum rotation
      group.rotation.y += 0.005
      ring1.rotation.z = t * 0.2
      ring2.rotation.z = -t * 0.15

      // Core pulse
      const pulse = 1.0 + Math.sin(t * 3.0) * 0.08
      coreMesh.scale.set(pulse, pulse, pulse)

      // Mouse lerp
      currentRotX += (targetRotX - currentRotX) * 0.05
      currentRotY += (targetRotY - currentRotY) * 0.05
      group.rotation.x = currentRotX
      group.position.x = currentRotY * 0.5

      renderer.render(scene, camera)
    }

    animate()

    // 8. Resize Observer
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const w = entry.contentRect.width
        const h = entry.contentRect.height
        if (w > 0 && h > 0) {
          camera.aspect = w / h
          camera.updateProjectionMatrix()
          renderer.setSize(w, h)
        }
      }
    })
    ro.observe(container)

    return () => {
      cancelAnimationFrame(animId)
      container.removeEventListener("pointermove", handlePointerMove)
      ro.disconnect()
      renderer.dispose()
      coreGeo.dispose()
      coreMat.dispose()
      glowGeo.dispose()
      glowMat.dispose()
      nodeGeo.dispose()
      lineGeo.dispose()
      lineMat.dispose()
      ringGeo1.dispose()
      ringMat1.dispose()
      ringGeo2.dispose()
      ringMat2.dispose()
    }
  }, [])

  return (
    <div className={s.container} ref={containerRef} aria-label="Wizualizacja stanu kwantowego 3D">
      <canvas ref={canvasRef} className={s.canvas} />

      <div className={s.overlayTop}>
        <div className={s.statusPill}>
          <span className={s.pulseDot} />
          <span>FALOWA PRZESTRZEŃ STANÓW 3D</span>
        </div>
        <span className={s.fpsBadge}>60 FPS · WEBGL</span>
      </div>

      <div className={s.overlayBottom}>
        <div className={s.telemetryRow}>
          <div className={s.telemetryCell}>
            <span className={s.telemetryVal}>0.0000</span>
            <span className={s.telemetryLabel}>Residuum Błędu</span>
          </div>
          <div className={s.telemetryCell}>
            <span className={s.telemetryVal}>2^N</span>
            <span className={s.telemetryLabel}>Przeszukiwanie</span>
          </div>
          <div className={s.telemetryCell}>
            <span className={s.telemetryVal}>100%</span>
            <span className={s.telemetryLabel}>Gwarancja Reguł</span>
          </div>
        </div>

        {onOpenBrain && (
          <button
            type="button"
            className={s.exploreBrainBtn}
            onClick={onOpenBrain}
          >
            <span>🧠</span>
            <span>Otwórz Pełny Mózg Silnika 3D →</span>
          </button>
        )}
      </div>
    </div>
  )
}
