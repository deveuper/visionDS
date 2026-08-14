---
name: vision-ds-local
description: "免费离线 OCR：用 Windows 自带 OCR / macOS Vision 提取图片里的文字，不调用任何 API、不消耗 Key、无需联网。用户只想要图片文字（OCR）时使用。English: free offline OCR via built-in Windows OCR / macOS Vision — no API, no keys, no network. Use when only the text in an image is wanted."
---

# vision-ds-local（免费离线 OCR）

只做一件事：把图片里的文字原样提取出来。完全离线、免费、不消耗任何 API Key。

共享脚本位于同级 `vision-ds` 技能目录（`<Base directory>\..\vision-ds\scripts\vision_hub.py`）。依赖 Python 3.10+（`python` 不可用时用 `py`）。

## 命令

Windows：

```powershell
python "<Base directory>\..\vision-ds\scripts\vision_hub.py" "<图片路径>" --provider windows-ocr
```

macOS：

```bash
python3 "<Base directory>/../vision-ds/scripts/vision_hub.py" "<图片路径>" --provider macos-ocr
```

## 规则

- 必须实际运行脚本拿到结果后再回答，禁止猜测图片内容。
- 本技能只做 OCR 文字提取；要"看图描述内容"用 vision-ds（默认）或 vision-ds-api，配置 API 用 vision-setting。

## English

Free offline OCR: extracts text from images with built-in Windows OCR or macOS Vision. No API keys, no network. Run the command above, then report the recognized text. For full image descriptions use `vision-ds` (default) or `vision-ds-api`; for provider configuration use `vision-setting`.
