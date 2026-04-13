---
name: seedance2
description: "Generate videos using Volcengine Ark's Doubao Seedance 2.0 model. Use when the user says '生成视频', 'seedance', '豆包视频', 'text to video', '图生视频', '文生视频', '首尾帧', '视频生成', or asks to create/generate a video from text, images, or combine reference materials. Supports text-to-video, image-to-video (first frame), first+last frame, multimodal reference (image/video/audio), video editing, and video extension."
---

# Seedance 2.0 Video Generation

Create videos via Volcengine Ark Doubao Seedance 2.0. Async API: submit task → poll status → download MP4.

## Configuration

```
Base URL: https://ark.cn-beijing.volces.com/api/v3
API Key: env var ARK_API_KEY
Model IDs:
  - doubao-seedance-2-0-260128        (2.0, full features, 480p/720p)
  - doubao-seedance-2-0-fast-260128   (2.0 fast)
  - doubao-seedance-1-5-pro-251215    (1.5 pro, supports 1080p)
```

## Endpoints

- `POST /contents/generations/tasks` — create task, returns `{id}`
- `GET /contents/generations/tasks/{id}` — poll status (`queued`/`running`/`succeeded`/`failed`)

On `succeeded`, read MP4 from `content.video_url`.

## Request body

```json
{
  "model": "doubao-seedance-2-0-260128",
  "content": [
    {"type": "text", "text": "<prompt>"},
    {"type": "image_url", "image_url": {"url": "<image-url>"}}
  ],
  "generate_audio": true,
  "ratio": "adaptive",
  "duration": 5,
  "watermark": false
}
```

### Content items

- `text`: prompt (required). Describe scene, camera motion, subject action, style.
- `image_url`: reference image. Add `role` field to distinguish usage:
  - First-frame i2v: single `image_url` item (default behavior).
  - First+last frame: two `image_url` items with `"role": "first_frame"` and `"role": "last_frame"`.
  - Multimodal reference: `"role": "reference_image"` (seedance 2.0 only).
- `video_url`: `{"type": "video_url", "video_url": {"url": "..."}, "role": "reference_video" | "source_video"}` — for video reference / editing / extension.
- `audio_url`: `{"type": "audio_url", "audio_url": {"url": "..."}}` — reference audio (seedance 2.0).

### Top-level params

| Param | Values | Notes |
|---|---|---|
| `ratio` | `21:9`,`16:9`,`4:3`,`1:1`,`3:4`,`9:16`,`adaptive` | `adaptive` = match input image |
| `duration` | 4–15 (sec) seedance 2.0; 2–12 for older | |
| `resolution` | `480p`,`720p`,`1080p` | 2.0 only 480p/720p |
| `generate_audio` | bool | 2.0 / 1.5 pro only |
| `watermark` | bool | |
| `seed` | int | reproducibility |

## Common recipes

### 1. Text-to-video
```json
{"model":"doubao-seedance-2-0-260128","content":[{"type":"text","text":"<prompt>"}],"ratio":"16:9","duration":5}
```

### 2. Image-to-video (first frame)
```json
{"content":[
  {"type":"text","text":"<prompt>"},
  {"type":"image_url","image_url":{"url":"<first-frame>"}}
],"ratio":"adaptive","duration":5,"generate_audio":true}
```

### 3. First + last frame
```json
{"content":[
  {"type":"text","text":"360度环绕运镜"},
  {"type":"image_url","image_url":{"url":"<first>"},"role":"first_frame"},
  {"type":"image_url","image_url":{"url":"<last>"},"role":"last_frame"}
]}
```

### 4. Multimodal reference (2.0)
Combine images + video + audio as references:
```json
{"content":[
  {"type":"text","text":"<prompt referencing 图片1/图片2/音频1>"},
  {"type":"image_url","image_url":{"url":"..."},"role":"reference_image"},
  {"type":"image_url","image_url":{"url":"..."},"role":"reference_image"},
  {"type":"audio_url","audio_url":{"url":"..."}}
]}
```

### 5. Edit video
```json
{"content":[
  {"type":"text","text":"将视频1中房子刷成蓝色，天气参考图片1"},
  {"type":"video_url","video_url":{"url":"..."},"role":"source_video"},
  {"type":"image_url","image_url":{"url":"..."},"role":"reference_image"}
]}
```

### 6. Extend video
```json
{"content":[
  {"type":"text","text":"向后延长，汽车驶入沙漠绿洲"},
  {"type":"video_url","video_url":{"url":"..."},"role":"source_video"},
  {"type":"audio_url","audio_url":{"url":"..."}}
],"duration":11}
```

## How to run

Prefer curl for one-off generation. For Go integration, reuse the project pattern (`internal/gateway/...`) with `net/http` — no SDK needed.

```bash
# Submit
TASK_ID=$(curl -s https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -d @request.json | jq -r .id)

# Poll
while true; do
  RESP=$(curl -s https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/$TASK_ID \
    -H "Authorization: Bearer $ARK_API_KEY")
  STATUS=$(echo "$RESP" | jq -r .status)
  echo "status=$STATUS"
  [ "$STATUS" = "succeeded" ] && echo "$RESP" | jq -r .content.video_url && break
  [ "$STATUS" = "failed" ] && echo "$RESP" | jq . && exit 1
  sleep 10
done
```

## Gotchas

- Video generation can take minutes; poll every 10s, not faster.
- `ratio: "adaptive"` requires an input image/video — don't use for pure text-to-video.
- Seedance 2.0 max resolution is 720p; need 1080p → use `seedance-1-5-pro`.
- Each task ID is persistent — store it before polling so you can resume.
- `ARK_API_KEY` must be in env; never hardcode. Get from https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
- Rate limits: 600 RPM / 10 concurrent for seedance 2.0.
- Default returns watermarked video; set `watermark: false` for clean output.
- Image/video/audio URLs must be publicly accessible HTTPS URLs.

## Prompt tips

Include: subject + action + camera motion + style/lighting + audio cues (if `generate_audio`). E.g.:
`"写实风格，镜头围绕人物推镜头拉近，特写面部，她正在唱京剧'月移花影'，唱腔充满传统韵味"`
