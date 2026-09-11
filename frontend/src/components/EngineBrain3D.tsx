import React, { useEffect, useRef, useState } from "react"
import * as THREE from "three"

interface EngineBrain3DProps {
  interactive?: boolean
  className?: string
  height?: string | number
  compact?: boolean
  onNodeSelect?: (nodeInfo: { name: string; type: string; score: string }) => void
  onGoToDilemma?: () => void
  onExpand?: () => void
}

type ViewMode = "ALL" | "TOPOLOGY" | "ENERGY_LANDSCAPE" | "INTERFERENCE"

function checkWebGLSupport(): boolean {
  try {
    const canvas = document.createElement("canvas")
    return !!(
      window.WebGLRenderingContext &&
      (canvas.getContext("webgl") || canvas.getContext("experimental-webgl"))
    )
  } catch {
    return false
  }
}

export const EngineBrain3D: React.FC<EngineBrain3DProps> = ({
  interactive = true,
  height = "520px",
  compact = false,
  onNodeSelect,
  onGoToDilemma,
  onExpand,
}) => {
  const mountRef = useRef<HTMLDivElement>(null)
  const [viewMode, setViewMode] = useState<ViewMode>("ALL")
  const [selectedNode, setSelectedNode] = useState<{
    name: string
    type: string
    coherence: string
    synergy: string
  } | null>(null)
  const [isImpulsing, setIsImpulsing] = useState(false)
  const [useFallback2D, setUseFallback2D] = useState(false)

  // References for Three.js animation and visibility control
  const coreGroupRef = useRef<THREE.Group | null>(null)
  const landscapeGroupRef = useRef<THREE.Group | null>(null)
  const ringsGroupRef = useRef<THREE.Group | null>(null)

  const impulseRef = useRef<{ active: boolean; radius: number; maxRadius: number }>({
    active: false,
    radius: 0,
    maxRadius: 25,
  })

  // Synchronize layer visibility
  useEffect(() => {
    if (coreGroupRef.current) {
      coreGroupRef.current.visible =
        viewMode === "ALL" || viewMode === "TOPOLOGY" || viewMode === "INTERFERENCE"
    }
    if (landscapeGroupRef.current) {
      landscapeGroupRef.current.visible =
        viewMode === "ALL" || viewMode === "ENERGY_LANDSCAPE"
    }
    if (ringsGroupRef.current) {
      ringsGroupRef.current.visible =
        viewMode === "ALL" || viewMode === "INTERFERENCE"
    }
  }, [viewMode])

  const triggerImpulse = () => {
    impulseRef.current.active = true
    impulseRef.current.radius = 0
    setIsImpulsing(true)
    setTimeout(() => setIsImpulsing(false), 2400)
  }

  // ── Three.js / WebGL Lifecycle ──────────────────────────────
  useEffect(() => {
    const container = mountRef.current
    if (!container) return

    if (!checkWebGLSupport()) {
      setUseFallback2D(true)
      return
    }

    let renderer: THREE.WebGLRenderer | null = null
    let animationFrameId = 0
    let isDisposed = false

    const startTime = performance.now()
    const width = Math.max(container.clientWidth || 300, 300)
    const rawHeight = typeof height === "number" ? height : container.clientHeight || 520
    const heightPx = Math.max(rawHeight, 260)

    try {
      // 1. Scene, Camera, Renderer
      const scene = new THREE.Scene()
      scene.fog = new THREE.FogExp2(0x06080d, 0.02)

      const aspect = Math.max(0.1, width / heightPx)
      const camera = new THREE.PerspectiveCamera(50, aspect, 0.1, 1000)
      camera.position.set(0, compact ? 10 : 12, compact ? 24 : 28)
      camera.lookAt(0, 0, 0)

      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: "high-performance",
      })
      renderer.setSize(width, heightPx)
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))

      const canvasElement = renderer.domElement
      canvasElement.style.display = "block"
      canvasElement.style.width = "100%"
      canvasElement.style.height = "100%"

      // Safely clear old child canvases if any without destroying container
      while (container.firstChild) {
        container.removeChild(container.firstChild)
      }
      container.appendChild(canvasElement)

      // 2. Groups
      const coreGroup = new THREE.Group()
      const landscapeGroup = new THREE.Group()
      const ringsGroup = new THREE.Group()
      const particlesGroup = new THREE.Group()

      scene.add(coreGroup)
      scene.add(landscapeGroup)
      scene.add(ringsGroup)
      scene.add(particlesGroup)

      coreGroupRef.current = coreGroup
      landscapeGroupRef.current = landscapeGroup
      ringsGroupRef.current = ringsGroup

      // 3. Cognitive Hypergraph Nodes
      const nodeNames = [
        { name: "Spójność Celu", type: "Kryterium Rdzenne", color: 0x4df0ff },
        { name: "Bezpieczeństwo Zasobów", type: "Warunek Brzegowy", color: 0xfbbf24 },
        { name: "Wektor Rozwoju", type: "Funkcja Celu", color: 0xc084fc },
        { name: "Próg Odporności", type: "Ograniczenie Twarde", color: 0x34d399 },
        { name: "Napięcie Decyzyjne", type: "Relacja Nieliniowa", color: 0xf87171 },
        { name: "Wymiar Czasu", type: "Horyzont Planowania", color: 0x60a5fa },
        { name: "Synergia Alternatyw", type: "Sprzężenie Krzyżowe", color: 0xa78bfa },
        { name: "Równowaga Zysku", type: "Punkt Siodełkowy", color: 0x38bdf8 },
        { name: "Potencjał Zmiany", type: "Amplituda Prawdopodobieństwa", color: 0x4ade80 },
        { name: "Bufor Ryzyka", type: "Margines Pewności", color: 0xfacc15 },
        { name: "Entropia Preferencji", type: "Tensor Wyboru", color: 0xf472b6 },
        { name: "Punkt Ground-State", type: "Globalne Optimum", color: 0xffffff },
      ]

      const nodeObjects: Array<{
        mesh: THREE.Mesh
        initialPos: THREE.Vector3
        data: (typeof nodeNames)[0]
      }> = []

      const nodeGeo = new THREE.IcosahedronGeometry(compact ? 0.45 : 0.55, 1)

      nodeNames.forEach((data, i) => {
        const phi = Math.acos(-1 + (2 * i) / nodeNames.length)
        const theta = Math.sqrt(nodeNames.length * Math.PI) * phi
        const r = (compact ? 6.5 : 8.5) + (i % 3) * (compact ? 1.0 : 1.5)

        const x = r * Math.cos(theta) * Math.sin(phi)
        const y = (r * Math.sin(theta) * Math.sin(phi)) * 0.7 + (i % 2 === 0 ? 1 : -1)
        const z = r * Math.cos(phi)

        const mat = new THREE.MeshBasicMaterial({
          color: data.color,
          wireframe: false,
        })

        const mesh = new THREE.Mesh(nodeGeo, mat)
        mesh.position.set(x, y, z)

        // Outer glow ring
        const ringGeo = new THREE.RingGeometry(compact ? 0.55 : 0.7, compact ? 0.7 : 0.85, 20)
        const ringMat = new THREE.MeshBasicMaterial({
          color: data.color,
          side: THREE.DoubleSide,
          transparent: true,
          opacity: 0.5,
        })
        const ring = new THREE.Mesh(ringGeo, ringMat)
        ring.rotation.x = Math.PI / 2
        mesh.add(ring)

        coreGroup.add(mesh)
        nodeObjects.push({ mesh, initialPos: new THREE.Vector3(x, y, z), data })
      })

      // Connecting Synapses (Edges)
      const linesMaterial = new THREE.LineBasicMaterial({
        color: 0x38bdf8,
        transparent: true,
        opacity: 0.25,
        blending: THREE.AdditiveBlending,
      })

      const connectionsGeo = new THREE.BufferGeometry()
      const linePositions: number[] = []

      for (let i = 0; i < nodeObjects.length; i++) {
        for (let j = i + 1; j < nodeObjects.length; j++) {
          const dist = nodeObjects[i].initialPos.distanceTo(nodeObjects[j].initialPos)
          if (dist < (compact ? 9 : 11)) {
            linePositions.push(
              nodeObjects[i].initialPos.x,
              nodeObjects[i].initialPos.y,
              nodeObjects[i].initialPos.z,
              nodeObjects[j].initialPos.x,
              nodeObjects[j].initialPos.y,
              nodeObjects[j].initialPos.z
            )
          }
        }
      }

      connectionsGeo.setAttribute("position", new THREE.Float32BufferAttribute(linePositions, 3))
      const linesMesh = new THREE.LineSegments(connectionsGeo, linesMaterial)
      coreGroup.add(linesMesh)

      // 4. Energy Landscape (QUBO / Hamiltonian Surface)
      const landscapeSize = compact ? 26 : 36
      const landscapeSegments = compact ? 32 : 44
      const landscapeGeo = new THREE.PlaneGeometry(
        landscapeSize,
        landscapeSize,
        landscapeSegments,
        landscapeSegments
      )
      landscapeGeo.rotateX(-Math.PI / 2)
      landscapeGeo.translate(0, compact ? -4.5 : -6, 0)

      const landscapeMat = new THREE.MeshBasicMaterial({
        color: 0x1e3a8a,
        wireframe: true,
        transparent: true,
        opacity: 0.35,
      })
      const landscapeMesh = new THREE.Mesh(landscapeGeo, landscapeMat)
      landscapeGroup.add(landscapeMesh)

      // 5. Quantum Interference Rings
      const ringRadii = compact ? [8, 11, 14] : [11, 14, 17]
      const rings: THREE.Line[] = []
      ringRadii.forEach((r, idx) => {
        const curve = new THREE.EllipseCurve(0, 0, r, r, 0, 2 * Math.PI, false, 0)
        const points = curve.getPoints(90)
        const geo = new THREE.BufferGeometry().setFromPoints(points)
        geo.rotateX(Math.PI / 2 + idx * 0.3)
        geo.rotateY(idx * 0.5)

        const mat = new THREE.LineBasicMaterial({
          color: idx === 0 ? 0x4df0ff : idx === 1 ? 0xc084fc : 0xfbbf24,
          transparent: true,
          opacity: 0.4,
        })
        const ringLine = new THREE.Line(geo, mat)
        ringsGroup.add(ringLine)
        rings.push(ringLine)
      })

      // 6. Quantum Dust Particles
      const particleCount = compact ? 150 : 260
      const particleGeo = new THREE.BufferGeometry()
      const particleCoords = new Float32Array(particleCount * 3)

      for (let i = 0; i < particleCount * 3; i += 3) {
        particleCoords[i] = (Math.random() - 0.5) * 32
        particleCoords[i + 1] = (Math.random() - 0.5) * 18
        particleCoords[i + 2] = (Math.random() - 0.5) * 32
      }
      particleGeo.setAttribute("position", new THREE.BufferAttribute(particleCoords, 3))

      const particleMat = new THREE.PointsMaterial({
        size: 0.16,
        color: 0x93c5fd,
        transparent: true,
        opacity: 0.55,
        blending: THREE.AdditiveBlending,
      })
      const particleSystem = new THREE.Points(particleGeo, particleMat)
      particlesGroup.add(particleSystem)

      // 7. Interaction: Mouse dragging for 360 orbit
      let isDragging = false
      let previousMousePosition = { x: 0, y: 0 }
      const rotationVelocity = { x: 0.0015, y: 0.0008 }

      const onMouseDown = (e: MouseEvent) => {
        isDragging = true
        previousMousePosition = { x: e.clientX, y: e.clientY }
      }

      const onMouseMove = (e: MouseEvent) => {
        if (!isDragging) return
        const deltaX = e.clientX - previousMousePosition.x
        const deltaY = e.clientY - previousMousePosition.y

        coreGroup.rotation.y += deltaX * 0.006
        coreGroup.rotation.x += deltaY * 0.006
        landscapeGroup.rotation.y += deltaX * 0.003
        ringsGroup.rotation.y += deltaX * 0.004

        previousMousePosition = { x: e.clientX, y: e.clientY }
      }

      const onMouseUp = () => {
        isDragging = false
      }

      // Raycaster for node clicks
      const raycaster = new THREE.Raycaster()
      const mouse = new THREE.Vector2()

      const onPointerClick = (e: MouseEvent) => {
        if (!container) return
        const rect = container.getBoundingClientRect()
        mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1
        mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1

        raycaster.setFromCamera(mouse, camera)
        const meshes = nodeObjects.map((no) => no.mesh)
        const intersects = raycaster.intersectObjects(meshes)

        if (intersects.length > 0) {
          const clickedMesh = intersects[0].object as THREE.Mesh
          const match = nodeObjects.find((no) => no.mesh === clickedMesh)
          if (match) {
            const info = {
              name: match.data.name,
              type: match.data.type,
              coherence: (94 + Math.random() * 5.8).toFixed(1) + "%",
              synergy: "+0." + Math.floor(82 + Math.random() * 16),
            }
            setSelectedNode(info)
            if (onNodeSelect) {
              onNodeSelect({
                name: info.name,
                type: info.type,
                score: info.coherence,
              })
            }
          }
        }
      }

      // Mouse wheel zoom
      const onWheel = (e: WheelEvent) => {
        e.preventDefault()
        camera.position.z = Math.max(14, Math.min(45, camera.position.z + e.deltaY * 0.03))
      }

      if (interactive) {
        container.addEventListener("mousedown", onMouseDown)
        window.addEventListener("mousemove", onMouseMove)
        window.addEventListener("mouseup", onMouseUp)
        container.addEventListener("click", onPointerClick)
        container.addEventListener("wheel", onWheel, { passive: false })
      }

      // 8. Animation Loop with performance.now()
      const animate = () => {
        if (isDisposed) return
        animationFrameId = requestAnimationFrame(animate)
        const elapsedTime = (performance.now() - startTime) / 1000

        // Idle Rotation
        if (!isDragging) {
          coreGroup.rotation.y += rotationVelocity.x
          coreGroup.rotation.x += rotationVelocity.y * Math.sin(elapsedTime * 0.4)
          landscapeGroup.rotation.y += rotationVelocity.x * 0.4
          ringsGroup.rotation.y -= rotationVelocity.x * 0.8
          particlesGroup.rotation.y += rotationVelocity.x * 0.2
        }

        // Animate Nodes pulsation
        nodeObjects.forEach((no, idx) => {
          const offset = idx * 0.4
          no.mesh.scale.setScalar(1 + 0.12 * Math.sin(elapsedTime * 2 + offset))

          // Impulse shockwave handling
          if (impulseRef.current.active) {
            const dist = no.initialPos.length()
            if (Math.abs(dist - impulseRef.current.radius) < 2.5) {
              no.mesh.scale.setScalar(1.6)
            }
          }
        })

        // Impulse radius advancement
        if (impulseRef.current.active) {
          impulseRef.current.radius += 0.35
          if (impulseRef.current.radius > impulseRef.current.maxRadius) {
            impulseRef.current.active = false
          }
        }

        // Animate QUBO Landscape Undulation
        const pos = landscapeGeo.attributes.position as THREE.BufferAttribute
        for (let i = 0; i < pos.count; i++) {
          const vx = pos.getX(i)
          const vz = pos.getZ(i)
          const distCenter = Math.sqrt(vx * vx + vz * vz)
          const wave =
            Math.sin(distCenter * 0.4 - elapsedTime * 1.8) * 0.6 +
            Math.cos(vx * 0.3 + elapsedTime) * 0.4 -
            Math.exp(-distCenter * 0.15) * 2.2
          pos.setY(i, wave)
        }
        pos.needsUpdate = true

        // Rings wobbling
        rings.forEach((r, idx) => {
          r.rotation.z += (idx + 1) * 0.002
        })

        if (renderer && scene && camera) {
          renderer.render(scene, camera)
        }
      }

      animate()

      // 9. Resize Handling
      const handleResize = () => {
        if (!container || !renderer) return
        const newWidth = Math.max(container.clientWidth || 300, 300)
        const newHeightPx = Math.max(
          typeof height === "number" ? height : container.clientHeight || 520,
          260
        )
        camera.aspect = newWidth / newHeightPx
        camera.updateProjectionMatrix()
        renderer.setSize(newWidth, newHeightPx)
      }

      window.addEventListener("resize", handleResize)

      return () => {
        isDisposed = true
        cancelAnimationFrame(animationFrameId)
        window.removeEventListener("resize", handleResize)
        if (interactive) {
          container.removeEventListener("mousedown", onMouseDown)
          window.removeEventListener("mousemove", onMouseMove)
          window.removeEventListener("mouseup", onMouseUp)
          container.removeEventListener("click", onPointerClick)
          container.removeEventListener("wheel", onWheel)
        }
        if (renderer) {
          renderer.dispose()
          if (container && renderer.domElement && container.contains(renderer.domElement)) {
            container.removeChild(renderer.domElement)
          }
        }
      }
    } catch (err) {
      console.warn("WebGL initialization failed, switching to 2D Canvas fallback:", err)
      setUseFallback2D(true)
    }
  }, [interactive, height, compact, onNodeSelect])

  // ── 2D Canvas Fallback if WebGL unavailable ──────────────────
  const fallbackCanvasRef = useRef<HTMLCanvasElement>(null)
  useEffect(() => {
    if (!useFallback2D) return
    const canvas = fallbackCanvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    let animId = 0
    let startTime = performance.now()

    const render = () => {
      animId = requestAnimationFrame(render)
      const t = (performance.now() - startTime) / 1000
      const w = canvas.width
      const h = canvas.height

      ctx.clearRect(0, 0, w, h)

      // Background gradient
      const grad = ctx.createRadialGradient(w / 2, h / 2, 20, w / 2, h / 2, w / 2)
      grad.addColorStop(0, "rgba(20, 30, 55, 0.85)")
      grad.addColorStop(1, "rgba(8, 12, 22, 0.95)")
      ctx.fillStyle = grad
      ctx.fillRect(0, 0, w, h)

      // Concentric interference rings
      for (let r = 40; r < Math.min(w, h) / 2; r += 36) {
        ctx.beginPath()
        ctx.arc(w / 2, h / 2, r + Math.sin(t * 1.5 + r * 0.05) * 6, 0, Math.PI * 2)
        ctx.strokeStyle = "rgba(77, 240, 255, 0.18)"
        ctx.lineWidth = 1.2
        ctx.stroke()
      }

      // Nodes & connections
      const nodes = [
        { name: "Spójność", angle: 0, r: 90, color: "#4df0ff" },
        { name: "Bezpieczeństwo", angle: 0.9, r: 110, color: "#fbbf24" },
        { name: "Wektor Celu", angle: 1.8, r: 85, color: "#c084fc" },
        { name: "Ograniczenia", angle: 2.7, r: 120, color: "#34d399" },
        { name: "Napięcia", angle: 3.6, r: 95, color: "#f87171" },
        { name: "Optimum", angle: 4.5, r: 115, color: "#60a5fa" },
        { name: "Synergia", angle: 5.4, r: 100, color: "#a78bfa" },
      ]

      // Draw connections
      ctx.strokeStyle = "rgba(100, 180, 255, 0.22)"
      ctx.lineWidth = 1
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a1 = nodes[i].angle + t * 0.2
          const x1 = w / 2 + Math.cos(a1) * nodes[i].r
          const y1 = h / 2 + Math.sin(a1) * (nodes[i].r * 0.65)
          const a2 = nodes[j].angle + t * 0.2
          const x2 = w / 2 + Math.cos(a2) * nodes[j].r
          const y2 = h / 2 + Math.sin(a2) * (nodes[j].r * 0.65)
          ctx.beginPath()
          ctx.moveTo(x1, y1)
          ctx.lineTo(x2, y2)
          ctx.stroke()
        }
      }

      // Draw nodes
      nodes.forEach((n) => {
        const a = n.angle + t * 0.2
        const x = w / 2 + Math.cos(a) * n.r
        const y = h / 2 + Math.sin(a) * (n.r * 0.65)
        ctx.beginPath()
        ctx.arc(x, y, 7, 0, Math.PI * 2)
        ctx.fillStyle = n.color
        ctx.shadowColor = n.color
        ctx.shadowBlur = 14
        ctx.fill()
        ctx.shadowBlur = 0

        ctx.fillStyle = "rgba(240, 245, 255, 0.85)"
        ctx.font = "10px sans-serif"
        ctx.fillText(n.name, x + 10, y + 3)
      })

      // Central gravity well
      ctx.beginPath()
      ctx.arc(w / 2, h / 2, 12, 0, Math.PI * 2)
      ctx.fillStyle = "#ffffff"
      ctx.shadowColor = "#4df0ff"
      ctx.shadowBlur = 20
      ctx.fill()
      ctx.shadowBlur = 0
    }

    render()
    return () => cancelAnimationFrame(animId)
  }, [useFallback2D])

  return (
    <div
      style={{
        position: "relative",
        width: "100%",
        height: height,
        background:
          "radial-gradient(ellipse at 50% 40%, oklch(14% 0.025 250) 0%, oklch(7% 0.01 250) 75%)",
        borderRadius: "16px",
        overflow: "hidden",
        border: "1px solid oklch(22% 0.03 250)",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* 3D WebGL or 2D Fallback Mount */}
      {useFallback2D ? (
        <canvas
          ref={fallbackCanvasRef}
          width={700}
          height={480}
          style={{ width: "100%", height: "100%", display: "block" }}
        />
      ) : (
        <div
          ref={mountRef}
          style={{
            width: "100%",
            height: "100%",
            cursor: interactive ? "grab" : "default",
          }}
        />
      )}

      {/* Top Controls Overlay */}
      <div
        style={{
          position: "absolute",
          top: "0.875rem",
          left: "0.875rem",
          right: "0.875rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          pointerEvents: "none",
          zIndex: 10,
          flexWrap: "wrap",
          gap: "0.5rem",
        }}
      >
        <div style={{ pointerEvents: "auto", display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.375rem",
              background: "oklch(14% 0.02 250 / 0.88)",
              backdropFilter: "blur(8px)",
              border: "1px solid oklch(28% 0.03 250)",
              borderRadius: "8px",
              padding: "0.3rem 0.65rem",
              fontSize: "0.75rem",
              fontWeight: 800,
              color: "oklch(75% 0.12 80)",
              letterSpacing: "0.06em",
              textTransform: "uppercase",
            }}
          >
            <span
              style={{
                width: "6px",
                height: "6px",
                borderRadius: "50%",
                background: "oklch(75% 0.12 80)",
                boxShadow: "0 0 8px oklch(75% 0.12 80)",
              }}
            />
            Mózg Silnika • 3D Matrix
          </div>

          <button
            onClick={triggerImpulse}
            disabled={isImpulsing}
            type="button"
            style={{
              background: isImpulsing ? "oklch(25% 0.05 170)" : "oklch(18% 0.03 240 / 0.88)",
              border: "1px solid oklch(35% 0.08 170)",
              backdropFilter: "blur(8px)",
              borderRadius: "8px",
              padding: "0.3rem 0.65rem",
              fontSize: "0.75rem",
              fontWeight: 700,
              color: isImpulsing ? "oklch(90% 0.1 168)" : "oklch(80% 0.12 168)",
              cursor: "pointer",
              transition: "all 200ms ease",
              boxShadow: isImpulsing ? "0 0 16px oklch(78% 0.16 168 / 0.6)" : "none",
            }}
          >
            {isImpulsing ? "Impuls w toku..." : "Wyślij impuls kwantowy ⚡"}
          </button>

          {/* Layer switcher - hidden in compact mode */}
          {!compact && (
            <div
              style={{
                display: "flex",
                gap: "0.2rem",
                background: "oklch(14% 0.02 250 / 0.88)",
                backdropFilter: "blur(8px)",
                padding: "0.2rem",
                borderRadius: "8px",
                border: "1px solid oklch(24% 0.03 250)",
              }}
            >
              {[
                { id: "ALL", label: "Wszystko" },
                { id: "TOPOLOGY", label: "Topologia" },
                { id: "ENERGY_LANDSCAPE", label: "QUBO" },
                { id: "INTERFERENCE", label: "Fazy" },
              ].map((m) => (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => setViewMode(m.id as ViewMode)}
                  style={{
                    background: viewMode === m.id ? "oklch(26% 0.04 250)" : "transparent",
                    border: "none",
                    borderRadius: "5px",
                    padding: "0.2rem 0.5rem",
                    fontSize: "0.6875rem",
                    fontWeight: viewMode === m.id ? 700 : 500,
                    color: viewMode === m.id ? "oklch(95% 0.01 250)" : "oklch(65% 0.02 250)",
                    cursor: "pointer",
                  }}
                >
                  {m.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right side controls: Expand or Return */}
        <div style={{ pointerEvents: "auto", display: "flex", alignItems: "center", gap: "0.5rem" }}>
          {onExpand && (
            <button
              onClick={onExpand}
              type="button"
              style={{
                background: "oklch(18% 0.03 250 / 0.88)",
                border: "1px solid oklch(30% 0.04 250)",
                color: "oklch(88% 0.02 250)",
                padding: "0.3rem 0.65rem",
                borderRadius: "8px",
                fontSize: "0.75rem",
                fontWeight: 700,
                cursor: "pointer",
                backdropFilter: "blur(8px)",
              }}
            >
              Pełen ekran ↗
            </button>
          )}

          {onGoToDilemma && (
            <button
              onClick={onGoToDilemma}
              type="button"
              style={{
                background: "linear-gradient(135deg, oklch(75% 0.12 80), oklch(62% 0.18 240))",
                border: "none",
                color: "oklch(10% 0.02 250)",
                padding: "0.35rem 0.85rem",
                borderRadius: "8px",
                fontSize: "0.75rem",
                fontWeight: 800,
                cursor: "pointer",
                boxShadow: "0 0 12px oklch(75% 0.12 80 / 0.4)",
              }}
            >
              ✍️ Rozwiąż dylemat
            </button>
          )}
        </div>
      </div>

      {/* Selected Node HUD Card */}
      {selectedNode && (
        <div
          style={{
            position: "absolute",
            bottom: "1rem",
            left: "1rem",
            background: "oklch(12% 0.02 250 / 0.94)",
            backdropFilter: "blur(12px)",
            border: "1px solid oklch(30% 0.04 250)",
            borderRadius: "10px",
            padding: "0.875rem 1rem",
            maxWidth: "280px",
            boxShadow: "0 12px 32px oklch(0% 0 0 / 0.6)",
            fontSize: "0.75rem",
            color: "oklch(90% 0.01 250)",
            zIndex: 10,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.375rem" }}>
            <span style={{ fontWeight: 800, color: "oklch(75% 0.12 80)", fontSize: "0.8125rem" }}>
              {selectedNode.name}
            </span>
            <button
              onClick={() => setSelectedNode(null)}
              type="button"
              style={{
                background: "none",
                border: "none",
                color: "oklch(50% 0.01 250)",
                cursor: "pointer",
                padding: "0 0.2rem",
                fontSize: "1rem",
              }}
            >
              ×
            </button>
          </div>
          <div style={{ color: "oklch(65% 0.02 250)", marginBottom: "0.5rem" }}>
            {selectedNode.type}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", borderTop: "1px solid oklch(22% 0.02 250)", paddingTop: "0.5rem" }}>
            <div>
              <span style={{ display: "block", color: "oklch(55% 0.01 250)", fontSize: "0.6875rem" }}>Spójność fazy</span>
              <strong style={{ color: "oklch(78% 0.14 168)" }}>{selectedNode.coherence}</strong>
            </div>
            <div>
              <span style={{ display: "block", color: "oklch(55% 0.01 250)", fontSize: "0.6875rem" }}>Wpływ synergii</span>
              <strong style={{ color: "oklch(80% 0.14 280)" }}>{selectedNode.synergy}</strong>
            </div>
          </div>
        </div>
      )}

      {/* Bottom Hint / Return strip */}
      <div
        style={{
          position: "absolute",
          bottom: "0.75rem",
          right: "0.875rem",
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
          pointerEvents: "none",
          zIndex: 10,
        }}
      >
        <div
          style={{
            fontSize: "0.6875rem",
            color: "oklch(60% 0.01 250)",
            background: "oklch(12% 0.015 250 / 0.85)",
            padding: "0.25rem 0.6rem",
            borderRadius: "6px",
            border: "1px solid oklch(20% 0.02 250)",
          }}
        >
          Obrót 360° • Zoom • Kliknij węzeł
        </div>
      </div>
    </div>
  )
}
