<br>

<div align="center">

<a href="#"><img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=42&duration=2800&pause=1200&color=3B82F6&center=true&vCenter=true&width=700&lines=InkAI;From+Idea+to+Novel;%E4%BB%8E%E5%88%9B%E6%84%8F%E5%88%B0%E6%88%90%E5%93%81" /></a>

<br>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/AI_x_Novel_Generation-25_Agents_%C2%B7_5_Stages_%C2%B7_6_Dimensions-3B82F6?style=for-the-badge&labelColor=0F172A" />
  <img src="https://img.shields.io/badge/AI_x_Novel_Generation-25_Agents_%C2%B7_5_Stages_%C2%B7_6_Dimensions-3B82F6?style=for-the-badge&labelColor=1E293B" />
</picture>

<br>
<br>

<table>
<tr>
<td align="center" width="160"><b style="font-size:28px">25</b><br><sub>Agents</sub></td>
<td align="center" width="160"><b style="font-size:28px">5</b><br><sub>Pipeline Stages</sub></td>
<td align="center" width="160"><b style="font-size:28px">6D</b><br><sub>Quality Audit</sub></td>
<td align="center" width="160"><b style="font-size:28px">70+</b><br><sub>Genre Tags</sub></td>
<td align="center" width="160"><b style="font-size:28px">∞</b><br><sub>Chapter Continuation</sub></td>
</tr>
</table>

<br>

<a href="#quickstart"><img src="https://img.shields.io/badge/⚡_Quick_Start-3B82F6?style=for-the-badge&logo=rocket&logoColor=white&labelColor=1E293B" /></a>
&nbsp;
<a href="#architecture"><img src="https://img.shields.io/badge/🏗_Architecture-6366F1?style=for-the-badge&labelColor=1E293B" /></a>
&nbsp;
<a href="#api"><img src="https://img.shields.io/badge/🔌_API_Reference-8B5CF6?style=for-the-badge&labelColor=1E293B" /></a>

</div>

---

<div align="center">

### &nbsp;&nbsp;🎯 A Complete AI Novel Writing Factory&nbsp;&nbsp;

</div>

**InkAI** is not an "AI autocomplete" tool. It is a full-stack fiction generation framework.

Give it *one sentence* — "I want to write an urban suspense thriller" — and 25 specialized AI agents spring into action. They analyze your intent, recommend genre tags, design characters with psychological depth (Big Five personality model), construct a three-act narrative architecture, write chapter after chapter at 2,000-5,000 words each, and then audit every output across 6 quality dimensions — rewriting anything that falls below the 80-point threshold. The result is a coherent, consistent long-form novel with proper foreshadowing, character arcs, and world-building.

---

```mermaid
graph LR
    A("<b>🎯 Input</b><br/>One-sentence<br/>description") --> B("<b>🏷 Tags</b><br/>4D genre<br/>classification")
    B --> C("<b>👤 Characters</b><br/>Big Five<br/>personality model")
    C --> D("<b>📖 Storyline</b><br/>Three-act structure<br/>chapter outline")
    D --> E("<b>✍ Write</b><br/>2000-5000<br/>words/chapter")
    E --> F{"<b>✅ Audit</b><br/>5D scoring"}
    F -->|"Pass ≥80"| G("<b>📦 Save</b><br/>to library")
    F -->|"Retry <80"| H("<b>🔧 Improve</b><br/>auto-rewrite")
    H --> E

    style A fill:#2563EB,color:#fff,stroke:#1D4ED8,stroke-width:2px
    style B fill:#4F46E5,color:#fff,stroke:#4338CA,stroke-width:2px
    style C fill:#7C3AED,color:#fff,stroke:#6D28D9,stroke-width:2px
    style D fill:#9333EA,color:#fff,stroke:#7E22CE,stroke-width:2px
    style E fill:#DB2777,color:#fff,stroke:#BE185D,stroke-width:2px
    style F fill:#D97706,color:#fff,stroke:#B45309,stroke-width:2px
    style G fill:#059669,color:#fff,stroke:#047857,stroke-width:2px
    style H fill:#DC2626,color:#fff,stroke:#B91C1C,stroke-width:2px
```

---

<div id="architecture"></div>

<div align="center">

### &nbsp;&nbsp;🏗 System Architecture&nbsp;&nbsp;

</div>

