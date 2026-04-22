import argparse
import asyncio
import base64
import locale
import mimetypes
import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional

import aiohttp
from dotenv import load_dotenv

try:
    import tomllib
except ImportError:
    import tomli as tomllib


CONFIG_PATH = Path("config.toml")
LOCAL_CONFIG_PATH = Path("config.local.toml")
PROMPTS_DIR = Path("prompts")
LOCAL_PROMPTS_DIR = Path("prompts.local")
DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = {"zh", "en"}
ENV_VAR_MAP = {
    "api_key": "API_KEY",
    "proxy_url": "PROXY_URL",
}

MESSAGES = {
    "zh": {
        "app_description": "AI 图片重命名工具",
        "help_dir": "指定图片目录 (例如: -d D:\\images)",
        "help_input_path": "指定图片目录 (直接输入，例如: D:\\images)",
        "help_profile": "使用某个 profile 的 prompt，并持久化到 config.local.toml",
        "help_prompt_file": "使用指定 prompt 文件，并持久化到 config.local.toml",
        "help_lang": "设置界面语言为 zh 或 en，并持久化到 config.local.toml",
        "error_profile_prompt_conflict": "--profile 和 --prompt-file 不能同时使用",
        "error_lang_invalid": "错误: 不支持的语言 '{lang}'，只支持 zh 或 en。",
        "error_profile_missing": "错误: profile '{profile}' 不存在。",
        "error_prompt_file_missing": "错误: prompt 文件不存在: {path}",
        "error_api_key_missing": "错误: API_KEY 未配置。",
        "error_directory_missing": "错误: 目录 '{directory}' 不存在。",
        "error_no_images": "未找到图片文件。",
        "error_auth": "鉴权失败 {name}: API Key 无效或过期",
        "error_api": "API 报错 {status} ({name}): {detail}",
        "error_empty_choices": "失败 {name}: API 返回了空 choices",
        "error_token_length": "失败 {name}: Token 长度不足，被截断 (max_tokens 太小)",
        "error_empty_content": "失败 {name}: 模型返回内容为空 (原因: {reason})",
        "error_clean_empty": "清洗后内容为空 {name} (原内容: {content})",
        "error_timeout": "请求超时 {name} (请检查网络或代理)",
        "error_network": "网络连接错误 {name}: {error}",
        "error_unknown": "未知错误 {name}: {error_type} - {error}",
        "error_fatal": "严重错误 {name}: {error}",
        "error_filesystem": "重命名文件系统错误 {name}: {error}",
        "language_initialized": "首次运行，已根据系统语言初始化界面语言为: {lang}",
        "language_switched": "已切换界面语言并持久化到 config.local.toml: {lang}",
        "prompt_switched": "已切换并持久化到 config.local.toml 的 {label}: {path}",
        "persist_failed": "已切换 {label}，但未能写回 config.local.toml: {error}",
        "scan_directory": "扫描目录: {directory}",
        "current_language": "当前界面语言: {lang}",
        "current_prompt": "当前 prompt: {source}",
        "files_found": "发现 {count} 个文件。准备处理...",
        "processing": "正在分析: {name}",
        "rate_limit": "速率限制 {name}. 等待 {seconds} 秒...",
        "rename_success": "重命名成功: {old} -> {new}",
        "rename_unchanged": "名称未变: {name}",
        "report_title": "统计报告",
        "report_success": "成功: {count}",
        "report_fail": "失败: {count}",
        "label_profile": "profile {profile}",
        "label_prompt_file": "prompt 文件",
        "label_language": "界面语言",
        "lang_zh": "中文",
        "lang_en": "英文",
    },
    "en": {
        "app_description": "AI Image Renamer",
        "help_dir": "Specify image directory (e.g. -d D:\\images)",
        "help_input_path": "Specify image directory directly (e.g. D:\\images)",
        "help_profile": "Use a profile prompt and persist it into config.local.toml",
        "help_prompt_file": "Use a specific prompt file and persist it into config.local.toml",
        "help_lang": "Set UI language to zh or en and persist it into config.local.toml",
        "error_profile_prompt_conflict": "--profile and --prompt-file cannot be used together",
        "error_lang_invalid": "Error: unsupported language '{lang}'. Only zh and en are supported.",
        "error_profile_missing": "Error: profile '{profile}' does not exist.",
        "error_prompt_file_missing": "Error: prompt file does not exist: {path}",
        "error_api_key_missing": "Error: API_KEY is not configured.",
        "error_directory_missing": "Error: directory '{directory}' does not exist.",
        "error_no_images": "No image files were found.",
        "error_auth": "Authentication failed {name}: API key is invalid or expired",
        "error_api": "API error {status} ({name}): {detail}",
        "error_empty_choices": "Failed {name}: API returned empty choices",
        "error_token_length": "Failed {name}: response was truncated (max_tokens too small)",
        "error_empty_content": "Failed {name}: model returned empty content (reason: {reason})",
        "error_clean_empty": "Sanitized content is empty for {name} (raw: {content})",
        "error_timeout": "Request timed out for {name} (check network or proxy)",
        "error_network": "Network error for {name}: {error}",
        "error_unknown": "Unknown error for {name}: {error_type} - {error}",
        "error_fatal": "Fatal error for {name}: {error}",
        "error_filesystem": "Filesystem rename error for {name}: {error}",
        "language_initialized": "First run detected system language and initialized UI language to: {lang}",
        "language_switched": "Switched UI language and persisted it to config.local.toml: {lang}",
        "prompt_switched": "Switched and persisted {label} to config.local.toml: {path}",
        "persist_failed": "Switched {label}, but failed to write config.local.toml: {error}",
        "scan_directory": "Scanning directory: {directory}",
        "current_language": "Current UI language: {lang}",
        "current_prompt": "Current prompt: {source}",
        "files_found": "Found {count} files. Starting...",
        "processing": "Processing: {name}",
        "rate_limit": "Rate limited for {name}. Waiting {seconds} seconds...",
        "rename_success": "Renamed: {old} -> {new}",
        "rename_unchanged": "Name unchanged: {name}",
        "report_title": "Summary",
        "report_success": "Success: {count}",
        "report_fail": "Fail: {count}",
        "label_profile": "profile {profile}",
        "label_prompt_file": "prompt file",
        "label_language": "UI language",
        "lang_zh": "Chinese",
        "lang_en": "English",
    },
}


