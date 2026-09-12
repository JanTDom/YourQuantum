import React, { useEffect, useRef, useState } from "react"
import * as THREE from "three"
import s from "./EngineBrain3D.module.css"

export type BrainLobeId = "FRONTAL_INTAKE" | "LEFT_CONSTRAINTS" | "RIGHT_QUANTUM" | "CORE_OPTIMUM"

interface LobeInfo {
  id: BrainLobeId
  name: string
  subtitle: string
  color: string
  glowHex: number
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
    glowHex: 0xfbbf24,
    badge: "Etap 1: Intake",
    cameraPos: [0, 4, 19],
    targetPos: [0, 0.5, 3],
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
    glowHex: 0x38bdf8,
    badge: "Etap 2: Warunki Brzegowe",
    cameraPos: [-14, 4, 14],
    targetPos: [-4.5, 0, 0],
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
    glowHex: 0xc084fc,
    badge: "Etap 3: Optymalizacja Kwantowa",
    cameraPos: [14, 4, 14],
    targetPos: [4.5, 0, 0],
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
    glowHex: 0xffffff,
    badge: "Etap 4: Wynik z Dowodem",
    cameraPos: [0, 7, 13],
    targetPos: [0, 0, 0],
    explanation:
      "Punkt najniższej energii potencjalnej. Rozwiązanie o najwyższej synergii, poparte niezależnym audytem sprawdzającym linijka po linijce wszystkie warunki.",
    bulletPoints: [
      "Punkt równowagi o maksymalnej użyteczności dla Twojego życia.",
      "Niezależny weryfikator (Verdict: PASS) przed pokazaniem wyniku.",
      "Konkretny punkt zwrotny: wiesz dokładnie, co musiałoby się zmienić, by inna opcja wygrała.",
    ],
  },
}

