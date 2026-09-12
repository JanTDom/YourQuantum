import React, { useEffect, useRef } from 'react'

interface QuantumEntanglementCanvasProps {
  className?: string
}

interface Particle {
  s: number // 0 to 1 along beam
  speed: number
  radiusOffset: number
  phaseOffset: number
  size: number
  color: string
}

interface Soliton {
  s: number
  speed: number
  direction: 1 | -1
  color: string
  glowColor: string
}

interface Ripple {
  x: number
  y: number
  radius: number
  maxRadius: number
  alpha: number
  speed: number
  color: string
}

export const QuantumEntanglementCanvas: React.FC<QuantumEntanglementCanvasProps> = ({
  className,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const mouseRef = useRef<{ x: number; y: number; active: boolean }>({
    x: -9999,
    y: -9999,
    active: false,
  })

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animId: number
    const startTime = performance.now()

    // 1. Initialize Particles
    const PARTICLE_COUNT = 48
    const particles: Particle[] = []
    const PARTICLE_COLORS = [
      'rgba(56, 189, 248, ',   // cyan
      'rgba(147, 197, 253, ',  // sky blue
      'rgba(251, 191, 36, ',   // amber gold
      'rgba(216, 180, 254, ',  // purple violet
    ]

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push({
        s: Math.random(),
        speed: 0.04 + Math.random() * 0.08,
        radiusOffset: (Math.random() - 0.5) * 18,
        phaseOffset: Math.random() * Math.PI * 2,
        size: 0.8 + Math.random() * 1.6,
        color: PARTICLE_COLORS[i % PARTICLE_COLORS.length],
      })
    }

    // 2. Soliton Energy Packets
    const solitons: Soliton[] = [
      { s: 0.1, speed: 0.22, direction: 1, color: '#ffffff', glowColor: 'rgba(56, 189, 248, 0.8)' },
      { s: 0.7, speed: 0.19, direction: -1, color: '#fffbeb', glowColor: 'rgba(251, 191, 36, 0.75)' },
      { s: 0.45, speed: 0.26, direction: 1, color: '#e0f2fe', glowColor: 'rgba(96, 165, 250, 0.8)' },
      { s: 0.9, speed: 0.24, direction: -1, color: '#fef3c7', glowColor: 'rgba(245, 158, 11, 0.75)' },
    ]

    // 3. Expanding Interference Ripples
    const ripples: Ripple[] = []
    let lastRippleTime = 0

    // Resize handling
    const setCanvasSize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      const rect = canvas.getBoundingClientRect()
      canvas.width = Math.floor(rect.width * dpr)
      canvas.height = Math.floor(rect.height * dpr)
    }

    setCanvasSize()
    window.addEventListener('resize', setCanvasSize)

    // Mouse tracking
    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect()
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      mouseRef.current = {
        x: (e.clientX - rect.left) * dpr,
        y: (e.clientY - rect.top) * dpr,
        active: true,
      }
    }

    const handleMouseLeave = () => {
      mouseRef.current.active = false
    }

    const parentEl = canvas.parentElement
    if (parentEl) {
      parentEl.addEventListener('mousemove', handleMouseMove)
      parentEl.addEventListener('mouseleave', handleMouseLeave)
    }

    // Animation loop
    const render = (now: number) => {
      animId = requestAnimationFrame(render)
      const t = (now - startTime) / 1000
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      const W = canvas.width
      const H = canvas.height

      ctx.clearRect(0, 0, W, H)

      // ── Precise geometry synchronization with hero-entanglement.jpg ──
      // Original photo resolution: 1024 x 576 (aspect ratio 16:9)
      const IMG_ASPECT = 1024 / 576
      const SCREEN_ASPECT = W / H

      let dispW: number
      let dispH: number
      let offX: number
      let offY: number

      if (SCREEN_ASPECT >= IMG_ASPECT) {
        dispW = W
        dispH = W / IMG_ASPECT
        offX = 0
        offY = (H - dispH) / 2
      } else {
        dispH = H
        dispW = H * IMG_ASPECT
        offX = (W - dispW) / 2
        offY = 0
      }

      // Exact pixel coordinates on original 1024x576 image:
      // Left Sphere center: (320, 250), radius ~90
      // Right Sphere center: (705, 252), radius ~90
      const x1 = offX + dispW * (320 / 1024)
      const y1 = offY + dispH * (250 / 576)
      const r1 = dispW * (88 / 1024)

      const x2 = offX + dispW * (705 / 1024)
      const y2 = offY + dispH * (252 / 576)
      const r2 = dispW * (88 / 1024)

      const dx = x2 - x1
      const dy = y2 - y1
      const beamLen = Math.hypot(dx, dy)
      if (beamLen < 10) return

      const tx = dx / beamLen
      const ty = dy / beamLen
      const nx = -ty
      const ny = tx

      // Mouse interaction factor near beam
      const mouse = mouseRef.current
      let mouseBeamFactor = 0
      let mouseBeamS = 0.5

      if (mouse.active) {
        // Project mouse onto beam
        const vmx = mouse.x - x1
        const vmy = mouse.y - y1
        const proj = (vmx * tx + vmy * ty) / beamLen
        if (proj >= -0.1 && proj <= 1.1) {
          const perpDist = Math.abs(vmx * nx + vmy * ny)
          if (perpDist < 160 * dpr) {
            mouseBeamFactor = (1 - perpDist / (160 * dpr)) * 0.8
            mouseBeamS = Math.max(0, Math.min(1, proj))
          }
        }
      }

      // ── Periodic interference ripples from nodes ──
      if (now - lastRippleTime > 2200) {
        lastRippleTime = now
        ripples.push({
          x: x1,
          y: y1,
          radius: r1 * 0.5,
          maxRadius: r1 * 2.8,
          alpha: 0.45,
          speed: 28 * dpr,
          color: 'rgba(56, 189, 248, ',
        })
        ripples.push({
          x: x2,
          y: y2,
          radius: r2 * 0.5,
          maxRadius: r2 * 2.8,
          alpha: 0.45,
          speed: 28 * dpr,
          color: 'rgba(251, 191, 36, ',
        })
      }

      // Update and draw ripples
      for (let i = ripples.length - 1; i >= 0; i--) {
        const rip = ripples[i]
        rip.radius += (rip.speed / 60)
        const progress = rip.radius / rip.maxRadius
        const currentAlpha = rip.alpha * (1 - progress)

        if (progress >= 1) {
          ripples.splice(i, 1)
          continue
        }

        ctx.beginPath()
        ctx.arc(rip.x, rip.y, rip.radius, 0, Math.PI * 2)
        ctx.strokeStyle = `${rip.color}${currentAlpha.toFixed(3)})`
        ctx.lineWidth = 1.2 * dpr
        ctx.stroke()
      }

      // ── 1. Core Pulsating Glow on Photo Spheres ──
      const pulse1 = 1 + Math.sin(t * 2.8) * 0.15
      const pulse2 = 1 + Math.cos(t * 2.4) * 0.15

      // Left Core (Cool Cyan/Blue Quantum State)
      const g1 = ctx.createRadialGradient(x1, y1, 0, x1, y1, r1 * 0.95 * pulse1)
      g1.addColorStop(0, 'rgba(255, 255, 255, 0.45)')
      g1.addColorStop(0.25, 'rgba(56, 189, 248, 0.35)')
      g1.addColorStop(0.65, 'rgba(37, 99, 235, 0.15)')
      g1.addColorStop(1, 'rgba(37, 99, 235, 0)')
      ctx.fillStyle = g1
      ctx.beginPath()
      ctx.arc(x1, y1, r1 * 0.95 * pulse1, 0, Math.PI * 2)
      ctx.fill()

      // Right Core (Warm Gold/Purple Quantum State)
      const g2 = ctx.createRadialGradient(x2, y2, 0, x2, y2, r2 * 0.95 * pulse2)
      g2.addColorStop(0, 'rgba(255, 255, 255, 0.48)')
      g2.addColorStop(0.28, 'rgba(251, 191, 36, 0.35)')
      g2.addColorStop(0.7, 'rgba(192, 132, 252, 0.16)')
      g2.addColorStop(1, 'rgba(192, 132, 252, 0)')
      ctx.fillStyle = g2
      ctx.beginPath()
      ctx.arc(x2, y2, r2 * 0.95 * pulse2, 0, Math.PI * 2)
      ctx.fill()

      // ── 2. 3D Rotating Orbital Rings around Spheres ──
      const drawOrbitalRing = (
        cx: number,
        cy: number,
        rx: number,
        ry: number,
        tiltRad: number,
        orbitAngle: number,
        ringColor: string,
        dotColor: string
      ) => {
        ctx.save()
        ctx.translate(cx, cy)
        ctx.rotate(tiltRad)

        // Draw ellipse ring
        ctx.beginPath()
        ctx.ellipse(0, 0, rx, ry, 0, 0, Math.PI * 2)
        ctx.strokeStyle = ringColor
        ctx.lineWidth = 1 * dpr
        ctx.stroke()

        // Orbiting Qubit Phase Dot
        const dotX = rx * Math.cos(orbitAngle)
        const dotY = ry * Math.sin(orbitAngle)
        const dotDepth = Math.sin(orbitAngle) // front vs back

        // Orbit dot glow
        const dotGlow = ctx.createRadialGradient(dotX, dotY, 0, dotX, dotY, 7 * dpr)
        dotGlow.addColorStop(0, dotColor)
        dotGlow.addColorStop(1, 'rgba(255, 255, 255, 0)')
        ctx.fillStyle = dotGlow
        ctx.beginPath()
        ctx.arc(dotX, dotY, 7 * dpr, 0, Math.PI * 2)
        ctx.fill()

        // Orbit dot core
        ctx.fillStyle = '#ffffff'
        ctx.beginPath()
        ctx.arc(dotX, dotY, (dotDepth > 0 ? 2.2 : 1.4) * dpr, 0, Math.PI * 2)
        ctx.fill()

        ctx.restore()
      }

      // Left sphere orbital rings
      drawOrbitalRing(
        x1, y1,
        r1 * 1.25, r1 * 0.42,
        22 * (Math.PI / 180),
        t * 1.1,
        'rgba(56, 189, 248, 0.3)',
        'rgba(56, 189, 248, 0.9)'
      )
      drawOrbitalRing(
        x1, y1,
        r1 * 1.38, r1 * 0.35,
        -38 * (Math.PI / 180),
        -t * 0.85 + 1.5,
        'rgba(147, 197, 253, 0.25)',
        'rgba(147, 197, 253, 0.85)'
      )

      // Right sphere orbital rings
      drawOrbitalRing(
        x2, y2,
        r2 * 1.28, r2 * 0.44,
        -24 * (Math.PI / 180),
        t * 0.95 + 0.8,
        'rgba(251, 191, 36, 0.3)',
        'rgba(251, 191, 36, 0.9)'
      )
      drawOrbitalRing(
        x2, y2,
        r2 * 1.42, r2 * 0.36,
        35 * (Math.PI / 180),
        -t * 1.2 + 2.2,
        'rgba(192, 132, 252, 0.25)',
        'rgba(192, 132, 252, 0.85)'
      )

      // ── 3. Entanglement Beam Quantum Waves ──
      // Multi-harmonic standing and traveling waves with Dirichlet boundary envelope
      const STEPS = 120
      const waveGrad = ctx.createLinearGradient(x1, y1, x2, y2)
      waveGrad.addColorStop(0, 'rgba(56, 189, 248, 0.85)')
      waveGrad.addColorStop(0.5, 'rgba(192, 132, 252, 0.75)')
      waveGrad.addColorStop(1, 'rgba(251, 191, 36, 0.85)')

      // Wave 1: Cyan / High Coherence
      ctx.beginPath()
      for (let i = 0; i <= STEPS; i++) {
        const s = i / STEPS
        const env = Math.sin(Math.PI * s) // Envelope zeroes at spheres
        const amp = (13 * dpr + mouseBeamFactor * 18 * dpr * Math.exp(-Math.pow((s - mouseBeamS) / 0.18, 2)))
        const wave = amp * env * Math.sin(Math.PI * 2 * 3.5 * s - t * 3.4)

        const px = x1 + s * dx + nx * wave
        const py = y1 + s * dy + ny * wave

        if (i === 0) ctx.moveTo(px, py)
        else ctx.lineTo(px, py)
      }
      ctx.strokeStyle = waveGrad
      ctx.lineWidth = 1.8 * dpr
      ctx.stroke()

      // Wave 2: Counter-propagating Gold Wave
      ctx.beginPath()
      for (let i = 0; i <= STEPS; i++) {
        const s = i / STEPS
        const env = Math.sin(Math.PI * s)
        const amp = (11 * dpr + mouseBeamFactor * 14 * dpr * Math.exp(-Math.pow((s - mouseBeamS) / 0.18, 2)))
        const wave = amp * env * Math.sin(Math.PI * 2 * 4.5 * s + t * 2.9 + 1.2)

        const px = x1 + s * dx + nx * wave
        const py = y1 + s * dy + ny * wave

        if (i === 0) ctx.moveTo(px, py)
        else ctx.lineTo(px, py)
      }
      ctx.strokeStyle = 'rgba(251, 191, 36, 0.55)'
      ctx.lineWidth = 1.2 * dpr
      ctx.stroke()

      // Wave 3: High-frequency carrier ripple
      ctx.beginPath()
      for (let i = 0; i <= STEPS; i++) {
        const s = i / STEPS
        const env = Math.sin(Math.PI * s)
        const wave = (6 * dpr) * env * Math.sin(Math.PI * 2 * 9.0 * s - t * 5.2) * Math.cos(Math.PI * 2 * 1.5 * s - t * 0.8)

        const px = x1 + s * dx + nx * wave
        const py = y1 + s * dy + ny * wave

        if (i === 0) ctx.moveTo(px, py)
        else ctx.lineTo(px, py)
      }
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.45)'
      ctx.lineWidth = 0.9 * dpr
      ctx.stroke()

      // ── 4. Soliton Energy Packets (Traveling Light Quanta) ──
      for (const sol of solitons) {
        sol.s += sol.speed * sol.direction * 0.016
        if (sol.direction === 1 && sol.s > 1) sol.s = 0
        if (sol.direction === -1 && sol.s < 0) sol.s = 1

        const s = sol.s
        const env = Math.sin(Math.PI * s)
        const wave = 12 * dpr * env * Math.sin(Math.PI * 2 * 3.5 * s - t * 3.4)

        const px = x1 + s * dx + nx * wave
        const py = y1 + s * dy + ny * wave

        // Soliton glow halo
        const haloR = (16 + env * 12) * dpr
        const solGlow = ctx.createRadialGradient(px, py, 0, px, py, haloR)
        solGlow.addColorStop(0, sol.color)
        solGlow.addColorStop(0.35, sol.glowColor)
        solGlow.addColorStop(1, 'rgba(0, 0, 0, 0)')
        ctx.fillStyle = solGlow
        ctx.beginPath()
        ctx.arc(px, py, haloR, 0, Math.PI * 2)
        ctx.fill()

        // Soliton intense core
        ctx.fillStyle = '#ffffff'
        ctx.beginPath()
        ctx.arc(px, py, 2.5 * dpr, 0, Math.PI * 2)
        ctx.fill()
      }

      // ── 5. Helical Quantum Particle Stream ──
      for (const p of particles) {
        p.s += p.speed * 0.016
        if (p.s > 1) p.s = 0

        const s = p.s
        const env = Math.sin(Math.PI * s)
        const helixAngle = Math.PI * 2 * 4 * s + t * 3.2 + p.phaseOffset
        const rad = (14 * dpr + p.radiusOffset * dpr) * env

        const wave = 10 * dpr * env * Math.sin(Math.PI * 2 * 3.5 * s - t * 3.4)

        const px = x1 + s * dx + nx * (wave + Math.cos(helixAngle) * rad)
        const py = y1 + s * dy + ny * (wave + Math.sin(helixAngle) * rad * 0.4) // vertical projection

        const depth = Math.sin(helixAngle)
        const currentSize = (depth > 0 ? p.size * 1.3 : p.size * 0.8) * dpr
        const alpha = depth > 0 ? 0.85 : 0.4

        ctx.fillStyle = `${p.color}${alpha.toFixed(2)})`
        ctx.beginPath()
        ctx.arc(px, py, currentSize, 0, Math.PI * 2)
        ctx.fill()
      }

      // ── 6. Interactive Mouse Proximity Beam Reaction ──
      if (mouse.active && mouseBeamFactor > 0.05) {
        // Draw subtle field line from mouse to beam
        const targetX = x1 + mouseBeamS * dx
        const targetY = y1 + mouseBeamS * dy

        const beamMouseGrad = ctx.createLinearGradient(mouse.x, mouse.y, targetX, targetY)
        beamMouseGrad.addColorStop(0, `rgba(56, 189, 248, ${(mouseBeamFactor * 0.6).toFixed(2)})`)
        beamMouseGrad.addColorStop(1, 'rgba(255, 255, 255, 0)')

        ctx.beginPath()
        ctx.moveTo(mouse.x, mouse.y)
        ctx.lineTo(targetX, targetY)
        ctx.strokeStyle = beamMouseGrad
        ctx.lineWidth = 1 * dpr
        ctx.setLineDash([4 * dpr, 4 * dpr])
        ctx.stroke()
        ctx.setLineDash([])

        // Subtle spark at cursor
        ctx.fillStyle = 'rgba(56, 189, 248, 0.7)'
        ctx.beginPath()
        ctx.arc(mouse.x, mouse.y, 3 * dpr, 0, Math.PI * 2)
        ctx.fill()
      }

      // ── 7. Minimalist Scientific HUD Telemetry (Desktop/Tablet) ──
      if (W >= 840 * dpr) {
        ctx.font = `${Math.round(10.5 * dpr)}px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace`
        ctx.textBaseline = 'middle'

        // 7A. Left Node Telemetry (Near Left Sphere)
        const lx0 = x1 - r1 * 0.35
        const ly0 = y1 - r1 * 0.85
        const lx1 = lx0 - 24 * dpr
        const ly1 = ly0 - 28 * dpr
        const lx2 = lx1 - 90 * dpr

        ctx.strokeStyle = 'rgba(56, 189, 248, 0.45)'
        ctx.lineWidth = 1 * dpr
        ctx.beginPath()
        ctx.moveTo(lx0, ly0)
        ctx.lineTo(lx1, ly1)
        ctx.lineTo(lx2, ly1)
        ctx.stroke()

        // Diamond anchor dot
        ctx.fillStyle = '#38bdf8'
        ctx.beginPath()
        ctx.arc(lx0, ly0, 2.2 * dpr, 0, Math.PI * 2)
        ctx.fill()

        ctx.fillStyle = 'rgba(224, 242, 254, 0.92)'
        ctx.textAlign = 'right'
        ctx.fillText('WĘZEŁ A · |ψ₁⟩ = α|0⟩ + β|1⟩', lx2 - 6 * dpr, ly1 - 7 * dpr)
        ctx.fillStyle = 'rgba(56, 189, 248, 0.75)'
        ctx.fillText('KOHERENCJA: 99.98% · T₂: 142µs', lx2 - 6 * dpr, ly1 + 9 * dpr)

        // 7B. Right Node Telemetry (Near Right Sphere)
        const rx0 = x2 + r2 * 0.35
        const ry0 = y2 - r2 * 0.85
        const rx1 = rx0 + 24 * dpr
        const ry1 = ry0 - 28 * dpr
        const rx2 = rx1 + 90 * dpr

        ctx.strokeStyle = 'rgba(251, 191, 36, 0.45)'
        ctx.beginPath()
        ctx.moveTo(rx0, ry0)
        ctx.lineTo(rx1, ry1)
        ctx.lineTo(rx2, ry1)
        ctx.stroke()

        ctx.fillStyle = '#fbbf24'
        ctx.beginPath()
        ctx.arc(rx0, ry0, 2.2 * dpr, 0, Math.PI * 2)
        ctx.fill()

        ctx.fillStyle = 'rgba(254, 243, 199, 0.92)'
        ctx.textAlign = 'left'
        ctx.fillText('WĘZEŁ B · |ψ₂⟩ = OPTIMUM', rx2 + 6 * dpr, ry1 - 7 * dpr)
        ctx.fillStyle = 'rgba(251, 191, 36, 0.75)'
        ctx.fillText('SOLVER: QAOA + CP-SAT', rx2 + 6 * dpr, ry1 + 9 * dpr)

        // 7C. Center EPR Channel Badge (Above the Entangled Beam)
        const cx = (x1 + x2) / 2
        const cy = (y1 + y2) / 2 - 34 * dpr

        ctx.textAlign = 'center'
        ctx.fillStyle = 'rgba(192, 132, 252, 0.85)'
        ctx.fillText('── KANAŁ EPR · STAN BELLA |Φ⁺⟩ · FIDELITY 1.000 ──', cx, cy)
      }
    }

    animId = requestAnimationFrame(render)

    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener('resize', setCanvasSize)
      if (parentEl) {
        parentEl.removeEventListener('mousemove', handleMouseMove)
        parentEl.removeEventListener('mouseleave', handleMouseLeave)
      }
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className={className}
      aria-hidden="true"
    />
  )
}
