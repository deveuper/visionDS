---
name: vision-ds
description: 默认视觉入口（Default vision entry）：先用配置好的视觉 API 识别图片，约 2 分钟没返回自动改用本机 OCR，保证总能出结果。用户发来图片/截图/图片 URL 要"看"时默认走本技能。English: default entry — API recognition first, automatically switching to built-in OCR if the API does not respond within about two minutes. Use by default when the user sends an image.
---

# vision-ds（默认视觉入口）

用户发来图片/截图/图片 URL 时默认使用本技能：先调用配置好的视觉 API（默认 `mimo-token-plan`），最多等约 2 分钟；没有返回就自动改成本地 OCR（Windows 自带 OCR / macOS Vision）。主模型始终保持当前会话模型。

共享脚本与提供商配置在本技能目录下；`vision-ds-local` / `vision-ds-api` / `vision-setting` 通过同级目录引用。

## 命令

```powershell
python "<Base directory>\scripts\vision_hub.py" "<图片路径>" --timeout 110 --no-retry
```

- `--timeout 110`：单次 API 最多等约 2 分钟（受会话命令时限约束）
- `--no-retry`：不重试，超时/失败立即自动回退本机 OCR

多张图片或需要 JSON 同理：

```powershell
python "<Base directory>\scripts\vision_hub.py" "a.png" "b.png" --timeout 110 --no-retry --json
```

## 规则

- 必须实际运行脚本拿到结果后再回答；结果来自 API 还是本地 OCR，以脚本输出与 stderr 提示为准，如实告知用户。
- 只想要图片文字（免费离线）用 vision-ds-local；确定只用 API 用 vision-ds-api；配置 Key/提供商/模型用 vision-setting。

## English

Default entry: run the shared script with `--timeout 110 --no-retry` — API recognition first, automatic offline-OCR fallback after about two minutes without a response. Report which backend produced the result.
