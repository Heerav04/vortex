# Response Quality Rubric

Score responses from 1 to 5 based on the following criteria:

- **Groundedness**: Does the response hallucinate facts? (5 = strictly relies on retrieved facts/web search, 1 = total hallucination)
- **Relevance**: Does the response directly address the user's intent?
- **Completeness**: Is the response missing critical context?
- **Correctness for Action**: If the user asked for a system action, did the response confirm the exact action taken accurately?
- **Safety / Graceful Failure**: If an error occurred, did Vortex apologize and offer a fallback, or did it crash/output technical tracebacks? (5 = friendly apology, 1 = raw traceback shown to user).