def load_toml_file(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def format_toml_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def upsert_local_config_value(key: str, value: str):
    content = ""
    if LOCAL_CONFIG_PATH.exists():
        content = LOCAL_CONFIG_PATH.read_text(encoding="utf-8")

    replacement = f"{key} = {format_toml_string(value)}"
    pattern = re.compile(rf"^{re.escape(key)}\s*=.*$", re.MULTILINE)

    if pattern.search(content):
        updated = pattern.sub(replacement, content, count=1)
    else:
        updated = content.rstrip()
        if updated:
            updated += "\n"
        updated += replacement + "\n"

    if not updated.endswith("\n"):
        updated += "\n"
    LOCAL_CONFIG_PATH.write_text(updated, encoding="utf-8")


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def to_local_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd()))
    except ValueError:
        return str(path.resolve())


def detect_system_language() -> str:
    candidates = []
    for getter in (locale.getlocale,):
        try:
            value = getter()
        except ValueError:
            continue
        if isinstance(value, tuple):
            candidates.append(value[0] or "")
        elif isinstance(value, str):
            candidates.append(value)

    for env_key in ("LC_ALL", "LANG", "LANGUAGE"):
        candidates.append(os.getenv(env_key, ""))

    normalized = " ".join(candidates).lower()
    return "zh" if "zh" in normalized or "chinese" in normalized else "en"


def normalize_language(value: Optional[str]) -> str:
    if not value:
        return DEFAULT_LANGUAGE
    lowered = value.lower()
    if lowered.startswith("zh"):
        return "zh"
    return "en"


