# Research sources

Keep this list with the skill so future revisions can re-check fast-changing
ComfyUI behavior.

- ComfyUI workflow concepts and JSON persistence: <https://docs.comfy.org/development/core-concepts/workflow>
- ComfyUI nodes, typed links, and missing-node behavior: <https://docs.comfy.org/development/core-concepts/nodes>
- ComfyUI server routes and local queue/WebSocket endpoints: <https://docs.comfy.org/development/comfyui-server/comms_routes>
- ComfyUI built-in `ImageBatch`: <https://docs.comfy.org/built-in-nodes/ImageBatch>
- ComfyUI built-in `ImageFromBatch`: <https://docs.comfy.org/built-in-nodes/ImageFromBatch>
- ComfyUI built-in `CreateVideo`: <https://docs.comfy.org/built-in-nodes/CreateVideo>
- ComfyUI built-in `SaveVideo`: <https://docs.comfy.org/built-in-nodes/SaveVideo>
- Official frame-interpolation workflow guidance: <https://docs.comfy.org/tutorials/utility/frame-interpolation>
- ComfyUI-VideoHelperSuite video I/O and `Video Combine`: <https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite>
- ComfyUI official video workflow examples: <https://docs.comfy.org/tutorials/video/wan/fun-control>
- MiniMax H3 node implementation used by this workspace: `ComfyUI/comfy_extras/nodes_minimax_h3.py`
- MiniMax H3 official model repository: <https://huggingface.co/Comfy-Org/MiniMax-H3>

Treat local source and live `/object_info` as the authority when they disagree
with an older web page or exported workflow.
