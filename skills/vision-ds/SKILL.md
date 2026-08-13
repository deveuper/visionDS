---
name: vision-ds
description: 视觉识别中枢（Vision hub）。当主模型没有视觉能力时，把图片/截图/图片 URL 交给配置好的视觉提供商（MiMo、GLM、豆包、Qwen-VL、Moonshot、OpenAI 兼容网关、Ollama/LM Studio）识别；失败或未配 Key 时自动回退 Windows/macOS 自带 OCR。也用于配置 Key、base URL、模型。识别前必须实际运行脚本，禁止猜测。English: routes images to a configured vision provider with automatic fallback to offline OCR; also configures provider keys, base URLs, and models. Always run the script before answering.
---

# visionDS（视觉识别中枢）

主模型（如 DeepSeek 这类纯文本模型）没有视觉能力时，把图片交给配置好的视觉提供商识别，返回文字结果。会话主模型保持不变。

**English**: routes images to a configurable vision provider and returns the text result, keeping the text-only main model unchanged.

## 三个入口

- 只想提取图片文字（免费离线）→ 用 **vision-local** 技能
- 只用 API 识别图片内容 → 用 **vision-api** 技能
- 配置/更换 Key、base URL、模型，或需要完整提供商列表 → 用本技能

## 脚本位置

共享脚本在本技能目录下的 `scripts/vision_hub.py`，vision-local / vision-api 通过同级目录引用它。依赖 Python 3.10+（`python` 不可用时用 `py`）。

## 快速开始

```powershell
# 默认提供商识别（失败自动回退本机 OCR）
python "<Base directory>\scripts\vision_hub.py" "C:\path\to\image.png"

# 免费离线 OCR
python "<Base directory>\scripts\vision_hub.py" "C:\path\to\image.png" --provider windows-ocr
```

## 支持的提供商

| 提供商 | 默认模型 | 说明 |
| --- | --- | --- |
| `mimo` | `mimo-v2.5` | 小米 MiMo，按量付费（`sk-`） |
| `mimo-token-plan` | `mimo-v2.5` | MiMo Token Plan（`tp-`，国内地址） |
| `glm` | `glm-4.7v` | 智谱 GLM 视觉 |
| `ark` | `doubao-seed-1-6-vision-250815` | 火山方舟，模型名或 `ep-xxx` 接入点 |
| `dashscope` | `qwen-vl-max` | 阿里云百炼 Qwen-VL |
| `moonshot` | `moonshot-v1-32k-vision-preview` | Moonshot Kimi 视觉 |
| `openai` | `gpt-4o-mini` | 任意 OpenAI 兼容接口/中转 |
| `ollama` | `qwen2.5vl` | 本机 Ollama，离线 |
| `lmstudio` | `qwen2.5vl-7b-instruct` | LM Studio 本地服务器，离线 |
| `windows-ocr` | - | Windows 自带 OCR，离线免费 |
| `macos-ocr` | - | macOS Vision OCR + 物体分类，离线免费 |

## 配置方式（按优先级）

1. 命令行参数：`--api-key`、`--base-url`、`--model`、`--provider`
2. 环境变量：`MIMO_API_KEY`、`GLM_API_KEY`、`ARK_API_KEY`、`DASHSCOPE_API_KEY`、`MOONSHOT_API_KEY`、`OPENAI_API_KEY`，以及通用 `VISION_HUB_API_KEY` / `VISION_HUB_BASE_URL`
3. `.env` 文件（推荐放 Key）：用户配置目录（Windows `%APPDATA%\vision-ds`，macOS/Linux `~/.config/vision-ds`，可用 `VISION_DS_CONFIG_DIR` 覆盖）→ 技能目录
4. 用户配置目录下的 `config.json`（`--set` 写入）
5. `config/providers.json` 中的默认值

## 自动回退

AI 提供商瞬时失败（网络抖动、429、5xx、空响应）自动重试一次；仍失败或没配 Key 时自动改用本机 OCR。`--no-fallback` 关闭；`--set fallback_provider=windows-ocr` 持久化回退目标；`--set fallback_provider=none` 彻底关闭。

## 常用命令

```powershell
python "...\vision_hub.py" "a.png" --provider glm --model glm-4.7v     # 指定提供商
python "...\vision_hub.py" "a.png" --provider windows-ocr              # 纯 OCR
python "...\vision_hub.py" "a.png" "b.png" --max-tokens 2048 --json    # 多图/JSON
python "...\vision_hub.py" --list                                      # 查看提供商与 Key 状态
python "...\vision_hub.py" --set default_provider=glm                  # 持久化默认提供商
```

新增自定义提供商：编辑 `config/providers.json`，按现有条目添加（`auth.kind` 支持 `bearer` / `header`，`type: local` 为本地脚本类）。

## 规则

- 必须实际运行脚本拿到结果后再回答，禁止在运行前猜测图片内容。
- 不要把 Key 打印到对话里；报错信息需脱敏。
- 主模型始终是当前会话模型，不允许切换整个会话的模型。
- Key 只能写入环境变量或 `.env`（用户配置目录/技能目录），绝不写入版本库。

## English quick reference

- Offline OCR: `--provider windows-ocr` (Windows) / `--provider macos-ocr` (macOS).
- API recognition: default provider is `mimo-token-plan`; pick another with `--provider`.
- Config priority: CLI flags → environment variables → user-config `.env` → user-config `config.json` → `config/providers.json` defaults.
- Failure falls back to built-in OCR automatically; disable with `--no-fallback`.
- Run the script and read its output before answering; never expose keys.