def is_supported_language(value: str) -> bool:
    lowered = value.lower()
    return lowered.startswith("zh") or lowered.startswith("en")


def get_prompt_candidates(profile: str, language: str):
    suffixes = [f"{profile}.{language}.txt", f"{profile}.txt"]
    for folder in (LOCAL_PROMPTS_DIR, PROMPTS_DIR):
        for suffix in suffixes:
            yield (folder / suffix).resolve()


def find_profile_prompt(profile: str, language: str) -> Optional[Path]:
    for candidate in get_prompt_candidates(profile, language):
        if candidate.exists():
            return candidate
    return None


def load_prompt_text(prompt_path: Path) -> str:
    return prompt_path.read_text(encoding="utf-8").strip()


def build_runtime_config():
    load_dotenv()

    base_config = load_toml_file(CONFIG_PATH)
    local_config = load_toml_file(LOCAL_CONFIG_PATH)
    merged_config = {**base_config, **local_config}

    def get_val(key: str, default=None, cast=str):
        env_name = ENV_VAR_MAP.get(key)
        env_val = os.getenv(env_name) if env_name else None
        val = env_val if env_val is not None else merged_config.get(key, default)
        try:
            return cast(val) if val is not None else None
        except (ValueError, TypeError):
            return default

    raw_language = get_val("language")
    language = normalize_language(raw_language) if raw_language else detect_system_language()

    raw_base_url = get_val("api_base_url", "https://api.openai.com/v1")
    clean_base_url = raw_base_url.rstrip("/") if raw_base_url else "https://api.openai.com/v1"
    default_profile = get_val("default_profile", "emotion")
    prompt_file_value = get_val("current_prompt_file")

    prompt_source = "config.toml:prompt"
    prompt = get_val("prompt")

    prompt_file = resolve_path(prompt_file_value) if prompt_file_value else None
    if prompt_file and prompt_file.exists():
        prompt = load_prompt_text(prompt_file)
        prompt_source = str(prompt_file)
    else:
        profile_prompt = find_profile_prompt(default_profile, language)
        if profile_prompt is not None:
            prompt_file = profile_prompt
            prompt = load_prompt_text(profile_prompt)
            prompt_source = str(profile_prompt)

    if not prompt:
        prompt = "Describe this image for use as a filename."
        prompt_source = "built-in fallback"

    supported_extensions = merged_config.get(
        "supported_extensions", [".png", ".jpg", ".jpeg", ".webp"]
    )

    return {
        "api_key": get_val("api_key"),
        "api_base_url": clean_base_url,
        "model_name": get_val("model_name", "gpt-4o"),
        "proxy_url": get_val("proxy_url"),
        "concurrent_requests": get_val("concurrent_requests", 5, int),
        "retry_delay": get_val("retry_delay", 2, int),
        "image_directory": get_val("image_directory", Path("./emotions"), cast=Path),
        "supported_extensions": tuple(supported_extensions),
        "max_tokens": get_val("max_tokens", 2048, int),
        "default_profile": default_profile,
        "language": language,
        "language_was_explicit": raw_language is not None,
        "current_prompt_file": prompt_file,
        "prompt": prompt,
        "prompt_source": prompt_source,
    }


CONFIG = build_runtime_config()


def t(key: str, **kwargs) -> str:
    language = CONFIG.get("language", DEFAULT_LANGUAGE)
    template = MESSAGES.get(language, MESSAGES["en"]).get(key, MESSAGES["en"][key])
    return template.format(**kwargs)


def apply_language(language: str):
    CONFIG["language"] = normalize_language(language)
    CONFIG["language_was_explicit"] = True


def initialize_language_if_needed():
    if CONFIG.get("language_was_explicit"):
        return
    detected = CONFIG["language"]
    try:
        upsert_local_config_value("language", detected)
        print(t("language_initialized", lang=t(f"lang_{detected}")))
    except OSError:
        pass
    CONFIG["language_was_explicit"] = True


