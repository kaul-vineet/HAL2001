"""HAL Brain — M365 Copilot Search + Chat + Meeting Insights API.

Search API:           Semantic search across OneDrive/SharePoint content.
Chat API:             Natural language Q&A grounded in M365 data.
Meeting Insights API: AI-generated summaries, action items from Teams meetings.

Requires: M365 Copilot license per user.
"""

import httpx
from rich.console import Console

from auth import acquire_token

GRAPH_BASE = "https://graph.microsoft.com/beta"
GRAPH_V1 = "https://graph.microsoft.com/v1.0"


class Brain:
    """M365 Copilot Search + Chat + Meeting Insights client."""

    def __init__(self):
        self._conversation_id: str | None = None
        self._http: httpx.AsyncClient | None = None

    def _get_headers(self) -> dict:
        """Get fresh auth headers using MSAL token (auto-refreshes from cache)."""
        token = acquire_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def _client(self) -> httpx.AsyncClient:
        """Return an HTTP client with fresh auth headers."""
        # Always create fresh client to ensure token is current
        if self._http and not self._http.is_closed:
            await self._http.aclose()
        self._http = httpx.AsyncClient(
            headers=self._get_headers(),
            timeout=60.0,
        )
        return self._http

    # ── Search API ───────────────────────────────────────────────

    async def search(self, query: str, page_size: int = 10) -> list[dict]:
        """Semantic + lexical search across OneDrive/SharePoint content."""
        client = await self._client()
        body = {"query": query, "pageSize": min(page_size, 100)}
        resp = await client.post(f"{GRAPH_BASE}/copilot/search", json=body)
        resp.raise_for_status()
        data = resp.json()
        hits = []
        for item in data.get("searchHits", []):
            resource = item.get("resource", {})
            hits.append({
                "name": resource.get("name", "unknown"),
                "url": resource.get("webUrl", ""),
                "preview": item.get("preview", ""),
                "path": resource.get("parentReference", {}).get("path", ""),
            })
        return hits

    # ── Retrieval API ────────────────────────────────────────────

    async def retrieve(
        self,
        query: str,
        data_source: str = "sharePoint",
        max_results: int = 10,
        filter_expr: str | None = None,
    ) -> list[dict]:
        """Retrieve relevant text chunks from M365 content for RAG grounding.

        Unlike Search (which returns documents), this returns actual text
        paragraphs/snippets ready to feed into an LLM.

        Args:
            query: Natural language query.
            data_source: "sharePoint", "oneDrive", or "copilotConnectors".
            max_results: Max chunks to return (max 25).
            filter_expr: Optional KQL filter (e.g., path:"https://...").

        Returns:
            List of text chunks with content, source, and relevance score.
        """
        client = await self._client()
        body = {
            "queryString": query,
            "dataSource": data_source,
            "maximumNumberOfResults": min(max_results, 25),
        }
        if filter_expr:
            body["filterExpression"] = filter_expr

        resp = await client.post(f"{GRAPH_BASE}/copilot/retrieval", json=body)
        resp.raise_for_status()
        data = resp.json()

        chunks = []
        for item in data.get("value", []):
            web_url = item.get("webUrl", "")
            file_name = item.get("fileName", "unknown")
            for extract in item.get("extracts", []):
                chunks.append({
                    "text": extract.get("text", ""),
                    "relevance": extract.get("relevanceScore", 0.0),
                    "file": file_name,
                    "url": web_url,
                })
        return chunks

    async def retrieve_and_summarize(
        self,
        query: str,
        data_source: str = "sharePoint",
        instruction: str | None = None,
    ) -> dict:
        """Retrieve text chunks, then ask Copilot Chat to summarize them.

        Args:
            query: What to search for.
            data_source: Where to search.
            instruction: Optional custom instruction for the LLM summary.

        Returns:
            dict with 'chunks' (raw extracts) and 'summary' (LLM answer).
        """
        chunks = await self.retrieve(query, data_source=data_source)

        if not chunks:
            return {
                "chunks": [],
                "summary": f"No relevant content found for: {query}",
            }

        # Build context from retrieved chunks
        context_lines = []
        for i, chunk in enumerate(chunks[:10], 1):
            score = f" (relevance: {chunk['relevance']:.2f})" if chunk["relevance"] else ""
            context_lines.append(
                f"[{i}] From: {chunk['file']}{score}\n{chunk['text']}"
            )
        context = "\n\n".join(context_lines)

        # Ask Copilot to summarize
        if instruction:
            prompt = f"{instruction}\n\nRetrieved content:\n{context}"
        else:
            prompt = (
                f"Based on the following retrieved content, answer this query: {query}\n\n"
                f"Retrieved content:\n{context}\n\n"
                f"Provide a clear, concise summary. Cite the source documents."
            )

        summary = await self.ask(prompt)
        return {"chunks": chunks, "summary": summary}

    # ── Chat API ─────────────────────────────────────────────────

    async def _ensure_conversation(self) -> str:
        if self._conversation_id:
            return self._conversation_id
        client = await self._client()
        resp = await client.post(f"{GRAPH_BASE}/copilot/conversations", json={})
        resp.raise_for_status()
        data = resp.json()
        self._conversation_id = data.get("id")
        if not self._conversation_id:
            raise RuntimeError(f"Copilot did not return conversation ID: {data}")
        return self._conversation_id

    async def ask(self, prompt: str, web_search: bool = True) -> str:
        """Send a natural language prompt to M365 Copilot Chat API."""
        conv_id = await self._ensure_conversation()
        client = await self._client()
        body = {
            "message": {"text": prompt},
            "locationHint": {"timeZone": "Asia/Kolkata"},
        }
        if not web_search:
            body["contextualResources"] = {"webSearchGrounding": {"enabled": False}}
        resp = await client.post(
            f"{GRAPH_BASE}/copilot/conversations/{conv_id}/chat", json=body,
        )
        resp.raise_for_status()
        data = resp.json()

        # Extract the last assistant message from the conversation
        messages = data.get("messages", [])
        for msg in reversed(messages):
            if msg.get("@odata.type", "").endswith("ResponseMessage"):
                text = msg.get("text", "")
                if text and text != prompt:
                    return text
        # Fallback: try older response format
        if "message" in data and "text" in data["message"]:
            return data["message"]["text"]
        return str(data)

    # ── Meeting Insights API ─────────────────────────────────────

    async def get_meeting_insights(self) -> list[dict]:
        """Fetch AI insights from recent Teams meetings.

        Uses calendar events to find meetings with join URLs,
        then fetches AI insights for each.
        """
        client = await self._client()

        # Get current user ID
        me_resp = await client.get(f"{GRAPH_V1}/me", params={"$select": "id"})
        me_resp.raise_for_status()
        user_id = me_resp.json().get("id")
        if not user_id:
            return []

        # Get recent calendar events that are Teams meetings (last 24 hours)
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(hours=24)

        events_resp = await client.get(
            f"{GRAPH_V1}/me/calendarView",
            params={
                "startDateTime": yesterday.isoformat(),
                "endDateTime": now.isoformat(),
                "$select": "subject,onlineMeeting,start,end",
                "$top": "10",
                "$orderby": "start/dateTime desc",
            },
        )
        events_resp.raise_for_status()
        events = events_resp.json().get("value", [])

        results = []
        for event in events:
            subject = event.get("subject", "Untitled meeting")
            online_meeting = event.get("onlineMeeting")
            if not online_meeting:
                continue

            join_url = online_meeting.get("joinUrl")
            if not join_url:
                continue

            # Resolve joinUrl to online meeting ID
            try:
                encoded_url = join_url.replace("'", "''")
                meeting_resp = await client.get(
                    f"{GRAPH_V1}/me/onlineMeetings",
                    params={"$filter": f"joinWebUrl eq '{encoded_url}'"},
                )
                meeting_resp.raise_for_status()
                meetings = meeting_resp.json().get("value", [])
                if not meetings:
                    continue
                meeting_id = meetings[0]["id"]
            except httpx.HTTPStatusError:
                # Fallback: try using joinWebUrl query parameter directly
                try:
                    meeting_resp = await client.get(
                        f"{GRAPH_V1}/me/onlineMeetings",
                        params={"joinWebUrl": join_url},
                    )
                    meeting_resp.raise_for_status()
                    meeting_data = meeting_resp.json()
                    if "id" in meeting_data:
                        meeting_id = meeting_data["id"]
                    else:
                        continue
                except httpx.HTTPStatusError:
                    continue

            # Fetch AI insights for this meeting
            try:
                insights_resp = await client.get(
                    f"{GRAPH_BASE}/copilot/users/{user_id}"
                    f"/onlineMeetings/{meeting_id}/aiInsights"
                )
                insights_resp.raise_for_status()
                insight_list = insights_resp.json().get("value", [])

                for insight_summary in insight_list:
                    insight_id = insight_summary["id"]
                    # Get detailed insight
                    detail_resp = await client.get(
                        f"{GRAPH_BASE}/copilot/users/{user_id}"
                        f"/onlineMeetings/{meeting_id}"
                        f"/aiInsights/{insight_id}"
                    )
                    detail_resp.raise_for_status()
                    detail = detail_resp.json()

                    notes = []
                    for note in detail.get("meetingNotes", []):
                        notes.append(note.get("title", "") + ": " + note.get("text", ""))

                    actions = []
                    for action in detail.get("actionItems", []):
                        owner = action.get("ownerDisplayName", "unassigned")
                        actions.append(f"{action.get('text', '')} → {owner}")

                    mentions = []
                    vp = detail.get("viewpoint", {})
                    for mention in vp.get("mentionEvents", []):
                        speaker = mention.get("speaker", {}).get("user", {})
                        mentions.append({
                            "speaker": speaker.get("displayName", "unknown"),
                            "utterance": mention.get("transcriptUtterance", ""),
                        })

                    results.append({
                        "subject": subject,
                        "notes": notes,
                        "action_items": actions,
                        "mentions": mentions,
                    })

            except httpx.HTTPStatusError:
                # No insights available for this meeting (no transcript)
                results.append({
                    "subject": subject,
                    "notes": [],
                    "action_items": [],
                    "mentions": [],
                })

        return results

    # ── Search + Ask (combined flow for user queries) ────────────

    async def search_and_ask(self, user_query: str) -> dict:
        """Search API → find docs, Chat API → analyze with context."""
        search_hits = await self.search(user_query)

        if search_hits:
            context_lines = []
            for i, hit in enumerate(search_hits[:5], 1):
                context_lines.append(
                    f"{i}. [{hit['name']}]({hit['url']})\n   Preview: {hit['preview']}"
                )
            search_context = "\n".join(context_lines)
            enriched_prompt = (
                f"User question: {user_query}\n\n"
                f"Relevant documents found:\n{search_context}\n\n"
                f"Based on the user's question and the relevant documents above, "
                f"provide a comprehensive answer. Reference the documents where applicable."
            )
        else:
            enriched_prompt = user_query

        answer = await self.ask(enriched_prompt)
        return {"search_hits": search_hits, "answer": answer}

    async def new_conversation(self) -> None:
        self._conversation_id = None

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()
