# APIS Launch Checklist

Follow this checklist to maximize your visibility when pushing APIS to the public, GitHub, and your professional network.

## 1. Repository Prep
- [ ] Record the 30-60 second WOW-factor Demo GIF (using the `demo_plan.md` artifact).
- [ ] Add the Demo GIF to the `assets/` folder and link it at the very top of `README.md`.
- [ ] Add the 5 high-fidelity screenshots (`assets_plan.md`) into the `README.md` dashboard section.
- [ ] Add the 4 Phase 7 Evaluation charts (`assets/eval/`) to the Benchmarks section in `README.md` and the `dashboard/src/app/results/page.tsx` page.
- [ ] Double-check all local paths in the Markdown files resolve correctly.
- [ ] Ensure the repo is set to **Public**.
- [ ] Add relevant repository tags: `llm`, `observability`, `mlops`, `prompt-engineering`, `fastapi`, `nextjs`.
- [ ] Pin the repository to your GitHub profile overview.

## 2. The LinkedIn Post
Your LinkedIn post should not read like a junior project announcement. It should read like a senior systems engineer solving a hard production problem.

**Draft Post:**
> Over the last few months, I've noticed a recurring problem in AI engineering: prompts are treated as static strings. But LLMs are non-deterministic, and models undergo silent updates. A prompt that works today will inevitably suffer from "drift" tomorrow.
>
> To solve this, I built **APIS (Adaptive Prompt Infrastructure System)**.
>
> APIS does for LLM prompts what Kubernetes did for container deployments. It's a full self-healing MLOps pipeline that features:
> 🚦 **Automated Canary Rollouts**: Safely test new prompts on 10% of traffic.
> ⏪ **Automatic Rollbacks**: Instantly isolates bad configurations if latency or error rates spike.
> 🔍 **Drift Detection**: An async engine that aggregates user thumbs-downs and automatically generates healing candidate prompts.
>
> I just wrapped up a 14-day, 12,000-interaction controlled evaluation simulating severe model drift. APIS caught the drift, rolled out fixes via canary, and reduced the Mean Time To Recovery (MTTR) from days down to 1.8 hours. 
>
> It's fully open-source. Check out the GitHub repo and the live dashboard demo below! 👇 
> [Link to GitHub Repo]

## 3. Additional Distribution
- [ ] Post in relevant Discord/Slack communities (e.g., LangChain community, MLOps Community, Next.js showcase).
- [ ] Post a "Show HN" on Hacker News. Focus the title on the technical problem (e.g., "Show HN: I built an automated canary deployment system for LLM prompts").
- [ ] Update your Resume using the bullet points from `resume_bullets.md`.
