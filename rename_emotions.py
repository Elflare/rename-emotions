import asyncio
import base64
import mimetypes
import os
import re
import sys
import argparse  # [新增] 引入参数解析库
from pathlib import Path
from typing import Optional, Dict, TypeVar

import aiohttp
from dotenv import load_dotenv

# 兼容 Python 版本导入 TOML 解析器
try:
    import tomllib
except ImportError:
    import tomli as tomllib


# --- 1. 配置加载 ---
def load_config():
    load_dotenv()

    config_path = Path("config.toml")
    # 如果没有配置文件，给一个默认空字典
    if not config_path.exists():
        config = {}
    else:
        with open(config_path, "rb") as f:
            config = tomllib.load(f)

    T = TypeVar("T")

    def get_val(key: str, default=None, cast=str):
        env_val = os.getenv(key.upper())
        val = env_val if env_val is not None else config.get(key, default)
        try:
            return cast(val) if val is not None else None
        except (ValueError, TypeError):
            return default

    raw_base_url = get_val("api_base_url", "https://api.openai.com/v1")
    clean_base_url = (
        raw_base_url.rstrip("/") if raw_base_url else "https://api.openai.com/v1"
    )

    final_config = {
        "api_key": get_val("api_key"),
        "api_base_url": clean_base_url,
        "model_name": get_val("model_name", "gpt-4o"),
        "proxy_url": get_val("proxy_url"),
        "concurrent_requests": get_val("concurrent_requests", 5, int),
        "retry_delay": get_val("retry_delay", 2, int),
        "image_directory": get_val("image_directory", Path("./emotions"), cast=Path),
        "supported_extensions": tuple(
            config.get("supported_extensions", [".png", ".jpg", ".jpeg", ".webp"])
        ),
        "max_tokens": get_val("max_tokens", 2048, int),
        "prompt": get_val(
            "prompt",
            "你是一个表情包命名助手。请仔细观察这张图片所表达的情感，用2到5个字的中文短语概括其情感，用于作为文件名。要求：1. 只要中文。2. 不要标点符号。3. 不要序号。4. 只要一个结果。（如：大笑、思考）",
        ),
    }
    return final_config


CONFIG = load_config()


# --- 2. 文本清洗 ---
def clean_description(text: str) -> Optional[str]:
    if not text:
        return None
    text = text.strip().strip("\"'")
    first_line = text.split("\n")[0].strip()
    clean_line = re.sub(r"^\d+[\.\:：]\s*", "", first_line)
    clean_line = re.sub(r"[。，！!.]+$", "", clean_line)
    return clean_line.strip() or None


# --- 3. 核心处理逻辑 ---
async def process_image(
    session: aiohttp.ClientSession,
    image_path: Path,
    semaphore: asyncio.Semaphore,
    stats: Dict[str, int],
):
    async with semaphore:
        print(f"⏳ 正在分析: {image_path.name}")

        try:
            # 读取图片
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
                            {
                                "type": "text",
                                "text": CONFIG["prompt"],
                            },
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
                        # 处理非 200 响应
                        if response.status != 200:
                            error_text = await response.text()
                            if response.status == 429:
                                wait_time = CONFIG["retry_delay"] * (2**attempt)
                                print(
                                    f"⚠️  速率限制 {image_path.name}. 等待 {wait_time} 秒..."
                                )
                                await asyncio.sleep(wait_time)
                                continue
                            elif response.status == 401:
                                print(
                                    f"⛔ 鉴权失败 {image_path.name}: API Key 无效或过期"
                                )
                                stats["fail"] += 1
                                return
                            else:
                                print(
                                    f"❌ API 报错 {response.status} ({image_path.name}): {error_text[:200]}"
                                )
                                stats["fail"] += 1
                                return

                        # 处理 200 响应
                        result = await response.json()
                        try:
                            # 更加健壮的 JSON 解析
                            choices = result.get("choices", [])
                            if not choices:
                                print(
                                    f"❌ 失败 {image_path.name}: API 返回了空 choices"
                                )
                                stats["fail"] += 1
                                return

                            first_choice = choices[0]
                            finish_reason = first_choice.get("finish_reason")
                            message = first_choice.get("message", {})
                            raw_text = message.get("content")

                            # ✅ 专门检测 finish_reason: length
                            if not raw_text and finish_reason == "length":
                                print(
                                    f"❌ 失败 {image_path.name}: Token 长度不足，被截断 (max_tokens太小)"
                                )
                                stats["fail"] += 1
                                return

                            if not raw_text:
                                print(
                                    f"❌ 失败 {image_path.name}: 模型返回内容为空 (原因: {finish_reason})"
                                )
                                stats["fail"] += 1
                                return

                            desc = clean_description(raw_text)
                            if desc:
                                if rename_file(image_path, desc):
                                    stats["success"] += 1
                                else:
                                    stats["fail"] += 1  # 重命名过程失败
                                return
                            else:
                                print(
                                    f"⚠️ 清洗后内容为空 {image_path.name} (原内容: {raw_text})"
                                )
                                stats["fail"] += 1
                                return

                        except Exception as e:
                            print(
                                f"❌ 解析异常 {image_path.name}: {e} | 返回数据: {result}"
                            )
                            stats["fail"] += 1
                            return

                except asyncio.TimeoutError:
                    print(f"⌛ 请求超时 {image_path.name} (请检查网络或代理)")
                    # 如果最后一次重试也超时
                    if attempt == 2:
                        stats["fail"] += 1
                        break
                except aiohttp.ClientError as e:
                    print(f"🔌 网络连接错误 {image_path.name}: {e}")
                    if attempt == 2:
                        stats["fail"] += 1
                        break
                except Exception as e:
                    print(f"💥 未知错误 {image_path.name}: {type(e).__name__} - {e}")
                    if attempt == 2:
                        stats["fail"] += 1
                        break

        except Exception as e:
            print(f"💀 严重错误 {image_path.name}: {e}")
            stats["fail"] += 1


