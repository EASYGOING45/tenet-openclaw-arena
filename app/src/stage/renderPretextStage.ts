import { layoutNextLine, prepareWithSegments, setLocale } from '@chenglou/pretext'

// ── Pretext Text Particle System ─────────────────────────────────
interface TextParticle {
  x: number
  y: number
  vx: number        // 水平速度 px/frame
  vy: number        // 垂直速度 px/frame
  opacity: number   // 0.08–0.15
  text: string      // 粒子文字内容
  width: number     // Pretext 测量宽度
  height: number    // Pretext 测量高度
  fontSize: number  // 字号
  color: string     // 颜色
  alive: boolean
}

let _particlePool: TextParticle[] = []
let _particleSeg: ReturnType<typeof prepareWithSegments> | null = null
let _particleFont = ''

const PARTICLE_TEXTS = [
  'MODEL', 'ARENA', 'BENCHMARK', 'AGENT', 'RANK',
  'SCORE', 'PASS', 'FAIL', 'EVIDENCE', 'RUN',
  'CHART', 'PROMPT', 'TOOL', 'OUTPUT', 'TOKEN',
  'LLM', 'CTX', 'TASK', 'CASE', 'Verdict',
]

const PARTICLE_COLORS = [
  'rgba(91,200,255,',   // blue
  'rgba(245,200,66,',   // gold
  'rgba(232,234,240,',  // white
]

export interface PretextStage {
  headline: string
  accentLabel: string
  script: string
  words: string[]
}

type PreparedStage = ReturnType<typeof prepareWithSegments>
type Interval = { left: number; right: number }

let cachedKey = ''
let cachedPrepared: PreparedStage | null = null
let localeReady = false

function ensureLocale(): void {
  if (!localeReady) {
    setLocale('zh-CN')
    localeReady = true
  }
}

function getPrepared(script: string, font: string): PreparedStage {
  ensureLocale()

  const nextKey = `${font}::${script}`
  if (cachedPrepared && cachedKey === nextKey) {
    return cachedPrepared
  }

  cachedKey = nextKey
  cachedPrepared = prepareWithSegments(script, font, { wordBreak: 'keep-all' })
  return cachedPrepared
}

function resizeCanvas(canvas: HTMLCanvasElement, width: number, height: number): void {
  const ratio = window.devicePixelRatio || 1
  const nextWidth = Math.max(1, Math.round(width * ratio))
  const nextHeight = Math.max(1, Math.round(height * ratio))

  if (canvas.width !== nextWidth || canvas.height !== nextHeight) {
    canvas.width = nextWidth
    canvas.height = nextHeight
  }

  const context = canvas.getContext('2d')
  if (context) {
    context.setTransform(ratio, 0, 0, ratio, 0, 0)
  }
}

function carveLineSlots(base: Interval, blocked: Interval[]): Interval[] {
  let slots = [base]

  for (let index = 0; index < blocked.length; index += 1) {
    const interval = blocked[index]!
    const next: Interval[] = []

    for (let slotIndex = 0; slotIndex < slots.length; slotIndex += 1) {
      const slot = slots[slotIndex]!

      if (interval.right <= slot.left || interval.left >= slot.right) {
        next.push(slot)
        continue
      }

      if (interval.left > slot.left) {
        next.push({ left: slot.left, right: interval.left })
      }

      if (interval.right < slot.right) {
        next.push({ left: interval.right, right: slot.right })
      }
    }

    slots = next
  }

  return slots.filter((slot) => slot.right - slot.left >= 88)
}

function getRectIntervalForBand(
  x: number,
  width: number,
  top: number,
  bottom: number,
  bandTop: number,
  bandBottom: number,
  horizontalPadding: number,
): Interval | null {
  if (bandBottom <= top || bandTop >= bottom) {
    return null
  }

  return {
    left: x - horizontalPadding,
    right: x + width + horizontalPadding,
  }
}

function getCircleIntervalForBand(
  cx: number,
  cy: number,
  radiusX: number,
  radiusY: number,
  bandTop: number,
  bandBottom: number,
  horizontalPadding: number,
): Interval | null {
  const bandCenter = (bandTop + bandBottom) / 2
  const normalizedY = (bandCenter - cy) / radiusY
  if (Math.abs(normalizedY) >= 1) {
    return null
  }

  const xReach = radiusX * Math.sqrt(1 - normalizedY ** 2)
  return {
    left: cx - xReach - horizontalPadding,
    right: cx + xReach + horizontalPadding,
  }
}