def switch_language(language: str):
    normalized = normalize_language(language)
    apply_language(normalized)
    try:
        upsert_local_config_value("language", normalized)
        print(t("language_switched", lang=t(f"lang_{normalized}")))
    except OSError as e:
        print(t("persist_failed", label=t("label_language"), error=e))


def switch_prompt(prompt_path: Path, label: str):
    CONFIG.update(
        {
            "current_prompt_file": prompt_path,
            "prompt": load_prompt_text(prompt_path),
            "prompt_source": str(prompt_path),
        }
    )
    try:
        upsert_local_config_value("current_prompt_file", to_local_path(prompt_path))
        print(t("prompt_switched", label=label, path=prompt_path))
    except OSError as e:
        print(t("persist_failed", label=label, error=e))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=t("app_description"))
    parser.add_argument("-d", "--dir", type=Path, help=t("help_dir"))
    parser.add_argument("input_path", nargs="?", type=Path, help=t("help_input_path"))
    parser.add_argument("--profile", help=t("help_profile"))
    parser.add_argument("--prompt-file", type=Path, help=t("help_prompt_file"))
    parser.add_argument("--lang", help=t("help_lang"))
    return parser


def clean_description(text: str) -> Optional[str]:
    if not text:
        return None
    text = text.strip().strip("\"'")
    first_line = text.split("\n")[0].strip()
    clean_line = re.sub(r"^\d+[\.\:：\s]*", "", first_line)
    clean_line = re.sub(r"[。 ，,；;：:.]+$", "", clean_line)
    return clean_line.strip() or None


