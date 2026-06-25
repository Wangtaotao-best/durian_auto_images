# Fixed White Background Generator UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hide editable English scene prompt, always send a fixed white-background close-up prompt, and polish the generator UI so users only choose variety and click a Chinese generate button.

**Architecture:** Keep the existing React `Generator` component and backend API unchanged. Replace prompt state / scene template buttons / textarea with an internal `FIXED_PROMPT` constant and a static fixed-scene card, then submit `FIXED_PROMPT` in `handleGenerate`. Preserve advanced options and existing status/result/error panels to avoid introducing full-screen overlays or browser-specific rendering risks.

**Tech Stack:** React 19, TypeScript, Vite 7, Tailwind CSS, existing FastAPI `/api/generate` request shape.

---

## File Structure

- Modify: `frontend/src/sections/Generator.tsx`
  - Owns the online generation UI.
  - Replace prompt editing UI with fixed white-background scene card.
  - Keep API call shape unchanged by sending fixed prompt internally.
  - Change button text from `Generate` to `开始生成`.
- Modify: `PROGRESS.md`
  - Record the fixed prompt UI change, validation result, and remaining server deployment state.
- No backend files are modified.
- No model files or deployment bundles are modified.

## Current Starting Point

`frontend/src/sections/Generator.tsx` currently has already been partially edited in the working tree:

```ts
const SCENE_TEMPLATES = [
  {
    cn: '白底特写',
    cn_full: '白色背景榴莲特写,工作室灯光,清晰细节,真实摄影',
    en: 'close up shot of durian on a white background, studio lighting, sharp details, photorealistic',
  },
]
```

and still contains:

```ts
const [prompt, setPrompt] = useState(
  'close up shot of durian on a white background, studio lighting, sharp details, photorealistic',
)
```

This plan finishes the approved design by removing editable prompt UI entirely.

---

### Task 1: Replace Editable Prompt With Fixed Scene Card

**Files:**
- Modify: `frontend/src/sections/Generator.tsx:16-288`

- [ ] **Step 1: Replace scene template array with fixed constants**

In `frontend/src/sections/Generator.tsx`, replace the current comment and `SCENE_TEMPLATES` block at the top with:

```ts
const FIXED_PROMPT =
  'close up shot of durian on a white background, studio lighting, sharp details, photorealistic'

const FIXED_SCENE = {
  title: '白底特写',
  subtitle: '白色背景 · 工作室灯光 · 清晰细节',
  description: '已根据训练集固定场景,提升生成稳定性',
}
```

Expected result:
- No `SCENE_TEMPLATES` identifier remains in the file.
- `FIXED_PROMPT` is the only English prompt source.

- [ ] **Step 2: Remove prompt state**

Delete this state block from `Generator`:

```ts
const [prompt, setPrompt] = useState(
  'close up shot of durian on a white background, studio lighting, sharp details, photorealistic',
)
```

Keep the existing `negative`, `steps`, `cfg`, `num`, and `advancedOpen` states unchanged:

```ts
const [negative, setNegative] = useState('blurry, low quality, distorted, deformed')
const [steps, setSteps] = useState(6)
const [cfg, setCfg] = useState(1.5)
const [num, setNum] = useState(2)
const [advancedOpen, setAdvancedOpen] = useState(false)
```

Expected result:
- `prompt` and `setPrompt` are no longer defined.

- [ ] **Step 3: Update canGenerate logic**

Replace:

```ts
const canGenerate =
  !isRunning && Boolean(selectedVariety) && prompt.trim().length > 0
```

with:

```ts
const canGenerate = !isRunning && Boolean(selectedVariety)
```

Expected result:
- Generation availability depends only on selected variety and running state.

- [ ] **Step 4: Use fixed prompt in handleGenerate**

Replace this field inside `handleGenerate`:

```ts
prompt: prompt.trim(),
```

with:

```ts
prompt: FIXED_PROMPT,
```

The full `handleGenerate` function should become:

```ts
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
```

Expected result:
- The backend API receives the fixed English prompt.
- The prompt is not user-editable.

- [ ] **Step 5: Replace prompt UI block with fixed scene card**

In `frontend/src/sections/Generator.tsx`, replace the entire block from this comment:

```tsx
{/* Prompt 输入 */}
```

through the end of the prompt textarea / Chinese reference area, but keep the advanced options button and advanced options content.

Replace the prompt area opening with this fixed scene UI:

```tsx
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
```

Then keep the existing advanced options button immediately after the fixed scene card:

```tsx
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
```

Expected result:
- There is no `<textarea>` in the prompt section.
- There is no `onChange={(e) => setPrompt(e.target.value)}`.
- The fixed scene card is visible and uses existing Tailwind classes only.

- [ ] **Step 6: Change generate button text to Chinese**

Replace the idle button label:

```tsx
Generate
```

with:

```tsx
开始生成
```

The running label remains:

```tsx
生成中...
```