function fillBeam(
  context: CanvasRenderingContext2D,
  x: number,
  top: number,
  bottom: number,
  width: number,
): void {
  const beamGradient = context.createLinearGradient(x, top, x, bottom)
  beamGradient.addColorStop(0, 'rgba(240, 172, 58, 0)')
  beamGradient.addColorStop(0.1, 'rgba(240, 172, 58, 0.86)')
  beamGradient.addColorStop(0.46, 'rgba(240, 172, 58, 0.92)')
  beamGradient.addColorStop(0.62, 'rgba(29, 182, 255, 0.92)')
  beamGradient.addColorStop(0.9, 'rgba(240, 172, 58, 0.82)')
  beamGradient.addColorStop(1, 'rgba(240, 172, 58, 0)')
  context.fillStyle = beamGradient
  context.fillRect(x - width / 2, top, width, bottom - top)
}

export function renderPretextStage(
  canvas: HTMLCanvasElement,
  stage: PretextStage,
  time = 0,
): void {
  const bounds = canvas.getBoundingClientRect()
  const width = bounds.width
  const height = bounds.height

  if (width < 8 || height < 8) {
    return
  }

  resizeCanvas(canvas, width, height)

  const context = canvas.getContext('2d')
  if (!context) {
    return
  }

  const drift = time * 0.0004
  const scriptFont = '500 15px "IBM Plex Sans Condensed", "Noto Sans SC", sans-serif'
  const prepared = getPrepared(stage.script, scriptFont)
  const beamX = width * 0.72 + Math.sin(drift) * 6
  const beamTop = height * 0.12
  const beamBottom = height * 0.9
  const beamWidth = Math.max(8, width * 0.014)
  const orbCenterY = height * 0.36

  context.clearRect(0, 0, width, height)

  const backdrop = context.createLinearGradient(0, 0, width, height)
  backdrop.addColorStop(0, '#08111c')
  backdrop.addColorStop(0.55, '#05070d')
  backdrop.addColorStop(1, '#020309')
  context.fillStyle = backdrop
  context.fillRect(0, 0, width, height)

  const skyGlow = context.createRadialGradient(
    width * 0.78,
    height * 0.22,
    10,
    width * 0.78,
    height * 0.22,
    width * 0.36,
  )
  skyGlow.addColorStop(0, 'rgba(29, 182, 255, 0.26)')
  skyGlow.addColorStop(0.46, 'rgba(29, 182, 255, 0.1)')
  skyGlow.addColorStop(1, 'rgba(29, 182, 255, 0)')
  context.fillStyle = skyGlow
  context.fillRect(0, 0, width, height)

  context.save()
  context.translate(width * 0.92, height * 0.1)
  context.rotate(-Math.PI / 2)
  context.font = '700 76px "Bebas Neue", "IBM Plex Sans Condensed", sans-serif'
  context.fillStyle = 'rgba(255, 255, 255, 0.05)'
  context.fillText(stage.headline.toUpperCase(), 0, 0)
  context.restore()

  context.strokeStyle = 'rgba(29, 182, 255, 0.12)'
  context.lineWidth = 1
  for (let index = 0; index < 12; index += 1) {
    const y = height * 0.18 + index * 32 + Math.sin(drift * 2 + index) * 1.4
    context.beginPath()
    context.moveTo(width * 0.46, y)
    context.lineTo(width * 0.95, y)
    context.stroke()
  }

  fillBeam(context, beamX, beamTop, beamBottom, beamWidth)

  context.beginPath()
  context.ellipse(beamX, orbCenterY, width * 0.03, height * 0.11, 0, 0, Math.PI * 2)
  context.fillStyle = 'rgba(29, 182, 255, 0.14)'
  context.fill()

  context.beginPath()
  context.ellipse(beamX, orbCenterY, width * 0.011, height * 0.055, 0, 0, Math.PI * 2)
  context.fillStyle = 'rgba(29, 182, 255, 0.92)'
  context.fill()

  context.font = scriptFont
  context.textBaseline = 'top'

  let cursor = { segmentIndex: 0, graphemeIndex: 0 }
  const lineHeight = 22
  const maxBands = Math.max(8, Math.floor((height * 0.5) / lineHeight))

  for (let bandIndex = 0; bandIndex < maxBands; bandIndex += 1) {
    const bandTop = height * 0.18 + bandIndex * lineHeight
    const bandBottom = bandTop + lineHeight
    const slots = carveLineSlots(
      { left: width * 0.46, right: width * 0.95 },
      [
        getRectIntervalForBand(
          beamX - beamWidth / 2,
          beamWidth,
          beamTop,
          beamBottom,
          bandTop,
          bandBottom,
          22,
        ),
        getCircleIntervalForBand(
          beamX,
          orbCenterY,
          width * 0.08,
          height * 0.13,
          bandTop,
          bandBottom,
          14,
        ),
      ].filter((slot): slot is Interval => slot !== null),
    )

    if (slots.length === 0) continue

    for (let slotIndex = 0; slotIndex < slots.length; slotIndex += 1) {
      const slot = slots[slotIndex]!
      const line = layoutNextLine(prepared, cursor, slot.right - slot.left)

      if (!line) {
        break
      }

      cursor = line.end
      context.fillStyle =
        slotIndex === 0 ? 'rgba(245, 212, 160, 0.58)' : 'rgba(245, 212, 160, 0.42)'
      context.fillText(
        line.text,
        slot.left + Math.sin(drift + bandIndex * 0.2) * 1.5,
        bandTop,
      )
    }
  }

  stage.words.slice(0, 3).forEach((word, index) => {
    context.font = `700 ${index === 0 ? 54 : 34}px "Bebas Neue", "IBM Plex Sans Condensed", sans-serif`
    context.fillStyle =
      index % 2 === 0 ? 'rgba(29, 182, 255, 0.9)' : 'rgba(240, 172, 58, 0.92)'
    context.fillText(
      word.toUpperCase(),
      width * 0.56,
      height * (0.28 + index * 0.19) + Math.sin(drift * 1.8 + index) * 4,
    )
  })

  context.font = '700 24px "Bebas Neue", "IBM Plex Sans Condensed", sans-serif'
  context.fillStyle = 'rgba(255, 255, 255, 0.56)'
  context.fillText(stage.accentLabel.toUpperCase(), width * 0.76, height * 0.86)

  // 确保粒子池已初始化
  if (_particlePool.length === 0) {
    initParticlePool(width, height, scriptFont)
  }

  // ── 粒子背景层（最后渲染，透明度极淡）────────────────────────────
  updateAndDrawParticles(context, width, height, time)
}

