# MiniMax H3 Prompt Language and Cinematic Terminology Style

Status: canonical project policy
Scope: every MiniMax H3 prompt written for T2VA, I2VA, FL2VA, L2VA, or R2VA
Encoding: UTF-8

This document is the single source of truth for prompt language and cinematic
terminology in this repository. `AGENTS.md` and H3-related skills must point to
this document rather than restating or creating competing language rules.

## 1. Precedence and scope

Apply these rules in the following order:

1. Preserve user-supplied dialogue, lyrics, visible text, named references, and
   explicitly requested language or style exactly as requested.
2. Apply this document to all authored H3 prompt prose and camera terminology.
3. Preserve the official H3 field names, reference labels, control tokens, and
   timing conventions even when the surrounding prose is Chinese.

This document governs prompt language. It does not change plot, performance,
canon, shot boundaries, timing, H3 mode selection, ComfyUI graph structure, or
render settings.

## 2. Default language contract

- The natural-language body of an H3 prompt uses fluent Simplified Chinese as
  its structural language: description, action, blocking, environment,
  lighting, sound, pacing, continuity, and exclusions.
- Chinese is the default even when the user's brief is written in English,
  unless the user explicitly requests another prompt language.
- Do not translate protocol tokens, field names, reference labels, or control
  markers. They remain exactly as required by the selected H3 mode.
- Do not turn a Chinese prompt into a sentence-by-sentence English translation.
  The Chinese should read as original production direction, not translated
  prose.

## 3. H3 protocol text that remains exact

The following items are format tokens, not natural-language prose. Keep them in
their official English spelling and order:

- Core fields: `integrated_multimodal_description`, `overall_soundscape`, and
  `non_diegetic_music`.
- Full-reference fields: `subject_definitions`, `summary`,
  `retention_analysis`, `detailed_description`, `overall_soundscape`, and
  `non_diegetic_music`.
- Shot and timing markers: `[Shot 1]`, `[Shot 2]`, and `At 00:03.500`.
- Reference labels: `<Subject N>`, `<Picture N>`, `<Video N>`, and
  `<Audio N>`.
- Dialogue and continuity markers: `<d>`, `<scenetrans>`, and `<cutoff>`.
- Official relationship markers such as `fully_preserved`,
  `partially_preserved`, `attribute_transfer`, `weak_reference`, `fully_copy`,
  `partially_copy`, and `reference`.

Inside a dialogue tag, use the language marker required by the actual line,
for example `<d>[Chinese]……</d>`. Keep the supplied spoken words and
punctuation verbatim.

## 4. Bilingual professional camera terminology

Every authored camera instruction must use a professional Chinese term followed
by its canonical English equivalent in parentheses:

| 中文术语 | English term | Usage boundary |
| --- | --- | --- |
| 大远景 | extreme long shot (ELS) | Establishes a very broad environment and a small subject. |
| 远景 | long shot (LS) | Shows the subject within substantial surrounding space. |
| 全景 | full shot (FS) | Frames the subject's full body. |
| 中景 | medium shot (MS) | Frames roughly from the waist or mid-torso upward. |
| 中近景 | medium close-up (MCU) | Frames roughly from the chest upward. |
| 近景 | close-up (CU) | Emphasizes the face or a key object. |
| 大特写 | extreme close-up (ECU) | Isolates a small facial or object detail. |
| 过肩镜头 | over-the-shoulder shot (OTS) | Uses a foreground shoulder or head to anchor the viewpoint. |
| 主观镜头 | point-of-view shot (POV) | Presents the subject's visual viewpoint. |
| 平视机位 | eye-level angle | Keeps the optical axis approximately level with the subject. |
| 低机位 | low-angle shot | Places the camera below the subject's eye line. |
| 高机位 | high-angle shot | Places the camera above the subject's eye line. |
| 鸟瞰镜头 | bird's-eye view | Looks steeply downward from an overhead viewpoint. |
| 推轨 | dolly in / push-in | Physically moves the camera toward the subject. |
| 拉轨 | dolly out / pull-out | Physically moves the camera away from the subject. |
| 横摇 | pan left / pan right | Rotates the camera horizontally from a fixed position. |
| 横移 | truck left / truck right | Translates the camera laterally through space. |
| 俯仰 | tilt up / tilt down | Rotates the camera vertically from a fixed position. |
| 升降 | pedestal up / pedestal down | Moves the entire camera vertically. |
| 弧线环绕 | arc shot | Moves the camera along an arc around the subject. |
| 跟拍 | tracking shot | Follows a moving subject through space. |
| 静止镜头 | static shot | Keeps camera position and lens stable. |
| 手持轻晃 | slight handheld shake | Adds restrained handheld movement, not random camera motion. |
| 变焦推进 | zoom in | Changes focal length while the camera body remains stationary. |
| 变焦拉远 | zoom out | Widens focal length while the camera body remains stationary. |
| 焦点转移 | rack focus | Shifts focus between depth planes without changing the framing. |
| 浅景深 | shallow depth of field | Keeps a narrow depth range sharp. |
| 深焦 | deep focus | Keeps foreground and background readable at the same time. |

