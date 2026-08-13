---
name: vision-ds
description: 图片/图像识别、OCR 文字提取、截图分析。当主模型没有视觉能力（如 DeepSeek、Kimi、GLM 等纯文本模型）时，用户发来图片、截图、图片 URL 或让你"看"某张图，使用本技能把图片交给配置好的视觉提供商（小米 MiMo、智谱 GLM、火山豆包、百炼 Qwen-VL、Moonshot、OpenAI 兼容网关、本地 Ollama/LM Studio）识别；API 没配 Key 或调用失败时自动回退到 Windows/macOS 自带识别。也用于配置视觉 API 的 Key、base URL、模型。识别前必须实际运行脚本，禁止猜测图片内容。
---

# visionDS（视觉识别中枢）

一个可配置的多家视觉模型入口。主模型（比如 DeepSeek 这类不支持图片的模型）保持当前会话不变，只把图片交给选中的视觉提供商识别，再把返回的文字结果交给你。

## 核心场景

- 主模型没有视觉能力（DeepSeek / Kimi / GLM 纯文本模型等），用户发来图片、截图、图片 URL，希望知道内容 → **用本技能**。
- 想提取图片里的文字（OCR）→ 用本技能，可指定 `windows-ocr` / `macos-ocr` 免费离线识别。
- 想配置/更换视觉 API 的 Key、base URL、模型 → 用本技能。

## 脚本位置

脚本在本技能目录下的 `scripts/vision_hub.py`。请使用本技能说明里给出的 Base directory（`<skill_resources>` 中的路径）拼接脚本路径，例如：

```powershell
python "<Base directory>\scripts\vision_hub.py" "<图片路径>"
```

依赖 Python 3.10+（`python` 不可用时用 `py`）。

## 快速开始

```powershell
# 默认提供商识别（未配置 Key 时自动回退到本机 OCR）
python "<Base directory>\scripts\vision_hub.py" "C:\path\to\image.png"

# Windows 自带 OCR（免费、离线、只识别文字）
python "<Base directory>\scripts\vision_hub.py" "C:\path\to\image.png" --provider windows-ocr

# macOS 自带视觉（免费、离线，OCR + 物体分类）
python3 "<Base directory>/scripts/vision_hub.py" "/path/to/image.png" --provider macos-ocr
```

## 支持的提供商

| 提供商 | 默认模型 | 说明 |
| --- | --- | --- |
| `mimo` | `mimo-v2.5` | 小米 MiMo，按量付费（`sk-`） |
| `mimo-token-plan` | `mimo-v2.5` | MiMo Token Plan（`tp-`，国内专属地址） |
| `glm` | `glm-4.7v` | 智谱 GLM 视觉，模型名以控制台为准 |
| `ark` | `doubao-seed-1-6-vision-250815` | 火山方舟，模型名或 `ep-xxx` 接入点 |
| `dashscope` | `qwen-vl-max` | 阿里云百炼 Qwen-VL |
| `moonshot` | `moonshot-v1-32k-vision-preview` | Moonshot Kimi 视觉 |
| `openai` | `gpt-4o-mini` | 任意 OpenAI 兼容接口/中转（自建网关用这个） |
| `ollama` | `qwen2.5vl` | 本机 Ollama，离线 |
| `lmstudio` | `qwen2.5vl-7b-instruct` | LM Studio 本地服务器，离线 |
| `windows-ocr` | - | Windows 自带 OCR，离线免费 |
| `macos-ocr` | - | macOS Vision OCR + 物体分类，离线免费 |

## 配置方式（按优先级）

1. 命令行参数：`--api-key`、`--base-url`、`--model`、`--provider`
2. 环境变量：`VISION_HUB_API_KEY`、`VISION_HUB_BASE_URL`、`VISION_HUB_MODEL`、`VISION_HUB_PROVIDER`，以及各家专用变量（见下表）
3. `.env` 文件（推荐放 Key）——查找顺序：用户配置目录（Windows `%APPDATA%\vision-ds`，macOS/Linux `~/.config/vision-ds`，可用 `VISION_DS_CONFIG_DIR` 覆盖）→ 技能目录
4. 用户配置目录下的 `config.json`（推荐放非敏感配置，`--set` 写入）
5. `config/providers.json` 中的默认值

