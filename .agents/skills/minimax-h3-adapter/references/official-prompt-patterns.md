# Official-manual-derived H3 prompt patterns

Source: [MiniMax H3 模型使用手册](https://vrfi1sk8a0.feishu.cn/wiki/FIWjwgL33ipnkekzk30crmKUnIh), verified 2026-08-16.

Use these as structural patterns, not fixed looks. Preserve upstream decisions and the canonical language policy in `docs/prompt-language-style.md`.

## Style-source rule

- Explicit style or style reference: preserve its family and describe observable palette, lighting, texture, motion, typography, and edit behavior.
- No style source: omit the named style family. Do not add “电影感,” “写实,” “动画,” “广告,” or another habitual look.
- The adapter must remain equally usable for live action, documentary, fashion, clay animation, cel animation, MG/typography, UI/game footage, AR compositing, product work, and experimental visuals.

## Pattern A: declared multi-shot segment

```text
参考素材说明：
<Picture 1> 只提供人物身份；<Video 1> 只提供动作节奏；<Audio 1> 只提供环境节拍。未声明的服装、场景和镜头属性不从参考素材迁移。

核心创意：
人物在狭窄工作间完成一次交接；不指定额外的命名风格，沿用上游已声明的空间、光线和材质。

integrated_multimodal_description:
[Shot 1] 0.00–2.80 秒。中景（medium shot），人物 A 在画面左侧把红色工具递向人物 B；摄影机静止镜头（static shot）。人物 A 说：<d>[Chinese]拿稳。</d> 金属工具轻响。结尾硬切（hard cut）。
[Shot 2] 2.80–6.00 秒。近景（close-up），保持同一红色工具和人物 B 的右手；摄影机缓慢推轨（dolly in / push-in）。人物 B 完成接握，人物 A 的声音以 L-cut 延续到本镜头前 0.20 秒。室内底噪连续。
```

Why it is stable: every asset has one job, each shot has view/content/camera/action/dialogue/sound, and the cut plus audio overlap are explicit.

## Pattern B: exact first and last frame, one take

```text
参考素材说明：
<Picture 1> 是 0.00 秒的精确首帧；<Picture 2> 是 6.00 秒的精确尾帧。两图之间是同一镜头的连续动作与光影变化，不代表切镜。

核心创意：
人物从首帧的静止站姿自然走到尾帧位置并停住。

integrated_multimodal_description:
全程一个连续镜头，不切镜。全景（full shot）保持人物全身与路径可见，摄影机向左横移（truck left）并向右横摇（pan right）保持主体构图；动作从左脚起步，经两次自然重心转移，在尾帧姿势前减速停稳。环境声连续，无新增对白。
```

Why it is stable: endpoint images constrain the ends while the prompt supplies one causal path and forbids an invented montage.

## Pattern C: split interaction continuation

Predecessor exit capsule:

```yaml
action_phase: right hand has closed on the red handle; clockwise turn has started but is incomplete
left_right_limb_state: right hand holding PROP_RED_HANDLE; left hand free
camera_motion_vector: slow dolly in continues
focus_plane: hand and handle
active_speaker_and_dialogue_span: none
next_allowed_delta: complete the clockwise turn, then release
```

Successor prompt opening:

```text
<Picture 1> 是前段实际最后解码帧，也是本段精确首帧。保持右手已经握住红色把手、顺时针转动尚未完成、左手空闲、摄影机缓慢推轨（dolly in / push-in）和手部焦平面。不要重新伸手或再次抓握；只继续完成剩余转动，然后松手。
```

Why it is stable: the successor begins from the exact physical phase and describes only the remaining delta.