Expected result:
- Button shows `开始生成` when idle.
- Button shows `生成中...` while generating.

- [ ] **Step 7: Search for removed prompt identifiers**

Run:

```powershell
Set-Location "D:\谷歌下载\Kimi_Agent_榴莲图像生成代码"
rg "SCENE_TEMPLATES|setPrompt|prompt\.trim\(\)|<textarea" frontend/src/sections/Generator.tsx
```

Expected:

```text
(no output)
```

If output remains, remove the leftover code before continuing.

- [ ] **Step 8: Build frontend**

Run:

```powershell
Set-Location "D:\谷歌下载\Kimi_Agent_榴莲图像生成代码\frontend"
npm run build
```

Expected:

```text
✓ built in ...
```

Notes:
- Browserslist stale data warning is acceptable.
- Do not treat existing `npm run lint` failures as this task's blocker unless the new changes add errors in `Generator.tsx`.

- [ ] **Step 9: Manual browser check**

Run the frontend dev server:

```powershell
Set-Location "D:\谷歌下载\Kimi_Agent_榴莲图像生成代码\frontend"
npm run dev
```

Open the printed local URL, typically:

```text
http://localhost:5173
```

Verify:

1. The page shows `生成场景`.
2. It shows `白底特写`.
3. It shows `固定推荐`.
4. It shows `白色背景 · 工作室灯光 · 清晰细节`.
5. It does not show the English prompt.
6. It does not show a prompt textarea.
7. The button says `开始生成`.
8. When clicked, it says `生成中...`.
9. The page does not display a full-screen black overlay during generation.

- [ ] **Step 10: Commit implementation**

Run:

```powershell
Set-Location "D:\谷歌下载\Kimi_Agent_榴莲图像生成代码"
git status --short
git add frontend/src/sections/Generator.tsx
git commit -m @'
feat(ui): 固定白底特写生成场景

- 隐藏可编辑英文 prompt,内部使用固定白底特写 prompt
- 用固定场景卡片替换描述场景输入框
- 将 Generate 按钮改为中文开始生成

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

Expected:

```text
[master <hash>] feat(ui): 固定白底特写生成场景
```

Do not add `.superpowers/` to the commit.

---

### Task 2: Update Progress Handoff

**Files:**
- Modify: `PROGRESS.md`

- [ ] **Step 1: Update current progress**

In `PROGRESS.md`, under `## 已完成`, add this line after the existing footer update entry:

```markdown
- [x] **2026-06-25** 生成器场景固定为白底特写:隐藏英文 prompt,按钮改为「开始生成」,减少与训练集不一致导致的不稳定
```

- [ ] **Step 2: Update todo list**

In `PROGRESS.md`, update the server frontend deployment todo so it mentions the new fixed scene UI. Replace:

```markdown
- [ ] 如果生成成功,重新构建/上传新版 `frontend/dist/`,让 footer 显示「开发人: 寒鸣」且不显示 GitHub
```

with:

```markdown
- [ ] 如果生成成功,重新构建/上传新版 `frontend/dist/`,让 footer 显示「开发人: 寒鸣」且不显示 GitHub,生成器只显示固定「白底特写」场景
```

- [ ] **Step 3: Build frontend again after handoff update**

Run:

```powershell
Set-Location "D:\谷歌下载\Kimi_Agent_榴莲图像生成代码\frontend"
npm run build
```

Expected:

```text
✓ built in ...
```

- [ ] **Step 4: Commit handoff update**

Run:

```powershell
Set-Location "D:\谷歌下载\Kimi_Agent_榴莲图像生成代码"
git add PROGRESS.md
git commit -m @'
docs: 更新固定白底特写 UI 交接记录

- 记录生成器固定白底特写场景
- 更新服务器前端部署待办

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

Expected:

```text
[master <hash>] docs: 更新固定白底特写 UI 交接记录
```

---

## Self-Review

### Spec Coverage

- Hide English prompt: Task 1 Steps 1, 2, 5, 7.
- Fixed white-background prompt sent to backend: Task 1 Step 4.
- Chinese generate button: Task 1 Step 6.
- Keep advanced options: Task 1 Step 5 explicitly preserves the existing advanced options block.
- Black-screen UI risk: Task 1 Step 5 avoids full-screen overlays; Task 1 Step 9 checks no full-screen black overlay during generation.
- Browser compatibility: Task 1 Step 5 uses existing Tailwind utility classes only; Task 1 Step 9 includes manual browser check.
- No backend API change: Task 1 Step 4 keeps the same `start` payload shape.
- Handoff update: Task 2.

### Placeholder Scan

No placeholders, TBDs, or undefined implementation references remain.

### Type Consistency

- `FIXED_PROMPT` is a string constant used by `handleGenerate`.
- `FIXED_SCENE` has `title`, `subtitle`, and `description`, and the JSX uses those exact names.
- Existing `negative`, `steps`, `cfg`, `num`, and `advancedOpen` state names remain unchanged.
