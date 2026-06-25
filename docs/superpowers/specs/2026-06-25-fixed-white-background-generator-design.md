# 固定白底特写生成器 UI 设计

## 背景

当前榴莲 AIGC 前端的 `Generator` 区域允许用户编辑英文描述场景。实际训练集主要是白底特写图,其他场景如桌面、市场、手持、厨房台面等与训练分布不一致,会增加生成结果不稳定、构图错误、画面黑屏或异常的概率。

本次设计目标是:隐藏英文 prompt,固定生成场景为白底特写,让普通用户只选择品种并点击中文生成按钮,减少误操作和不稳定因素,同时保持页面美观。

## 目标

1. 用户不再看到或编辑英文 prompt。
2. 生成请求内部始终使用固定白底特写英文 prompt。
3. `Generate` 按钮改成中文,降低使用门槛。
4. 保留高级参数区域,方便必要时调整 negative prompt、步数、CFG、数量。
5. 检查并规避生成过程中出现黑屏的前端展示风险。
6. 保持不同浏览器下的兼容性,避免依赖过新的 CSS 或不稳定渲染行为。

## 非目标

1. 不改后端 API 结构。
2. 不改模型权重、OpenVINO 导出流程或推理参数语义。
3. 不重新开放自由 prompt 输入。
4. 不增加新的场景模板。

## 设计方案

采用方案 A:隐藏英文 prompt,显示固定白底特写场景卡片。

### UI 结构

在品种选择下方保留一个「生成场景」卡片区域,替换原来的模板按钮和 textarea。卡片展示中文语义,不展示英文 prompt。

建议显示内容:

```text
生成场景

白底特写
白色背景 · 工作室灯光 · 清晰细节
已根据训练集固定场景,提升生成稳定性
```

视觉风格:

- 外层使用现有 `rounded-2xl`, `bg-slate-800/40`, `border-slate-700/50`, `backdrop-blur-md`。
- 场景卡片使用 amber/yellow 高亮边框和柔和背景。
- 可以使用 `Sparkles` 图标或简洁圆形标识强化「固定推荐场景」。
- 不显示英文 prompt、不显示可编辑 textarea、不显示多个场景按钮。

### 交互行为

用户流程变为:

1. 选择品种。
2. 查看固定场景卡片。
3. 可选:展开高级选项调整参数。
4. 点击中文按钮「开始生成」。

按钮文案:

- 空闲状态:`开始生成`
- 运行状态:`生成中...`

`canGenerate` 逻辑改为只依赖品种和运行状态:

```ts
const canGenerate = !isRunning && Boolean(selectedVariety)
```

### Prompt 数据流

前端新增或保留固定常量:

```ts
const FIXED_PROMPT =
  'close up shot of durian on a white background, studio lighting, sharp details, photorealistic'
```

生成请求仍然向后端传 `prompt`,但来源改为 `FIXED_PROMPT`:

```ts
start({
  variety: selectedVariety,
  prompt: FIXED_PROMPT,
  negative_prompt: negative.trim() || undefined,
  num_images: num,
  steps,
  cfg_scale: cfg,
})
```

这样后端无需改动,兼容当前 `/api/generate` 请求结构。

## 黑屏问题检查设计

用户测试时提到生成过程中出现黑屏。本次前端修改时同步检查以下风险点:

1. 生成中状态不能覆盖整个页面为纯黑层。
2. 进度面板、错误面板、结果区域必须保持在正常文档流中,不使用全屏 fixed 黑色遮罩。
3. 图片结果渲染时保留现有 `ImageOff` 或错误占位,避免图片加载失败时出现空白黑块。
4. 对生成按钮禁用状态只降低透明度,不改变页面背景。
5. 避免把 prompt 区域隐藏逻辑写成条件渲染导致布局高度瞬间塌陷;使用稳定的固定场景卡片替代原区域。

如果黑屏来自后端生成出的图片本身,前端只能显示实际结果;需要通过日志和生成图判断是 UI 黑屏还是模型输出黑图。实现后应至少验证一次生成流程中的:

- 加载中页面状态
- 失败错误状态
- 成功图片展示状态

## 浏览器兼容性设计

保持当前 React/Vite 架构,不引入新依赖。样式仍使用现有 Tailwind 类。为减少浏览器兼容风险:

1. 不新增 CSS Houdini、复杂 mask、容器查询等高风险特性。
2. 不使用浏览器实验 API。
3. 不新增全屏滤镜遮罩。
4. 卡片样式使用已有项目中广泛使用的 `rounded`, `border`, `bg`, `backdrop-blur`, `gradient` 类。
5. 对 `backdrop-blur` 不做功能依赖,即使浏览器弱化毛玻璃效果,信息仍可读。

建议手动检查浏览器:

- Chrome / Edge:主要目标浏览器。
- 手机浏览器:确认按钮、品种卡片、固定场景卡片不会横向溢出。

## 涉及文件

预计修改:

- `frontend/src/sections/Generator.tsx`
  - 删除 `SCENE_TEMPLATES` 或改为固定展示数据。
  - 删除 prompt state 和 textarea UI。
  - 新增 `FIXED_PROMPT` 常量。
  - `handleGenerate` 使用固定 prompt。
  - `canGenerate` 不依赖 prompt 输入。
  - `Generate` 改为「开始生成」。
  - 固定场景区域替换原描述场景区域。

预计不修改:

- `backend/serve/app.py`
- `backend/serve/pipeline.py`
- `frontend/src/api/*`
- 模型和部署包

## 验证计划

本地验证:

```bash
cd frontend
npm run build
```

期望:

```text
build 成功
```

已知 `npm run lint` 当前会因项目既有问题失败,不是本次改动的通过门槛。本次可记录为已知失败,不把 lint 作为完成标准。

手动验证:

1. 打开页面后,不再看到英文 prompt 输入框。
2. 只看到固定「白底特写」场景卡片。
3. 按钮显示「开始生成」。
4. 点击后按钮显示「生成中...」。
5. 浏览器控制台没有前端运行时错误。
6. 生成过程中页面不出现整页黑屏遮罩。
7. 生成成功时图片正常展示;失败时红色错误面板正常展示。

服务器验证:

更新 `frontend/dist/` 后,服务器重建或重启容器,浏览器访问 `http://<server>:8008` 验证页面表现。若后端依赖仍在修复中,可先验证前端 UI 静态显示,生成验证等后端恢复后再做。

## 风险

1. 隐藏 prompt 后,用户不能临时尝试其他场景。这是有意限制,用于匹配训练集和减少错误。
2. 如果以后训练集加入更多场景,需要重新设计场景选择区。
3. 如果黑屏来自模型输出黑图,前端 UI 修改不能彻底解决,需要后续从 prompt、negative prompt、OpenVINO pipeline 或模型质量排查。

## 通过标准

1. UI 中英文 prompt 不可见、不可编辑。
2. 生成请求仍携带固定英文白底特写 prompt。
3. 中文按钮文案已生效。
4. `npm run build` 通过。
5. 页面生成中状态不出现前端造成的整页黑屏。
6. 设计不改变后端 API 和部署模型结构。
