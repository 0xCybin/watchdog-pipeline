# Launch Playbook: Getting Watchdog Pipeline Out There

A step-by-step guide for getting traction as a solo dev with no audience.
Written plain and simple — no fluff.

---

## Phase 1: Clean Up the Project (1-2 days)

Before anyone sees your code, make it presentable.

### Step 1: Make sure no secrets are in the repo
- [x] .env.example has placeholder API key (already done)
- [x] .env is gitignored (already done)
- [ ] Search the entire codebase for any API keys, passwords, or personal info
  ```
  grep -r "sk-ant" . --include="*.py"
  grep -r "password" . --include="*.py"
  ```
- [ ] Check git history for accidentally committed secrets
  ```
  git log --all --full-history -- .env
  ```

### Step 2: Write a README that sells the project in 30 seconds
Your README is your landing page. Most people will decide in 30 seconds
whether to keep reading. Structure it like this:

1. **One-line hook** — what it does in plain English
   Example: "AI pipeline that reads thousands of government documents and
   automatically finds names, money trails, contradictions, and cover-ups."

2. **Demo screenshot or GIF** — show the Swagger UI with real results
   (redact any sensitive victim info)

3. **Key numbers** — "Processed 500 DOJ Epstein documents in 2 hours.
   Found 1,156 entities, 558 anomalies, and surfaced details not yet
   reported by major media."

4. **Quick start** — copy-paste commands to get running in 5 minutes
   ```
   git clone <repo>
   cp .env.example .env        # add your API key
   docker compose up -d
   alembic upgrade head
   watchdog-pipeline --step all --limit 50
   ```

5. **How it works** — simple diagram of the 6 pipeline steps

6. **Use cases** — not just Epstein files. Emphasize it works on ANY
   large document dump (court records, FOIA, leaked files, etc.)

### Step 3: Add a LICENSE file
- Use MIT License (most permissive, most stars on GitHub)
- This tells people "yes, you can use this"

### Step 4: Clean up the code
- Remove any debug prints or commented-out code
- Make sure `pip install -e .` works cleanly
- Make sure tests pass: `pytest`
- Add a `requirements.txt` or make sure `pyproject.toml` is complete

---

## Phase 2: First Commit to GitHub (1 day)

### Step 5: Create the GitHub repo
1. Go to github.com > New Repository
2. Name it something memorable and searchable:
   - Good: `watchdog-pipeline` or `document-watchdog`
   - Avoid: `epstein-watchdog` (too narrow — limits future use cases)
3. Description: "Automated pipeline for analyzing large document dumps.
   Extracts entities, flags anomalies, finds contradictions."
4. Make it PUBLIC
5. Push your code:
   ```
   git remote add origin https://github.com/YOUR_USERNAME/watchdog-pipeline.git
   git push -u origin master
   ```

### Step 6: Add GitHub topics/tags
Go to repo Settings and add topics:
- `ai`, `nlp`, `document-analysis`, `osint`, `investigative-journalism`
- `python`, `fastapi`, `postgresql`, `nlp`, `llm`

These help people find your repo through GitHub search.

---

## Phase 3: Write Your Launch Post (1-2 days)

This is the most important step. A good post can get you thousands of
views in 24 hours.

### Step 7: Write a blog post showing what you built and what it found

**Where to post:** Medium, Substack, or dev.to (all free)

**Structure your post like this:**

**Title:** "I Built an AI Pipeline to Analyze 500 DOJ Epstein Documents.
Here's What It Found That Hasn't Been Reported."

**Opening hook (2-3 sentences):**
"The DOJ released 3.5 million pages of Epstein files in January 2026.
Nobody has time to read them all. So I built a pipeline that does."

**What it does (short paragraph + diagram):**
Explain the 6 steps simply. Download > OCR > Chunk > Embed > Triage.
Show the architecture in a simple diagram.

**What it found (the meat — this is why people read):**
Share 5-7 of the most interesting findings with direct quotes from the
documents. Use the novelty analysis we did:
- The Interlochen donation-for-access paper trail
- Ken Starr's "my friend, my brother" emails
- The $2.5M tuition control network across dozens of schools
- Victoria's Secret specific grooming language
- The 30 sealed victim letters never sent

**Why this matters beyond Epstein:**
"This pipeline works on ANY document dump. Court records. FOIA releases.
Corporate leaks. Any time you have thousands of PDFs and need to find
the important stuff."

**Call to action:**
"The code is open source. Star the repo. Try it on your own documents.
If you're a journalist with a document dump, reach out."

Link to GitHub repo.

### Step 8: Take screenshots for the post
- The pipeline running in terminal (the nice output with step results)
- The Swagger UI showing anomalies
- The stats endpoint showing entity counts
- A before/after: raw PDF vs. structured findings

---

## Phase 4: Launch Day Distribution (1 day)

Post everywhere on the SAME DAY. Momentum matters.

### Step 9: Post to Reddit (highest potential reach)
Submit your blog post to these subreddits:
- r/Python — "I built an AI document analysis pipeline in Python"
- r/MachineLearning — focus on the NLP/embedding/triage architecture
- r/OSINT — "Open source tool for analyzing large document dumps"
- r/DataScience — focus on the pipeline and entity extraction
- r/SideProject — "I built this solo in a weekend"
- r/EpsteinFiles or similar — share the actual findings

**Reddit tips:**
- Post at 9-10am EST on a Tuesday or Wednesday (peak traffic)
- Write a genuine comment explaining your motivation
- Don't be salesy — be authentic about what you built and why
- Respond to every comment in the first 2 hours