async def process_image(
    session: aiohttp.ClientSession,
    image_path: Path,
    semaphore: asyncio.Semaphore,
    stats: Dict[str, int],
):
    async with semaphore:
        print(f"⏳ {t('processing', name=image_path.name)}")

        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")

            mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
            data_url = f"data:{mime_type};base64,{base64_image}"
            url = f"{CONFIG['api_base_url']}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {CONFIG['api_key']}",
            }
            payload = {
                "model": CONFIG["model_name"],
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": CONFIG["prompt"]},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }
                ],
                "max_tokens": CONFIG["max_tokens"],
            }

            for attempt in range(3):
                try:
                    async with session.post(
                        url, headers=headers, json=payload, proxy=CONFIG["proxy_url"]
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            if response.status == 429:
                                wait_time = CONFIG["retry_delay"] * (2**attempt)
                                print(f"⚠️ {t('rate_limit', name=image_path.name, seconds=wait_time)}")
                                await asyncio.sleep(wait_time)
                                continue
                            if response.status == 401:
                                print(f"⛔ {t('error_auth', name=image_path.name)}")
                                stats["fail"] += 1
                                return

                            print(
                                f"❌ {t('error_api', name=image_path.name, status=response.status, detail=error_text[:200])}"
                            )
                            stats["fail"] += 1
                            return

                        result = await response.json()
                        choices = result.get("choices", [])
                        if not choices:
                            print(f"❌ {t('error_empty_choices', name=image_path.name)}")
                            stats["fail"] += 1
                            return

                        first_choice = choices[0]
                        finish_reason = first_choice.get("finish_reason")
                        message = first_choice.get("message", {})
                        raw_text = message.get("content")

                        if not raw_text and finish_reason == "length":
                            print(f"❌ {t('error_token_length', name=image_path.name)}")
                            stats["fail"] += 1
                            return

                        if not raw_text:
                            print(f"❌ {t('error_empty_content', name=image_path.name, reason=finish_reason)}")
                            stats["fail"] += 1
                            return

                        desc = clean_description(raw_text)
                        if not desc:
                            print(f"⚠️ {t('error_clean_empty', name=image_path.name, content=raw_text)}")
                            stats["fail"] += 1
                            return

                        if rename_file(image_path, desc):
                            stats["success"] += 1
                        else:
                            stats["fail"] += 1
                        return

                except asyncio.TimeoutError:
                    print(f"⌛ {t('error_timeout', name=image_path.name)}")
                    if attempt == 2:
                        stats["fail"] += 1
                        break
                except aiohttp.ClientError as e:
                    print(f"🔌 {t('error_network', name=image_path.name, error=e)}")
                    if attempt == 2:
                        stats["fail"] += 1
                        break
                except Exception as e:
                    print(
                        f"💥 {t('error_unknown', name=image_path.name, error_type=type(e).__name__, error=e)}"
                    )
                    if attempt == 2:
                        stats["fail"] += 1
                        break

        except Exception as e:
            print(f"💀 {t('error_fatal', name=image_path.name, error=e)}")
            stats["fail"] += 1


def rename_file(original_path: Path, description: str) -> bool:
    safe_desc = re.sub(r'[\\/*?:"<>|\n\r]', "", description).strip()
    if not safe_desc:
        return False

    new_filename = f"{safe_desc}{original_path.suffix}"
    new_path = original_path.with_name(new_filename)

    if new_path.resolve() == original_path.resolve():
        print(f"ℹ️ {t('rename_unchanged', name=original_path.name)}")
        return True

    counter = 1
    while new_path.exists():
        new_filename = f"{safe_desc}_{counter}{original_path.suffix}"
        new_path = original_path.with_name(new_filename)
        counter += 1

    try:
        original_path.rename(new_path)
        print(f"✅ {t('rename_success', old=original_path.name, new=new_path.name)}")
        return True
    except OSError as e:
        print(f"❌ {t('error_filesystem', name=original_path.name, error=e)}")
        return False


async def main():
    initialize_language_if_needed()
    parser = build_parser()
    args = parser.parse_args()

    if args.lang:
        if not is_supported_language(args.lang):
            print(t("error_lang_invalid", lang=args.lang))
            return
        requested = normalize_language(args.lang)
        switch_language(requested)
        parser = build_parser()
        args = parser.parse_args()

    if args.profile and args.prompt_file:
        parser.error(t("error_profile_prompt_conflict"))

    if args.profile:
        prompt_path = find_profile_prompt(args.profile, CONFIG["language"])
        if prompt_path is None:
            print(t("error_profile_missing", profile=args.profile))
            return
        switch_prompt(prompt_path, t("label_profile", profile=args.profile))
    elif args.prompt_file:
        prompt_path = resolve_path(str(args.prompt_file))
        if not prompt_path.exists():
            print(t("error_prompt_file_missing", path=prompt_path))
            return
        switch_prompt(prompt_path, t("label_prompt_file"))

    if args.dir:
        directory = args.dir
    elif args.input_path:
        directory = args.input_path
    else:
        directory = CONFIG["image_directory"]

    if not CONFIG["api_key"]:
        print(f"🔴 {t('error_api_key_missing')}")
        return

    if not directory.exists():
        print(f"🔴 {t('error_directory_missing', directory=directory)}")
        return

    lang_label = t(f"lang_{CONFIG['language']}")
    print(f"📂 {t('scan_directory', directory=directory.resolve())}")
    print(f"🌐 {t('current_language', lang=lang_label)}")
    print(f"🧠 {t('current_prompt', source=CONFIG['prompt_source'])}")

    files = [
        f
        for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() in CONFIG["supported_extensions"]
    ]

    if not files:
        print(f"🪹 {t('error_no_images')}")
        return

    print(f"🚀 {t('files_found', count=len(files))}")

    semaphore = asyncio.Semaphore(CONFIG["concurrent_requests"])
    timeout = aiohttp.ClientTimeout(total=180)
    stats = {"success": 0, "fail": 0}

    async with aiohttp.ClientSession(timeout=timeout) as session:
        await asyncio.gather(
            *(process_image(session, img_path, semaphore, stats) for img_path in files)
        )

    print("\n" + "=" * 30)
    print(f"📊 {t('report_title')}")
    print(f"✅ {t('report_success', count=stats['success'])}")
    print(f"❌ {t('report_fail', count=stats['fail'])}")
    print("=" * 30 + "\n")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