```mermaid
graph TB
    subgraph L1["&nbsp;&nbsp;🖥 PRESENTATION&nbsp;&nbsp;"]
        WEB("<b>Web UI</b><br/>Bootstrap 5 SPA<br/>Interactive wizard<br/>Real-time monitor")
    end

    subgraph L2["&nbsp;&nbsp;🌐 API GATEWAY&nbsp;&nbsp;"]
        FLASK("<b>Flask REST</b><br/>Routing · Validation<br/>Orchestration · State")
    end

    subgraph L3["&nbsp;&nbsp;⚙ ORCHESTRATION&nbsp;&nbsp;"]
        WF("<b>InkAIWorkflow</b><br/>140KB state machine<br/>Creation pipeline")
        QCE("<b>Continuation Engine</b><br/>Async chapter<br/>generation loop")
    end

    subgraph L4["&nbsp;&nbsp;🤖 AGENT LAYER · 25 Agents&nbsp;&nbsp;"]
        direction LR
        A1("<b>Creation</b> ×5")
        A2("<b>Continuation</b> ×3")
        A3("<b>Assessment</b> ×6")
        A4("<b>Improvement</b> ×11")
    end

    subgraph L5["&nbsp;&nbsp;📦 INFRASTRUCTURE&nbsp;&nbsp;"]
        direction LR
        CORE("<b>Core Services</b><br/>Knowledge Graph<br/>Context Selector")
        DATA("<b>Data Layer</b><br/>JSON File Store<br/>Zero DB Dependencies")
    end

    WEB --> FLASK
    FLASK --> WF
    FLASK --> QCE
    WF --> L4
    QCE --> L4
    L4 --> CORE
    CORE --> DATA

    style L1 fill:#EFF6FF,stroke:#3B82F6,stroke-width:2px
    style L2 fill:#EEF2FF,stroke:#6366F1,stroke-width:2px
    style L3 fill:#F3E8FF,stroke:#8B5CF6,stroke-width:2px
    style L4 fill:#FCE7F3,stroke:#EC4899,stroke-width:2px
    style L5 fill:#ECFDF5,stroke:#10B981,stroke-width:2px
```

---

<div align="center">

### &nbsp;&nbsp;🔄 Intelligent Continuation Engine&nbsp;&nbsp;

</div>

```mermaid
sequenceDiagram
    autonumber
    participant K as 📚 Knowledge Base
    participant S as 🧠 Storyline Planner
    participant W as ✍ Chapter Writer
    participant A as 🔍 Audit Matrix
    participant I as 🔧 Improver

    rect rgb(239, 246, 255)
        Note over K,I: Per-Chapter Quality Loop
        W->>K: Extract prior state
        K-->>S: Characters · Plot · Foreshadowing · World rules
        S->>S: Generate chapter outline
        S-->>W: Scene beats · Character dispatch · Tone
        W->>W: Write chapter body
        W-->>A: 2000-5000 word draft
        A->>A: 6-dimension parallel audit
        alt Score above threshold
            A-->>K: Pass · Save · Update knowledge graph
        else Score below threshold
            A-->>I: Trigger targeted improvement
            I-->>W: Rewrite with feedback
        end
    end
```

<table align="center">
<tr>
<td align="center" width="150"><b>Character<br/>Consistency</b><br/><sub>Behavior · Voice<br/>Arc trajectory</sub></td>
<td align="center" width="150"><b>Plot<br/>Logic</b><br/><sub>Causality · No holes<br/>Closure</sub></td>
<td align="center" width="150"><b>World<br/>Coherence</b><br/><sub>Rules · Setting<br/>Continuity</sub></td>
<td align="center" width="150"><b>Style<br/>Fidelity</b><br/><sub>Tone · Narrative<br/>Pacing</sub></td>
<td align="center" width="150"><b>Reader<br/>Experience</b><br/><sub>Tension · Emotion<br/>Readability</sub></td>
<td align="center" width="150"><b>Long-Term<br/>Threads</b><br/><sub>Cross-volume clues<br/>Grand finale</sub></td>
</tr>
</table>

---

<div id="quickstart"></div>

<div align="center">

### &nbsp;&nbsp;⚡ Quick Start&nbsp;&nbsp;

</div>

```bash
git clone https://github.com/yan2959088709/InkAI-.git
cd InkAI-
pip install -r requirements.txt
```

Edit `config.py` with your API credentials, then:

```bash
python start_web.py
# → Open http://localhost:5000
```

<table align="center">
<tr>
<td align="center" width="300"><b>API_KEY</b><br/><sub>Zhipu AI GLM-4.5-flash</sub></td>
<td align="center" width="300"><b>BASE_URL</b><br/><sub>OpenAI-compatible · Swap any model</sub></td>
<td align="center" width="300"><b>QUALITY_THRESHOLD</b><br/><sub>Pass line · Default 80/100</sub></td>
</tr>
</table>

