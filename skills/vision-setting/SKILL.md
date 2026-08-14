---
name: vision-setting
description: "视觉配置中枢（Vision settings）：配置/更换视觉 API 的 Key、base URL、模型、默认提供商；查看全部提供商与 Key 状态；新增自定义提供商。需要配置或排查识别设置时使用。English: configures vision API keys, base URLs, models, and the default provider; lists providers and key status. Use for any configuration or troubleshooting of vision recognition."
---

# vision-setting（视觉配置中枢）

配置 vision-ds / vision-ds-api 所用的 Key、base URL、模型与默认提供商。共享脚本与提供商配置位于同级 `vision-ds` 技能目录（`<Base directory>\..\vision-ds\`）。依赖 Python 3.10+。

## 查看状态

```powershell
python "<Base directory>\..\vision-ds\scripts\vision_hub.py" --list
```

## 配置方式（按优先级）

1. 命令行参数：`--api-key`、`--base-url`、`--model`、`--provider`
2. 环境变量：`MIMO_API_KEY`、`GLM_API_KEY`、`ARK_API_KEY`、`DASHSCOPE_API_KEY`、`MOONSHOT_API_KEY`、`OPENAI_API_KEY`，以及通用 `VISION_HUB_API_KEY` / `VISION_HUB_BASE_URL`
3. `.env` 文件（推荐放 Key）：用户配置目录（Windows `%APPDATA%\vision-ds`，macOS/Linux `~/.config/vision-ds`，可用 `VISION_DS_CONFIG_DIR` 覆盖）→ 技能目录
4. 用户配置目录下的 `config.json`（`--set` 写入）
5. `config/providers.json` 中的默认值

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

## 持久化设置

```powershell
# 换默认提供商（影响 vision-ds / vision-ds-api）
python "<Base directory>\..\vision-ds\scripts\vision_hub.py" --set default_provider=glm --set providers.glm.model=glm-4.7v

# 接自己的 OpenAI 兼容网关
python "<Base directory>\..\vision-ds\scripts\vision_hub.py" --set providers.openai.base_url="https://你的网关/v1/chat/completions" --set providers.openai.model="你的视觉模型"

# 回退目标（默认按系统自动选本机 OCR；none 彻底关闭回退）
python "<Base directory>\..\vision-ds\scripts\vision_hub.py" --set fallback_provider=windows-ocr
```

新增自定义提供商：编辑 `..\vision-ds\config\providers.json`，按现有条目添加（`auth.kind` 支持 `bearer` / `header`，`type: local` 为本地脚本类）。

## 规则

- 不要把 Key 打印到对话里；报错信息需脱敏。
- Key 只能写入环境变量或 `.env`（用户配置目录/技能目录），绝不写入版本库。

## English quick reference

- `--list` shows every provider and whether its key is configured.
- Config priority: CLI flags → environment variables → user-config `.env` → user-config `config.json` → `config/providers.json` defaults.
- `--set default_provider=glm` makes GLM the default for `vision-ds` / `vision-ds-api`; `--set fallback_provider=none` disables the offline fallback.
- Never print keys; store them only in environment variables or `.env` files.
