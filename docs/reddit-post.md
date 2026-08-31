# Reddit draft (not posted)

Suggested subs: **r/LocalLLaMA**, Strix Halo Discord / AMD Ryzen AI threads.
Do not post until Tome says go. Title + body below are ready to paste.

---

**Title:** Strix Halo (395 / 8060S) measured recipes: Flash-Next 30 t/s, GLM-5.3-Flash 14.6 t/s ROCm, 27B MTP, MiniMax H3 Czech

**Body:**

I have been measuring local LLM + MiniMax H3 on a Ryzen AI MAX+ 395 / Radeon 8060S (`gfx1151`). `free -h` on this box is **124 GiB**, not 128 — that gap is enough to OOM a 112 GiB MoE.

Exact commands, HF file names, byte sizes, and failed arms are in:

https://github.com/tomasreminek/strix-halo

Living dashboard (same numbers + video): http://hilbertkb.31.97.126.27.sslip.io/strix-halo.html

**Qwen3.8-Flash-Next (idle-GPU chat)**  
Nathanw v0.7.2 portable Vulkan + `agentionai` **AP-IQ4_XS** (90,447,294,368 B).  
llama-bench: **pp512 428 t/s · tg64 30.0 t/s**. llama-server Czech/EN ~30.1 t/s, one tool-call PASS. Production ctx **128k** (~103 GiB). qwen4exp still cannot cache-reuse, so this is not a full agent daily driver. ICD must come from the Nathanw bundle (`RADV STRIX_HALO`, `int dot: 1`). CIRU HIP no-MTP was 433 pp / **22.6** tg — slower decode. apepojken IQ4 aborted (`ggml-vulkan.cpp:7794`). julianmb/haloq38flash 56 t/s is MTP @ 8k; at 128k they report 19–27, which is worse than 30 here without MTP.

**GLM-5.3-Flash (320B MoE, arch `glm5next`)**  
Nathanw cannot load it. Unsloth MIX `b10698-mix` can.  
Winner: [`aj9o9` AJ-IQ2_XXS](https://huggingface.co/aj9o9/GLM-5.3-Flash-GGUF) **81.35 GiB** on the **ROCm gfx1151** tarball (same tag as Vulkan).  
`llama-server` decode **14.63 t/s**, llama-bench tg64 **14.53**. Same GGUF on Vulkan all-gpu: **8.57 t/s**. Threads/ubatch/KV-q4 did not move Vulkan decode. Unsloth UD-IQ3_XXS 112 GiB only ran with `--no-op-offload` at **1.26 t/s**; community `--fit off` + extra 1.28 GiB radv buffer OOM’d the kernel. Do not quote 3090 CUDA 11.5 t/s.

**Qwen3.8 27B (agent / cache-reuse)**  
ROCmFP4 FAST + MTP **`n-max=2 --spec-draft-p-min 0.6`**: Czech **20.2 t/s / 73% acc**. AMD’s n-max=4 was **25% acc** on Czech. No-draft ~14.2 t/s. Type-101 FAST is not portable to upstream llama.cpp. `--temp 0` with no DRY/presence penalty loops identical tool calls.

**MiniMax H3 (ComfyUI 0.33.0, ROCm 7.13)**  
Czech production: **FP8 + Qwen3-VL 32B + Euler/simple 8–11**, native audio, no Sage (noise, GH#15263). 3s T2V ~11 min, human 8/10. FastH3 v0.2 LoRA 4-step = 5.67 min but audio 5/10 — not a winner. Acc-4 = metallic echo. Do not download the 148 GB FastVideo repo.

Happy to answer flags. Please copy from the repo, not from memory — the Vulkan vs ROCm GLM swap is the whole story.
