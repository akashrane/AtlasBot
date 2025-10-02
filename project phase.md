# Project Roadmap: Atlas Bot (Agentic AI Word Game)

---

##  Phase 1: Foundations (Core Game + Simple Bot)

**Goal:** Build a working Atlas game with a baseline bot.  
**Timeline:** 2–3 weeks

 **Tasks:**
- Basic web app (HTML/React hosted on GitHub Pages).
- Wordlist JSON for offline validation.
- Game engine: validate words, enforce last-letter rule, prevent repeats.
- Simple bot: choose **any random valid word**.
- Game state stored in localStorage.
- UI showing: last letter, used words, current turn.

**Deliverable:**
- Playable Atlas game (user vs bot) in browser.
- Report section: *Game rules, initial implementation, basic evaluation.*

---

##  Phase 2: Intelligent Bot (Strategies + Analytics)

**Goal:** Add strategy and intelligence → move from toy app to research-worthy project.  
**Timeline:** 4–5 weeks

 **Tasks:**
- **Graph Representation:** Words as nodes, edges = valid transitions.
- **Strategy Modes:**
  - Random (baseline).
  - Longest word.
  - Rarest-starting-letter trap.
  - Graph-based minimax (1–2 lookahead moves).
- **Difficulty levels** (Easy/Medium/Hard).
- **Analytics dashboard:** Track most-used words, average game length, win rates by difficulty.
- **Leaderboard:** Scores stored in browser (or optional small backend).

**Deliverable:**
- Demo where you can switch bot strategies and difficulty.
- Analytics page with plots.
- Report section: *Comparison of strategies (win rates, complexity).*

---

##  Phase 3: Agentic AI (RL + Explainability + Research)

**Goal:** Make it a true **agentic Master’s project**.  
**Timeline:** 5–6 weeks

 **Tasks:**
- **Reinforcement Learning Bot**: Train via self-play.
  - Reward = survive longer / win.
  - Train Q-learning / policy gradient agent.
- **Adaptive Bot:** Adjust difficulty based on player skill.
- **Explainable Moves:** Bot explains reasoning (e.g., “I played *xylophone* because it forces you to start with E”).
- **Human-like personality:** Friendly / aggressive / tricky modes.
- **Extensions:**
  - Timed mode (user must answer in 5s).
  - Themed Atlas (only cities, animals, etc.).
  - Voice input/output.

**Deliverable:**
- A research-grade Atlas Bot that feels like a smart opponent.
- Evaluation study: Compare random vs heuristic vs RL strategies.
- Report section: *Results, analysis, future scope.*

---

#  Final Deliverables (for Master’s submission)

1. **Live Demo:** GitHub Pages app.  
2. **Codebase:** Well-documented repo.  
3. **Dashboard:** Game analytics & performance charts.  
4. **Research Paper Report:**
   - Problem definition
   - Game modeling (graph/decision problem)
   - Strategies & algorithms
   - Experimental results (graphs, win % comparisons)
   - Conclusions & future work
