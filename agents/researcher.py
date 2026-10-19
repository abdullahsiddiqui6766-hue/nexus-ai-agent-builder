from agents.base import BaseAgent
from tools.search.base import SearchProvider


class ResearcherAgent(BaseAgent):
    """Research a topic using AI and optional web search."""

    def __init__(
        self,
        name,
        groq_client,
        system_prompt,
        search_provider: SearchProvider | None = None,
    ) -> None:
        super().__init__(
            name=name,
            groq_client=groq_client,
            system_prompt=system_prompt,
        )

        self.search_provider = search_provider

    def run(self, task: str, use_search: bool = False) -> str:
        """Research a task using available search results."""

        if not task or not task.strip():
            raise ValueError("Research task cannot be empty.")

        task = task.strip()
        search_context = ""
        sources = []

        if use_search:
            if self.search_provider is None:
                raise RuntimeError(
                    "Web search is enabled but no search provider is configured."
                )

            # Search using the configured provider.
            try:
                results = self.search_provider.search(
                    query=task,
                    max_results=8,
                )
            except Exception as exc:
                raise RuntimeError(
                    "Web search failed. Check the search provider "
                    "and internet connection."
                ) from exc

            if results:
                search_context = (
                    "\n\nWEB SEARCH RESULTS\n"
                    "These results are search snippets, not full webpage contents.\n"
                )

                for index, result in enumerate(results, start=1):
                    title = getattr(result, "title", "Untitled source")
                    url = getattr(result, "url", "")
                    snippet = getattr(result, "snippet", "")

                    source = {
                        "title": title,
                        "url": url,
                        "snippet": snippet,
                    }
                    sources.append(source)

                    search_context += (
                        f"\nSOURCE {index}\n"
                        f"Title: {title}\n"
                        f"URL: {url}\n"
                        f"Snippet: {snippet}\n"
                    )

            else:
                search_context = (
                    "\n\nWEB SEARCH STATUS\n"
                    "No search results were returned. "
                    "Do not pretend that live information was verified.\n"
                )

        prompt = f"""
You are the Researcher Agent in a multi-agent AI workspace.

YOUR TASK
{task}

{search_context}

RESEARCH REQUIREMENTS

1. Identify the main questions that must be answered to complete the task.
2. Organize the research into useful sections with clear headings.
3. Answer the requested questions directly instead of merely explaining
   where the user could find the answers.
4. Prioritize the supplied search results when web research is enabled.
5. Use only claims that are reasonably supported by the available evidence.
6. Never invent player statistics, dates, match results, quotations,
   URLs, or other factual details.
7. Do not claim to have opened or verified a webpage when only a
   search snippet is available.
8. Cite supplied source URLs next to the claims they support.
9. If a requested fact cannot be established from the available evidence,
   explicitly mark it as "Not verified from available sources".
10. If the task requests current information, distinguish current,
    historical, and undated information.
11. Do not replace missing information with instructions telling the user
    to search another website.
12. Avoid repeating the same fact in multiple sections.

OUTPUT FORMAT

## Research Objective
Briefly explain what the task requires.

## Key Findings
Present the most relevant supported findings.

## Detailed Research
Answer the specific questions contained in the task.

## Limitations
List any requested information that could not be verified.

## Sources
List the supplied source URLs and their titles when available.

IMPORTANT:
Search snippets are not equivalent to reading complete webpages.
Never claim that information is fully verified solely because a URL
appears in the search results.

Produce useful research notes for the Content Agent.
"""

        research_notes = self.generate(prompt)

        if not research_notes or not research_notes.strip():
            raise RuntimeError(
                "Researcher Agent returned empty research notes."
            )

        return research_notes.strip()