# --- 4. 文件重命名 ---
def rename_file(original_path: Path, description: str) -> bool:
    safe_desc = re.sub(r'[\\/*?:"<>|\n\r]', "", description).strip()
    if not safe_desc:
        return False

    new_filename = f"{safe_desc}{original_path.suffix}"
    new_path = original_path.with_name(new_filename)

    if new_path.resolve() == original_path.resolve():
        print(f"⏹️  名称未变: {original_path.name}")
        return True  # 算作处理成功

    counter = 1
    while new_path.exists():
        new_filename = f"{safe_desc}_{counter}{original_path.suffix}"
        new_path = original_path.with_name(new_filename)
        counter += 1

    try:
        original_path.rename(new_path)
        print(f"✅ 重命名成功: {original_path.name} -> {new_path.name}")
        return True
    except OSError as e:
        print(f"❌ 重命名文件系统错误 {original_path.name}: {e}")
        return False


# --- 5. 主流程 ---
async def main():
    # --- [修改] 命令行参数解析 ---
    parser = argparse.ArgumentParser(description="AI 表情包重命名工具")
    
    # 支持 -d 或 --dir 参数
    parser.add_argument(
        "-d", "--dir",
        type=Path,
        help="指定图片目录 (Flag方式，例如: -d D:\\images)"
    )
    
    # 支持直接输入路径 (位置参数)
    parser.add_argument(
        "input_path", 
        nargs="?", 
        type=Path, 
        help="指定图片目录 (直接输入，例如: D:\\images)"
    )

    args = parser.parse_args()

    # 优先级逻辑：
    # 1. 命令行 -d / --dir
    # 2. 命令行 直接路径
    # 3. 配置文件中的 image_directory
    if args.dir:
        directory = args.dir
    elif args.input_path:
        directory = args.input_path
    else:
        directory = CONFIG["image_directory"]
    # -----------------------------

    if not CONFIG["api_key"]:
        print("🔴 错误: API_KEY 未配置。")
        return

    # 检查目录是否存在
    if not directory.exists():
        print(f"🔴 错误: 目录 '{directory}' 不存在。")
        return

    print(f"📂 扫描目录: {directory.resolve()}")

    files = [
        f
        for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() in CONFIG["supported_extensions"]
    ]

    if not files:
        print("🟠 未找到图片文件。")
        return

    print(f"🚀 发现 {len(files)} 个文件。准备处理...")

    semaphore = asyncio.Semaphore(CONFIG["concurrent_requests"])
    # ✅ 设置明确的超时时间 (30秒)
    timeout = aiohttp.ClientTimeout(total=30)

    # 初始化统计数据
    stats = {"success": 0, "fail": 0}

    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = [
            process_image(session, img_path, semaphore, stats) for img_path in files
        ]
        await asyncio.gather(*tasks)

    print("\n" + "=" * 30)
    print(f"📊 统计报告")
    print(f"✅ 成功: {stats['success']}")
    print(f"❌ 失败: {stats['fail']}")
    print("=" * 30 + "\n")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ 用户手动停止。")
