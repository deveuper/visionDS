# visionDS — DeepSeek Harness 视觉技能包

四个互补的视觉技能（skill）：主模型没有视觉能力（如 DeepSeek 纯文本模型）时，把图片/截图/图片 URL 交给它们识别，主模型保持不变。

**English**: four complementary vision skills for DeepSeek Harness. When the main model cannot see images (e.g. text-only DeepSeek), these skills recognize images, screenshots, and URLs and hand the text result back — the main model never changes.

## 四个技能 / Four skills

| 技能 Skill | 用途 Purpose | 说明 Notes |
| --- | --- | --- |
| `vision-ds` | 默认入口 Default entry | 先 API 识别，约 2 分钟没返回自动改本机 OCR。API first, offline OCR after ~2 minutes without a response. |
| `vision-ds-local` | 免费离线 OCR Offline OCR | 只用 Windows 自带 OCR / macOS Vision 提取图片文字，不消耗 API。Text extraction only, no API, no keys. |
| `vision-ds-api` | API 识别 API recognition | 调用配置好的视觉 API（MiMo/GLM/豆包/Qwen-VL/Moonshot/OpenAI 兼容等）描述图片，失败自动回退本机 OCR。Describe images via a configured vision provider, with offline fallback. |
| `vision-setting` | 配置中枢 Settings | 配置/更换 Key、base URL、模型、默认提供商；查看提供商与 Key 状态。Configure providers, keys, and models. |

共享脚本位于 `skills/vision-ds/scripts/vision_hub.py`（Python 3.10+），其余三个技能通过同级目录引用。

**The four skills share one script** at `skills/vision-ds/scripts/vision_hub.py`; the other three reference it via the sibling directory.

## 安装 / Install

### 方式一：dsh plugin（推荐，官方 publish 机制）

```sh
dsh plugin --profile <你的profile名> add github:deveuper/visionDS
```

安装后三个技能自动注册进会话。纯 JS、无 `prepare`，无需构建授权。

### 方式二：手动复制 / Manual copy

把 `skills/` 下的四个目录复制到技能根（如 `~/.agents/skills/`），保持四个目录同级：

```powershell
Copy-Item .\skills\vision-ds        "$env:USERPROFILE\.agents\skills\vision-ds"        -Recurse
Copy-Item .\skills\vision-ds-local  "$env:USERPROFILE\.agents\skills\vision-ds-local"  -Recurse
Copy-Item .\skills\vision-ds-api    "$env:USERPROFILE\.agents\skills\vision-ds-api"    -Recurse
Copy-Item .\skills\vision-setting   "$env:USERPROFILE\.agents\skills\vision-setting"   -Recurse
```

Copy the four directories under `skills/` into a skill root (e.g. `~/.agents/skills/`), keeping them siblings. Refresh the Harness page afterwards.

## 配置 Key / Configure API keys

仓库不含任何 Key。三种方式（优先级从高到低）：

1. 环境变量：`MIMO_API_KEY` / `GLM_API_KEY` / `ARK_API_KEY` / `DASHSCOPE_API_KEY` / `MOONSHOT_API_KEY` / `OPENAI_API_KEY`
2. 用户配置目录 `.env`：Windows `%APPDATA%\vision-ds\.env`，macOS/Linux `~/.config/vision-ds/.env`（模板见 `.env.example`）
3. 命令行临时参数：`--api-key` / `--base-url`

不配 Key 也能用：`vision-ds-local` 永远可用；`vision-ds` / `vision-ds-api` 失败会自动回退本机 OCR。

**No keys ship in this repo.** Priority: environment variables → user-config `.env` (Windows `%APPDATA%\vision-ds\.env`, macOS/Linux `~/.config/vision-ds/.env`) → CLI flags. Without any key, `vision-ds-local` always works and the other two fall back to built-in OCR.

## 用法 / Usage

```powershell
# 默认入口（API 优先，约 2 分钟没返回自动本机 OCR）
python "<vision-ds目录>\scripts\vision_hub.py" "a.png" --timeout 110 --no-retry

# 离线 OCR（vision-ds-local）
python "<vision-ds目录>\scripts\vision_hub.py" "a.png" --provider windows-ocr

# API 识别（vision-ds-api，默认提供商 mimo-token-plan）
python "<vision-ds目录>\scripts\vision_hub.py" "a.png" --provider glm --model glm-4.7v --timeout 55

# 查看提供商与 Key 状态 / 持久化设置（vision-setting）
python "<vision-ds目录>\scripts\vision_hub.py" --list
python "<vision-ds目录>\scripts\vision_hub.py" --set default_provider=glm
```

## 安全 / Security

- 仓库零密钥：全量扫描无 `sk-*`/`tp-*`；`.env` 已被 `.gitignore` 排除。
- 脚本不会把 Key 打印到输出；`--list` 只显示"已配置/未配置"。

**Zero keys in the repo**: no secrets are committed, `.env` is gitignored, and the script never prints keys (`--list` shows only configured / not configured).

## License

[MIT](./LICENSE)
