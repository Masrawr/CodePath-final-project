# System Architecture — Glitch Investigator AI

```mermaid
flowchart TD
    User([👤 User pastes Python code]) --> Guard{Guardrail:<br/>valid Python?}
    Guard -- no --> Reject[Reject / ask again]
    Guard -- yes --> Retriever[🔎 Retriever<br/>RAG over bug-pattern KB]

    Retriever --> Agent

    subgraph Agent [🤖 Agent: plan → detect → fix → verify]
        LLM[Gemini detector<br/>structured bug report]
        Clf[🎯 Specialized classifier<br/>tags bug category]
        Verify[Verify loop<br/>apply fix + re-detect]
        LLM --> Clf --> Verify
        Verify -- not fixed --> LLM
    end

    Agent --> Eval[📊 Evaluator / Tester<br/>precision·recall, classifier-vs-detector,<br/>consistency, guardrail tests]
    Eval --> Output([📝 Bug report: line · category · fix · confidence])

    Output --> Human{{👀 Human review:<br/>accept / reject findings}}
    Human -. feedback .-> Retriever

    classDef ai fill:#e8f0fe,stroke:#4285f4;
    classDef check fill:#fef7e0,stroke:#f9ab00;
    class Retriever,LLM,Clf,Agent ai;
    class Guard,Eval,Human,Verify check;
```

**How to read it:** input flows left-to-right through a guardrail, retrieval, and an agentic detect→classify→verify loop; the **checker components** (amber) are where testing and humans validate the AI — the guardrail screens input, the self-verify loop re-runs the detector on the fixed code, the evaluator measures reliability, and a human reviews the final findings and feeds corrections back.