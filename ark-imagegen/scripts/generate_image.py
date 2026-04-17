#!/usr/bin/env python3

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Optional

ARK_DEFAULT_MODEL = os.environ.get("ARK_IMAGE_MODEL", "doubao-seedream-5-0-260128")
VERTEX_DEFAULT_MODEL = os.environ.get("VERTEX_IMAGE_MODEL", "gemini-2.5-flash-image")
VERTEX_MODEL_ALIASES = {
    "nano-banana": "gemini-2.5-flash-image",
    "nano-banana2": "gemini-2.5-flash-image",
    "nano-banana-2": "gemini-2.5-flash-image",
    "nano-banana-pro": "gemini-3-pro-image-preview",
    "nanobanana-pro": "gemini-3-pro-image-preview",
}
VERTEX_DEFAULT_OUTPUT = "generated-image.png"
VERTEX_DEFAULT_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an image with a Volcengine Ark or Google Vertex AI image model."
    )
    parser.add_argument("--prompt", required=True, help="Text prompt for image generation.")
    parser.add_argument(
        "--provider",
        choices=("ark", "vertex"),
        default=os.environ.get("IMAGE_PROVIDER", "ark"),
        help="Image provider to use. Defaults to IMAGE_PROVIDER or ark.",
    )
    parser.add_argument(
        "--size",
        default=None,
        help="Ark: literal API size like 2K or 1440x2560. Vertex: image size 1K, 2K, or 4K.",
    )
    parser.add_argument(
        "--aspect-ratio",
        default=None,
        help="Vertex only. Supported values include 1:1, 3:4, 4:5, 9:16, 16:9, and 21:9.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model ID or supported alias to call. Defaults depend on provider.",
    )
    parser.add_argument(
        "--response-format",
        default="url",
        help="Ark only. Response format to request from the API.",
    )
    parser.add_argument(
        "--watermark",
        choices=("true", "false"),
        default="true",
        help="Ark only. Whether to request a watermarked image.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output file path. Required to persist Vertex output; if omitted, Vertex writes generated-image.png.",
    )
    parser.add_argument(
        "--project",
        default=os.environ.get("GOOGLE_CLOUD_PROJECT"),
        help="Vertex only. Google Cloud project id. Defaults to GOOGLE_CLOUD_PROJECT or the service account JSON project_id.",
    )
    parser.add_argument(
        "--location",
        default=VERTEX_DEFAULT_LOCATION,
        help="Vertex only. Defaults to GOOGLE_CLOUD_LOCATION or global.",
    )
    parser.add_argument(
        "--credentials-file",
        default=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
        help="Vertex only. Service account JSON file. Defaults to GOOGLE_APPLICATION_CREDENTIALS.",
    )
    return parser.parse_args()


def normalize_vertex_model(model: Optional[str]) -> str:
    if not model:
        return VERTEX_DEFAULT_MODEL
    normalized = model.strip().lower().replace("_", "-").replace(" ", "-")
    return VERTEX_MODEL_ALIASES.get(normalized, model)


def ensure_parent_dir(path: Path) -> None:
    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)


def save_url_to_file(url: str, output_path: Path) -> None:
    ensure_parent_dir(output_path)
    with urllib.request.urlopen(url) as response, open(output_path, "wb") as output_file:
        output_file.write(response.read())


def generate_with_ark(args: argparse.Namespace) -> int:
    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        print("ARK_API_KEY is not set.", file=sys.stderr)
        return 1

    try:
        from openai import OpenAI
    except ImportError:
        print("Python package 'openai' is not installed.", file=sys.stderr)
        return 1

    client = OpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=api_key,
    )
    model = args.model or ARK_DEFAULT_MODEL
    size = args.size or "2K"

    response = client.images.generate(
        model=model,
        prompt=args.prompt,
        size=size,
        response_format=args.response_format,
        extra_body={"watermark": args.watermark == "true"},
    )

    data = getattr(response, "data", None) or []
    url = getattr(data[0], "url", None) if data else None
    if not url:
        print("Image URL missing in API response.", file=sys.stderr)
        return 1

    if args.output:
        output_path = Path(args.output)
        save_url_to_file(url, output_path)
        print(output_path)
        return 0

    print(url)
    return 0


def infer_project_from_credentials(credentials_file: Path) -> Optional[str]:
    with open(credentials_file, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload.get("project_id")


def generate_with_vertex(args: argparse.Namespace) -> int:
    try:
        from google import genai
        from google.genai import types
        from google.oauth2 import service_account
    except ImportError:
        print("Python packages 'google-genai' and 'google-auth' are required for Vertex.", file=sys.stderr)
        return 1

    credentials = None
    project = args.project

    if args.credentials_file:
        credentials_path = Path(args.credentials_file).expanduser()
        if not credentials_path.exists():
            print(f"Vertex credentials file not found: {credentials_path}", file=sys.stderr)
            return 1
        credentials = service_account.Credentials.from_service_account_file(
            str(credentials_path),
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        if not project:
            project = infer_project_from_credentials(credentials_path)

    if not project:
        print(
            "Vertex project id is not set. Pass --project, set GOOGLE_CLOUD_PROJECT, or use a service account JSON with project_id.",
            file=sys.stderr,
        )
        return 1

    client = genai.Client(
        vertexai=True,
        credentials=credentials,
        project=project,
        location=args.location,
    )

    model = normalize_vertex_model(args.model)
    image_size = args.size or os.environ.get("VERTEX_IMAGE_SIZE", "1K")
    aspect_ratio = args.aspect_ratio or os.environ.get("VERTEX_IMAGE_ASPECT_RATIO")
    output_path = Path(args.output or VERTEX_DEFAULT_OUTPUT)

    config = types.GenerateContentConfig(
        responseModalities=["TEXT", "IMAGE"],
        imageConfig=types.ImageConfig(
            aspectRatio=aspect_ratio,
            imageSize=image_size,
            personGeneration="ALLOW_ALL",
            outputMimeType="image/png",
        ),
    )

    response = client.models.generate_content(
        model=model,
        contents=args.prompt,
        config=config,
    )

    candidates = getattr(response, "candidates", None) or []
    if not candidates or not getattr(candidates[0], "content", None):
        print("Vertex returned no image candidates.", file=sys.stderr)
        return 1

    text_parts: list[str] = []
    image_bytes = None
    for part in candidates[0].content.parts or []:
        if getattr(part, "text", None):
            text_parts.append(part.text)
        inline_data = getattr(part, "inline_data", None)
        if inline_data and getattr(inline_data, "mime_type", "").startswith("image/"):
            image_bytes = inline_data.data
            break

    if not image_bytes:
        if text_parts:
            print("\n".join(text_parts), file=sys.stderr)
        print("Vertex returned no image bytes.", file=sys.stderr)
        return 1

    ensure_parent_dir(output_path)
    with open(output_path, "wb") as output_file:
        output_file.write(image_bytes)

    print(output_path)
    return 0


def main() -> int:
    args = parse_args()
    if args.provider == "vertex":
        return generate_with_vertex(args)
    return generate_with_ark(args)


if __name__ == "__main__":
    raise SystemExit(main())
