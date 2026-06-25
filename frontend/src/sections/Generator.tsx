import { useEffect, useState, useRef } from 'react'
import {
  Sparkles,
  Loader2,
  Download,
  ChevronDown,
  AlertCircle,
  ImageOff,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { api } from '@/api/client'
import type { Variety } from '@/api/types'
import { useGeneration } from '@/hooks/useGeneration'

const FIXED_PROMPT =
  'close up shot of durian on a white background, studio lighting, sharp details, photorealistic'

const FIXED_SCENE = {
  title: '白底特写',
  subtitle: '白色背景 · 工作室灯光 · 清晰细节',
  description: '已根据训练集固定场景,提升生成稳定性',
}

/**
 * 在线生成器 — 嵌在 Hero 之后,作为"立即使用"区。
 * 沿用项目深色 slate 主题,与现有展示页风格协调。
 */
const Generator = () => {
  const [varieties, setVarieties] = useState<Variety[]>([])
  const [loadingVarieties, setLoadingVarieties] = useState(true)
  const [varietiesError, setVarietiesError] = useState<string | null>(null)
  const [selectedVariety, setSelectedVariety] = useState<string>('')

  const [negative, setNegative] = useState('blurry, low quality, distorted, deformed')
  const [steps, setSteps] = useState(6)
  const [cfg, setCfg] = useState(1.5)
  const [num, setNum] = useState(2)
  const [advancedOpen, setAdvancedOpen] = useState(false)

  const { status, isRunning, error, start } = useGeneration()
  const resultRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api
      .listVarieties()
      .then((vs) => {
        setVarieties(vs)
        if (vs.length > 0) setSelectedVariety(vs[0].id)
      })
      .catch((e) => setVarietiesError(e?.message || '加载品种列表失败'))
      .finally(() => setLoadingVarieties(false))
  }, [])

  useEffect(() => {
    if (status?.status === 'done' && resultRef.current) {
      resultRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [status?.status])

  const canGenerate = !isRunning && Boolean(selectedVariety)

  const handleGenerate = () => {
    if (!canGenerate) return
    start({
      variety: selectedVariety,
      prompt: FIXED_PROMPT,
      negative_prompt: negative.trim() || undefined,
      num_images: num,
      steps,
      cfg_scale: cfg,
    })
  }

  return (
    <section
      id="generator"
      className="relative scroll-mt-8 py-20 md:py-24 px-4 overflow-hidden"
    >
      {/* 背景层(融入整体深色主题,加点暖色透明斑) */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-900 via-slate-950 to-slate-900" />
      <div className="absolute top-1/4 left-1/3 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-yellow-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="relative max-w-5xl mx-auto">
        {/* 标题 */}
        <div className="text-center mb-12">
          <Badge
            variant="outline"
            className="mb-4 border-amber-500/40 text-amber-300 bg-amber-500/10"
          >
            <Sparkles className="w-3.5 h-3.5 mr-1.5" />
            在线使用
          </Badge>
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="bg-gradient-to-r from-amber-300 via-yellow-400 to-amber-500 bg-clip-text text-transparent">
              立即生成
            </span>
            <span className="text-white">你的榴莲图像</span>
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            选品种 · 写一段描述 · 等待几十秒 — 完全在服务器 CPU 上跑,基于 OpenVINO + LCM 加速
          </p>
        </div>

        {/* 品种选择 */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-slate-300 mb-3">
            选择品种
          </label>
          {varietiesError && (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm flex items-start gap-3">
              <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <div>
                <div className="font-medium">无法加载品种列表</div>
                <div className="text-xs text-red-400/80 mt-1">{varietiesError}</div>
                <div className="text-xs text-slate-400 mt-2">
                  服务器可能未启动 — 仍可浏览下方页面查看项目介绍。
                </div>
              </div>
            </div>
          )}
          {!varietiesError && loadingVarieties && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[0, 1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-24 rounded-2xl bg-slate-800/40 animate-pulse"
                />
              ))}
            </div>
          )}
          {!varietiesError && !loadingVarieties && varieties.length === 0 && (
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-sm">
              服务器尚未部署任何模型 — 详见{' '}
              <code className="bg-black/30 px-1.5 py-0.5 rounded">
                docs/deployment.md
              </code>
            </div>
          )}
          {!varietiesError && !loadingVarieties && varieties.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {varieties.map((v) => {
                const isActive = selectedVariety === v.id
                return (
                  <button
                    key={v.id}
                    onClick={() => setSelectedVariety(v.id)}
                    className={[
                      'group relative p-4 rounded-2xl text-left transition-all duration-200',
                      'backdrop-blur-md border',
                      isActive
                        ? 'bg-amber-500/15 border-amber-400/60 shadow-lg shadow-amber-500/20 scale-[1.02]'
                        : 'bg-slate-800/40 border-slate-700/50 hover:bg-slate-800/60 hover:border-slate-600 hover:scale-[1.01]',
                    ].join(' ')}
                  >
                    <div
                      className={[
                        'text-xl font-bold mb-1',
                        isActive ? 'text-amber-200' : 'text-white',
                      ].join(' ')}
                    >
                      {v.name_cn}
                    </div>
                    <div className="text-xs text-slate-400">{v.name_en}</div>
                  </button>
                )
              })}
            </div>
          )}
        </div>

        {/* 固定生成场景 */}
        <div className="rounded-2xl p-6 backdrop-blur-md bg-slate-800/40 border border-slate-700/50 mb-6">
          <label className="block text-sm font-medium text-slate-300 mb-3">
            生成场景
          </label>

          <div className="rounded-2xl border border-amber-400/40 bg-gradient-to-br from-amber-500/15 via-yellow-500/10 to-slate-900/40 p-5 shadow-lg shadow-amber-500/10">
            <div className="flex items-start gap-4">
              <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-300 to-yellow-500 text-slate-950 shadow-lg shadow-amber-500/30">
                <Sparkles className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-lg font-bold text-amber-100">
                    {FIXED_SCENE.title}
                  </h3>
                  <span className="rounded-full border border-amber-300/40 bg-amber-300/10 px-2.5 py-0.5 text-[11px] font-medium text-amber-200">
                    固定推荐
                  </span>
                </div>
                <p className="mt-1 text-sm text-slate-300">
                  {FIXED_SCENE.subtitle}
                </p>
                <p className="mt-2 text-xs leading-relaxed text-slate-500">
                  {FIXED_SCENE.description}
                </p>
              </div>
            </div>
          </div>

          {/* 高级选项 */}
          <button
            onClick={() => setAdvancedOpen((v) => !v)}
            className="mt-4 inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-200 transition-colors"
          >
            <ChevronDown
              className={[
                'w-4 h-4 transition-transform',
                advancedOpen ? 'rotate-180' : '',
              ].join(' ')}
            />
            高级选项
          </button>
          {advancedOpen && (
            <div className="mt-4 space-y-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">
                  Negative prompt
                </label>
                <input
                  type="text"
                  value={negative}
                  onChange={(e) => setNegative(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900/60 border border-slate-700/60 text-sm text-slate-100 focus:outline-none focus:border-amber-400/60"
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <SliderField
                  label={`步数 (${steps})`}
                  hint="LCM 4-12"
                  min={4}
                  max={12}
                  value={steps}
                  onChange={setSteps}
                />
                <SliderField
                  label={`CFG (${cfg.toFixed(1)})`}
                  hint="LCM 1.0-2.5"
                  min={0.5}
                  max={5}
                  step={0.1}
                  value={cfg}
                  onChange={setCfg}
                />
                <SliderField
                  label={`数量 (${num})`}
                  hint="1-4"
                  min={1}
                  max={4}
                  value={num}
                  onChange={setNum}
                />
              </div>
            </div>
          )}
        </div>

        {/* Generate 按钮 */}
        <div className="flex justify-center mb-8">
          <Button
            onClick={handleGenerate}
            disabled={!canGenerate}
            size="lg"
            className="bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-400 hover:to-yellow-400 text-slate-900 font-bold px-10 py-6 text-base shadow-lg shadow-amber-500/30 hover:shadow-amber-500/40 hover:scale-105 transition-all disabled:opacity-50 disabled:hover:scale-100"
          >
            {isRunning ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                生成中...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5 mr-2" />
                开始生成
              </>
            )}
          </Button>
        </div>

        {/* 进度面板 */}
        {status && status.status !== 'done' && status.status !== 'failed' && (
          <ProgressPanel status={status} />
        )}

        {/* 错误 */}
        {error && (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm flex items-start gap-3 mb-6">
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <div>
              <div className="font-medium">生成失败</div>
              <div className="text-xs text-red-400/80 mt-1">{error}</div>
            </div>
          </div>
        )}

        {/* 结果 */}
        {status?.status === 'done' && status.image_urls && status.image_urls.length > 0 && (
          <div ref={resultRef}>
            <ResultGrid imageUrls={status.image_urls} />
          </div>
        )}
        {status?.status === 'done' &&
          (!status.image_urls || status.image_urls.length === 0) && (
            <div className="p-6 rounded-xl bg-slate-800/40 border border-slate-700/50 text-slate-400 text-center flex flex-col items-center gap-2">
              <ImageOff className="w-8 h-8 text-slate-500" />
              <div>任务完成但未返回图像 — 请检查服务器日志</div>
            </div>
          )}
      </div>
    </section>
  )
}

