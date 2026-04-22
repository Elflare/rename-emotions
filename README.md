# AI Image Renamer

[中文](#中文) | [English](#english)

## 中文

一个使用 AI 视觉模型批量重命名图片文件的 Python 脚本。

### 功能

- 支持常见图片格式批量重命名
- 兼容 OpenAI 风格视觉接口
- 支持中英文界面输出
- 支持公开默认配置与本地私有配置分层
- 支持 profile / prompt 文件切换

### 配置结构

项目现在采用四层配置：

1. `config.toml`
项目默认配置，适合提交到 GitHub。

2. `config.local.toml`
你自己的本地覆盖配置，已被 `.gitignore` 忽略，不会被提交。

3. `.env`
只放敏感信息，比如 `API_KEY`，已被 `.gitignore` 忽略，不会被提交。

4. 命令行参数
优先级最高。

实际优先级：

```text
命令行参数 > config.local.toml > config.toml
```

### Prompt 结构

- `prompts/`
仓库公开的默认 prompt，可以提交到 GitHub。

- `prompts.local/`
你自己的私有 prompt，已被 `.gitignore` 忽略，不会被提交。

profile 查找顺序：

```text
prompts.local/<profile>.<lang>.txt
prompts.local/<profile>.txt
prompts/<profile>.<lang>.txt
prompts/<profile>.txt
```

### 安装

```bash
git clone https://github.com/Elflare/rename-emotions.git
cd rename-emotions
uv sync
```

### 配置

1. 复制 `.env.example` 为 `.env`
2. 在 `.env` 中填写 `API_KEY`
3. 按需修改 `config.local.toml`

`config.local.toml` 示例：

```toml
model_name = "qwen3.5-122b-a10b"
image_directory = "D:/images"
current_prompt_file = "prompts.local/image.txt"
```

`.env` 示例：

```env
API_KEY="your_api_key_here"
```

说明：

- `.env` 只用于 `API_KEY`
- `PROXY_URL` 也可放 `.env`
- 当前代码中，只有 `API_KEY` 和 `PROXY_URL` 会从 `.env` 读取
- 其他普通配置不要放 `.env`
- 普通配置统一写在 `config.toml` 或 `config.local.toml`

### 语言

- 支持 `zh` 和 `en`
- 第一次运行时，如果未配置 `language`，脚本会检测系统语言
- 系统语言是中文则默认写入 `zh`
- 其他情况默认写入 `en`
- 检测结果会持久化到 `config.local.toml`

你也可以手动切换：

```bash
uv run rename_emotions.py --lang zh
uv run rename_emotions.py --lang en
```

### 使用

直接运行：

```bash
uv run rename_emotions.py
```

指定目录：

```bash
uv run rename_emotions.py --dir D:/images
uv run rename_emotions.py D:/images
```

切换 profile，并持久化到 `config.local.toml`：

```bash
uv run rename_emotions.py --profile emotion
uv run rename_emotions.py --profile image
```

指定 prompt 文件，并持久化到 `config.local.toml`：

```bash
uv run rename_emotions.py --prompt-file prompts/image.en.txt
uv run rename_emotions.py --prompt-file prompts.local/image.txt
```

### 防止泄露个人配置

以下内容不会被 push：

- `.env`
- `config.local.toml`
- `prompts.local/`

因此你的这些内容默认不会上传到 GitHub：

- API Key
- 本地图片目录
- 当前选择的 prompt
- 私人 prompt 内容
- 个人语言偏好

但仍然有一条硬规则：

- 不要把密钥写进 `config.toml`
- 不要把密钥写进 `config.local.toml`
- 不要把私人 prompt 写进 `prompts/`

## English

A Python script that uses AI vision models to batch rename image files.

### Features

- Batch rename common image formats
- Works with OpenAI-style vision APIs
- Bilingual CLI output in Chinese and English
- Layered shared and local configuration
- Switchable profiles and prompt files

### Configuration Layout

The project now uses four layers:

1. `config.toml`
Shared default config that is safe to commit.

2. `config.local.toml`
Your private local overrides. This file is ignored by Git.

3. `.env`
Sensitive values only, such as `API_KEY`. This file is ignored by Git.

4. Command-line arguments
Highest priority.

Priority order:

```text
command line > config.local.toml > config.toml
```

### Prompt Layout

- `prompts/`
Public default prompts that can be committed.

- `prompts.local/`
Your private prompts. This directory is ignored by Git.

Profile lookup order:

```text
prompts.local/<profile>.<lang>.txt
prompts.local/<profile>.txt
prompts/<profile>.<lang>.txt
prompts/<profile>.txt
```

### Install

```bash
git clone https://github.com/Elflare/rename-emotions.git
cd rename-emotions
uv sync
```

### Configuration

1. Copy `.env.example` to `.env`
2. Put your `API_KEY` into `.env`
3. Adjust `config.local.toml` as needed

Example `config.local.toml`:

```toml
model_name = "qwen3.5-122b-a10b"
image_directory = "D:/images"
current_prompt_file = "prompts.local/image.txt"
```

Example `.env`:

```env
API_KEY="your_api_key_here"
```

Notes:

- `.env` is only for `API_KEY`
- `PROXY_URL` may also be stored in `.env`
- In the current implementation, only `API_KEY` and `PROXY_URL` are read from `.env`
- Do not put normal runtime settings into `.env`
- Keep normal settings in `config.toml` or `config.local.toml`

### Language

- Supported values: `zh` and `en`
- On first run, if `language` is not configured, the script detects the system language
- Chinese systems default to `zh`
- Everything else defaults to `en`
- The detected result is persisted into `config.local.toml`

You can also switch manually:

```bash
uv run rename_emotions.py --lang zh
uv run rename_emotions.py --lang en
```

### Usage

Run directly:

```bash
uv run rename_emotions.py
```

Specify a directory:

```bash
uv run rename_emotions.py --dir D:/images
uv run rename_emotions.py D:/images
```

Switch profile and persist it into `config.local.toml`:

```bash
uv run rename_emotions.py --profile emotion
uv run rename_emotions.py --profile image
```

Use a prompt file and persist it into `config.local.toml`:

```bash
uv run rename_emotions.py --prompt-file prompts/image.en.txt
uv run rename_emotions.py --prompt-file prompts.local/image.txt
```

### Prevent Leaks

These paths will not be pushed:

- `.env`
- `config.local.toml`
- `prompts.local/`

So the following personal data stays local by default:

- API keys
- Local image directories
- Current prompt selection
- Private prompt content
- Personal language preference

Still, keep these rules:

- Do not put secrets into `config.toml`
- Do not put secrets into `config.local.toml`
- Do not put private prompts into `prompts/`
