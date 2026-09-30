---
name: vision-ds
description: "视觉兜底（Vision fallback）：仅在模型看不到图、模型识图不可靠、用户要求 OCR/指定提供商/离线识别、或需把本地图片路径转成文字时使用；先用视觉 API，约 2 分钟没返回自动改本机 OCR。模型自己有视觉且能看清时不要调用。English: fallback vision skill — API first, built-in OCR after about two minutes. Use only when the model cannot see the image, its reading is unreliable, the user asks for OCR / a named provider / offline recognition, or a local path must become text. Never route when the model already sees the image."
---

# vision-ds（视觉兜底：API 优先 + 自动回退本机 OCR）

把一张图片变成文字内容。会话主模型始终保持不变。

## 什么时候用（满足其一才用）

1. **模型看不到图**：当前会话模型没有视觉能力（例如纯文本模型），或贴图被拒（提示"当前模型不支持图片"）。
2. **模型识图失败或不可靠**：模型看过但答错/幻觉，或内容是密集表格、长截图、小字号、价格与数字等需要精确读出的信息。
3. **用户明确要求**：要 OCR 文字、指定某个视觉提供商/模型，或要求离线、免费识别。
4. **手上是本地图片路径**：需要把某个路径对应的图片内容读成文字（例如附件路径、工作区里的截图）。

**不要用**：模型自己有视觉、并且已经看清了图片时，直接让模型看图即可——绕道跑脚本更慢也更贵。

## 图片怎么到我手上

- **文件附件**：非图片类型的文件附件，官方会以文本形式给出本地只读路径（形如 `verbatim read-only copy saved at "<路径>"`），直接用那个路径。
- **用户直接给路径**：工作区或磁盘上的截图/图片路径，直接用。
- **纯文本模型 + 图片附件**：本版本仍会拒绝（门禁只拦图片类型的附件）。可行办法是把图片存成**非图片扩展名**（如 `.bin`）再作为文件附件上传：文件通道不受门禁限制，模型会拿到路径；本技能脚本按文件头魔数识别格式，不依赖扩展名。
- **图片 URL**：脚本支持直接传 URL。

## 命令

```powershell
python "<Base directory>\scripts\vision_hub.py" "<图片路径或URL>" --timeout 110 --no-retry
```

- `--timeout 110`：单次 API 最多等约 2 分钟（受会话命令时限约束）
- `--no-retry`：不重试，超时/失败立即自动回退本机 OCR

多张图片或需要 JSON：

```powershell
python "<Base directory>\scripts\vision_hub.py" "a.png" "b.png" --timeout 110 --no-retry --json
```

## 规则

- 必须实际运行脚本拿到结果后再回答，禁止猜测图片内容。
- 结果来自 API 还是本地 OCR，以脚本输出与 stderr 提示为准，如实告知用户。
- 确定只用 API 用 vision-ds-api；只要文字、要免费离线用 vision-ds-local；配置 Key/提供商/模型用 vision-setting。

## English

Fallback vision entry. **Use only when** the model cannot see the image (text-only model, or the image attachment was refused), its own image reading failed or looks unreliable (dense tables, long screenshots, exact numbers), the user explicitly asks for OCR / a named provider / offline recognition, or a local image path must be turned into text. **Do not use** when the model already sees the image well.

Run: `python "<Base directory>\scripts\vision_hub.py" "<path-or-url>" --timeout 110 --no-retry` — API first, built-in OCR after about two minutes. Non-image file attachments arrive as a read-only local path; for a text-only model, attach the picture with a non-image extension (e.g. `.bin`) so the file channel delivers a path (the script sniffs magic bytes, not the extension). Report which backend produced the result.
