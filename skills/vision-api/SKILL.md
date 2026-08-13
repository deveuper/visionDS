---
name: vision-api
description: 用视觉 API 识别图片：把图片交给配置好的 AI 视觉提供商（MiMo、GLM、豆包、Qwen-VL、Moonshot、OpenAI 兼容网关等）返回内容描述；失败自动回退本机 OCR。用户要"看图/描述图片内容"且想用 API 时使用。English: recognizes images through a configured AI vision provider (MiMo, GLM, Doubao, Qwen-VL, Moonshot, OpenAI-compatible); falls back to offline OCR on failure. Use when API-based recognition is wanted.
---

# vision-api（API 视觉识别）

把图片交给配置好的 AI 视觉提供商，返回对图片内容的文字描述。默认提供商 `mimo-token-plan`（Key 在用户配置目录，未配置则自动回退本机 OCR）。

共享脚本位于同级 `vision-ds` 技能目录（`<Base directory>\..\vision-ds\scripts\vision_hub.py`）。依赖 Python 3.10+（`python` 不可用时用 `py`）。

## 命令

```powershell
python "<Base directory>\..\vision-ds\scripts\vision_hub.py" "<图片路径>"

# 指定提供商/模型
python "<Base directory>\..\vision-ds\scripts\vision_hub.py" "<图片路径>" --provider glm --model glm-4.7v
```

## 说明

- Key、默认提供商、模型的配置方式见 vision-ds 技能；查看状态：`python "<Base directory>\..\vision-ds\scripts\vision_hub.py" --list`
- 瞬时失败自动重试一次；仍失败自动回退本机 OCR（加 `--no-fallback` 关闭），并在结果里说明回退原因。
- 只要图片文字（免费离线）用 vision-local 更合适。

## 规则

- 必须实际运行脚本拿到结果后再回答，禁止猜测图片内容。
- 不要把 Key 打印到对话里；报错信息需脱敏。
- 主模型始终是当前会话模型。

## English

Sends images to the configured AI vision provider (default `mimo-token-plan`) and returns a text description. Transient failures retry once, then fall back to offline OCR; disable with `--no-fallback`. Provider/key configuration lives in `vision-ds`. Run the command above before answering.
