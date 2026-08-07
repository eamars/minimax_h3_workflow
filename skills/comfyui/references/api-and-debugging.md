# ComfyUI API and debugging reference

Use this reference when a workflow must run repeatedly, when a UI export fails
in automation, or when an error message does not identify the real cause.

## Two JSON representations

ComfyUI commonly exposes two related workflow representations:

- **UI workflow:** contains `nodes`, `links`, layout, widget values, groups, and
  notes. Use it for reopening and editing in the frontend.
- **API prompt format:** maps node IDs to `{class_type, inputs}` objects. Use it
  for `/prompt` execution. Linked inputs are arrays such as `["12", 0]`.

Generate API format from the frontend's `Save (API Format)` action or convert it
against the live server. Do not assume the order of `widgets_values` from an
older export. Custom nodes and frontend versions can insert, remove, or expose
inputs.

## Local request loop

Use a client ID and the following sequence:

```text
GET  /system_stats       -> confirm Python, devices, VRAM, and version
GET  /object_info        -> confirm node classes and live input schemas
POST /prompt             -> {"prompt": <api graph>, "client_id": <id>}
GET  /history/<id>       -> wait for completion or inspect status/messages
WS   /ws?clientId=<id>   -> optional live status, progress, and node events
```

The local server returns a `prompt_id` when the queue accepts the graph. A
validation failure returns `error` and `node_errors`; do not poll a missing
prompt ID. On completion, inspect the output records for filename, subfolder,
and type. Query `/queue` when diagnosing a stuck job and `/interrupt` only when
the user wants the current execution stopped.

For this repository, inspect `scripts/comfy_api_runner.py` before reusing it. It
already avoids stale scalar values in tensor slots and reads widget orders from
`/object_info`, but its fallback lists are version-specific and must not outrank
the live schema.

## Minimal validation routine

1. Parse JSON locally and verify that every link source exists.
2. Compare every node `type` with `/object_info`.
3. Confirm required model names against the server's model lists and local model
   directories.
4. Submit a tiny fixed-seed test. Save the returned prompt ID and full status.
5. Inspect the first and last decoded frames, not only the final video player.
6. Record the exact successful graph and output paths.

## Useful diagnostic routes

| Route | Use |
| --- | --- |
| `/system_stats` | device order, VRAM, Python, and server information |
| `/object_info` | node classes, required/optional inputs, widget schemas |
| `/prompt` GET | queue status and current execution information |
| `/prompt` POST | validate and queue an API prompt |
| `/history` and `/history/{prompt_id}` | completed outputs and error messages |
| `/queue` | pending/running queue entries |
| `/view` | inspect a saved image or preview with query parameters |
| `/interrupt` | stop the current execution |

## Failure triage

- **Unknown node class:** install the package named by the workflow's node
  source badge, or replace it with a tested built-in equivalent.
- **`node_errors` on queue:** read the node-specific error object; fix model
  names, missing required inputs, or incompatible links before retrying.
- **Wrong widget value:** re-export API format or use `/object_info`; do not
  shift values by index after a node update.
- **Tensor type error:** a stale scalar or filename entered a tensor input. Check
  the UI link first, then the converter's input-type filter.
- **No output record:** verify that a Save Image/Save Video/VHS Video Combine
  node is connected and configured to save to the intended directory.
- **Job completes but media is wrong:** check frame count, FPS, resolution,
  seed, and the actual model/LoRA/VAE loaded; success only means execution did
  not throw an exception.