> **Zero infrastructure**: Python 3.8+ only. No database. No Docker. Copy the directory and run. Windows / macOS / Linux.

---

<div id="api"></div>

<div align="center">

### &nbsp;&nbsp;🔌 REST API&nbsp;&nbsp;

</div>

All endpoints follow a uniform contract:

```json
{ "ok": true,  "data": { } }
{ "ok": false, "error": "..." }
```

<table>
<tr><th width="10%">Method</th><th width="45%">Endpoint</th><th width="45%">Description</th></tr>
<tr><td><code>POST</code></td><td><code>/api/novels</code></td><td>Create new novel project</td></tr>
<tr><td><code>POST</code></td><td><code>/api/novels/&lt;id&gt;/tags</code></td><td>AI-powered tag recommendation</td></tr>
<tr><td><code>POST</code></td><td><code>/api/novels/&lt;id&gt;/characters</code></td><td>Generate character profiles</td></tr>
<tr><td><code>POST</code></td><td><code>/api/novels/&lt;id&gt;/storyline</code></td><td>Build three-act storyline</td></tr>
<tr><td><code>POST</code></td><td><code>/api/novels/&lt;id&gt;/chapters</code></td><td>Write first chapter</td></tr>
<tr><td><code>POST</code></td><td><code>/api/novels/&lt;id&gt;/continue</code></td><td>Start async continuation</td></tr>
<tr><td><code>GET</code></td><td><code>/api/novels/&lt;id&gt;/continue/status</code></td><td>Poll continuation progress</td></tr>
<tr><td><code>POST</code></td><td><code>/api/novels/&lt;id&gt;/continue/stop</code></td><td>Stop continuation task</td></tr>
<tr><td><code>GET</code></td><td><code>/api/novels/&lt;id&gt;</code></td><td>Fetch full novel dataset</td></tr>
<tr><td><code>GET</code></td><td><code>/api/novels/&lt;id&gt;/chapter/&lt;n&gt;</code></td><td>Retrieve chapter by number</td></tr>
</table>

---

<div align="center">

### &nbsp;&nbsp;📂 Project Map&nbsp;&nbsp;

</div>

```
InkAI/
│
├── 🤖 agents/                   ── 25 specialized AI agents ──
│   ├── tag_selector.py            Label recommendation
│   ├── character_creator.py       Big Five personality design
│   ├── storyline_generator.py     Three-act narrative architecture
│   ├── chapter_writer.py          Long-form prose generation
│   ├── quality_assessor.py        Multi-dimensional scoring
│   ├── novel_continuation_agent.py Continuation orchestrator
│   ├── continuation_storyline_*.py Per-chapter plot planning
│   ├── continuation_chapter_*.py  Chapter writing & improvement
│   ├── continuation_*_assessor.py Six consistency auditors
│   └── continuation_*_improver.py Eleven targeted fixers
│
├── ⚙ core/                     ── Knowledge & context services ──
│   ├── core_knowledge_manager.py  Graph-based knowledge extraction
│   ├── dynamic_knowledge_manager.py Real-time state tracking
│   └── intelligent_context_selector.py Smarter than a sliding window
│
├── 🖥 frontend/                 ── Web interface ──
│   ├── index.html                 Bootstrap 5 SPA
│   ├── app.js                     Client logic
│   └── styles.css                 Custom design system
│
├── ⚡ app.py                      Flask API server (1,500 LOC)
├── ⚡ inkai_workflow_optimized.py Core engine (1,650 LOC)
├── ⚡ quick_continuation_executor.py Async loop (900 LOC)
├── ⚡ data_manager.py             Persistence layer
├── ⚡ workflow_context.py         State container
├── ⚡ base_agent.py               LLM client · JSON repair · retry
├── ⚡ config.py                   Global configuration
│
└── 💾 data/                     ── Runtime storage ──
    ├── novels/<uuid>/             One directory per novel
    └── knowledge_graphs/          Persistent graph snapshots
```

---

<br>

<div align="center">

<img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white" />
<img src="https://img.shields.io/badge/Bootstrap-5-7952B3?style=flat-square&logo=bootstrap&logoColor=white" />
<img src="https://img.shields.io/badge/GLM-4.5-1A73E8?style=flat-square&logo=googleearthengine&logoColor=white" />
<img src="https://img.shields.io/badge/License-MIT-10B981?style=flat-square" />
<img src="https://img.shields.io/badge/Version-1.10-3B82F6?style=flat-square" />

<br>
<br>

<sub>Built for storytellers · Powered by LLMs</sub>

</div>
