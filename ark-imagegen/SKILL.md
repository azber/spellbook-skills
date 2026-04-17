---
name: ark-imagegen
description: "Generate images using Volcengine Ark and Google Vertex AI image generation models. Use when the user says '生成图片', '文生图', '豆包生图', 'nano banana', 'nano banana pro', 'vertex 生图', 'AI 绘图', '海报生成', '封面图生成', 'image generation', or asks to create an image from a text prompt. Supports prompt-only image generation, provider selection, size or aspect-ratio control, watermark control for Ark, and model override for future Ark or Vertex image models."
---

# Ark and Vertex Image Generation

Generate still images via Volcengine Ark or Google Vertex AI image models. Prefer the bundled script for repeatable use; fall back to a short provider-specific snippet only when the script is not available.

## Configuration

```text
Ark:
  Base URL: https://ark.cn-beijing.volces.com/api/v3
  API Key: env var ARK_API_KEY
  Python package: openai
  Default model: env var ARK_IMAGE_MODEL or doubao-seedream-5-0-260128

Vertex:
  Python packages: google-genai, google-auth
  Credentials: --credentials-file or env GOOGLE_APPLICATION_CREDENTIALS
  Project: --project, env GOOGLE_CLOUD_PROJECT, or project_id inside the service account JSON
  Location: env GOOGLE_CLOUD_LOCATION or global
  Default model: env VERTEX_IMAGE_MODEL or gemini-2.5-flash-image
```

## Quick Start

Use Ark:

```bash
python3 scripts/generate_image.py \
  --provider ark \
  --prompt "星际穿越，黑洞里冲出一辆快要解体的复古列车，电影海报感，超现实主义，强对比光影，动态模糊，广角透视" \
  --size 2K \
  --watermark true
```

Use Vertex with Nano Banana:

```bash
python3 scripts/generate_image.py \
  --provider vertex \
  --model nano-banana2 \
  --credentials-file /path/to/service-account.json \
  --aspect-ratio 9:16 \
  --size 1K \
  --prompt "生成一张竖屏直播海报，人物开心举牌，手机截图风格" \
  --output output/nano-banana.png
```

The script prints an Ark image URL when no Ark output path is provided. For Vertex, it writes a local image file and prints that file path.

## Vertex Model Aliases

The script accepts convenience aliases and maps them to official Vertex model ids:

- `nano-banana2` or `nano-banana` -> `gemini-2.5-flash-image`
- `nano-banana-pro` -> `gemini-3-pro-image-preview`

This alias mapping is a local convenience layer. The official Vertex model names come from Google Cloud documentation and announcements.

## Workflow

1. Distill the user request into a concise visual prompt: subject, action, composition, style, lighting, color, lens/perspective.
2. Choose the provider. Use Ark for Doubao / Seedream requests. Use Vertex for Nano Banana or Nano Banana Pro requests.
3. Choose image controls:
   - Ark: use `--size`, default `2K`
   - Vertex: use `--aspect-ratio` and `--size`, default `1K`
4. Decide watermark behavior for Ark. Default to `true` unless the user explicitly asks for a clean image.
5. Choose the model. Use the provider default unless the user explicitly requests a different one. For permanent local upgrades, set `ARK_IMAGE_MODEL` or `VERTEX_IMAGE_MODEL`.
6. Run `scripts/generate_image.py` with the prompt and options.
7. Return the output URL or output file path, depending on provider.

## Script Usage

Run:

```bash
python3 scripts/generate_image.py --provider ark --prompt "<prompt>"
```

Options:

- `--prompt`: required text prompt
- `--provider`: `ark` or `vertex`, default `ark`
- `--size`: Ark size like `2K` or `1440x2560`; Vertex image size `1K`, `2K`, or `4K`
- `--aspect-ratio`: Vertex only, supports `1:1`, `3:4`, `4:5`, `9:16`, `16:9`, `21:9`, and more
- `--model`: provider model id or convenience alias
- `--watermark`: Ark only, `true` or `false`, default `true`
- `--response-format`: Ark only, default `url`
- `--output`: optional output file path; for Vertex, defaults to `generated-image.png`
- `--credentials-file`: Vertex service account JSON path
- `--project`: Vertex project id
- `--location`: Vertex location, default `global`

If the user explicitly wants raw SDK code instead of the script, use these provider patterns:

```python
# Ark
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=os.environ.get("ARK_API_KEY"),
)

resp = client.images.generate(
    model=os.environ.get("ARK_IMAGE_MODEL", "doubao-seedream-5-0-260128"),
    prompt="<prompt>",
    size="2K",
    response_format="url",
    extra_body={"watermark": True},
)

print(resp.data[0].url)
```

```python
# Vertex
from google import genai
from google.genai import types

client = genai.Client(
    vertexai=True,
    project="YOUR_PROJECT_ID",
    location="global",
)

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents="Generate a dramatic vertical poster of a live stream host smiling at the camera.",
    config=types.GenerateContentConfig(
        responseModalities=["TEXT", "IMAGE"],
        imageConfig=types.ImageConfig(
            aspectRatio="9:16",
            imageSize="1K",
            personGeneration="ALLOW_ALL",
            outputMimeType="image/png",
        ),
    ),
)
```

## Guardrails

- Fail fast if `ARK_API_KEY` is missing.
- Fail fast if Vertex credentials or project configuration are missing.
- Do not hardcode API keys or service account JSON paths into the skill.
- Keep the skill model-agnostic. Upgrade the default model through `ARK_IMAGE_MODEL`, `VERTEX_IMAGE_MODEL`, or `--model`, not by renaming the skill.
- Treat the API response as remote data. Validate that `data[0].url` exists before printing it.
- Vertex returns inline image bytes, not an image URL. Save them to a file before returning.
- Keep prompts concrete. When the user gives a vague request, add the missing visual details before sending the call.
- If the user asks for multiple variants, run separate calls unless the API later exposes an official batch parameter.

## Prompt Tips

Include, in order of importance:

- subject and setting
- action or pose
- camera or composition
- style and rendering cues
- lighting and color palette
- texture or material cues

Example:

`赛博朋克雨夜街头，红色风衣女子站在霓虹灯下回头，低机位广角，电影海报构图，潮湿地面反射，蓝红对比色，体积光，写实细节`