const SliderField = ({
  label,
  hint,
  min,
  max,
  step = 1,
  value,
  onChange,
}: {
  label: string
  hint?: string
  min: number
  max: number
  step?: number
  value: number
  onChange: (v: number) => void
}) => (
  <div>
    <label className="flex items-baseline justify-between text-xs text-slate-400 mb-1.5">
      <span>{label}</span>
      {hint && <span className="text-[10px] text-slate-500">{hint}</span>}
    </label>
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={(e) => onChange(Number(e.target.value))}
      className="w-full accent-amber-500"
    />
  </div>
)

const ProgressPanel = ({ status }: { status: import('@/api/types').TaskStatus }) => {
  if (status.status === 'queued') {
    return (
      <div className="p-5 rounded-2xl bg-slate-800/40 backdrop-blur-md border border-slate-700/50 mb-6">
        <div className="flex items-center gap-3 mb-2">
          <Loader2 className="w-4 h-4 animate-spin text-amber-400" />
          <span className="font-medium text-white">排队中</span>
        </div>
        <div className="text-sm text-slate-400">
          队列位置: 第 {status.queue_position} 位 · 预计等待{' '}
          {status.estimated_seconds}s
        </div>
      </div>
    )
  }
  if (status.status === 'running') {
    const pct = Math.round((status.progress || 0) * 100)
    return (
      <div className="p-5 rounded-2xl bg-slate-800/40 backdrop-blur-md border border-slate-700/50 mb-6">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <Loader2 className="w-4 h-4 animate-spin text-amber-400" />
            <span className="font-medium text-white">生成中</span>
          </div>
          {status.total_steps !== undefined && status.current_step !== undefined && (
            <span className="text-xs text-slate-400">
              {status.current_step}/{status.total_steps} 步
            </span>
          )}
        </div>
        <div className="h-2 bg-slate-900/60 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-amber-500 to-yellow-400 transition-all duration-300"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    )
  }
  return null
}

const ResultGrid = ({ imageUrls }: { imageUrls: string[] }) => {
  if (!imageUrls.length) return null
  const cols =
    imageUrls.length === 1
      ? 'grid-cols-1 max-w-md mx-auto'
      : imageUrls.length === 2
        ? 'grid-cols-1 sm:grid-cols-2'
        : 'grid-cols-2 lg:grid-cols-4'
  return (
    <div className={`grid ${cols} gap-4`}>
      {imageUrls.map((url, i) => (
        <div
          key={i}
          className="group relative rounded-2xl overflow-hidden bg-slate-800/40 backdrop-blur-md border border-slate-700/50 shadow-lg"
        >
          <img
            src={url}
            alt={`Generated ${i}`}
            className="w-full aspect-square object-cover"
          />
          <a
            href={url}
            download={`durian_${Date.now()}_${i}.png`}
            className="absolute bottom-3 right-3 p-2.5 rounded-full bg-slate-900/90 text-amber-300 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-slate-900 hover:scale-110"
            aria-label="下载"
          >
            <Download className="w-4 h-4" />
          </a>
        </div>
      ))}
    </div>
  )
}

export default Generator
