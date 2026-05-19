import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .memory import VortexMemory, VortexProfile


@dataclass
class PlanStep:
    tool: str
    action: str
    params: Dict[str, Any]


@dataclass
class VortexPlan:
    mode: str
    steps: List[PlanStep]
    summary: str


class VortexPlanner:
    """
    Lightweight rule-based planner that determines the best tool 
    path for a user's query.
    """

    def __init__(self, memory: VortexMemory):
        self.memory = memory

    def create_plan(
        self,
        query: str,
        screenshot_text: Optional[str] = None,
    ) -> VortexPlan:
        q = (query or "").lower().strip()

        def _extract_scope_and_target(raw_query: str) -> tuple[Optional[str], str]:
            ql = (raw_query or "").lower().strip()
            scope = None
            scope_patterns = [
                (r"\bin\s+desktop\b", "Desktop"),
                (r"\bin\s+documents\b", "Documents"),
                (r"\bin\s+downloads\b", "Downloads"),
                (r"\bin\s+([a-z])\s+drive\b", None),
            ]
            for pat, fixed_scope in scope_patterns:
                m = re.search(pat, ql)
                if not m:
                    continue
                if fixed_scope:
                    scope = fixed_scope
                else:
                    scope = f"{m.group(1).upper()}:"
                ql = re.sub(pat, " ", ql).strip()
                break

            cleaned = ql
            cleaned = re.sub(r"^(open|find|search)\s+", "", cleaned).strip()
            cleaned = re.sub(r"\b(file|folder|pdf|docx?|xlsx?|pptx?|txt)\b", " ", cleaned)
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            return scope, cleaned

        # --- Filesystem commands (High Priority) --------------------------
        if q.startswith("open downloads") or "open downloads folder" in q:
            return VortexPlan(
                mode="filesystem",
                steps=[PlanStep(tool="filesystem", action="open_folder", params={"path": "Downloads"})],
                summary="Opening Downloads.",
            )
        if q.startswith("open documents") or "open documents folder" in q:
            return VortexPlan(
                mode="filesystem",
                steps=[PlanStep(tool="filesystem", action="open_folder", params={"path": "Documents"})],
                summary="Opening Documents.",
            )
        if q.startswith("open desktop") or "open desktop folder" in q:
            return VortexPlan(
                mode="filesystem",
                steps=[PlanStep(tool="filesystem", action="open_folder", params={"path": "Desktop"})],
                summary="Opening Desktop.",
            )
        if q.startswith("open ") and " drive" in q:
            # e.g. "open d drive"
            m = re.search(r"open\s+([a-z])\s+drive", q)
            if m:
                return VortexPlan(
                    mode="filesystem",
                    steps=[PlanStep(tool="filesystem", action="open_drive", params={"drive": m.group(1).upper()})],
                    summary=f"Opening {m.group(1).upper()} drive.",
                )

        if q.startswith("open ") and " in " in q:
            scope, target = _extract_scope_and_target(query)
            if target:
                kind = "folder" if " folder" in q else "file"
                return VortexPlan(
                    mode="filesystem",
                    steps=[
                        PlanStep(
                            tool="filesystem",
                            action="find_and_open",
                            params={"query": target, "scope": scope, "kind": kind},
                        )
                    ],
                    summary=f"Opening '{target}' from {scope or 'your PC'}...",
                )

        if q.startswith("find ") or q.startswith("search "):
            # Basic rule-based parse:
            # - scope: "in d drive", "in downloads", "in c drive"
            # - size: "around 9.5 gb"
            scope = None
            kind = "any"
            if " folder" in q:
                kind = "folder"
            if " file" in q:
                kind = "file"

            m_scope_drive = re.search(r"in\s+([a-z])\s+drive", q)
            if m_scope_drive:
                scope = m_scope_drive.group(1).upper() + ":"
            elif " in downloads" in q:
                scope = "Downloads"
            elif " in documents" in q:
                scope = "Documents"
            elif " in desktop" in q:
                scope = "Desktop"

            m_size = re.search(r"(around|about|~)\s*([0-9]+(\.[0-9]+)?)\s*(gb|g|mb|m|kb|k|tb|t)", q)
            if m_size:
                approx = f"{m_size.group(2)}{m_size.group(4)}"
                name_part = query
                return VortexPlan(
                    mode="filesystem",
                    steps=[
                        PlanStep(
                            tool="filesystem",
                            action="search_by_size",
                            params={"query": name_part, "approx_size": approx, "scope": scope, "kind": "file"},
                        )
                    ],
                    summary="Searching files by name and size...",
                )
            return VortexPlan(
                mode="filesystem",
                steps=[PlanStep(tool="filesystem", action="search", params={"query": query, "scope": scope, "kind": kind})],
                summary="Searching your PC...",
            )

        # --- Modes --------------------------------------------------------
        if "rescan apps" in q or "scan apps" in q or "refresh apps" in q:
            return VortexPlan(
                mode="system",
                steps=[PlanStep(tool="system", action="scan_apps", params={})],
                summary="Rescan installed applications.",
            )

        if "interview" in q or "prep" in q:
            return self._plan_interview_prep(query)
        if "leetcode" in q or "dsa" in q or "study" in q:
            return self._plan_study(query)
        if "productivity" in q or "focus" in q:
            return self._plan_productivity(query)
        if "game" in q or "gaming" in q:
            return self._plan_gaming(query)
        if "error" in q or "screen" in q:
            return self._plan_screen_error(query, screenshot_text)

        # --- Capabilities / Info ------------------------------------------
        if any(x in q for x in ["what can you do", "what do you do", "what you do", "help me", "commands"]):
            return VortexPlan(
                mode="chat",
                steps=[PlanStep(tool="llm", action="chat", params={"query": "Briefly list your top 3 capabilities like opening apps, searching the web, and system control in a witty way."})],
                summary="Display capabilities.",
            )

        # --- Deep Link Patterns (e.g. "search X on YouTube") ---------------
        import urllib.parse as _urlparse

        _DEEP_SEARCH = {
            # site keyword → search URL template (use {q} for query)
            "youtube":   "https://www.youtube.com/results?search_query={q}",
            "spotify":   "https://open.spotify.com/search/{q}",
            "github":    "https://github.com/search?q={q}",
            "google":    "https://www.google.com/search?q={q}",
            "reddit":    "https://www.reddit.com/search/?q={q}",
            "linkedin":  "https://www.linkedin.com/search/results/all/?keywords={q}",
            "netflix":   "https://www.netflix.com/search?q={q}",
            "twitter":   "https://twitter.com/search?q={q}",
            "x":         "https://x.com/search?q={q}",
            "amazon":    "https://www.amazon.in/s?k={q}",
            "leetcode":  "https://leetcode.com/search?q={q}",
            "npm":       "https://www.npmjs.com/search?q={q}",
            "pypi":      "https://pypi.org/search/?q={q}",
        }

        # Patterns: "search X on site", "play X on site", "find X on site", "look up X on site"
        _deep_match = re.search(
            r"(?:search|play|find|look up|open|show)\s+(.+?)\s+on\s+(\w+)$", q
        )
        if _deep_match:
            search_term = _deep_match.group(1).strip()
            site        = _deep_match.group(2).strip().lower()
            if site in _DEEP_SEARCH:
                url = _DEEP_SEARCH[site].replace("{q}", _urlparse.quote_plus(search_term))
                return VortexPlan(
                    mode="browser",
                    steps=[PlanStep(tool="browser", action="open_url", params={"url": url})],
                    summary=f"Searching '{search_term}' on {site.capitalize()}...",
                )

        # "compose email" / "write email" / "new email" → Gmail compose
        if any(x in q for x in ["compose email", "write email", "new email", "send email"]):
            return VortexPlan(
                mode="browser",
                steps=[PlanStep(tool="browser", action="open_url",
                                params={"url": "https://mail.google.com/mail/u/0/#compose"})],
                summary="Opening Gmail compose window...",
            )

        # Website → URL map (handles "open gmail", "open gmail in chrome", etc.)
        _SITE_URLS = {
            "gmail":        "https://mail.google.com",
            "google mail":  "https://mail.google.com",
            "youtube":      "https://youtube.com",
            "chatgpt":      "https://chat.openai.com",
            "chat gpt":     "https://chat.openai.com",
            "github":       "https://github.com",
            "google":       "https://google.com",
            "instagram":    "https://instagram.com",
            "twitter":      "https://twitter.com",
            "x":            "https://x.com",
            "linkedin":     "https://linkedin.com",
            "netflix":      "https://netflix.com",
            "spotify":      "https://open.spotify.com",
            "reddit":       "https://reddit.com",
            "notion":       "https://notion.so",
            "whatsapp":     "https://web.whatsapp.com",
            "drive":        "https://drive.google.com",
            "google drive": "https://drive.google.com",
            "calendar":     "https://calendar.google.com",
            "meet":         "https://meet.google.com",
            "docs":         "https://docs.google.com",
            "sheets":       "https://sheets.google.com",
            "leetcode":     "https://leetcode.com",
        }

        _BROWSER_ALIASES = {
            "chrome": "google chrome", "google chrome": "google chrome",
            "edge": "microsoft edge", "firefox": "firefox",
            "brave": "brave", "browser": "google chrome",
        }

        if "open" in q:
            raw = q.replace("open", "").replace("vortex", "").replace(" please", "").strip()

            # Pattern: "open [site] in [browser]" → open URL directly in browser
            if " in " in raw:
                parts = raw.split(" in ", 1)
                site_part    = parts[0].strip()
                browser_part = parts[1].strip()

                # Is the left side a known website?
                if site_part in _SITE_URLS:
                    url = _SITE_URLS[site_part]
                    return VortexPlan(
                        mode="browser",
                        steps=[PlanStep(tool="browser", action="open_url", params={"url": url})],
                        summary=f"Opening {site_part} in your browser...",
                    )

                # Left is not a known site → open right side as app
                browser_app = _BROWSER_ALIASES.get(browser_part, browser_part)
                return VortexPlan(
                    mode="system",
                    steps=[PlanStep(tool="system", action="open_app", params={"query": browser_app})],
                    summary=f"Opening {browser_app}...",
                )

            # Split at 'and', 'search', 'tell' to isolate app name
            target = raw
            for sep in [" and ", " search ", " tell "]:
                target = target.split(sep)[0].strip()

            # Known website? → open URL directly (no app lookup needed)
            if target in _SITE_URLS:
                url = _SITE_URLS[target]
                return VortexPlan(
                    mode="browser",
                    steps=[PlanStep(tool="browser", action="open_url", params={"url": url})],
                    summary=f"Opening {target}...",
                )

            # App aliases
            _APP_ALIASES = {
                "mail":       "outlook",
                "browser":    "google chrome",
                "chrome":     "google chrome",
                "edge":       "microsoft edge",
                "code":       "visual studio code",
                "vscode":     "visual studio code",
                "vs code":    "visual studio code",
                "terminal":   "powershell",
                "word":       "microsoft word",
                "excel":      "microsoft excel",
                "powerpoint": "microsoft powerpoint",
                "teams":      "microsoft teams",
                "explorer":   "file explorer",
                "files":      "file explorer",
            }
            app_to_open = _APP_ALIASES.get(target, target)

            return VortexPlan(
                mode="system",
                steps=[PlanStep(tool="system", action="open_app", params={"query": app_to_open})],
                summary=f"Opening {app_to_open}...",
            )


        if "close" in q or "exit" in q or "quit" in q:
            raw_target = q.replace("close", "").replace("exit", "").replace("quit", "").replace("vortex", "").replace(" please", "").strip()
            return VortexPlan(
                mode="system",
                steps=[PlanStep(tool="system", action="close_app", params={"query": raw_target})],
                summary=f"Closing {raw_target}...",
            )

        if "volume" in q:
            m = re.search(r"(\d{1,3})", q)
            vol = int(m.group(1)) if m else 50
            return VortexPlan(
                mode="system",
                steps=[PlanStep(tool="system", action="set_volume", params={"percent": vol})],
                summary=f"Adjusting volume to {vol}%...",
            )

        if "music" in q or "song" in q or "youtube" in q:
            return VortexPlan(
                mode="coding",
                steps=[PlanStep(tool="browser", action="play_youtube_music", params={"query": query})],
                summary="Searching for music...",
            )

        # --- Real-time queries (news, scores, weather, time) ---------------
        # Time / Date
        time_words = ["time", "date", "day today", "what day"]
        if any(w in q for w in time_words) and len(q.split()) <= 6:
            return VortexPlan(
                mode="realtime",
                steps=[PlanStep(tool="realtime", action="time", params={})],
                summary="Checking the time...",
            )

        # News / Headlines
        news_words = ["news", "headline", "headlines", "happening", "latest update"]
        if any(w in q for w in news_words):
            return VortexPlan(
                mode="realtime",
                # Use grounded search for news - it's much better than raw scraping
                steps=[PlanStep(tool="realtime", action="grounded", params={"query": query})],
                summary="Fetching live news...",
            )

        # Live scores vs Schedule
        score_words = ["score", "match", "ipl", "cricket", "football", "nba", "fifa", "league", "playing"]
        if any(w in q for w in score_words):
            # If they ask "when" or "next", they want a schedule (Grounded LLM)
            # If they ask "score" or "match", they likely want live scores (Scraper)
            if any(w in q for w in ["when", "next", "tomorrow", "date", "upcoming", "who is"]):
                 return VortexPlan(
                    mode="realtime",
                    steps=[PlanStep(tool="realtime", action="grounded", params={"query": query})],
                    summary="Checking schedule...",
                )
            return VortexPlan(
                mode="realtime",
                steps=[PlanStep(tool="realtime", action="live_score", params={"query": query})],
                summary="Checking live scores...",
            )

        # Weather
        weather_words = ["weather", "temperature", "rain", "forecast", "climate"]
        if any(w in q for w in weather_words):
             # Grounded weather is more detailed
             return VortexPlan(
                mode="realtime",
                steps=[PlanStep(tool="realtime", action="grounded", params={"query": query})],
                summary="Checking weather...",
            )

        # General real-time questions ("what's trending", "current", "today", "latest")
        realtime_words = ["trending", "current", "right now", "today's", "live", "latest", "who is", "who won"]
        if any(w in q for w in realtime_words):
            return VortexPlan(
                mode="realtime",
                steps=[PlanStep(tool="realtime", action="grounded", params={"query": query})],
                summary="Searching for real-time info...",
            )

        if "search" in q or "google" in q:
            return VortexPlan(
                mode="general",
                steps=[PlanStep(tool="browser", action="web_search", params={"query": query})],
                summary="Searching the web...",
            )

        # --- Conversational / Handlers (High Priority Chat) ---------------
        greetings = [
            "hey", "hello", "hi", "vortex", "morning", "evening", "sup", "yo",
            "whats up", "what's up", "how are", "thanks", "thank", "bye", "ok",
            "good", "nice", "cool", "wow", "lol", "haha", "hmm", "okay", "sure",
            "my name", "who am i", "do you know me", "remember",
        ]
        is_greeting = any(w in q for w in greetings) and len(q.split()) < 6

        # Very short messages (1-3 words) that aren't clear questions → chat mode
        # This handles typos like "hwy", casual remarks like "sup", etc.
        is_short_casual = len(q.split()) <= 3 and not any(
            w in q for w in ["what", "why", "where", "when", "define", "explain", "how to"]
        )

        if is_greeting or is_short_casual:
            return VortexPlan(
                mode="chat",
                steps=[PlanStep(tool="llm", action="chat", params={"query": query})],
                summary="Chatting...",
            )

        # --- Universal AI Response (For ANY question or chat) -------------
        # If it doesn't match a specific system mode or command above, 
        # send it to the LLM. This makes Vortex respond to everything.
        return VortexPlan(
            mode="qa",
            steps=[PlanStep(tool="llm", action="qa", params={"query": query})],
            summary="Thinking...",
        )

    # --- Predefined multi-step plans --------------------------------------
    def _plan_interview_prep(self, query: str) -> VortexPlan:
        profile = self.memory.profile
        steps: List[PlanStep] = [
            PlanStep(tool="plugins", action="set_mode", params={"mode": "interview"}),
            PlanStep(tool="system", action="open_app", params={"query": "browser"}),
            PlanStep(tool="browser", action="open_url", params={"url": "https://calendar.google.com"}),
            PlanStep(tool="browser", action="open_url", params={"url": "https://leetcode.com/problemset/all/"}),
            PlanStep(
                tool="browser",
                action="open_url",
                params={"url": "https://github.com/topics/system-design-interview"},
            ),
        ]
        summary = (
            f"Prepare AI interview for {profile.name}: calendar, LeetCode, and system design resources opened."
        )
        return VortexPlan(mode="interview", steps=steps, summary=summary)

    def _plan_study(self, query: str) -> VortexPlan:
        profile = self.memory.profile
        focus_topic = profile.weak_areas[0] if profile.weak_areas else "recursion"
        steps: List[PlanStep] = [
            PlanStep(tool="plugins", action="set_mode", params={"mode": "study"}),
            PlanStep(
                tool="browser",
                action="open_url",
                params={"url": f"https://leetcode.com/tag/{focus_topic.replace(' ', '-')}/"},
            ),
        ]
        summary = f"Study session focused on {focus_topic}."
        return VortexPlan(mode="study", steps=steps, summary=summary)

    def _plan_productivity(self, query: str) -> VortexPlan:
        steps: List[PlanStep] = [
            PlanStep(tool="plugins", action="set_mode", params={"mode": "productivity"}),
            PlanStep(tool="system", action="set_volume", params={"percent": 30}),
        ]
        summary = "Productivity mode: lower volume and enable focus."
        return VortexPlan(mode="productivity", steps=steps, summary=summary)

    def _plan_gaming(self, query: str) -> VortexPlan:
        steps: List[PlanStep] = [
            PlanStep(tool="plugins", action="set_mode", params={"mode": "gaming"}),
            PlanStep(tool="system", action="set_volume", params={"percent": 80}),
        ]
        summary = "Gaming mode: louder volume and gaming profile."
        return VortexPlan(mode="gaming", steps=steps, summary=summary)

    def _plan_screen_error(self, query: str, screenshot_text: Optional[str]) -> VortexPlan:
        steps: List[PlanStep] = [
            PlanStep(tool="screen", action="analyze_error", params={"query": query, "screenshot_text": screenshot_text}),
        ]
        summary = "Analyze the screen error using OCR."
        return VortexPlan(mode="coding", steps=steps, summary=summary)


__all__ = ["VortexPlanner", "VortexPlan", "PlanStep"]