Do not use `zoom in` for a physical camera move. Use `dolly in / push-in` for
camera translation and `zoom in` only for a focal-length change. This distinction
follows the official H3 camera vocabulary.

Write the term as part of natural Chinese direction, for example:

> 中近景（medium close-up）保持人物与桌面道具同框，摄影机缓慢推轨
> （dolly in / push-in）靠近她握紧的信件，同时进行焦点转移（rack focus）
> 从前景信件转到她的眼睛。

Do not append a loose English keyword list such as `cinematic, camera, zoom`.
The English term must identify the same operation as the Chinese term.

## 5. Dialogue and visible text

- User-provided dialogue, lyrics, and visible scene text are immutable. Do not
  translate, polish, paraphrase, or normalize them.
- When dialogue must be authored and no language or dialogue style is supplied,
  write natural, conversational Chinese appropriate to the speaker and scene.
- Prefer spoken Chinese word order, omissions, particles, rhythm, and character
  diction over formal written prose. Do not imitate English syntax or produce
  literal-translation phrasing.
- If the user specifies a language, dialect, period register, genre voice, or
  other dialogue style, follow that request instead of the default colloquial
  Chinese rule.
- Keep stable speaker IDs and the official `<d>[Language]... </d>` structure;
  the language style applies to the words inside the tag, not to the tag itself.

## 6. Official Chinese H3 examples used as the reference basis

These are short source notes and paraphrased patterns, not a replacement copy
of the official documentation. They are kept here so future prompt authors can
work from the same verified basis without creating another language guide.

- The official Chinese H3 launch article demonstrates a direct multimodal
  relationship sentence: reference a video's Hitchcock camera movement, make
  the person in an image sing, and use an audio reference for the vocal sound.
  The pattern is **reference role → target action → audio relationship**. See
  [MiniMax H3 官方中文发布文章](https://www.minimaxi.com/blog/minimax-h3).
- The official H3 API documentation uses a Chinese cinematic T2VA premise that
  identifies the format, central subject, environment, event progression, and
  physical audiovisual effects in one natural paragraph. See
  [创建视频生成任务](https://platform.minimaxi.com/docs/api-reference/video-generation-v2-create).
- The official H3 feature examples use Chinese production prose to combine
  aspect ratio, reference-asset roles, subject action, environment, visual
  style, camera behavior, and sound intent. See
  [H3 亮点功能示例](https://platform.minimaxi.com/docs/guides/video-prompt).
- The official open-source prompt guide remains the authority for H3 field
  order, shot timing, reference labels, speaker tags, and the semantic
  distinction between `Push In` and `Zoom In`. See the
  [official base-mode guide](https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/main/skills/h3-prompt-writing/references/base-en.txt)
  and the [official full-reference guide](https://raw.githubusercontent.com/MiniMax-AI/MiniMax-H3/main/skills/h3-prompt-writing/references/ref-en.txt).

## 7. Authoring checklist

Before accepting an H3 prompt, verify:

- Natural-language prose is Simplified Chinese unless the user explicitly
  requested another language.
- Every authored camera operation has a professional Chinese term and matching
  English term in parentheses.
- Dolly/tracking movement is not mislabeled as zoom, and pan is not mislabeled
  as truck.
- Official H3 fields, labels, timing, and control markers are unchanged.
- User dialogue, lyrics, and visible text are preserved verbatim.
- Newly authored Chinese dialogue sounds spoken and character-specific rather
  than translated or bureaucratic.
- The prompt still preserves the upstream shot, camera, continuity, audio, and
  reference decisions.