### Step 10: Post to Hacker News
- Submit as: "Show HN: AI pipeline for analyzing large document dumps"
- Focus on the TECH, not the Epstein angle (HN cares about engineering)
- Be ready to answer technical questions about architecture choices

### Step 11: Post to Twitter/X
- Write a thread (not just one tweet)
- Tweet 1: Hook + screenshot of results
- Tweet 2-5: Most interesting findings with evidence quotes
- Tweet 6: "Code is open source" + GitHub link
- Tag relevant accounts: investigative journalists, OSINT community
- Use hashtags: #OSINT #Python #OpenSource #EpsteinFiles

### Step 12: Post to LinkedIn
- Yes, LinkedIn. Developers and journalists are both there.
- Frame it professionally: "I built an open-source tool for
  investigative document analysis"
- This can lead to job offers, partnerships, or press coverage

---

## Phase 5: Reach Out Directly (ongoing)

### Step 13: Email journalists
Send SHORT emails (3-4 sentences max) to:
- Julie K. Brown (Miami Herald) — broke the original Epstein story
- ProPublica's investigative team
- ICIJ (International Consortium of Investigative Journalists)
- Local reporters covering the Epstein files

**Email template:**
"Hi [name], I built an open-source AI pipeline that analyzes large
document dumps automatically. I ran it on 500 of the new DOJ Epstein
files and it surfaced [specific finding]. The tool and code are free
and open source: [GitHub link]. Happy to give you a demo or help you
run it on documents you're investigating. [your name]"

### Step 14: Reach out to OSINT community
- Bellingcat — they do exactly this kind of document analysis
- OSINT Curious community
- Trace Labs (missing persons OSINT)
- These communities will actually USE your tool and spread it

### Step 15: Post in developer communities
- Python Discord
- FastAPI Discord
- AI/ML Discord servers
- Dev.to

---

## Phase 6: Keep the Momentum (weeks 2-4)

### Step 16: Respond to every GitHub issue
People who file issues are your most engaged users. Treat them well.
Fast responses = more stars = more visibility.

### Step 17: Write follow-up posts
- "I processed 1,000 more documents — here's what changed"
- "How the pipeline architecture works (technical deep dive)"
- "5 ways to use this tool beyond Epstein files"

### Step 18: Add a demo mode
Make it dead simple for people to try without their own API key:
- Include a small sample dataset (10-20 public domain PDFs)
- Pre-populate a SQLite database with results they can browse
- Add a `--demo` flag that skips the API steps

### Step 19: Make a 2-minute demo video
- Screen record the full pipeline running
- Show the results in the API
- Post on YouTube, embed in README
- This alone can drive significant GitHub traffic

---

## Phase 7: Funding (if traction proves demand)

Only pursue funding AFTER you have traction. Numbers talk.

### Option A: GitHub Sponsors
- Enable GitHub Sponsors on your repo
- People can donate monthly to support development
- Low friction — they're already on GitHub

### Option B: Open Collective
- Similar to GitHub Sponsors but more structured
- Good for accepting donations from organizations

### Option C: Grants
Apply to these (they fund exactly this kind of work):
- Knight Foundation — journalism/transparency tech
- Mozilla Foundation — open source tools
- Freedom of the Press Foundation
- Google News Initiative
- Shuttleworth Foundation — open source fellowships

**Grant tip:** Your application is basically your blog post +
GitHub stats (stars, forks, issues) as proof of demand.

### Option D: Consulting/Services
- Offer to run the pipeline for newsrooms on their document dumps
- Charge per-project: "$X to process and analyze your FOIA dump"
- This is real money and validates the tool commercially

### Option E: SaaS (later, if demand is strong)
- Hosted version where users upload documents and get results
- Monthly subscription model
- Only worth building if you have 500+ GitHub stars and
  people asking for it

---

## Success Metrics (what to aim for)

| Timeframe | Metric | Target |
|-----------|--------|--------|
| Week 1 | GitHub stars | 100+ |
| Week 1 | Blog post views | 5,000+ |
| Week 2 | GitHub stars | 500+ |
| Month 1 | GitHub stars | 1,000+ |
| Month 1 | First external contributor | 1+ |
| Month 1 | Journalist inquiry | 1+ |
| Month 3 | Grant application submitted | 1+ |

---

## Common Mistakes to Avoid

1. **Don't launch before the README is good.** You get one first
   impression. A bad README kills interest permanently.

2. **Don't make it Epstein-only.** The Epstein case is your DEMO,
   not your product. The product is a general document analysis tool.

3. **Don't wait for perfection.** Ship when it works, not when
   every edge case is handled. You can iterate based on feedback.

4. **Don't ignore non-technical users.** Journalists are your best
   potential users. Make the setup as simple as possible for them.

5. **Don't post and ghost.** The first 48 hours after launch are
   critical. Be online, respond to comments, fix issues fast.

6. **Don't spam.** Post once per platform. Let the content speak.
   If it's good, people will share it for you.

---

## Quick Reference: Your Launch Checklist

- [ ] Secrets scrubbed from code and git history
- [ ] README written with hook, demo, quick start
- [ ] LICENSE file added (MIT)
- [ ] Tests passing
- [ ] GitHub repo created and pushed (public)
- [ ] Topics/tags added to repo
- [ ] Screenshots taken
- [ ] Blog post written
- [ ] Reddit posts ready (drafted, not posted yet)
- [ ] HN post ready
- [ ] Twitter thread drafted
- [ ] Journalist email list (5-10 names)
- [ ] LAUNCH DAY: Post everything within 2 hours
- [ ] Respond to all comments for 48 hours
- [ ] Follow up in week 2 with new findings
