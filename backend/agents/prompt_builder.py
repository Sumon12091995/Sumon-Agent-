def _build_prompt(prompt, context="", debate_context=None):
    base = f"Question/Topic: {prompt}"
    if context:
        base += f"\n\nWeb Search & Background Context:\n{context}"
    if debate_context:
        base += f"\n\nPrevious Debate / Opinions from other Agents:\n{debate_context}\n\nAnalyze the opinions above, point out any flaws, agreements, or disagreements, and provide your refined response."
    return base
