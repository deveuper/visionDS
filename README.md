# visionDS

> DeepSeek Harness 的多提供商视觉识别技能（skill）。原名 vision-hub（ZCode 版），本仓库为 DeepSeek Harness 版，**技能名 `vision-ds`，显示名 visionDS**（Harness 的技能名只允许小写 kebab-case，故目录名为 `vision-ds`）。

主模型没有视觉能力（如 DeepSeek 这类纯文本模型）时，把图片/截图/图片 URL 交给本技能，由配置好的视觉提供商识别后返回文字结果：

- **AI 提供商**：小米 MiMo、智谱 GLM、火山豆包、百炼 Qwen-VL、Moonshot、任意 OpenAI 兼容网关、本地 Ollama / LM Studio；
- **免费离线回退**：AI 提供商没配 Key 或调用失败（重试一次仍失败）时，自动回退到 Windows 自带 OCR / macOS Vision；
- **OCR**：直接用 `windows-ocr` / `macos-ocr` 提取图片文字。

## 安全声明

- 本仓库**不包含任何 API Key**，也从不内置任何密钥。所有 Key 由用户通过环境变量或本地 `.env` 文件提供（文件已被 `.gitignore` 排除）。
- 请勿把 Key 写进任何会被提交的文件；`--list` 只显示"已配置/未配置"，不打印 Key。

## 目录结构

```
visionDS/
├── package.json         # dsh bundle 声明（dsh.bundle.patch）
├── cordis.patch.yml     # 组合层：挂载本包插件
├── index.js             # 插件入口：把 skill/SKILL.md 注册为运行时技能
├── skill/               # 技能本体（也可直接手动安装）
│   ├── SKILL.md         # Harness 技能定义（frontmatter: name/description）
│   ├── config/providers.json   # 各提供商默认地址与模型（无密钥）
│   └── scripts/
│       ├── vision_hub.py       # 识别主脚本（Python 3.10+）
│       ├── ocr_windows.ps1     # Windows 自带 OCR
│       └── ocr_macos.swift     # macOS Vision OCR + 物体分类
├── .env.example         # 配置模板（复制后填入自己的 Key）
└── README.md
```

## 安装

### 方式一：dsh plugin 安装（对应官方文档《打包与安装插件》）