常用 Key 环境变量：

| 提供商 | Key 变量 | 地址变量 |
| --- | --- | --- |
| mimo / mimo-token-plan | `MIMO_API_KEY` | `MIMO_API_URL` |
| glm | `GLM_API_KEY` | - |
| ark | `ARK_API_KEY` | - |
| dashscope | `DASHSCOPE_API_KEY` | - |
| moonshot | `MOONSHOT_API_KEY` | - |
| openai | `OPENAI_API_KEY` | - |

MiMo Token Plan 配置示例（写入用户配置目录的 `.env`，Key 不会进对话）：

```text
MIMO_API_KEY=tp-你的key
MIMO_API_URL=https://token-plan-cn.xiaomimimo.com/v1
```

## 自动回退

**AI 提供商瞬时失败（空响应、网络抖动、限流 429、5xx）会自动重试一次**；重试仍失败或没配 Key 时，
**自动改用本机自带识别**（Windows 用 Windows OCR，macOS 用 macOS Vision），并在 stderr 提示原因。
这样即使 API 抖动或全挂，图片识别也不会失败。

- 关闭回退：加 `--no-fallback`
- 指定回退目标（持久化）：`--set fallback_provider=windows-ocr`
- 彻底关闭回退（持久化）：`--set fallback_provider=none`

示例——没配 GLM 的 Key，直接跑会自动回退到 Windows OCR：

```powershell
python "...\vision_hub.py" "a.png" --provider glm
# ⚠ glm 不可用，已自动回退到 windows-ocr（原因：提供商 glm 缺少 API Key...）
```

## 持久化设置

把默认提供商改为 GLM，并把模型改为 `glm-4.7v`：

```powershell
python "...\vision_hub.py" --set default_provider=glm --set providers.glm.model=glm-4.7v
```

自己接的第三方网关（DeepSeek 兼容中转、OneAPI、new-api 等，只要 OpenAI 格式都行）：

```powershell
python "...\vision_hub.py" --set providers.openai.base_url="https://你的网关/v1/chat/completions" --set providers.openai.model="你的视觉模型"
# Key 放 .env：OPENAI_API_KEY=sk-xxx
```

查看所有提供商和 Key 配置状态：

```powershell
python "...\vision_hub.py" --list
```

## 常用调用

指定提供商和模型：

```powershell
python "...\vision_hub.py" "a.png" --provider glm --model glm-4.7v
python "...\vision_hub.py" "a.png" --provider ark --model ep-xxxxxxxx
python "...\vision_hub.py" "a.png" --provider dashscope --model qwen3-vl-plus
```

指定临时 Key 和地址（不持久化）：

```powershell
python "...\vision_hub.py" "a.png" --provider openai --base-url "https://你的中转/v1" --api-key "sk-xxx" --model "你的模型"
```

OCR 提取文字：

```powershell
python "...\vision_hub.py" "a.png" --provider windows-ocr --prompt "请原样输出图片里的所有文字"
```

多张图片、JSON 输出、长回答：

```powershell
python "...\vision_hub.py" "a.png" "b.png" --provider mimo --max-tokens 2048 --json
```

## 新增自定义提供商

编辑 `config/providers.json`，按现有格式添加：

```json
{
  "my-gateway": {
    "label": "我的网关",
    "type": "openai",
    "base_url": "https://example.com/v1/chat/completions",
    "model": "my-vision-model",
    "auth": {"kind": "bearer"},
    "env_key": "MY_GATEWAY_API_KEY"
  }
}
```

`auth.kind` 支持 `bearer`（Authorization: Bearer）和 `header`（自定义头，如 MiMo 的 `api-key`）。也可以复制整个 `providers.json` 结构，新增本地脚本类提供商（`type: local`）。

## 规则

- 必须实际运行脚本拿到结果后再回答，不要在运行前承诺识别内容。
- 不要把 Key 打印到对话里；报错信息需脱敏。
- 主模型始终是当前会话模型，不允许把整个会话切换成别的模型。
- Key 只能写入环境变量或 `.env`（用户配置目录/技能目录），绝不写入任何会被提交到版本库的文件。
