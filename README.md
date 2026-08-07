# MiniMax H3 in ComfyUI - local setup (RTX 4090 + RTX 5090, 128 GB RAM)

End-to-end, command-level setup for running the open-weights **MiniMax H3**
omni-modal video+audio model in ComfyUI on this machine. All changes stay
inside this workspace (`D:\minimax_h3_workflow`).

## What MiniMax H3 is

H3 is **not a language model** and there is no "chat jailbreak" involved. It is
a general-purpose omni-modal **video generation system**: a ~33 B diffusion
transformer (DiT) denoises video **and native 32 kHz stereo audio latents
together** in one pass, conditioned by a frozen Qwen3-VL-32B text encoder, with
separate video and audio VAEs. Output: up to 2K, 24 fps, ~15 s per clip.

- Released open-weights 2026-08-02 (`MiniMaxAI/MiniMax-H3` on Hugging Face).
- Native ComfyUI support since **v0.30.0** (nodes `MiniMaxH3ImageToVideo`,
  `MiniMaxH3ReferenceToVideo`, `MiniMaxH3SigmaShift`, `EmptyMiniMaxH3LatentAV`).
- Official optimized weights (pruned + int8/fp8 quantized, ~66% smaller than
  full precision) live at `Comfy-Org/MiniMax-H3`.
- Community GGUF quantizations exist for the DiT (`joeygambino/MiniMax-H3-GGUF`,
  `molbal/MiniMax-H3-GGUF`, `Abiray/MiniMax-H3-GGUF`, `realrebelai/MiniMax-H3_GGUFs`).

## License note (optional)

MiniMax H3 is released under the MiniMax H3 Community License
(`huggingface.co/MiniMaxAI/MiniMax-H3`, LICENSE file). This guide targets
local, personal use; if you plan to redistribute outputs or use them
commercially, read the license text at the HF repo - that is the authoritative
source. The Qwen3-VL text encoder is Apache-2.0, and the community encoder
fine-tunes listed under Step 3 are third-party uploads with their own model
cards, so check those before swapping them in. Nothing in this guide requires
an account, API key, or online service beyond the initial downloads.

## Hardware fit for this machine

| Piece | File (recommended path) | Size | Notes |
|---|---|---|---|
| DiT (GGUF) | `models/diffusion_models/minimax_h3_fl2va_pruned_fp8_Q8_CR.gguf` | 18.78 GB | Best fit for the 32 GB RTX 5090 |
| DiT (GGUF, 24 GB card) | `models/diffusion_models/minimax_h3_fl2va_pruned_fp8_U16G.gguf` | 14.00 GB | For the RTX 4090 |
| DiT (GGUF, lowest VRAM) | `models/diffusion_models/minimax_h3_fl2va_pruned_fp8_Q4_0.gguf` | 10.60 GB | Last resort |
| Text encoder | `models/text_encoders/qwen3vl_32b_h3_ultra_uncensored_heretic_int8_convrot.safetensors` | 26.36 GB | Community "Ultra Heretic" INT8 ConvRot fine-tune (Apache-2.0); same file for all paths |
| Video VAE | `models/vae/minimax_h3_video_vae_fp16.safetensors` | 4.85 GB | |
| Audio VAE | `models/vae/minimax_h3_audio_vae_fp32.safetensors` | 0.56 GB | |
| (R2V only) | `models/diffusion_models/minimax-h3-ref2va-Q8_CR.gguf` | 18.78 GB | ref2va weight set, only for reference workflows |

Recommended total download: **~50.6 GB** (Q8_CR + community encoder + both VAEs). Keep
~100 GB free on disk. The encoder is only resident during conditioning and is
evicted before sampling, so the 32 GB 5090 comfortably holds the Q8_CR DiT;
any overflow is offloaded to the 128 GB system RAM (normal, slightly slower).
Both GPUs stay visible to a single ComfyUI instance, with the 5090 as the
default sampling device (see Step 4).

## Step 1 - Install ComfyUI (local workspace)

```powershell
cd D:\minimax_h3_workflow
git clone https://github.com/Comfy-Org/ComfyUI.git ComfyUI
cd ComfyUI
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip wheel
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
python -m pip install -r requirements.txt
```

`cu128` (CUDA 12.8) wheels are required for the RTX 5090 (Blackwell sm_120).
This also works for the 4090. If you only had a 4090, `cu126` would do, but
keep `cu128` here since the 5090 is present.

Sanity check (no models needed):