// Generate smooth circular radial glow texture for high-luminosity particles
function createGlowTexture(): THREE.Texture {
  const canvas = document.createElement("canvas")
  canvas.width = 64
  canvas.height = 64
  const ctx = canvas.getContext("2d")
  if (ctx) {
    const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32)
    gradient.addColorStop(0, "rgba(255, 255, 255, 1.0)")
    gradient.addColorStop(0.25, "rgba(255, 255, 255, 0.85)")
    gradient.addColorStop(0.6, "rgba(120, 200, 255, 0.35)")
    gradient.addColorStop(1, "rgba(0, 0, 0, 0.0)")
    ctx.fillStyle = gradient
    ctx.fillRect(0, 0, 64, 64)
  }
  const texture = new THREE.CanvasTexture(canvas)
  return texture
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
  const activeLobeRef = useRef<BrainLobeId>("FRONTAL_INTAKE")
  const [isSimulating, setIsSimulating] = useState(false)
  const [simStep, setSimStep] = useState<string | null>(null)
  const [telemetry, setTelemetry] = useState({
    activeNeurons: 2240,
    coherence: "99.8%",
    searchSpeed: "0.84s",
    mode: "CP-SAT + QAOA Aer",
  })

  // Target camera state for responsive tweening
  const camTargetRef = useRef({
    x: 0,
    y: 4,
    z: 19,
    lookX: 0,
    lookY: 0.5,
    lookZ: 3,
  })

  const focusLobe = (lobeId: BrainLobeId) => {
    setActiveLobe(lobeId)
    activeLobeRef.current = lobeId
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
    }, 3500)

    // Phase 3: Global Optimum Collapse (after 7s)
    setTimeout(() => {
      focusLobe("CORE_OPTIMUM")
      setSimStep("Krok 3/3: Kolaps do Globalnego Optimum i audyt niezależny (PASS)!")
    }, 7000)

    // Finish simulation (after 10.5s)
    setTimeout(() => {
      setIsSimulating(false)
      setSimStep(null)
    }, 10500)
  }

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    let isDisposed = false
    let animationFrameId = 0
    let retryRafId = 0

    // Outer-scope cleanup handles that initThreeScene will assign
    let cleanupFn: (() => void) | null = null

    // Defer Three.js initialisation until the container has real pixel dimensions.
    // Safari is slower than Chrome to resolve flex:1 heights — poll up to 60 frames.
    let retryCount = 0
    const startInit = () => {
      const w = container.clientWidth
      // In Safari, height:"100%" on a flex:1 child may report 0 for many frames.
      // Fall back to the parent's clientHeight if needed.
      let h = typeof height === "number"
        ? (height as number)
        : container.clientHeight || container.parentElement?.clientHeight || 0

      if ((w === 0 || h === 0) && !isDisposed && retryCount < 60) {
        retryCount++
        retryRafId = requestAnimationFrame(startInit)
        return
      }
      // Ultimate fallback so we never start with 0
      if (h === 0) h = window.innerHeight * 0.85
      if (!isDisposed) initThreeScene()
    }
    retryRafId = requestAnimationFrame(startInit)

    function initThreeScene() {
    // container is guaranteed non-null (checked before startInit was called)
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const c = container!

    // Setup initial dimensions (guaranteed > 0 at this point)
    const width = c.clientWidth > 50 ? c.clientWidth : 320
    const rawHeight = typeof height === "number" ? height : (c.clientHeight || 300)
    const heightPx = rawHeight > 50 ? (rawHeight as number) : 300


    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene()
    // Very gentle background fog to preserve crisp particle brightness
    scene.fog = new THREE.FogExp2(0x04060c, 0.006)

    const camera = new THREE.PerspectiveCamera(45, width / heightPx, 0.1, 1000)
    const initialLobe = BRAIN_LOBES[activeLobeRef.current]
    camera.position.set(initialLobe.cameraPos[0], initialLobe.cameraPos[1], initialLobe.cameraPos[2])
    const currentLookAt = new THREE.Vector3(initialLobe.targetPos[0], initialLobe.targetPos[1], initialLobe.targetPos[2])
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

    while (c.firstChild) {
      c.removeChild(c.firstChild)
    }
    c.appendChild(renderer.domElement)

    // Glow texture for bright point sprites
    const glowTexture = createGlowTexture()

    // 2. Main Groups
    const mainBrainGroup = new THREE.Group()
    const axonCurvesGroup = new THREE.Group()
    const photonsGroup = new THREE.Group()
    const coreGlowGroup = new THREE.Group()
    const gyroscopeRingsGroup = new THREE.Group()
    const lobeHighlightsGroup = new THREE.Group()

    scene.add(mainBrainGroup)
    scene.add(axonCurvesGroup)
    scene.add(photonsGroup)
    scene.add(coreGlowGroup)
    scene.add(gyroscopeRingsGroup)
    scene.add(lobeHighlightsGroup)

    // 3. Volumetric Dual-Hemisphere Brain Point Cloud
    // 2,600 luminous particles with anatomical clustering
    const brainParticlesCount = 2600
    const brainGeo = new THREE.BufferGeometry()
    const positions = new Float32Array(brainParticlesCount * 3)
    const colors = new Float32Array(brainParticlesCount * 3)

    const colorLogicCyan = new THREE.Color("#38bdf8")
    const colorLogicAmber = new THREE.Color("#fbbf24")
    const colorQuantumViolet = new THREE.Color("#c084fc")
    const colorQuantumCyan = new THREE.Color("#4df0ff")
    const colorCoreWhite = new THREE.Color("#ffffff")

    const corticalNodes: THREE.Vector3[] = []

    for (let i = 0; i < brainParticlesCount; i++) {
      const isRightHemisphere = i % 2 === 0
      const sideSign = isRightHemisphere ? 1 : -1

      const u = Math.random() * Math.PI
      const v = (Math.random() - 0.5) * Math.PI * 2

      const rx = 5.8
      const ry = 4.8
      const rz = 7.2

      const gyrusRipple =
        Math.sin(u * 9 + (isRightHemisphere ? 1 : 0)) * 0.45 +
        Math.cos(v * 8) * 0.35

      const fissureGap = 0.55

      let x = sideSign * (fissureGap + Math.abs(Math.sin(u) * Math.cos(v) * rx * (1 + gyrusRipple * 0.12)))
      let y = Math.cos(u) * ry * (1 + gyrusRipple * 0.12)
      let z = Math.sin(u) * Math.sin(v) * rz * (1 + gyrusRipple * 0.12)

      if (y < -1.5 && z < 0) {
        x *= 0.75
        y += 0.7
        z *= 0.75
      }

      if (z > 1) {
        y += 0.4 * Math.sin(u)
      }

      // Add a cluster of deep core singularity points
      if (i < 260) {
        const coreDist = Math.random() * 2.4
        const coreAng = Math.random() * Math.PI * 2
        const coreZ = (Math.random() - 0.5) * 3
        x = Math.cos(coreAng) * coreDist
        y = Math.sin(coreAng) * coreDist * 0.8
        z = coreZ
      }

      positions[i * 3] = x
      positions[i * 3 + 1] = y
      positions[i * 3 + 2] = z

      const c = new THREE.Color()
      const distFromCenter = Math.sqrt(x * x + y * y + z * z)

      if (distFromCenter < 2.8) {
        c.copy(colorCoreWhite)
      } else if (z > 2.8) {
        c.copy(colorLogicAmber).lerp(colorCoreWhite, 0.25)
      } else if (isRightHemisphere) {
        const t = Math.min(1, (z + 4) / 8)
        c.copy(colorQuantumViolet).lerp(colorQuantumCyan, t)
      } else {
        const t = Math.min(1, (z + 4) / 8)
        c.copy(colorLogicCyan).lerp(colorLogicAmber, t * 0.3)
      }

      colors[i * 3] = c.r
      colors[i * 3 + 1] = c.g
      colors[i * 3 + 2] = c.b

      if (i % 35 === 0) {
        corticalNodes.push(new THREE.Vector3(x, y, z))
      }
    }

    brainGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3))
    brainGeo.setAttribute("color", new THREE.BufferAttribute(colors, 3))

    // High luminosity point material using circular glow sprite
    const brainMaterial = new THREE.PointsMaterial({
      size: 0.62,
      map: glowTexture,
      vertexColors: true,
      transparent: true,
      opacity: 0.95,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    })

    const brainPoints = new THREE.Points(brainGeo, brainMaterial)
    mainBrainGroup.add(brainPoints)

    // 4. Central Radiant Singularity (The Quantum Ground State Core)
    const coreMeshGeo = new THREE.IcosahedronGeometry(1.8, 2)
    const coreMeshMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      wireframe: true,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
    })
    const coreMesh = new THREE.Mesh(coreMeshGeo, coreMeshMat)
    coreGlowGroup.add(coreMesh)

    // Glowing core nucleus sphere
    const coreSphereGeo = new THREE.SphereGeometry(1.1, 16, 16)
    const coreSphereMat = new THREE.MeshBasicMaterial({
      color: 0x4df0ff,
      transparent: true,
      opacity: 0.6,
      blending: THREE.AdditiveBlending,
    })
    const coreSphere = new THREE.Mesh(coreSphereGeo, coreSphereMat)
    coreGlowGroup.add(coreSphere)

    // Core halo ring
    const haloGeo = new THREE.RingGeometry(1.8, 3.2, 48)
    const haloMat = new THREE.MeshBasicMaterial({
      color: 0xfbbf24,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.5,
      blending: THREE.AdditiveBlending,
    })
    const haloRing = new THREE.Mesh(haloGeo, haloMat)
    haloRing.rotation.x = Math.PI / 2
    coreGlowGroup.add(haloRing)

    // 5. Interactive Lobe Focal Highlights (Visual feedback on active lobe!)
    // Frontal Lobe Highlight Aura
    const frontalAuraGeo = new THREE.RingGeometry(2.4, 3.8, 32)
    const frontalAuraMat = new THREE.MeshBasicMaterial({
      color: 0xfbbf24,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.7,
      blending: THREE.AdditiveBlending,
    })
    const frontalAura = new THREE.Mesh(frontalAuraGeo, frontalAuraMat)
    frontalAura.position.set(0, 0.5, 4.5)
    lobeHighlightsGroup.add(frontalAura)

    // Left Lobe (Constraints) Highlight Aura
    const leftAuraGeo = new THREE.RingGeometry(2.8, 4.2, 32)
    const leftAuraMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.7,
      blending: THREE.AdditiveBlending,
    })
    const leftAura = new THREE.Mesh(leftAuraGeo, leftAuraMat)
    leftAura.position.set(-5, 0, 0)
    leftAura.rotation.y = Math.PI / 2
    lobeHighlightsGroup.add(leftAura)

    // Right Lobe (Quantum) Highlight Aura
    const rightAuraGeo = new THREE.RingGeometry(2.8, 4.2, 32)
    const rightAuraMat = new THREE.MeshBasicMaterial({
      color: 0xc084fc,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.7,
      blending: THREE.AdditiveBlending,
    })
    const rightAura = new THREE.Mesh(rightAuraGeo, rightAuraMat)
    rightAura.position.set(5, 0, 0)
    rightAura.rotation.y = -Math.PI / 2
    lobeHighlightsGroup.add(rightAura)

    // 6. Synaptic Axon Splines & Action Potential Photons
    const splineCount = 36
    const splines: THREE.CatmullRomCurve3[] = []
    const photons: Array<{
      mesh: THREE.Mesh
      curve: THREE.CatmullRomCurve3
      progress: number
      speed: number
    }> = []

    const photonGeo = new THREE.SphereGeometry(0.24, 8, 8)
    const photonMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      blending: THREE.AdditiveBlending,
    })

    for (let s = 0; s < splineCount; s++) {
      const p1 = corticalNodes[s % corticalNodes.length]
      const p2 = corticalNodes[(s + 7) % corticalNodes.length]
      const mid = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5)
      mid.y += (Math.random() - 0.5) * 2.2
      mid.x += (Math.random() - 0.5) * 1.4

      const curve = new THREE.CatmullRomCurve3([p1, mid, p2])
      splines.push(curve)

      const curvePoints = curve.getPoints(30)
      const curveGeo = new THREE.BufferGeometry().setFromPoints(curvePoints)
      const isQuantumSide = s % 2 === 0
      const curveMat = new THREE.LineBasicMaterial({
        color: isQuantumSide ? 0xc084fc : 0x38bdf8,
        transparent: true,
        opacity: 0.38,
        blending: THREE.AdditiveBlending,
      })
      const line = new THREE.Line(curveGeo, curveMat)
      axonCurvesGroup.add(line)

      const photonMesh = new THREE.Mesh(photonGeo, photonMat)
      photonsGroup.add(photonMesh)
      photons.push({
        mesh: photonMesh,
        curve,
        progress: Math.random(),
        speed: 0.005 + Math.random() * 0.006,
      })
    }

    // 7. Quantum Phase Interference Gyroscope Rings
    const gyroRadii = [8.8, 10.8, 12.8]
    const gyroColors = [0x4df0ff, 0xc084fc, 0xfbbf24]
    const gyroRings: THREE.Line[] = []

    gyroRadii.forEach((r, idx) => {
      const curve = new THREE.EllipseCurve(0, 0, r, r * 0.94, 0, Math.PI * 2, false, 0)
      const pts = curve.getPoints(80)
      const geo = new THREE.BufferGeometry().setFromPoints(pts)
      geo.rotateX(Math.PI / 2 + idx * 0.4)
      geo.rotateY(idx * 0.6)

      const mat = new THREE.LineBasicMaterial({
        color: gyroColors[idx],
        transparent: true,
        opacity: 0.45,
        blending: THREE.AdditiveBlending,
      })
      const ring = new THREE.Line(geo, mat)
      gyroscopeRingsGroup.add(ring)
      gyroRings.push(ring)
    })

    // 8. Hamiltonian Energy Potential Grid Base
    const floorGeo = new THREE.PlaneGeometry(36, 36, 18, 18)
    floorGeo.rotateX(-Math.PI / 2)
    floorGeo.translate(0, -8, 0)

    const floorMat = new THREE.MeshBasicMaterial({
      color: 0x1d4ed8,
      wireframe: true,
      transparent: true,
      opacity: 0.35,
    })
    const floorMesh = new THREE.Mesh(floorGeo, floorMat)
    scene.add(floorMesh)

    // 9. Mouse Drag Controls with Inertia
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

      mainBrainGroup.rotation.y += dx * 0.005
      mainBrainGroup.rotation.x += dy * 0.005
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
      camTargetRef.current.z = Math.max(10, Math.min(36, camTargetRef.current.z + e.deltaY * 0.025))
    }

    const onTouchStart = (e: TouchEvent) => {
      if (e.touches.length === 1) {
        isDragging = true
        prevMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY }
      }
    }

    const onTouchMove = (e: TouchEvent) => {
      if (!isDragging || e.touches.length !== 1) return
      if (e.cancelable) e.preventDefault()
      const dx = e.touches[0].clientX - prevMouse.x
      const dy = e.touches[0].clientY - prevMouse.y

      mainBrainGroup.rotation.y += dx * 0.0055
      mainBrainGroup.rotation.x += dy * 0.0055
      axonCurvesGroup.rotation.y += dx * 0.0055
      axonCurvesGroup.rotation.x += dy * 0.0055
      photonsGroup.rotation.y += dx * 0.0055
      photonsGroup.rotation.x += dy * 0.0055

      prevMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY }
    }

    const onTouchEnd = () => {
      isDragging = false
    }

    if (interactive) {
      c.addEventListener("mousedown", onMouseDown)
      window.addEventListener("mousemove", onMouseMove)
      window.addEventListener("mouseup", onMouseUp)
      c.addEventListener("wheel", onWheel, { passive: false })
      c.addEventListener("touchstart", onTouchStart, { passive: true })
      window.addEventListener("touchmove", onTouchMove, { passive: false })
      window.addEventListener("touchend", onTouchEnd)
    }

    // 10. Ultra-Responsive Animation & Smooth Camera Tween Loop
    const startTime = performance.now()

    const animate = () => {
      if (isDisposed) return
      animationFrameId = requestAnimationFrame(animate)
      const t = (performance.now() - startTime) / 1000

      // Fast, snappy camera lerp (0.12 = fast smooth glide in ~300ms instead of 4 seconds!)
      const lerpFactor = 0.12
      camera.position.x += (camTargetRef.current.x - camera.position.x) * lerpFactor
      camera.position.y += (camTargetRef.current.y - camera.position.y) * lerpFactor
      camera.position.z += (camTargetRef.current.z - camera.position.z) * lerpFactor

      currentLookAt.x += (camTargetRef.current.lookX - currentLookAt.x) * lerpFactor
      currentLookAt.y += (camTargetRef.current.lookY - currentLookAt.y) * lerpFactor
      currentLookAt.z += (camTargetRef.current.lookZ - currentLookAt.z) * lerpFactor
      camera.lookAt(currentLookAt)

      // Active Lobe Dynamic 3D Feedback (Highlights the selected lobe instantly!)
      const currentLobe = activeLobeRef.current
      const pulseWave = 1 + 0.25 * Math.sin(t * 5.0)

      frontalAura.visible = currentLobe === "FRONTAL_INTAKE"
      if (frontalAura.visible) {
        frontalAura.scale.setScalar(pulseWave)
      }

      leftAura.visible = currentLobe === "LEFT_CONSTRAINTS"
      if (leftAura.visible) {
        leftAura.scale.setScalar(pulseWave)
      }

      rightAura.visible = currentLobe === "RIGHT_QUANTUM"
      if (rightAura.visible) {
        rightAura.scale.setScalar(pulseWave)
      }

      // Idle Rotation
      if (!isDragging) {
        mainBrainGroup.rotation.y += rotationVelocity.x
        mainBrainGroup.rotation.x = Math.sin(t * 0.3) * 0.06
        axonCurvesGroup.rotation.y += rotationVelocity.x
        axonCurvesGroup.rotation.x = mainBrainGroup.rotation.x
        photonsGroup.rotation.y += rotationVelocity.x
        photonsGroup.rotation.x = mainBrainGroup.rotation.x
        gyroscopeRingsGroup.rotation.y -= rotationVelocity.x * 0.7
      }

      // Central Quantum Singularity Pulse
      const isCoreActive = currentLobe === "CORE_OPTIMUM"
      const corePulseFactor = isCoreActive ? 1.4 + 0.3 * Math.sin(t * 6.0) : 1 + 0.15 * Math.sin(t * 3.5)
      coreMesh.scale.setScalar(corePulseFactor)
      coreSphere.scale.setScalar(corePulseFactor * 0.9)
      haloRing.scale.setScalar(corePulseFactor * 1.15)
      haloRing.rotation.z += 0.015

      // Advance Action Potential Photons along splines
      photons.forEach((p) => {
        p.progress += p.speed
        if (p.progress > 1) p.progress = 0
        const point = p.curve.getPointAt(p.progress)
        p.mesh.position.copy(point)
      })

      // Elegant Hamiltonian base slow rotation (0 CPU vertex recomputation!)
      floorMesh.rotation.z += 0.0015

      // Gyroscope wobble
      gyroRings.forEach((r, idx) => {
        r.rotation.z += (idx + 1) * 0.002
      })

      renderer.render(scene, camera)
    }

    animate()

    // 11. Dynamic Resize Observer for robust viewport fitting
    const handleResize = () => {
      if (!c || !renderer) return
      const w = c.clientWidth || 320
      const h = c.clientHeight || 300
      camera.aspect = w / h
      camera.updateProjectionMatrix()
      renderer.setSize(w, h)
    }

    const ro = new ResizeObserver(() => {
      if (!isDisposed) handleResize()
    })
    ro.observe(c)
    window.addEventListener("resize", handleResize)

    // Store full cleanup into outer-scope ref for the useEffect return
    cleanupFn = () => {
      ro.disconnect()
      window.removeEventListener("resize", handleResize)
      if (interactive) {
        c.removeEventListener("mousedown", onMouseDown)
        window.removeEventListener("mousemove", onMouseMove)
        window.removeEventListener("mouseup", onMouseUp)
        c.removeEventListener("wheel", onWheel)
        c.removeEventListener("touchstart", onTouchStart)
        window.removeEventListener("touchmove", onTouchMove)
        window.removeEventListener("touchend", onTouchEnd)
      }
      cancelAnimationFrame(animationFrameId)
      if (renderer) {
        renderer.dispose()
        if (renderer.domElement && c.contains(renderer.domElement)) {
          c.removeChild(renderer.domElement)
        }
      }
      glowTexture.dispose()
      brainGeo.dispose()
      brainMaterial.dispose()
    }

    } // end initThreeScene

    return () => {
      isDisposed = true
      cancelAnimationFrame(retryRafId)
      if (cleanupFn) cleanupFn()
    }
  }, [interactive, height])

  const activeInfo = BRAIN_LOBES[activeLobe]

  return (
    <div className={s.container} style={{ height: height }}>
      {/* 3D WebGL Canvas Viewport */}
      <div ref={containerRef} className={s.canvasWrapper} />

      {/* Top Telemetry HUD Strip */}
      <div className={s.telemetryHud}>
        <div style={{ pointerEvents: "auto", display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
          {/* Main Title Badge (Desktop only, hidden on mobile via CSS) */}
          <div className={s.titleBadge}>
            <span style={{ fontSize: "1.0625rem" }}>🧠</span>
            <span>Mózg Silnika YourQuantum</span>
            <span className={s.liveTag}>LIVE 3D</span>
          </div>

          {/* Simulation Action Button */}
          <button
            onClick={runSimulation}
            disabled={isSimulating}
            type="button"
            className={s.simButton}
            style={{
              background: isSimulating
                ? "linear-gradient(135deg, oklch(40% 0.1 170), oklch(35% 0.1 240))"
                : "linear-gradient(135deg, oklch(75% 0.12 80), oklch(62% 0.18 240))",
              cursor: isSimulating ? "wait" : "pointer",
            }}
          >
            {isSimulating ? (
              <span>⚡ Symulacja...</span>
            ) : (
              <>
                <span className={s.desktopOnly}>▶ Uruchom Proces Decyzyjny 3D</span>
                <span className={s.mobileOnly}>▶ Symuluj proces</span>
              </>
            )}
          </button>
        </div>

        {/* Live Simulation Step Pill if running */}
        {simStep && (
          <div className={s.simStepPill}>
            {simStep}
          </div>
        )}
      </div>

      {/* Interactive 4-Lobe Navigation Pills (Desktop: Top-Center overlay; Mobile: Docked tab bar) */}
      <div className={s.lobeNav}>
        {(Object.keys(BRAIN_LOBES) as BrainLobeId[]).map((lobeKey) => {
          const l = BRAIN_LOBES[lobeKey]
          const isSelected = activeLobe === lobeKey
          return (
            <button
              key={l.id}
              onClick={() => focusLobe(l.id)}
              type="button"
              className={s.lobePill}
              style={{
                background: isSelected ? "oklch(25% 0.05 250 / 0.98)" : "oklch(12% 0.02 250 / 0.85)",
                borderColor: isSelected ? l.color : "oklch(24% 0.03 250)",
                borderWidth: isSelected ? "2px" : "1px",
                color: isSelected ? "#ffffff" : "oklch(75% 0.015 250)",
                fontWeight: isSelected ? 800 : 600,
                boxShadow: isSelected ? `0 0 16px ${l.color}60` : "none",
                transform: isSelected ? "scale(1.03)" : "scale(1)",
              }}
            >
              <span className={s.lobeDot} style={{ background: l.color, boxShadow: `0 0 8px ${l.color}` }} />
              <span>{l.name.split(":")[0]}</span>
            </button>
          )
        })}
      </div>

      {/* Explanatory Narrative Card (Desktop: Right Sidebar; Mobile: Bottom Scrollable Sheet) */}
      <div className={s.detailSheet}>
        {/* Lobe Header */}
        <div>
          <span className={s.lobeBadge} style={{ color: activeInfo.color }}>
            {activeInfo.badge}
          </span>
          <h3 className={s.lobeTitle}>
            {activeInfo.name}
          </h3>
          <div className={s.lobeSubtitle}>
            {activeInfo.subtitle}
          </div>
        </div>

        {/* Lobe Description in Plain Polish */}
        <p className={s.lobeExplanation}>
          {activeInfo.explanation}
        </p>

        {/* Lobe Key Mechanism Bullets */}
        <div className={s.bulletsBox}>
          <div className={s.bulletsHeader}>
            Zasada Działania w Twoim Dylemacie
          </div>
          <ul className={s.bulletsList}>
            {activeInfo.bulletPoints.map((pt, idx) => (
              <li key={idx} className={s.bulletItem}>{pt}</li>
            ))}
          </ul>
        </div>

        {/* Live Engine Telemetry Block */}
        <div className={s.telemetryGrid}>
          <div>
            <span className={s.telemetryLabel}>Neurony sieci</span>
            <strong style={{ fontSize: "0.875rem", color: "oklch(92% 0.01 250)" }}>
              {telemetry.activeNeurons} punktów
            </strong>
          </div>
          <div>
            <span className={s.telemetryLabel}>Koherencja</span>
            <strong style={{ fontSize: "0.875rem", color: "oklch(78% 0.16 168)" }}>
              {telemetry.coherence}
            </strong>
          </div>
          <div style={{ gridColumn: "span 2" }}>
            <span className={s.telemetryLabel}>Aktywne Solwery</span>
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
              className={s.ctaBtn}
            >
              <span>✍️ Rozwiąż swój dylemat</span>
              <span style={{ fontSize: "1rem" }}>→</span>
            </button>
          </div>
        )}

        {/* Know-how Protection Disclaimer */}
        <div className={s.disclaimer}>
          🔒 <strong>Ochrona know-how:</strong> Model wizualizuje architekturę topologiczną. Algorytmy dekompozycji i funkcje strat pozostają chronione w zamkniętym silniku.
        </div>
      </div>
    </div>
  )
}