// 初始化粒子池（窗口尺寸变化时调用）
export function initParticlePool(width: number, height: number, font: string): void {
  _particleFont = font
  const count = Math.floor((width * height) / 12000)
  _particlePool = Array.from({ length: count }, () => spawnParticle(width, height))
  _particleSeg = prepareWithSegments(PARTICLE_TEXTS.join(' '), font, { wordBreak: 'keep-all' })
}

function spawnParticle(width: number, height: number): TextParticle {
  const fontSize = 9 + Math.random() * 13  // 9–22px
  const font = `${Math.random() > 0.5 ? '600' : '400'} ${fontSize}px "IBM Plex Sans Condensed", sans-serif`
  const colorBase = PARTICLE_COLORS[Math.floor(Math.random() * PARTICLE_COLORS.length)]!
  const opacity = 0.08 + Math.random() * 0.07  // 0.08–0.15
  const color = colorBase + opacity + ')'

  // 用 Pretext 测量粒子文字
  const seg = _particleSeg || prepareWithSegments(PARTICLE_TEXTS[0]!, font, { wordBreak: 'keep-all' })
  const cursor = { segmentIndex: 0, graphemeIndex: 0 }
  const line = layoutNextLine(seg, cursor, 200)
  const text = line?.text || PARTICLE_TEXTS[Math.floor(Math.random() * PARTICLE_TEXTS.length)]!

  // 重新测量实际文字
  const measureSeg = prepareWithSegments(text, font, { wordBreak: 'keep-all' })
  const mLine = layoutNextLine(measureSeg, { segmentIndex: 0, graphemeIndex: 0 }, 300)
  const measuredWidth = mLine ? mLine.text.length * fontSize * 0.55 : text.length * fontSize * 0.55

  return {
    x: Math.random() * width,
    y: Math.random() * height,
    vx: (Math.random() - 0.5) * 0.35,  // 0.2–0.5 px/frame，慢速漂移
    vy: (Math.random() - 0.5) * 0.25,
    opacity,
    text,
    width: measuredWidth,
    height: fontSize * 1.2,
    fontSize,
    color,
    alive: true,
  }
}

function updateAndDrawParticles(
  context: CanvasRenderingContext2D,
  width: number,
  height: number,
  time: number,
): void {
  if (_particlePool.length === 0) return

  context.save()
  context.textBaseline = 'top'

  const t = time * 0.0003

  for (let i = 0; i < _particlePool.length; i++) {
    const p = _particlePool[i]!

    // 更新位置
    p.x += p.vx + Math.sin(t + i * 0.7) * 0.15
    p.y += p.vy + Math.cos(t * 0.8 + i * 0.5) * 0.12

    // 边缘重生
    if (p.x < -p.width || p.x > width + p.width || p.y < -p.height || p.y > height + p.height) {
      const fresh = spawnParticle(width, height)
      p.x = fresh.x
      p.y = fresh.y
      p.vx = fresh.vx
      p.vy = fresh.vy
      p.text = fresh.text
      p.width = fresh.width
      p.height = fresh.height
      p.fontSize = fresh.fontSize
      p.color = fresh.color
      p.opacity = fresh.opacity
    }

    // 绘制（透明度极淡，只做背景氛围）
    const fontStr = `${p.fontSize}px "IBM Plex Sans Condensed", "Noto Sans SC", sans-serif`
    context.font = fontStr
    context.fillStyle = p.color
    context.fillText(p.text, p.x, p.y)
  }

  context.restore()
}
