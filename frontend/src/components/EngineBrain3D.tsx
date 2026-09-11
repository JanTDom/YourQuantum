import React, { useEffect, useRef, useState } from "react"
import * as THREE from "three"

export type BrainLobeId = "FRONTAL_INTAKE" | "LEFT_CONSTRAINTS" | "RIGHT_QUANTUM" | "CORE_OPTIMUM"

interface LobeInfo {
  id: BrainLobeId
  name: string
  subtitle: string
  color: string
  badge: string
  cameraPos: [number, number, number]
  targetPos: [number, number, number]
  explanation: string
  bulletPoints: string[]
}

export const BRAIN_LOBES: Record<BrainLobeId, LobeInfo> = {
  FRONTAL_INTAKE: {
    id: "FRONTAL_INTAKE",
    name: "Płat Czołowy: Ekstrakcja Faktów",
    subtitle: "Analiza Semantyczna & Opcje Wyboru",
    color: "#fbbf24",
    badge: "Etap 1: Intake",
    cameraPos: [0, 6, 26],
    targetPos: [0, 0, 4],
    explanation:
      "Tu Twój dylemat życiowy zostaje rozbity na czynniki pierwsze. System wyciąga z tekstu twarde fakty, alternatywne opcje i identyfikuje brakujące informacje.",
    bulletPoints: [
      "Zero wymyślonych danych i zero halucynacji.",
      "Identyfikacja sprzecznych celów i ukrytych kompromisów.",
      "Przygotowanie pytań doprecyzowujących, zanim rozpocznie się liczenie.",
    ],
  },
  LEFT_CONSTRAINTS: {
    id: "LEFT_CONSTRAINTS",
    name: "Płat Lewy: Filtr Ograniczeń Twardych",
    subtitle: "Dyskretny Solver Dokładny (CP-SAT)",
    color: "#38bdf8",
    badge: "Etap 2: Warunki Brzegowe",
    cameraPos: [-20, 8, 16],
    targetPos: [-6, 0, 0],
    explanation:
      "Bezwzględny matematyczny strażnik Twoich granic. Każdy wariant, który łamie Twój budżet, czas pracy czy nienaruszalne zasady osobiste, zostaje natychmiast wycięty z przestrzeni rozwiązań.",
    bulletPoints: [
      "100% determinizmu: reguła złamana = opcja odrzucona.",
      "Wykorzystanie zaawansowanego algorytmu CP-SAT / SAT-solver.",
      "Żaden chatbot nie potrafi dać takiej twardej gwarancji brzegowej.",
    ],
  },
  RIGHT_QUANTUM: {
    id: "RIGHT_QUANTUM",
    name: "Płat Prawy: Splątanie Kwantowe",
    subtitle: "Superpozycja & Tunelowanie (QAOA / Ising)",
    color: "#c084fc",
    badge: "Etap 3: Optymalizacja Kwantowa",
    cameraPos: [20, 8, 16],
    targetPos: [6, 0, 0],
    explanation:
      "Wielowymiarowa przestrzeń kompromisów. Trudne dylematy mają miliony kombinacji. Zamiast sprawdzać je po kolei, algorytm kwantowy traktuje je jak interferujące fale prawdopodobieństwa.",
    bulletPoints: [
      "Tunelowanie kwantowe przez pozorne bariery i pułapki decyzyjne.",
      "Równoczesna ocena dziesiątek sprzecznych kryteriów.",
      "Wykorzystanie modelu Hamiltoniana i rampy adiabatycznej (TQA).",
    ],
  },
  CORE_OPTIMUM: {
    id: "CORE_OPTIMUM",
    name: "Rdzeń Centralny: Globalne Optimum",
    subtitle: "Stan Podstawowy & Niezależny Audyt",
    color: "#ffffff",
    badge: "Etap 4: Wynik z Dowodem",
    cameraPos: [0, 14, 18],
    targetPos: [0, -1, 0],
    explanation:
      "Punkt najniższej energii potencjalnej. Rozwiązanie o najwyższej synergii, poparte niezależnym audytem sprawdzającym linijka po linijce wszystkie warunki.",
    bulletPoints: [
      "Punkt równowagi o maksymalnej użyteczności dla Twojego życia.",
      "Niezależny weryfikator (Verdict: PASS) przed pokazaniem wyniku.",
      "Konkretny punkt zwrotny: wiesz dokładnie, co musiałoby się zmienić, by inna opcja wygrała.",
    ],
  },
}

