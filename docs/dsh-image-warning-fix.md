# DeepSeek Harness: pasted images are rejected before any vision skill can run

> Standalone problem report for the warning **"当前模型不支持图片输入 / This model does not support image input"** shown when pasting an image into the web chat while the routed model is text-only, plus the source fix prepared on the fork `deveuper/deepseek-harness` (branch `fix/text-only-model-image-admission`).
>
> 这是一份把"纯文本模型贴图即弹警告"现象单独提出的问题报告，并附上在 fork 分支 `fix/text-only-model-image-admission` 上已完成的源码修复说明。

## 1. Problem / 现象

- **What the user does / 用户操作:** paste or drag an image into the DeepSeek Harness web chat input box, with a text-only main model selected (DeepSeek, Kimi, GLM text models, etc.).
- **What happens now / 目前的效果:** sending fails immediately. The UI banner shows `当前模型不支持图片，请切换支持图片的模型` (attachment-error, reason `MODEL_DOES_NOT_SUPPORT_IMAGES`). The image is refused at the door and **never reaches the conversation**, so no skill can ever read it.
- **Root cause / 根因:** the prompt admission code in `packages/host/apiproxy/src/api-proxy.ts` rejects any prompt containing image blocks when the routed model's `inputModalities` does not include `image`. This check runs **before** skills can act.
- **Why this is a source bug, not a skill problem / 为什么是源码问题而非技能问题:** the block sits in the harness admission layer, ahead of every skill. **Any** script-based vision skill — visionDS, vision-hub, or any other vision/OCR helper — is affected equally, because the image is rejected before the skill can receive it. The advertised workflow "keep the text-only main model, let another vision model look at the image" is therefore impossible out of the box.

## 2. The fix / 修复内容

Keep the main model text-only (unchanged), persist the uploaded images durably, and hand the model **local file paths** as text. The model then feeds those paths to a vision skill/script through its shell tools.

- `packages/attachment/attachment/src/index.ts` — add `AttachmentStore.imagePath(ref)` to the seam: resolve a stored image to its absolute local filesystem path.
- `packages/attachment/attachment-local/src/index.ts` / `src/store.ts` — implement `imagePath` and export `attachmentObjectPath(root, ref)`.
- `packages/host/apiproxy/src/api-proxy.ts` — prompt admission: when the routed model declares `inputModalities` without `image`, persist the uploads exactly as before (`durablePromptContent`), then replace the image blocks with text blocks carrying each stored image's local path, its media type, and a hint to use the `vision-ds` skill. The durable user message stays text-only, so the text-only LLM adapter never sees an image block and the "model-visible ⟺ logged" invariant holds.
- Tests — new coverage in `packages/host/apiproxy/tests/api-proxy-models.spec.ts` (image → path-text conversion for a text-only model) and `packages/attachment/attachment-local/tests/store.spec.ts` (`attachmentObjectPath`); the new abstract member is implemented in the existing test/tooling attachment stores (`packages/fs/tool-fs/tests/read-image.spec.ts`, `packages/host/apiproxy/tests/api-proxy-projections.spec.ts`, `packages/llm/llm-pi-ai/tests/adapter.spec.ts`, `packages/llm/llm-pi-ai/tests/provider-apis.e2e.ts`, `scripts/gen-tool-catalog.ts`, `scripts/test-invariants.ts`).

## 3. Why remove the warning / 为什么去掉这条警告

- With the warning, the image is rejected at admission, so **no vision skill can ever work** with a text-only main model. Removing the rejection is the only way to enable the "main model stays, vision goes elsewhere" workflow.
- The change is additive and safe: the main model still receives only text; images are stored in the durable attachment store exactly as the vision-capable path does; models that DO declare image input keep the previous behavior (real image blocks) unchanged.
- The client-side copy mapping for `MODEL_DOES_NOT_SUPPORT_IMAGES` stays in place for any other surface that still emits it; only the ordinary session admission path stops emitting it. The separate subagent-continuation guard (`SUBAGENT_IMAGE_UNSUPPORTED`) is untouched by this change.

## 4. Verification / 验证

- `tsc -b tsconfig.host.json` — clean.
- Affected vitest suites — **104 passed** (`api-proxy-models`, `api-proxy-projections`, `attachment-local/store`, `tool-fs/read-image`, `llm-pi-ai/adapter`).
- End-to-end on this machine — a pasted-style PNG is persisted under `~/.dsh/attachments/v1`, the text-only model receives the local path, the `vision-ds` skill script reads it, and a real MiMo vision API call returned a correct description of the image (620 tokens). Windows built-in OCR fallback also verified.

## 5. Links / 相关链接

- Fix branch on the fork: <https://github.com/deveuper/deepseek-harness/tree/fix/text-only-model-image-admission> (commit `9f56c37e48`)
- Ready-to-apply diff against official `master`: <https://github.com/deepseek-ai/deepseek-harness/compare/master...deveuper:fix/text-only-model-image-admission>
- The skill that consumes the paths: <https://github.com/deveuper/visionDS>
- Official discussion (this report): <https://github.com/deepseek-ai/deepseek-harness/discussions/427>
- Official discussion (visionDS announcement): <https://github.com/deepseek-ai/deepseek-harness/discussions/384>