按 DeepSeek Harness 官方文档 [打包与安装插件](https://deepseek-harness.github.io/deepseek-harness/develop/basic/publish) 的机制，从 GitHub 直接安装：

```sh
dsh plugin --profile <你的profile名> add github:deveuper/visionDS
```

安装后启动对应 profile，技能 `vision-ds` 即出现在会话的技能目录中。无需构建授权（纯 JS、无 `prepare` 脚本）。

> 从源码 checkout 运行 Harness 时，用 `pnpm dsh ...` 代替 `dsh ...`（见官方文档「从源码运行」）。

### 方式二：手动复制技能目录（任何支持 SKILL.md 的 Harness/Agent）

把 `skill/` 目录复制为技能根目录下的 `vision-ds`：

- DeepSeek Harness 用户技能根：`~/.agents/skills/`（Windows 即 `C:\Users\<你>\.agents\skills\`）

```powershell
Copy-Item .\skill "$env:USERPROFILE\.agents\skills\vision-ds" -Recurse
```

刷新 Harness 页面后，技能 `vision-ds` 会出现在可用技能列表里。

### 方式三：直接使用脚本（不装技能）

任何环境只要有 Python 3.10+：

```powershell
python skill\scripts\vision_hub.py "C:\path\to\image.png"
```

## 依赖

- **Python 3.10+**（`python` 或 `py`）；仅安装方式一需要 Node ≥ 18（Harness 本身提供）。
- 本机 OCR：Windows 10/11 自带（PowerShell + WinRT），macOS 自带（`swift`）。

## 配置 API Key（三选一，推荐 .env）

1. **环境变量**（进程级，不会落盘）：

   | 提供商 | Key 变量 | 地址变量（可选） |
   | --- | --- | --- |
   | mimo / mimo-token-plan | `MIMO_API_KEY` | `MIMO_API_URL` |
   | glm | `GLM_API_KEY` | - |
   | ark | `ARK_API_KEY` | - |
   | dashscope | `DASHSCOPE_API_KEY` | - |
   | moonshot | `MOONSHOT_API_KEY` | - |
   | openai（及任何兼容网关） | `OPENAI_API_KEY` | - |
   | 通用 | `VISION_HUB_API_KEY` | `VISION_HUB_BASE_URL` |

2. **`.env` 文件**（推荐；用户配置目录 `.env` 优先于技能目录 `.env`）：
   - Windows：`%APPDATA%\vision-ds\.env`（如 `C:\Users\<你>\AppData\Roaming\vision-ds\.env`）
   - macOS/Linux：`~/.config/vision-ds/.env`
   - 可用环境变量 `VISION_DS_CONFIG_DIR` 指向其它目录
   - 示例（MiMo Token Plan）：

     ```text
     MIMO_API_KEY=tp-你的key
     MIMO_API_URL=https://token-plan-cn.xiaomimimo.com/v1
     ```

3. **命令行参数**（临时、不持久化）：`--api-key`、`--base-url`。

未配置任何 Key 也可以直接用：识别会自动回退到 Windows/macOS 自带 OCR。

## 使用

在 Harness 会话里对技能 `vision-ds` 说"看这张图"，或按技能说明运行脚本。常用命令：

```powershell
python "...\vision_hub.py" "a.png"                          # 默认提供商
python "...\vision_hub.py" "a.png" --provider glm --model glm-4.7v
python "...\vision_hub.py" "a.png" --provider windows-ocr   # 免费离线 OCR
python "...\vision_hub.py" "a.png" "b.png" --provider mimo --max-tokens 2048 --json
python "...\vision_hub.py" --list                           # 查看各提供商与 Key 配置状态
python "...\vision_hub.py" --set default_provider=glm       # 持久化默认提供商
```

持久化设置写在用户配置目录的 `config.json`（`--set` 写入，也可用 `VISION_DS_CONFIG_DIR` 改位置），不会改仓库文件。

### 自动回退

AI 提供商瞬时失败（网络抖动、限流 429、5xx、空响应）自动重试一次；仍失败或没配 Key 时自动改用本机 OCR：

- 关闭回退：`--no-fallback`
- 持久化回退目标：`--set fallback_provider=windows-ocr`；彻底关闭：`--set fallback_provider=none`

## 自定义提供商

编辑 `skill/config/providers.json`，按现有格式新增 OpenAI 兼容网关或本地脚本类提供商（`type: local`）；`auth.kind` 支持 `bearer` 与 `header`。详见 `skill/SKILL.md`。

## 从 ZCode 版迁移

原 ZCode 版 `vision`/`vision-hub` 的 `.env` 直接可用：把其中的 `MIMO_API_KEY`（以及可选的 `MIMO_API_URL`）复制到 `%APPDATA%\vision-ds\.env` 即可，其它配置用 `--set` 重建。原 ZCode 目录请自行删除，避免旧 `.env` 泄漏。

## 常见问题

- **技能名为什么是 `vision-ds` 而不是 `visionDS`？** Harness 要求技能名匹配 `^[a-z0-9]+(?:-[a-z0-9]+)*$`（小写 kebab-case），显示名/品牌名是 visionDS。
- **`--list` 里 key 显示"未配置"但我想用默认提供商？** 不配 Key 也能跑：失败会自动回退到本机 OCR。要更高质量识别就按上文配 Key。
- **Windows OCR 没反应？** 确认是 Windows 10/11 且系统语言包完整；或改用任一 AI 提供商。

## License

[MIT](./LICENSE)
