# AI Image Renamer (AI 图片重命名工具)

[中文](#chinese) | [English](#english)

<a id="chinese"></a>

## 中文版

一个 Python 脚本，可根据图片内容使用 AI 视觉模型批量重命名图片文件。

### 功能

- **通用识别**: 可重命名任意图片文件 (`.png`, `.jpg`, `.jpeg`, `.webp` 等)。
- **AI 驱动**: 可接入任意兼容 OpenAI 格式的视觉模型（如 GPT-4o, Gemini, DeepSeek, Claude 等）进行重命名。
- **高度可配置**: 所有参数均可通过 `config.toml` 或 `.env` 文件灵活配置。
- **高效稳定**: 支持并发处理，并内置稳健的 API 速率限制处理与重试机制。

### 环境要求

- [uv](https://github.com/astral-sh/uv) (推荐)
- Python 3.8+ (如果使用 uv，它会自动帮你安装和管理合适的 Python 版本)
- 一个 AI 视觉模型的 API 密钥。

### 安装与配置

1.  **克隆仓库:**

    ```bash
    git clone https://github.com/Elflare/rename-emojis.git
    cd rename-emojis
    ```

2.  **安装依赖:**
    此命令会自动创建虚拟环境并同步所有依赖（基于 `uv.lock`）。

    ```bash
    uv sync
    ```

3.  **配置:**
    - 项目的默认配置存储在 `config.toml` 文件中。
    - **将 `.env.example` 文件复制并重命名为 `.env`**。
    - 在新的 `.env` 文件中填入你的 `API_KEY`。
    - 你可以在 `config.toml` 中修改默认设置，也可以在 `.env` 中覆盖它们。

### ⚙️ 配置参数说明 (config.toml)

| 参数项                  | 默认值示例                                                                                                                                                                                     | 说明                                      |
| :---------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------- |
| **api_key**             | (在 .env 中设置)                                                                                                                                                                               | 你的 API 密钥 (必填)                      |
| **api_base_url**        | `https://api.openai.com/v1`                                                                                                                                                                    | API 基础地址，根据服务商填写              |
| **model_name**          | `gemini-2.5-flash`                                                                                                                                                                             | 使用的模型名称                            |
| **max_tokens**          | `2048`                                                                                                                                                                                         | 最大输出长度，过小会导致响应被截断        |
| **image_directory**     | `./images`                                                                                                                                                                                     | 需要重命名的图片文件夹路径 (支持绝对路径) |
| **concurrent_requests** | `2`                                                                                                                                                                                            | 同时并发处理的图片数量，根据 API 限频调整 |
| **retry_delay**         | `30`                                                                                                                                                                                           | 遇到 API 限流 (429) 时等待的秒数          |
| **proxy_url**           | `http://127.0.0.1:7890`                                                                                                                                                                        | (可选) 网络代理地址                       |
| **prompt**              | `你是一个表情包命名助手。请仔细观察这张图片所表达的情感，用2到5个字的中文短语概括其情感，用于作为文件名。要求：1. 只要中文。2. 不要标点符号。3. 不要序号。4. 只要一个结果。（如：大笑、思考）` | 发给大模型的 prompt                       |

### 使用

直接使用 `uv run` 运行脚本，它会自动使用虚拟环境，无需手动激活：

```bash
uv run rename_emotions.py
```

<a id="english"></a>

---

## English Version

A Python script that uses AI vision models to batch rename image files based on their content.

### Features

- **Universal Recognition**: Can rename any image file (`.png`, `.jpg`, `.jpeg`, `.webp`, etc.).
- **AI-Powered**: Compatible with any OpenAI-format vision models (such as GPT-4o, Gemini, DeepSeek, Claude, etc.) for renaming.
- **Highly Configurable**: All parameters can be flexibly configured via `config.toml` or `.env` files.
- **Efficient and Stable**: Supports concurrent processing with built-in robust API rate limit handling and retry mechanisms.

### Requirements

- [uv](https://github.com/astral-sh/uv) (Recommended)
- Python 3.8+ (If using uv, it will automatically install and manage the appropriate Python version for you)
- An API key for an AI vision model.

### Installation & Configuration

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/Elflare/rename-emojis.git
    cd rename-emojis
    ```

2.  **Install dependencies:**
    This command will automatically create a virtual environment and sync all dependencies (based on `uv.lock`).

    ```bash
    uv sync
    ```

3.  **Configuration:**
    - The project's default configuration is stored in the `config.toml` file.
    - **Copy the `.env.example` file and rename it to `.env`**.
    - Fill in your `API_KEY` in the new `.env` file.
    - You can modify the default settings in `config.toml` or override them in `.env`.

### ⚙️ Configuration Parameters (config.toml)

| Parameter               | Default Example                                                                                                                                                                                                                                                                                                                                                  | Description                                                                  |
| :---------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------- |
| **api_key**             | (Set in .env)                                                                                                                                                                                                                                                                                                                                                    | Your API key (Required)                                                      |
| **api_base_url**        | `https://api.openai.com/v1`                                                                                                                                                                                                                                                                                                                                      | API base URL, fill according to your provider                                |
| **model_name**          | `gemini-2.5-flash`                                                                                                                                                                                                                                                                                                                                               | Model name to use                                                            |
| **max_tokens**          | `2048`                                                                                                                                                                                                                                                                                                                                                           | Maximum output length                                                        |
| **image_directory**     | `./images`                                                                                                                                                                                                                                                                                                                                                       | Path to the image folder to rename (Supports absolute path)                  |
| **concurrent_requests** | `2`                                                                                                                                                                                                                                                                                                                                                              | Number of concurrent image processing tasks, adjust based on API rate limits |
| **retry_delay**         | `30`                                                                                                                                                                                                                                                                                                                                                             | Delay in seconds when hitting API rate limits (429)                          |
| **proxy_url**           | `http://127.0.0.1:7890`                                                                                                                                                                                                                                                                                                                                          | (Optional) Network proxy address                                             |
| **prompt**              | `You are an emoji naming assistant. Please carefully observe the emotion expressed in this image and summarize it with a 2 to 5 word English phrase for use as a file name. Requirements: 1. English only. 2. No punctuation. 3. No numbering. 4. Only one result. 5. Separate multiple words with underscores. (e.g.: laughing_hard, deep_thought, happy_face)` | Prompt sent to the large language model                                      |

### Usage

Run the script directly using `uv run`, which automatically uses the virtual environment without manual activation:

```bash
uv run rename_emotions.py
```