```powershell
python main.py --listen 127.0.0.1 --port 8188
```

Open http://127.0.0.1:8188 - the UI should come up. Then stop it and continue.

## Step 2 - Custom nodes (GGUF path)

```powershell
cd D:\minimax_h3_workflow\ComfyUI\custom_nodes
git clone https://github.com/molbal/ComfyUI-GGUF.git
cd ..
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade gguf
```

Use **molbal's fork** of ComfyUI-GGUF: upstream `city96/ComfyUI-GGUF` does not
know the `minimax_h3` architecture yet, while this fork ships it plus the
`UnetLoaderGGUFDynamicVRAM` node the GGUF workflows use. (Alternative: install
upstream ComfyUI-GGUF and run the one-line patch inside
`ComfyUI-H3-Multishot` - `python apply_gguf_arch_patch.py` - which adds
`minimax_h3` to the loader's architecture list; restart after patching.)

Optional but recommended:

```powershell
cd D:\minimax_h3_workflow\ComfyUI\custom_nodes
git clone https://github.com/ltdrdata/ComfyUI-Manager.git
git clone https://github.com/kijai/ComfyUI-KJNodes.git
git clone https://github.com/jlucasmcrell/ComfyUI-H3-Multishot.git
```

- `ComfyUI-Manager`: node/model installs from the UI.
- `ComfyUI-KJNodes`: provides the `Patch Sage Attention KJ` node (~2x
  attention speedup; see Step 4).
- `ComfyUI-H3-Multishot`: multi-shot (2-5 min) and keyframe workflows; ships
  `H3_Multishot_AIO.json` etc. in its `workflows/` folder.

Restart ComfyUI after installing custom nodes.

## Step 3 - Download the full quantized model stack

```powershell
cd D:\minimax_h3_workflow\ComfyUI
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade "huggingface_hub[cli]"

huggingface-cli download molbal/MiniMax-H3-GGUF minimax_h3_fl2va_pruned_fp8_Q8_CR.gguf --local-dir models\diffusion_models
huggingface-cli download ethanfel/Qwen3-VL-32B-Ultra-Heretic-H3-ComfyUI-INT8-ConvRot qwen3vl_32b_h3_ultra_uncensored_heretic_int8_convrot.safetensors --local-dir models\text_encoders
huggingface-cli download Comfy-Org/MiniMax-H3 vae/minimax_h3_video_vae_fp16.safetensors vae/minimax_h3_audio_vae_fp32.safetensors --local-dir models
```

Resulting layout:

```text
ComfyUI\models\
├── diffusion_models\minimax_h3_fl2va_pruned_fp8_Q8_CR.gguf        (18.78 GB)
├── text_encoders\qwen3vl_32b_h3_ultra_uncensored_heretic_int8_convrot.safetensors  (26.36 GB)
└── vae\
    ├── minimax_h3_video_vae_fp16.safetensors                       ( 4.85 GB)
    └── minimax_h3_audio_vae_fp32.safetensors                       ( 0.56 GB)
```

Variants and alternatives (all sizes verified by HEAD request on 2026-08-06):

- Community encoder: the "Ultra Heretic" INT8 ConvRot fine-tune above is the
  drop-in replacement selected by the shipped workflows. Verify SHA-256
  `d84547412144b7c50a6ec77437a889b869d3ace88da77ef1775d3d2a4901c192` after
  download. For a 16 GB card, `sakamakismile/Qwen3-VL-32B-Heretic-MiniMax-H3-NVFP4`
  (`qwen3vl_32b_heretic_minimax_h3_nvfp4.safetensors`, 15.7 GB, NVFP4) is the
  same fine-tune re-quantized; the official censored
  `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` (14.61 GB) also still works
  if you switch the CLIPLoader dropdown back.

- 24 GB (4090): `minimax_h3_fl2va_pruned_fp8_U16G.gguf` (14.00 GB).
- 16 GB: `minimax_h3_fl2va_pruned_fp8_Q4_0.gguf` (10.60 GB).
- Higher quality, unpruned 33 B GGUF: `joeygambino/MiniMax-H3-GGUF` ->
  `fl2va/MiniMax-H3-fl2va-Q5_1.gguf` (24.14 GB, 24-32 GB cards) or
  `fl2va/MiniMax-H3-fl2va-Q4_0.gguf` (18.50 GB); encoder GGUF
  `joeygambino/MiniMax-H3-encoder-GGUF` (Q4_K_M 18.40 GB) + mmproj sidecar
  (1.12 GB) if you want the encoder quantized too.
- No-custom-node path (official safetensors, also quantized): download
  `diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors`
  (19.53 GB) plus the same encoder/VAEs, and use the official template
  workflows below directly.
- Reference-to-video (R2V): `python scripts\download_models_hf.py --only R2V`

These repos are public (not gated), no HF token needed.

## Step 4 - Launch and run end-to-end

```powershell
cd D:\minimax_h3_workflow
python scripts\launch_comfyui.py
```

`scripts\launch_comfyui.py` probes CUDA's real device order and starts ComfyUI
with **both GPUs visible**, ordered so the selected primary becomes `cuda:0`
and the other card stays addressable as `cuda:1`. The shipped default primary
is the RTX 4090 (matching the retired PowerShell launcher's behavior). Use
`--print-devices` to see the mapping, or
`python scripts\launch_comfyui.py --primary-gpu "RTX 5090" --port 8189` to
start a second instance with the 5090 as the primary. The old
`scripts\launch_comfyui.ps1` launcher was retired; the Python script is the
workspace entry point.

Equivalent manual command for the current wiring (CUDA order, not `nvidia-smi`
order - on this machine cuda:0 is the 4090 and cuda:1 the 5090):

```powershell
python main.py --listen 127.0.0.1 --port 8188 --cuda-device 0,1
```

Listing both indices instead of one is what fixes "only one card is used":
`--cuda-device 0` makes every other GPU invisible to that instance, and taking
the index from `nvidia-smi -L` selects the wrong card here because nvidia-smi
and CUDA enumerate this box in opposite order.
Optional speed flag: `--use-sage-attention` (or add the `Patch Sage Attention
KJ` node; dtype fallback messages in the console are expected and harmless).

### Multi-GPU scheduling (5090 + 4090)

- ComfyUI 0.30's multi-GPU support is **condition-parallel**: it deep-clones
  the diffusion model onto each GPU and computes each step's conditioning
  batches in parallel. Enable it by inserting the **MultiGPU CFG Split** node
  (`MultiGPU_WorkUnits`, category `advanced/multigpu`, max_gpus = 2) between
  the DiT loader and the guider.
- The shipped H3 graphs use `BasicGuider`, which is guidance-free (cfg = 1,
  one positive conditional per step). With a single conditional there is
  nothing to split, so a one-off H3 render still runs on the default device -
  ComfyUI's split is not tensor-parallel, and no launcher flag changes that.
  The 4090 joins the sampling loop for CFG > 1 or batched runs (requires H3
  nodes that emit negative conditioning, e.g. via ComfyUI-H3-Multishot).
- Per-component routing is available with `SelectModelDevice`,
  `SelectCLIPDevice`, and `SelectVAEDevice` (`advanced/multigpu`, value
  `gpu:1`). Note the 26.36 GB INT8 encoder does not fit the 4090's 24 GB; use
  the NVFP4/AWQ encoder variant there. The video/audio VAEs fit fine.
- For many independent renders, two instances are the dependable way to keep
  both cards busy: `python scripts\launch_comfyui.py --primary-gpu "RTX 5090" --port 8188`
  (5090 primary) and `python scripts\launch_comfyui.py --port 8189` (4090 primary).

Then, in the browser UI:

1. **Easiest (official safetensors path):** Template Library > Video > "MiniMax
   H3 T2V" (or I2V / R2V), follow the pop-up model notes, write your prompt,
   Queue.
2. **GGUF path (this guide's download):** Workflow > Open >
   `D:\minimax_h3_workflow\workflows\minimax_h3_t2v-gguf.json`. In the
   `UnetLoaderGGUFDynamicVRAM` dropdown pick
   `minimax_h3_fl2va_pruned_fp8_Q8_CR.gguf` (CLIP loader and both VAEs are
   already set). Write your prompt, Queue. Output lands in
   `ComfyUI\output\video\MiniMax_H3`.
3. I2V / R2V: open `workflows\minimax_h3_i2v-gguf.json` / `minimax_h3_ref2v-gguf.json`.
   For R2V, select the **ref2va** file in the GGUF loader
   (`minimax-h3-ref2va-Q8_CR.gguf`) and connect images/videos/audio; reference
   them in the prompt as `<Picture 1>`, `<Video 1>`, `<Audio 1>` in connection
   order.

## What the workflow graph contains (recipe)

The shipped JSONs are the full ready-to-run graphs. The core chain (same in all
six files) is:

```text
Load DiT (UNETLoader or UnetLoaderGGUFDynamicVRAM)
  -> MiniMaxH3SigmaShift (shift_video=12.0, shift_audio=3.0)   [native graphs]
  -> BasicGuider
Load CLIP ("minimax" type) + video VAE + audio VAE
  -> MiniMaxH3ImageToVideo (prompt, width, height, length; optional
     first_frame/last_frame) -> positive CONDITIONING + AV LATENT
     (or MiniMaxH3ReferenceToVideo for R2V)
RandomNoise + KSamplerSelect + BasicScheduler (simple, 20 steps)
  -> SamplerCustomAdvanced
  -> VAEDecode (video VAE) -> IMAGE
  -> VAEDecodeAudio (audio VAE) -> AUDIO
  -> CreateVideo (24 fps) -> SaveVideo (output/video/MiniMax_H3)
```

Key parameters:

- Resolution: H3's native canvas is a 768 px short edge, capped at 768x1344,
  rounded to a multiple of 32. Start at 16:9 / 0.4 MP (~864x480); the
  `ResolutionSelector` node computes width/height.
- Duration: snaps to the model's 17k+5 frame grid at 24 fps (5 s = 124 frames;
  ~15 s = 362 is the trained max).
- Sampling: `simple` scheduler, 20 steps; sampler `res_multistep` (T2V) or
  `er_sde` (R2V) in the GGUF graphs.
- References and keyframes cannot be combined per shot (core model behavior).

## Verification and troubleshooting

- `Get-ChildItem models\diffusion_models, models\text_encoders, models\vae -Recurse -File | Select Name, @{n='GB';e={[math]::Round($_.Length/1GB,2)}}`
  should match the size table above.
- First run: watch the console - encoder loads (~26.4 GB), conditions are
  computed, then the encoder is evicted and the DiT loads. A "loaded partially;
  ... offloaded" line is normal with dynamic VRAM and the 128 GB RAM.
- Both GPUs: `python scripts\launch_comfyui.py --print-devices` should map
  `cuda:0 -> RTX 4090` and `cuda:1 -> RTX 5090` (default primary); the console
  line `Device: cuda:0 NVIDIA GeForce RTX 4090` confirms the primary.
- Runtime expectation: on an RTX 5090, a ~15 s 960x544 render at Q5_1 measured
  ~15 min in the community; expect similar or better at Q8_CR / 864x480.
- Missing red nodes after loading a JSON -> restart ComfyUI (custom nodes not
  loaded) or install the fork named in Step 2.
- GGUF dropdown empty -> file is not in `models\diffusion_models` (flat, no
  subfolder).
- OOM / CUDA out of memory -> use a smaller quant (U16G / Q4_0), lower
  megapixels, or add `--lowvram`.
- Mono reference audio crashes with a shape mismatch -> the reference must be
  stereo 32 kHz (H3 Multishot's "stereo guard" fixes this case).
- Sage Attention "Input tensors must be dtype float16/bfloat16" messages are
  expected; those layers fall back to standard attention.

## Files in this workspace

```text
README.md                         this guide
scripts\setup_comfyui.ps1         Step 1 + 2 as a script
scripts\download_models.ps1       Step 3 as a script (quant selectable)
scripts\launch_comfyui.py         Step 4 launcher (Python; both GPUs visible, 4090 primary default)
workflows\minimax_h3_ref2v-gguf_kazusa_sfw_uncensored.json   Kazusa reference-to-video (SFW prompt, uncensored encoder, 5 s)
workflows\video_minimax_h3_t2v.json    official T2V template (sha256-verified)
workflows\video_minimax_h3_i2v.json    official I2V template (sha256-verified)
workflows\video_minimax_h3_r2v.json    official R2V template (sha256-verified)
workflows\minimax_h3_t2v-gguf.json     GGUF T2V graph (molbal)
workflows\minimax_h3_i2v-gguf.json     GGUF I2V graph (molbal)
workflows\minimax_h3_ref2v-gguf.json   GGUF R2V graph (molbal)
```

Sources: MiniMax H3 announcement, ComfyUI docs/blog (docs.comfy.org, blog.comfy.org),
the MiniMax H3 Community License (primary), HF model repos (Comfy-Org/MiniMax-H3,
molbal/MiniMax-H3-GGUF, joeygambino/*), and ComfyUI core source
(comfy_extras/nodes_minimax_h3.py).
