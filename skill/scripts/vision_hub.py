#!/usr/bin/env python3
"""visionDS: route image understanding through configurable providers.

主模型（如 DeepSeek 等纯文本模型）没有视觉能力时，把图片交给本脚本：
优先调用配置好的视觉 API（MiMo/GLM/豆包/Qwen-VL/Moonshot/OpenAI 兼容网关等），
API 没配 Key 或调用失败时，自动回退到 Windows/macOS 自带的本地识别（--no-fallback 可关闭）。
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import platform
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
PROVIDERS_FILE = SKILL_ROOT / "config" / "providers.json"
MAX_IMAGE_BYTES = 50 * 1024 * 1024


def user_config_dir() -> Path:
    """用户级配置目录：Key 与持久化设置都写在这里，绝不进入 skill 目录或版本库。

    顺序：VISION_DS_CONFIG_DIR 环境变量 > 系统默认（Windows: %APPDATA%\\vision-ds，其它: ~/.config/vision-ds）。
    """
    explicit = os.environ.get("VISION_DS_CONFIG_DIR", "").strip()
    if explicit:
        return Path(explicit).expanduser()
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home())
        return Path(base) / "vision-ds"
    return Path.home() / ".config" / "vision-ds"


def config_file() -> Path:
    return user_config_dir() / "config.json"


def env_files() -> list[Path]:
    return [user_config_dir() / ".env", SKILL_ROOT / ".env"]

EXTENSION_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}


def sniff_image_mime(path: Path) -> str | None:
    """按文件头魔数识别图片类型，兼容无扩展名的文件（如内容寻址的附件对象）。"""
    try:
        head = path.open("rb").read(16)
    except OSError:
        return None
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        return "image/webp"
    if head.startswith(b"BM"):
        return "image/bmp"
    return None


def ensure_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_env(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def env_value(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return None


def env_file_value(*names: str) -> str | None:
    for path in env_files():
        values = load_env(path)
        for name in names:
            if values.get(name):
                return values[name]
    return None


def registry() -> dict[str, Any]:
    return read_json(PROVIDERS_FILE)


def user_config() -> dict[str, Any]:
    return read_json(config_file())


def provider_def(name: str) -> dict[str, Any]:
    reg = registry().get("providers", {})
    if name not in reg:
        known = ", ".join(sorted(reg))
        raise RuntimeError(f"未知提供商: {name}。可用: {known}")
    merged = dict(reg[name])
    overrides = user_config().get("providers", {}).get(name, {})
    if isinstance(overrides, dict):
        merged.update(overrides)
    return merged


def default_provider() -> str:
    cfg_default = user_config().get("default_provider")
    if isinstance(cfg_default, str) and cfg_default:
        return cfg_default
    env_default = env_value("VISION_HUB_PROVIDER")
    if env_default:
        return env_default
    return "mimo"


def api_key_for(provider: str, explicit: str | None) -> str | None:
    if explicit:
        return explicit.strip()
    definition = provider_def(provider)
    env_key = definition.get("env_key")
    candidates = ["VISION_HUB_API_KEY"]
    if env_key:
        candidates.append(env_key)
    value = env_value(*candidates)
    if value:
        return value
    value = user_config().get("api_keys", {}).get(provider)
    if isinstance(value, str) and value:
        return value
    value = env_file_value(env_key or "VISION_DS_API_KEY")
    if value:
        return value
    return None


def base_url_for(provider: str, explicit: str | None) -> str:
    if explicit:
        return explicit.strip()
    definition = provider_def(provider)
    env_base = definition.get("env_base")
    if env_base:
        value = env_value("VISION_HUB_BASE_URL", env_base)
        if value:
            return value
        # .env 文件里也能写地址（如 MIMO_API_URL），与文档一致
        value = env_file_value(env_base)
        if value:
            return value
    value = env_value("VISION_HUB_BASE_URL")
    if value:
        return value
    value = env_file_value("VISION_HUB_BASE_URL")
    if value:
        return value
    return definition.get("base_url", "")


def resolve_url(url: str) -> str:
    url = url.rstrip("/")
    if not url.endswith("/chat/completions"):
        url += "/chat/completions"
    return url


def image_to_data_url(value: str) -> str:
    if value.startswith(("http://", "https://", "data:")):
        return value
    path = Path(value)
    if not path.is_file():
        raise RuntimeError(f"图片不存在: {value}")
    if path.stat().st_size > MAX_IMAGE_BYTES:
        raise RuntimeError(f"图片超过 50MB 限制: {value}")
    mime = EXTENSION_MIME.get(path.suffix.lower()) or sniff_image_mime(path) or mimetypes.guess_type(path.name)[0]
    mime = mime or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    if len(encoded) > MAX_IMAGE_BYTES:
        raise RuntimeError(f"图片 Base64 后超过 50MB 限制: {value}")
    return f"data:{mime};base64,{encoded}"


def call_openai_provider(
    provider: str,
    definition: dict[str, Any],
    api_key: str,
    images: list[str],
    prompt: str,
    max_tokens: int,
    temperature: float | None,
    timeout: int,
) -> tuple[str, dict[str, Any]]:
    payload: dict[str, Any] = {
        "model": definition.get("model", ""),
        "messages": [
            {
                "role": "system",
                "content": "You are an accurate image understanding assistant. Base every statement only on the provided image content.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": url}}
                    for url in images
                ]
                + [{"type": "text", "text": prompt}],
            },
        ],
    }
    max_field = definition.get("max_field", "max_tokens")
    payload[max_field] = max_tokens
    if temperature is not None:
        payload["temperature"] = temperature

    request = urllib.request.Request(
        resolve_url(definition.get("base_url", "")),
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )
    request.add_header("Content-Type", "application/json")
    auth = definition.get("auth", {})
    kind = auth.get("kind", "bearer")
    if kind == "header":
        request.add_header(auth.get("name", "Authorization"), api_key)
    else:
        request.add_header("Authorization", f"Bearer {api_key}")

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{provider} API 返回错误 {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"无法连接 {provider} API: {error.reason}") from error

    try:
        message = result["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError(
            f"{provider} API 响应格式异常: {json.dumps(result, ensure_ascii=False)}"
        ) from error
    content = message.get("content", "")
    if isinstance(content, list):
        text = "".join(
            part.get("text", "") for part in content if isinstance(part, dict)
        ).strip()
    else:
        text = str(content or "").strip()
    return text, result.get("usage", {})


def run_local_provider(
    provider: str,
    definition: dict[str, Any],
    image: str,
    language: str | None,
) -> str:
    command = list(definition.get("command", []))
    if not command:
        raise RuntimeError(f"提供商 {provider} 没有可执行命令")
    resolved: list[str] = []
    for item in command:
        item = os.path.expandvars(item.replace("{skill}", str(SKILL_ROOT)))
        if not os.path.isabs(item) and ("/" in item or "\\" in item):
            candidate = SKILL_ROOT / item
            if candidate.exists():
                item = str(candidate)
        resolved.append(item)
    full = resolved + [str(image)]
    if language and provider in ("windows-ocr",):
        full += ["-Language", language]
    try:
        result = subprocess.run(
            full,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
    except FileNotFoundError as error:
        raise RuntimeError(f"找不到本机命令: {error.filename}") from error
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("本机 OCR 超时") from error
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"{provider} 执行失败: {detail}")
    text = result.stdout.strip()
    if not text:
        raise RuntimeError("本机 OCR 没有识别到文字")
    return text


def auto_fallback_provider() -> str | None:
    """按操作系统选择免费离线的本机识别：Windows 自带 OCR / macOS Vision。"""
    if platform.system() == "Windows":
        return "windows-ocr"
    if platform.system() == "Darwin":
        return "macos-ocr"
    return None


def fallback_target_for(provider: str) -> str | None:
    """回退目标：config.json 的 fallback_provider 优先；设为 none/off/"" 可关闭；默认按系统自动选。"""
    cfg = user_config().get("fallback_provider")
    if isinstance(cfg, str):
        cfg = cfg.strip()
        if not cfg or cfg.lower() in ("none", "off", "disable", "false"):
            return None
        return cfg
    target = auto_fallback_provider()
    if target == provider:
        return None
    return target


def is_transient_error(message: str) -> bool:
    """瞬时失败（值得重试一次）：网络连不上、空响应、限流 429、5xx、响应格式异常。"""
    return (
        "无法连接" in message
        or "未返回内容" in message
        or "响应格式异常" in message
        or "返回错误 429" in message
        or "返回错误 5" in message
    )


def recognize(
    args: argparse.Namespace,
    provider: str,
    definition: dict[str, Any],
) -> tuple[str, dict[str, Any], str | None]:
    """调用选中的提供商；瞬时失败重试一次，仍失败自动回退到本机识别。

    返回 (text, usage, fallback_reason)。
    """
    if definition.get("type") == "local":
        text = run_local_provider(provider, definition, args.images[0], args.language)
        return text, {}, None

    def attempt() -> tuple[str, dict[str, Any]]:
        api_key = api_key_for(provider, args.api_key)
        if not api_key:
            api_key = (definition.get("auth") or {}).get("value")
        if not api_key:
            raise RuntimeError(
                f"提供商 {provider} 缺少 API Key：设置环境变量 {definition.get('env_key', 'VISION_HUB_API_KEY')}，"
                f"或在 {user_config_dir() / '.env'}、{config_file()} 中配置"
            )
        definition["base_url"] = base_url_for(provider, args.base_url)
        if not definition.get("base_url"):
            raise RuntimeError(f"提供商 {provider} 没有配置 base_url")
        image_urls = [image_to_data_url(item) for item in args.images]
        text, usage = call_openai_provider(
            provider,
            definition,
            api_key,
            image_urls,
            args.prompt,
            args.max_tokens,
            args.temperature,
            args.timeout,
        )
        if not text:
            raise RuntimeError(f"{provider} 未返回内容")
        return text, usage

    try:
        text, usage = attempt()
        return text, usage, None
    except RuntimeError as error:
        if is_transient_error(str(error)):
            print(f"⚠ {provider} 瞬时失败，重试一次…", file=sys.stderr)
            time.sleep(2)
            try:
                text, usage = attempt()
                return text, usage, None
            except RuntimeError as retry_error:
                error = retry_error
        if args.no_fallback or fallback_target_for(provider) is None:
            raise
        target = fallback_target_for(provider)
        reason = f"{error}"
        try:
            parts = []
            for image in args.images:
                parts.append(run_local_provider(target, provider_def(target), image, args.language))
            text = "\n\n".join(parts)
            print(
                f"⚠ {provider} 不可用，已自动回退到 {target}（原因：{reason}；加 --no-fallback 可关闭）",
                file=sys.stderr,
            )
            return text, {}, reason
        except RuntimeError as fallback_error:
            raise RuntimeError(
                f"{error}；且回退到 {target} 也失败: {fallback_error}"
            ) from error


def list_providers() -> list[dict[str, Any]]:
    reg = registry().get("providers", {})
    cfg = user_config()
    rows = []
    for name, definition in reg.items():
        merged = dict(definition)
        merged.update(cfg.get("providers", {}).get(name, {}) or {})
        key = api_key_for(name, None)
        rows.append(
            {
                "provider": name,
                "label": merged.get("label", name),
                "type": merged.get("type", "openai"),
                "model": merged.get("model", ""),
                "base_url": merged.get("base_url", ""),
                "key_set": bool(key),
                "note": merged.get("note", ""),
            }
        )
    return rows


def set_config(keys: list[str]) -> None:
    cfg = user_config()
    for item in keys:
        if "=" not in item:
            raise RuntimeError(f"--set 需要 key=value 格式: {item}")
        raw_key, raw_value = item.split("=", 1)
        parts = [p for p in raw_key.strip().split(".") if p]
        if not parts:
            raise RuntimeError(f"无效配置键: {raw_key}")
        target = cfg
        for part in parts[:-1]:
            target = target.setdefault(part, {})
            if not isinstance(target, dict):
                raise RuntimeError(f"配置路径被占用: {'.'.join(parts[:-1])}")
        target[parts[-1]] = raw_value.strip()
    write_json(config_file(), cfg)
    print(f"已写入 {config_file()}")


def main() -> int:
    ensure_utf8()
    parser = argparse.ArgumentParser(
        description="visionDS: 用可配置的多家视觉模型识别图片，失败时自动回退到本机 OCR",
    )
    parser.add_argument("images", nargs="*", help="本地图片路径、URL 或 data URI")
    parser.add_argument("--provider", "-P", help="提供商: mimo / mimo-token-plan / glm / ark / dashscope / moonshot / openai / ollama / lmstudio / windows-ocr / macos-ocr")
    parser.add_argument("--model", "-m", help="覆盖模型名或接入点")
    parser.add_argument("--api-key", help="覆盖 API Key")
    parser.add_argument("--base-url", help="覆盖接口地址")
    parser.add_argument("--prompt", "-p", default="请详细描述这张图片的内容，包括主体、场景、文字和关键细节。")
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--language", help="本机 OCR 语言（Windows）")
    parser.add_argument("--no-fallback", action="store_true", help="AI 提供商失败时不要回退到本机识别")
    parser.add_argument("--list", action="store_true", help="列出所有提供商及配置状态")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="持久化配置，如 --set default_provider=glm --set providers.glm.model=glm-4.7v")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = parser.parse_args()

    if args.set:
        if args.images:
            print(
                f"警告: 忽略多余参数（--set 一次只接受一个 KEY=VALUE，多个请重复 --set）: {' '.join(args.images)}",
                file=sys.stderr,
            )
        try:
            set_config(args.set)
        except RuntimeError as error:
            print(f"错误: {error}", file=sys.stderr)
            return 1
        return 0

    if args.list:
        rows = list_providers()
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
            return 0
        for row in rows:
            key_state = "已配置" if row["key_set"] else "未配置"
            print(f"{row['provider']:<16} {row['label']}")
            print(f"  model : {row['model'] or '-'}")
            print(f"  url   : {row['base_url'] or '-'}")
            print(f"  key   : {key_state}  {row['note']}")
        return 0

    if not args.images:
        print("用法: vision_hub.py <图片> [--provider 名称] [--model 模型] [--list]", file=sys.stderr)
        return 2

    try:
        provider = args.provider or default_provider()
        definition = dict(provider_def(provider))
        if args.model:
            definition["model"] = args.model
        if args.base_url:
            definition["base_url"] = args.base_url
        text, usage, fallback_reason = recognize(args, provider, definition)
    except (RuntimeError, ValueError) as error:
        print(f"错误: {error}", file=sys.stderr)
        return 1

    if args.json:
        print(
            json.dumps(
                {
                    "provider": provider,
                    "model": definition.get("model", ""),
                    "text": text,
                    "usage": usage,
                    "fallback": bool(fallback_reason),
                    "fallback_reason": fallback_reason,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(text)
        total = usage.get("total_tokens")
        if total is not None:
            print(f"{provider} 用量: {total} tokens", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