interface EngineBrain3DProps {
  interactive?: boolean
  className?: string
  height?: string | number
  onGoToDilemma?: () => void
}

export const EngineBrain3D: React.FC<EngineBrain3DProps> = ({
  interactive = true,
  height = "640px",
  onGoToDilemma,
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const [activeLobe, setActiveLobe] = useState<BrainLobeId>("FRONTAL_INTAKE")
  const [isSimulating, setIsSimulating] = useState(false)
  const [simStep, setSimStep] = useState<string | null>(null)
  const [telemetry, setTelemetry] = useState({
    activeNeurons: 2240,
    coherence: "99.8%",
    searchSpeed: "0.84s",
    mode: "CP-SAT + QAOA Aer",
  })

  // Target camera state for smooth tweening
  const camTargetRef = useRef({
    x: 0,
    y: 8,
    z: 28,
    lookX: 0,
    lookY: 0,
    lookZ: 0,
  })

  const focusLobe = (lobeId: BrainLobeId) => {
    setActiveLobe(lobeId)
    const lobe = BRAIN_LOBES[lobeId]
    camTargetRef.current = {
      x: lobe.cameraPos[0],
      y: lobe.cameraPos[1],
      z: lobe.cameraPos[2],
      lookX: lobe.targetPos[0],
      lookY: lobe.targetPos[1],
      lookZ: lobe.targetPos[2],
    }
  }

  // Cinematic Decision Simulation sequence
  const runSimulation = () => {
    if (isSimulating) return
    setIsSimulating(true)

    // Phase 1: Intake
    focusLobe("FRONTAL_INTAKE")
    setSimStep("Krok 1/3: Ekstrakcja faktów i mapowanie ograniczeń...")

    // Phase 2: Quantum Superposition (after 3.5s)
    setTimeout(() => {
      focusLobe("RIGHT_QUANTUM")
      setSimStep("Krok 2/3: Kwantowe splątanie w przestrzeni stanów (QAOA)...")
      setTelemetry((prev) => ({ ...prev, coherence: "99.9%", searchSpeed: "0.42s" }))
    }, 3800)

    // Phase 3: Global Optimum Collapse (after 7.5s)
    setTimeout(() => {
      focusLobe("CORE_OPTIMUM")
      setSimStep("Krok 3/3: Kolaps do Globalnego Optimum i audyt niezależny (PASS)!")
    }, 7800)

    // Finish simulation (after 12s)
    setTimeout(() => {
      setIsSimulating(false)
      setSimStep(null)
    }, 12000)
  }

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    let isDisposed = false
    let animationFrameId = 0

    // Setup dimensions
    const width = Math.max(container.clientWidth || 800, 320)
    const rawHeight = typeof height === "number" ? height : container.clientHeight || 640
    const heightPx = Math.max(rawHeight, 400)

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene()
    scene.fog = new THREE.FogExp2(0x05070d, 0.022)

    const camera = new THREE.PerspectiveCamera(45, width / heightPx, 0.1, 1000)
    camera.position.set(0, 8, 28)
    const currentLookAt = new THREE.Vector3(0, 0, 0)
    camera.lookAt(currentLookAt)

    let renderer: THREE.WebGLRenderer
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: "high-performance",
      })
    } catch {
      return
    }

    renderer.setSize(width, heightPx)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
    renderer.domElement.style.display = "block"
    renderer.domElement.style.width = "100%"
    renderer.domElement.style.height = "100%"

    while (container.firstChild) {
      container.removeChild(container.firstChild)
    }
    container.appendChild(renderer.domElement)

    // 2. Main Groups
    const brainGroup = new THREE.Group()
    const axonCurvesGroup = new THREE.Group()
    const photonsGroup = new THREE.Group()
    const coreGlowGroup = new THREE.Group()
    const gyroscopeRingsGroup = new THREE.Group()

    scene.add(brainGroup)
    scene.add(axonCurvesGroup)
    scene.add(photonsGroup)
    scene.add(coreGlowGroup)
    scene.add(gyroscopeRingsGroup)

    // 3. Volumetric Dual-Hemisphere Brain Point Cloud Generation
    // Mathematical Parametric Human Brain Model
    const brainParticlesCount = 2400
    const brainGeo = new THREE.BufferGeometry()
    const positions = new Float32Array(brainParticlesCount * 3)
    const colors = new Float32Array(brainParticlesCount * 3)
    const sizes = new Float32Array(brainParticlesCount)

    const colorLogicCyan = new THREE.Color("#38bdf8")
    const colorLogicAmber = new THREE.Color("#fbbf24")
    const colorQuantumViolet = new THREE.Color("#c084fc")
    const colorQuantumCyan = new THREE.Color("#4df0ff")
    const colorCoreWhite = new THREE.Color("#ffffff")

    const corticalNodes: THREE.Vector3[] = []

    for (let i = 0; i < brainParticlesCount; i++) {
      const isRightHemisphere = i % 2 === 0
      const sideSign = isRightHemisphere ? 1 : -1

      // Spherical & cortical harmonics for realistic brain lobes
      const u = Math.random() * Math.PI // theta (0 to PI)
      const v = (Math.random() - 0.5) * Math.PI * 2 // phi (-PI to PI)

      // Anisotropic brain shape scaling factors
      const rx = 6.2
      const ry = 5.2
      const rz = 7.8

      // Cortical convolutions (sulci & gyri wrinkles)
      const gyrusRipple =
        Math.sin(u * 9 + (isRightHemisphere ? 1 : 0)) * 0.45 +
        Math.cos(v * 8) * 0.35

      // Longitudinal fissure separation
      const fissureGap = 0.55

      // Anatomical shape coordinates
      let x = sideSign * (fissureGap + Math.abs(Math.sin(u) * Math.cos(v) * rx * (1 + gyrusRipple * 0.12)))
      let y = Math.cos(u) * ry * (1 + gyrusRipple * 0.12)
      let z = Math.sin(u) * Math.sin(v) * rz * (1 + gyrusRipple * 0.12)

      // Indent bottom (cerebellum / brainstem notch)
      if (y < -1.5 && z < 0) {
        x *= 0.7
        y += 0.8
        z *= 0.8
      }

      // Frontal elongation & parietal height
      if (z > 1) {
        y += 0.5 * Math.sin(u)
      }

      // Add a cluster of deep subcortical / quantum core points near center
      if (i < 240) {
        const coreDist = Math.random() * 2.8
        const coreAng = Math.random() * Math.PI * 2
        const coreZ = (Math.random() - 0.5) * 4
        x = Math.cos(coreAng) * coreDist
        y = Math.sin(coreAng) * coreDist * 0.8
        z = coreZ
      }

      positions[i * 3] = x
      positions[i * 3 + 1] = y
      positions[i * 3 + 2] = z

      // Particle colors based on brain lobe & hemisphere
      const c = new THREE.Color()
      const distFromCenter = Math.sqrt(x * x + y * y + z * z)

      if (distFromCenter < 3.2) {
        // Quantum Core
        c.copy(colorCoreWhite)
        sizes[i] = 2.4
      } else if (z > 3.0) {
        // Frontal Lobe (Intake & facts)
        c.copy(colorLogicAmber).lerp(colorLogicCyan, 0.4)
        sizes[i] = 1.8
      } else if (isRightHemisphere) {
        // Right Hemisphere (Quantum Superposition & QAOA)
        const t = Math.min(1, (z + 4) / 8)
        c.copy(colorQuantumViolet).lerp(colorQuantumCyan, t)
        sizes[i] = 1.6
      } else {
        // Left Hemisphere (Classical Logic & CP-SAT)
        const t = Math.min(1, (z + 4) / 8)
        c.copy(colorLogicCyan).lerp(colorLogicAmber, t * 0.5)
        sizes[i] = 1.6
      }

      colors[i * 3] = c.r
      colors[i * 3 + 1] = c.g
      colors[i * 3 + 2] = c.b

      // Store a subset for axon connection anchoring
      if (i % 38 === 0) {
        corticalNodes.push(new THREE.Vector3(x, y, z))
      }
    }

    brainGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3))
    brainGeo.setAttribute("color", new THREE.BufferAttribute(colors, 3))

    const brainMaterial = new THREE.PointsMaterial({
      size: 0.18,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
    })

    const brainPoints = new THREE.Points(brainGeo, brainMaterial)
    brainGroup.add(brainPoints)

    // 4. Central Radiant Singularity (The Quantum Ground State Core)
    const coreMeshGeo = new THREE.IcosahedronGeometry(1.6, 2)
    const coreMeshMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      wireframe: true,
      transparent: true,
      opacity: 0.7,
      blending: THREE.AdditiveBlending,
    })
    const coreMesh = new THREE.Mesh(coreMeshGeo, coreMeshMat)
    coreGlowGroup.add(coreMesh)

    // Core halo sprite
    const haloGeo = new THREE.RingGeometry(1.6, 2.5, 32)
    const haloMat = new THREE.MeshBasicMaterial({
      color: 0x4df0ff,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.45,
      blending: THREE.AdditiveBlending,
    })
    const haloRing = new THREE.Mesh(haloGeo, haloMat)
    haloRing.rotation.x = Math.PI / 2
    coreGlowGroup.add(haloRing)

    // 5. Synaptic Axon Splines & Action Potential Photons
    const splineCount = 42
    const splines: THREE.CatmullRomCurve3[] = []
    const photons: Array<{
      mesh: THREE.Mesh
      curve: THREE.CatmullRomCurve3
      progress: number
      speed: number
    }> = []

    const photonGeo = new THREE.SphereGeometry(0.16, 8, 8)
    const photonMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      blending: THREE.AdditiveBlending,
    })

    for (let s = 0; s < splineCount; s++) {
      const p1 = corticalNodes[s % corticalNodes.length]
      const p2 = corticalNodes[(s + 7) % corticalNodes.length]
      // Arc through the center core or arch across hemispheres
      const mid = new THREE.Vector3()
        .addVectors(p1, p2)
        .multiplyScalar(0.5)
      mid.y += (Math.random() - 0.5) * 2.5
      mid.x += (Math.random() - 0.5) * 1.5

      const curve = new THREE.CatmullRomCurve3([p1, mid, p2])
      splines.push(curve)

      const curvePoints = curve.getPoints(36)
      const curveGeo = new THREE.BufferGeometry().setFromPoints(curvePoints)
      const isQuantumSide = s % 2 === 0
      const curveMat = new THREE.LineBasicMaterial({
        color: isQuantumSide ? 0xc084fc : 0x38bdf8,
        transparent: true,
        opacity: 0.22,
        blending: THREE.AdditiveBlending,
      })
      const line = new THREE.Line(curveGeo, curveMat)
      axonCurvesGroup.add(line)

      // Spawn traveling action potential photon
      const photonMesh = new THREE.Mesh(photonGeo, photonMat)
      photonsGroup.add(photonMesh)
      photons.push({
        mesh: photonMesh,
        curve,
        progress: Math.random(),
        speed: 0.003 + Math.random() * 0.005,
      })
    }

    // 6. Quantum Phase Interference Gyroscope Rings
    const gyroRadii = [9.5, 11.5, 13.5]
    const gyroColors = [0x4df0ff, 0xc084fc, 0xfbbf24]
    const gyroRings: THREE.Line[] = []

    gyroRadii.forEach((r, idx) => {
      const curve = new THREE.EllipseCurve(0, 0, r, r * 0.92, 0, Math.PI * 2, false, 0)
      const pts = curve.getPoints(90)
      const geo = new THREE.BufferGeometry().setFromPoints(pts)
      geo.rotateX(Math.PI / 2 + idx * 0.4)
      geo.rotateY(idx * 0.6)

      const mat = new THREE.LineBasicMaterial({
        color: gyroColors[idx],
        transparent: true,
        opacity: 0.32,
        blending: THREE.AdditiveBlending,
      })
      const ring = new THREE.Line(geo, mat)
      gyroscopeRingsGroup.add(ring)
      gyroRings.push(ring)
    })

    // 7. Undulating Hamiltonian Potential Floor
    const floorSize = 40
    const floorGeo = new THREE.PlaneGeometry(floorSize, floorSize, 36, 36)
    floorGeo.rotateX(-Math.PI / 2)
    floorGeo.translate(0, -9, 0)

    const floorMat = new THREE.MeshBasicMaterial({
      color: 0x172554,
      wireframe: true,
      transparent: true,
      opacity: 0.25,
    })
    const floorMesh = new THREE.Mesh(floorGeo, floorMat)
    scene.add(floorMesh)

    // 8. Mouse Drag Controls with Inertia
    let isDragging = false
    let prevMouse = { x: 0, y: 0 }
    const rotationVelocity = { x: 0.0018, y: 0.0006 }

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true
      prevMouse = { x: e.clientX, y: e.clientY }
    }

    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging) return
      const dx = e.clientX - prevMouse.x
      const dy = e.clientY - prevMouse.y

      brainGroup.rotation.y += dx * 0.005
      brainGroup.rotation.x += dy * 0.005
      axonCurvesGroup.rotation.y += dx * 0.005
      axonCurvesGroup.rotation.x += dy * 0.005
      photonsGroup.rotation.y += dx * 0.005
      photonsGroup.rotation.x += dy * 0.005

      prevMouse = { x: e.clientX, y: e.clientY }
    }

    const onMouseUp = () => {
      isDragging = false
    }

    const onWheel = (e: WheelEvent) => {
      e.preventDefault()
      camTargetRef.current.z = Math.max(12, Math.min(46, camTargetRef.current.z + e.deltaY * 0.03))
    }

    if (interactive) {
      container.addEventListener("mousedown", onMouseDown)
      window.addEventListener("mousemove", onMouseMove)
      window.addEventListener("mouseup", onMouseUp)
      container.addEventListener("wheel", onWheel, { passive: false })
    }

    // 9. Animation & Smooth Camera Tween Loop
    const startTime = performance.now()

    const animate = () => {
      if (isDisposed) return
      animationFrameId = requestAnimationFrame(animate)
      const t = (performance.now() - startTime) / 1000

      // Smooth Camera Tweening towards target
      const lerpFactor = 0.04
      camera.position.x += (camTargetRef.current.x - camera.position.x) * lerpFactor
      camera.position.y += (camTargetRef.current.y - camera.position.y) * lerpFactor
      camera.position.z += (camTargetRef.current.z - camera.position.z) * lerpFactor

      currentLookAt.x += (camTargetRef.current.lookX - currentLookAt.x) * lerpFactor
      currentLookAt.y += (camTargetRef.current.lookY - currentLookAt.y) * lerpFactor
      currentLookAt.z += (camTargetRef.current.lookZ - currentLookAt.z) * lerpFactor
      camera.lookAt(currentLookAt)

      // Idle Rotation if user isn't dragging
      if (!isDragging) {
        brainGroup.rotation.y += rotationVelocity.x
        brainGroup.rotation.x = Math.sin(t * 0.3) * 0.08
        axonCurvesGroup.rotation.y += rotationVelocity.x
        axonCurvesGroup.rotation.x = brainGroup.rotation.x
        photonsGroup.rotation.y += rotationVelocity.x
        photonsGroup.rotation.x = brainGroup.rotation.x
        gyroscopeRingsGroup.rotation.y -= rotationVelocity.x * 0.6
      }

      // Pulse Central Quantum Singularity
      const corePulse = 1 + 0.15 * Math.sin(t * 3.5)
      coreMesh.scale.setScalar(corePulse)
      haloRing.scale.setScalar(corePulse * 1.1)

      // Advance Action Potential Photons along splines
      photons.forEach((p) => {
        p.progress += p.speed
        if (p.progress > 1) p.progress = 0
        const point = p.curve.getPointAt(p.progress)
        p.mesh.position.copy(point)
      })

      // Animate Undulating Hamiltonian Floor
      const pos = floorGeo.attributes.position as THREE.BufferAttribute
      for (let i = 0; i < pos.count; i++) {
        const vx = pos.getX(i)
        const vz = pos.getZ(i)
        const distCenter = Math.sqrt(vx * vx + vz * vz)
        const wave =
          Math.sin(distCenter * 0.4 - t * 1.6) * 0.5 +
          Math.cos(vx * 0.25 + t) * 0.3 -
          Math.exp(-distCenter * 0.16) * 2.8 // Gravitational well into ground state
        pos.setY(i, wave)
      }
      pos.needsUpdate = true

      // Wobble Gyroscope Rings
      gyroRings.forEach((r, idx) => {
        r.rotation.z += (idx + 1) * 0.0018
      })

      renderer.render(scene, camera)
    }

    animate()

    // 10. Resize Observer
    const handleResize = () => {
      if (!container || !renderer) return
      const w = Math.max(container.clientWidth || 800, 320)
      const h = Math.max(typeof height === "number" ? height : container.clientHeight || 640, 400)
      camera.aspect = w / h
      camera.updateProjectionMatrix()
      renderer.setSize(w, h)
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
        container.removeEventListener("wheel", onWheel)
      }
      if (renderer) {
        renderer.dispose()
        if (container && renderer.domElement && container.contains(renderer.domElement)) {
          container.removeChild(renderer.domElement)
        }
      }
    }
  }, [interactive, height])

  const activeInfo = BRAIN_LOBES[activeLobe]

  return (
    <div
      style={{
        position: "relative",
        width: "100%",
        height: height,
        background: "radial-gradient(ellipse at 50% 35%, oklch(14% 0.025 250) 0%, oklch(5% 0.01 250) 80%)",
        borderRadius: "20px",
        overflow: "hidden",
        border: "1px solid oklch(24% 0.035 250)",
        display: "flex",
      }}
    >
      {/* 3D WebGL Canvas Viewport */}
      <div
        ref={containerRef}
        style={{
          flex: 1,
          height: "100%",
          cursor: interactive ? "grab" : "default",
          minWidth: 0,
        }}
      />

      {/* Top Telemetry HUD Strip */}
      <div
        style={{
          position: "absolute",
          top: "1rem",
          left: "1rem",
          right: "1rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          pointerEvents: "none",
          zIndex: 10,
          flexWrap: "wrap",
          gap: "0.5rem",
        }}
      >
        <div style={{ pointerEvents: "auto", display: "flex", alignItems: "center", gap: "0.625rem", flexWrap: "wrap" }}>
          {/* Main Title Badge */}
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              background: "oklch(12% 0.025 250 / 0.9)",
              backdropFilter: "blur(12px)",
              border: "1px solid oklch(30% 0.05 250)",
              borderRadius: "10px",
              padding: "0.4rem 0.85rem",
              fontSize: "0.8125rem",
              fontWeight: 800,
              color: "oklch(95% 0.01 250)",
            }}
          >
            <span style={{ fontSize: "1.0625rem" }}>🧠</span>
            <span>Mózg Silnika YourQuantum</span>
            <span
              style={{
                fontSize: "0.6875rem",
                padding: "0.15rem 0.45rem",
                borderRadius: "4px",
                background: "oklch(22% 0.05 170)",
                color: "oklch(80% 0.16 168)",
                fontWeight: 700,
              }}
            >
              LIVE 3D
            </span>
          </div>

          {/* Simulation Action Button */}
          <button
            onClick={runSimulation}
            disabled={isSimulating}
            type="button"
            style={{
              background: isSimulating
                ? "linear-gradient(135deg, oklch(40% 0.1 170), oklch(35% 0.1 240))"
                : "linear-gradient(135deg, oklch(75% 0.12 80), oklch(62% 0.18 240))",
              border: "none",
              color: "oklch(8% 0.01 250)",
              padding: "0.42rem 1.1rem",
              borderRadius: "10px",
              fontSize: "0.8125rem",
              fontWeight: 800,
              cursor: isSimulating ? "wait" : "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: "0.45rem",
              boxShadow: "0 0 20px oklch(75% 0.12 80 / 0.4)",
              transition: "all 200ms ease",
            }}
          >
            <span>{isSimulating ? "⚡ Symulacja w toku..." : "▶ Uruchom Proces Decyzyjny 3D"}</span>
          </button>
        </div>

        {/* Live Simulation Step Pill if running */}
        {simStep && (
          <div
            style={{
              pointerEvents: "auto",
              background: "oklch(14% 0.05 170 / 0.95)",
              border: "1px solid oklch(45% 0.12 168)",
              borderRadius: "10px",
              padding: "0.4rem 1rem",
              fontSize: "0.8125rem",
              fontWeight: 800,
              color: "oklch(95% 0.1 168)",
              boxShadow: "0 0 24px oklch(78% 0.16 168 / 0.6)",
              animation: "pulse 1.5s ease-in-out infinite",
            }}
          >
            {simStep}
          </div>
        )}
      </div>

      {/* Interactive 4-Lobe Navigation Pills (Top-Center) */}
      <div
        style={{
          position: "absolute",
          top: "4.25rem",
          left: "1rem",
          display: "flex",
          gap: "0.375rem",
          zIndex: 10,
          flexWrap: "wrap",
        }}
      >
        {(Object.keys(BRAIN_LOBES) as BrainLobeId[]).map((lobeKey) => {
          const l = BRAIN_LOBES[lobeKey]
          const isSelected = activeLobe === lobeKey
          return (
            <button
              key={l.id}
              onClick={() => focusLobe(l.id)}
              type="button"
              style={{
                background: isSelected ? "oklch(22% 0.04 250 / 0.95)" : "oklch(12% 0.02 250 / 0.85)",
                border: isSelected ? `1.5px solid ${l.color}` : "1px solid oklch(24% 0.03 250)",
                borderRadius: "8px",
                padding: "0.35rem 0.75rem",
                fontSize: "0.75rem",
                fontWeight: isSelected ? 800 : 600,
                color: isSelected ? "#ffffff" : "oklch(75% 0.015 250)",
                cursor: "pointer",
                backdropFilter: "blur(10px)",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.375rem",
                boxShadow: isSelected ? `0 0 16px ${l.color}40` : "none",
                transition: "all 180ms ease",
              }}
            >
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: l.color }} />
              <span>{l.name.split(":")[0]}</span>
            </button>
          )
        })}
      </div>

      {/* Explanatory Narrative Card (Right Sidebar) — Explains exactly WHAT is on screen */}
      <div
        style={{
          width: "360px",
          background: "oklch(10% 0.015 250 / 0.95)",
          borderLeft: "1px solid oklch(20% 0.025 250)",
          backdropFilter: "blur(18px)",
          padding: "1.75rem 1.5rem",
          display: "flex",
          flexDirection: "column",
          gap: "1.25rem",
          zIndex: 10,
          overflowY: "auto",
        }}
      >
        {/* Lobe Header */}
        <div>
          <span
            style={{
              fontSize: "0.6875rem",
              fontWeight: 800,
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              color: activeInfo.color,
              display: "inline-block",
              marginBottom: "0.375rem",
            }}
          >
            {activeInfo.badge}
          </span>
          <h3
            style={{
              margin: "0 0 0.25rem 0",
              fontSize: "1.125rem",
              fontWeight: 900,
              color: "oklch(97% 0.008 250)",
              letterSpacing: "-0.02em",
            }}
          >
            {activeInfo.name}
          </h3>
          <div style={{ fontSize: "0.78125rem", color: "oklch(68% 0.02 250)", fontWeight: 600 }}>
            {activeInfo.subtitle}
          </div>
        </div>

        {/* Lobe Description in Plain Polish */}
        <p style={{ margin: 0, fontSize: "0.84375rem", color: "oklch(82% 0.015 250)", lineHeight: 1.65 }}>
          {activeInfo.explanation}
        </p>

        {/* Lobe Key Mechanism Bullets */}
        <div
          style={{
            background: "oklch(13% 0.02 250)",
            border: "1px solid oklch(22% 0.025 250)",
            borderRadius: "12px",
            padding: "1rem",
          }}
        >
          <div
            style={{
              fontSize: "0.6875rem",
              fontWeight: 800,
              textTransform: "uppercase",
              letterSpacing: "0.06em",
              color: "oklch(60% 0.02 250)",
              marginBottom: "0.625rem",
            }}
          >
            Zasada Działania w Twoim Dylemacie
          </div>
          <ul style={{ margin: 0, paddingLeft: "1.1rem", fontSize: "0.78125rem", color: "oklch(75% 0.015 250)", lineHeight: 1.6 }}>
            {activeInfo.bulletPoints.map((pt, idx) => (
              <li key={idx} style={{ marginBottom: "0.375rem" }}>{pt}</li>
            ))}
          </ul>
        </div>

        {/* Live Engine Telemetry Block */}
        <div
          style={{
            background: "oklch(12% 0.02 250)",
            border: "1px solid oklch(20% 0.025 250)",
            borderRadius: "10px",
            padding: "0.875rem",
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "0.625rem",
          }}
        >
          <div>
            <span style={{ fontSize: "0.6875rem", color: "oklch(55% 0.01 250)", display: "block" }}>
              Neurony sieci
            </span>
            <strong style={{ fontSize: "0.875rem", color: "oklch(92% 0.01 250)" }}>
              {telemetry.activeNeurons} punktów
            </strong>
          </div>
          <div>
            <span style={{ fontSize: "0.6875rem", color: "oklch(55% 0.01 250)", display: "block" }}>
              Koherencja
            </span>
            <strong style={{ fontSize: "0.875rem", color: "oklch(78% 0.16 168)" }}>
              {telemetry.coherence}
            </strong>
          </div>
          <div style={{ gridColumn: "span 2" }}>
            <span style={{ fontSize: "0.6875rem", color: "oklch(55% 0.01 250)", display: "block" }}>
              Aktywne Solwery
            </span>
            <strong style={{ fontSize: "0.8125rem", color: "oklch(75% 0.12 80)" }}>
              {telemetry.mode}
            </strong>
          </div>
        </div>

        {/* Bottom Call to Action: Return to Dilemma Form */}
        {onGoToDilemma && (
          <div style={{ marginTop: "auto" }}>
            <button
              onClick={onGoToDilemma}
              type="button"
              style={{
                width: "100%",
                background: "linear-gradient(135deg, oklch(75% 0.12 80), oklch(62% 0.18 240))",
                border: "none",
                borderRadius: "10px",
                padding: "0.75rem 1rem",
                color: "oklch(8% 0.01 250)",
                fontSize: "0.875rem",
                fontWeight: 800,
                cursor: "pointer",
                boxShadow: "0 0 20px oklch(75% 0.12 80 / 0.4)",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "0.5rem",
              }}
            >
              <span>✍️ Rozwiąż swój dylemat</span>
              <span style={{ fontSize: "1rem" }}>→</span>
            </button>
          </div>
        )}

        {/* Know-how Protection Disclaimer */}
        <div style={{ fontSize: "0.6875rem", color: "oklch(50% 0.01 250)", lineHeight: 1.45 }}>
          🔒 <strong>Ochrona know-how:</strong> Model wizualizuje architekturę topologiczną. Algorytmy dekompozycji i funkcje strat pozostają chronione w zamkniętym silniku.
        </div>
      </div>
    </div>
  )
}
