"""
External metadata providers for enriching ACL papers with citations,
references, and related works. Designed to degrade gracefully when
network is unavailable and to cache results locally.
"""
from __future__ import annotations

import os
import json
import hashlib
import time
from typing import Any, Dict, List, Optional, Tuple

try:
    import requests
except Exception:
    requests = None  # Degrade gracefully if requests is missing


def _norm(s: Optional[str]) -> Optional[str]:
    return s.strip() if isinstance(s, str) else s


class MetadataCache:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.getenv("METADATA_CACHE_DIR", ".cache/metadata")
        os.makedirs(self.base_dir, exist_ok=True)

    def _key(self, doi: Optional[str], title: Optional[str]) -> str:
        key_src = (doi or "") + "::" + (title or "")
        return hashlib.sha256(key_src.encode("utf-8")).hexdigest()

    def get(self, doi: Optional[str], title: Optional[str]) -> Optional[Dict[str, Any]]:
        path = os.path.join(self.base_dir, self._key(doi, title) + ".json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def set(self, doi: Optional[str], title: Optional[str], data: Dict[str, Any]) -> None:
        path = os.path.join(self.base_dir, self._key(doi, title) + ".json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception:
            pass


class ExternalMetadataProvider:
    def __init__(self, cache: Optional[MetadataCache] = None, timeout: float = 6.0):
        self.cache = cache or MetadataCache()
        self.timeout = timeout
        self.offline = os.getenv("METADATA_OFFLINE", "false").lower() in {"1", "true", "yes"}

    def fetch(self, *, doi: Optional[str], title: Optional[str], authors: List[str], year: Optional[int],
              max_related: int = 3) -> Dict[str, Any]:
        # Cache first
        cached = self.cache.get(doi, title)
        if cached is not None:
            return cached

        if self.offline or requests is None:
            result = self._empty_result(reason="offline or requests not installed")
            self.cache.set(doi, title, result)
            return result

        # Try providers in order of preference
        provider_pref = os.getenv("METADATA_PROVIDER", "openalex,crossref,semanticscholar").split(",")
        provider_pref = [p.strip().lower() for p in provider_pref if p.strip()]

        last_error = None
        for provider in provider_pref:
            try:
                if provider == "openalex":
                    data = self._fetch_openalex(doi=doi, title=title, authors=authors, year=year, max_related=max_related)
                elif provider == "crossref":
                    data = self._fetch_crossref(doi=doi, title=title, authors=authors, year=year, max_related=max_related)
                elif provider in {"semanticscholar", "s2"}:
                    data = self._fetch_semantic_scholar(doi=doi, title=title, authors=authors, year=year, max_related=max_related)
                else:
                    continue
                self.cache.set(doi, title, data)
                # If we have no related works, try augmenting with a secondary provider
                if not data.get("related_works"):
                    # Prefer DOI discovered from the first provider
                    doi_for_aug = data.get("doi") or doi
                    for alt in provider_pref:
                        if alt == provider:
                            continue
                        try:
                            if alt == "openalex":
                                aug = self._fetch_openalex(doi=doi_for_aug, title=title, authors=authors, year=year, max_related=max_related)
                            elif alt == "crossref":
                                aug = self._fetch_crossref(doi=doi_for_aug, title=title, authors=authors, year=year, max_related=max_related)
                            else:
                                aug = self._fetch_semantic_scholar(doi=doi_for_aug, title=title, authors=authors, year=year, max_related=max_related)
                            if aug.get("related_works"):
                                combined = data.get("related_works", []) + aug.get("related_works", [])
                                # Deduplicate by title+year+doi
                                seen = set()
                                unique: List[Dict[str, Any]] = []
                                for rw in combined:
                                    key = (rw.get("doi") or "", (rw.get("title") or "").lower(), rw.get("year") or 0, rw.get("url") or "")
                                    if key in seen:
                                        continue
                                    seen.add(key)
                                    unique.append(rw)
                                data["related_works"] = unique[:max_related]
                                note = data.get("note") or ""
                                data["note"] = (note + " | augmented from " + aug.get("provider", "alt")).strip(" |")
                                break
                        except Exception:
                            continue
                return data
            except Exception as e:
                last_error = str(e)
                continue

        # Fallback: empty
        result = self._empty_result(reason=f"no provider succeeded: {last_error}")
        self.cache.set(doi, title, result)
        return result

    def _empty_result(self, reason: str = "") -> Dict[str, Any]:
        return {
            "provider": None,
            "citations_count": None,
            "references_count": None,
            "doi": None,
            "openalex_id": None,
            "s2_paper_id": None,
            "related_works": [],
            "source_url": None,
            "note": reason,
            "fetched_at": int(time.time()),
        }

    # --- OpenAlex ---
    def _fetch_openalex(self, *, doi: Optional[str], title: Optional[str], authors: List[str], year: Optional[int],
                        max_related: int) -> Dict[str, Any]:
        base = "https://api.openalex.org/works"
        headers = {"User-Agent": os.getenv("OPENALEX_UA", "acl-search/0.1 (+https://example.com)")}

        # Resolve
        work = None
        source_url = None
        if doi:
            url = f"{base}/doi:{doi}"
            r = requests.get(url, timeout=self.timeout, headers=headers)
            if r.status_code == 200:
                work = r.json()
                source_url = url
        if work is None and title:
            # Search by title with year window and multiple candidates
            params = {
                "search": title,
                "per_page": 5,
            }
            # Narrow by year if provided
            if year:
                y = int(year)
                params["filter"] = f"from_publication_date:{y}-01-01,to_publication_date:{y}-12-31"
            r = requests.get(base, params=params, timeout=self.timeout, headers=headers)
            if r.status_code == 200:
                j = r.json()
                candidates = (j or {}).get("results") or []
                if candidates:
                    work = self._select_best_openalex_candidate(title, authors, year, candidates)
                    source_url = r.url

        if not isinstance(work, dict):
            raise RuntimeError("OpenAlex: work not found")

        oa_id = work.get("id")
        cited_by_count = work.get("cited_by_count")
        referenced_works = work.get("referenced_works") or []
        incoming = work.get("ids", {})
        doi_found = (incoming.get("doi") or doi)

        related: List[Dict[str, Any]] = []
        note_parts: List[str] = []
        # Resolve a few related works by IDs if available
        if work.get("related_works"):
            rel_ids = [rid for rid in work["related_works"]][:max_related]
            for rid in rel_ids:
                try:
                    rr = requests.get(rid, timeout=self.timeout, headers=headers)
                    if rr.status_code == 200:
                        w = rr.json()
                        related.append({
                            "title": w.get("title"),
                            "year": w.get("publication_year"),
                            "authors": [a.get("author", {}).get("display_name") for a in (w.get("authorships") or [])],
                            "url": (w.get("ids") or {}).get("openalex") or w.get("id"),
                            "doi": (w.get("ids") or {}).get("doi"),
                        })
                except Exception:
                    continue
            if related:
                note_parts.append("related_works")
        # Fallback: fetch citing papers
        if not related and work.get("cited_by_api_url"):
            try:
                cb_url = work["cited_by_api_url"]
                rr = requests.get(cb_url, params={"per_page": max_related}, timeout=self.timeout, headers=headers)
                if rr.status_code == 200:
                    j = rr.json() or {}
                    for item in (j.get("results") or [])[:max_related]:
                        related.append({
                            "title": item.get("title"),
                            "year": item.get("publication_year"),
                            "authors": [a.get("author", {}).get("display_name") for a in (item.get("authorships") or [])],
                            "url": (item.get("ids") or {}).get("openalex") or item.get("id"),
                            "doi": (item.get("ids") or {}).get("doi"),
                        })
                if related:
                    note_parts.append("cited_by")
            except Exception:
                pass
        # Fallback: resolve first referenced works
        if not related and isinstance(referenced_works, list) and referenced_works:
            for rid in referenced_works[:max_related]:
                try:
                    rr = requests.get(rid, timeout=self.timeout, headers=headers)
                    if rr.status_code == 200:
                        w = rr.json()
                        related.append({
                            "title": w.get("title"),
                            "year": w.get("publication_year"),
                            "authors": [a.get("author", {}).get("display_name") for a in (w.get("authorships") or [])],
                            "url": (w.get("ids") or {}).get("openalex") or w.get("id"),
                            "doi": (w.get("ids") or {}).get("doi"),
                        })
                except Exception:
                    continue
            if related:
                note_parts.append("references")

        return {
            "provider": "openalex",
            "citations_count": cited_by_count,
            "references_count": len(referenced_works) if isinstance(referenced_works, list) else None,
            "doi": doi_found,
            "openalex_id": oa_id,
            "s2_paper_id": None,
            "related_works": related[:max_related],
            "source_url": source_url or oa_id,
            "fetched_at": int(time.time()),
            "note": "openalex:" + ",".join(note_parts) if note_parts else None,
        }

    # --- Semantic Scholar ---
    def _fetch_semantic_scholar(self, *, doi: Optional[str], title: Optional[str], authors: List[str], year: Optional[int],
                                max_related: int) -> Dict[str, Any]:
        base = "https://api.semanticscholar.org/graph/v1/paper"
        headers = {"User-Agent": os.getenv("S2_UA", "acl-search/0.1 (+https://example.com)"), "Accept": "application/json"}
        api_key = os.getenv("S2_API_KEY")
        if api_key:
            headers["x-api-key"] = api_key

        # Resolve
        fields = [
            "title", "year", "authors", "citationCount", "referenceCount", "externalIds", "url",
            # Note: fetching full citations list is heavy; skip for now
        ]
        params = {"fields": ",".join(fields)}
        source_url = None
        res = None
        if doi:
            url = f"{base}/DOI:{doi}"
            r = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            if r.status_code == 200:
                res = r.json()
                source_url = r.url
        if res is None and title:
            # Title search endpoint with multiple candidates
            search_url = "https://api.semanticscholar.org/graph/v1/paper/search"
            sp = {"query": title, "limit": 5, "fields": ",".join(fields)}
            r = requests.get(search_url, params=sp, headers=headers, timeout=self.timeout)
            if r.status_code == 200:
                j = r.json()
                items = (j or {}).get("data") or []
                if items:
                    res = self._select_best_s2_candidate(title, authors, year, items)
                    source_url = r.url
                # Fallback: try truncated/normalized title (before colon)
                if not res:
                    base_title = (title.split(":")[0] or title).strip()
                    if base_title and base_title != title:
                        sp2 = {"query": base_title, "limit": 5, "fields": ",".join(fields)}
                        r2 = requests.get(search_url, params=sp2, headers=headers, timeout=self.timeout)
                        if r2.status_code == 200:
                            j2 = r2.json() or {}
                            items2 = (j2 or {}).get("data") or []
                            if items2:
                                res = self._select_best_s2_candidate(base_title, authors, year, items2)
                                source_url = r2.url
                # Fallback: try title with first author last name and year
                if not res and authors:
                    last_name = (authors[0].split()[-1] if authors[0] else "").strip()
                    if last_name:
                        q3 = f"{base_title if 'base_title' in locals() and base_title else title} {last_name}"
                        if year:
                            q3 += f" {int(year)}"
                        sp3 = {"query": q3, "limit": 5, "fields": ",".join(fields)}
                        r3 = requests.get(search_url, params=sp3, headers=headers, timeout=self.timeout)
                        if r3.status_code == 200:
                            j3 = r3.json() or {}
                            items3 = (j3 or {}).get("data") or []
                            if items3:
                                res = self._select_best_s2_candidate(title, authors, year, items3)
                                source_url = r3.url
        # As a last resort, try Crossref to resolve DOI, then re-query S2
        if res is None and not doi and title:
            try:
                cr_doi = self._resolve_doi_crossref(title=title, authors=authors, year=year)
                if cr_doi:
                    url = f"{base}/DOI:{cr_doi}"
                    r = requests.get(url, params=params, headers=headers, timeout=self.timeout)
                    if r.status_code == 200:
                        res = r.json()
                        source_url = r.url
                        doi = cr_doi
                        # annotate later with note
            except Exception:
                pass

        if not isinstance(res, dict):
            raise RuntimeError("Semantic Scholar: paper not found")

        s2_id = res.get("paperId")
        doi_found = ((res.get("externalIds") or {}).get("DOI") or doi)

        # Related works via recommendations; fallback to citations
        related: List[Dict[str, Any]] = []
        note_parts: List[str] = []
        try:
            if s2_id:
                rec_url = f"https://api.semanticscholar.org/recommendations/v1/papers/forpaper/{s2_id}"
                # Recommendations API expects POST; some deployments reject GET
                rp = {"limit": max_related}
                rr = requests.post(rec_url, json=rp, headers=headers, timeout=self.timeout)
                if rr.status_code == 200:
                    j = rr.json() or {}
                    for item in (j.get("recommendedPapers") or [])[:max_related]:
                        related.append({
                            "title": item.get("title"),
                            "year": item.get("year"),
                            "authors": [a.get("name") for a in (item.get("authors") or [])],
                            "url": item.get("url"),
                            "doi": ((item.get("externalIds") or {}).get("DOI")),
                        })
                elif rr.status_code in (401, 403):
                    note_parts.append("recommendations_auth")
                elif rr.status_code in (429,):
                    note_parts.append("recommendations_rate_limited")
        except Exception:
            pass
        # Fallback: citations list
        if not related and s2_id:
            try:
                cit_url = f"https://api.semanticscholar.org/graph/v1/paper/{s2_id}/citations"
                cp = {"limit": max_related, "fields": "title,year,authors,url,externalIds"}
                rr = requests.get(cit_url, params=cp, headers=headers, timeout=self.timeout)
                if rr.status_code == 200:
                    j = rr.json() or {}
                    for entry in (j.get("data") or [])[:max_related]:
                        p = (entry.get("citingPaper") or {})
                        related.append({
                            "title": p.get("title"),
                            "year": p.get("year"),
                            "authors": [a.get("name") for a in (p.get("authors") or [])],
                            "url": p.get("url"),
                            "doi": ((p.get("externalIds") or {}).get("DOI")),
                        })
                if related:
                    note_parts.append("citations")
                elif rr.status_code in (401, 403):
                    note_parts.append("citations_auth")
                elif rr.status_code in (429,):
                    note_parts.append("citations_rate_limited")
            except Exception:
                pass

        return {
            "provider": "semanticscholar",
            "citations_count": res.get("citationCount"),
            "references_count": res.get("referenceCount"),
            "doi": doi_found,
            "openalex_id": None,
            "s2_paper_id": s2_id,
            "related_works": related[:max_related],
            "source_url": source_url,
            "fetched_at": int(time.time()),
            "note": ("semanticscholar:" + ",".join(note_parts) if note_parts else None) or ("crossref:resolved_doi" if doi and doi == doi_found else None),
        }

    # --- Helpers ---
    @staticmethod
    def _normalize_title(title: str) -> str:
        import re as _re
        t = (title or "").lower()
        t = _re.sub(r"[^a-z0-9\s]", "", t)
        t = " ".join(t.split())
        return t

    def _select_best_openalex_candidate(self, title: str, authors: List[str], year: Optional[int], candidates: List[Dict[str, Any]]):
        target = self._normalize_title(title)
        norm_auth = {a.lower() for a in authors}
        best = None
        best_score = -1
        for c in candidates:
            ctitle = self._normalize_title(c.get("title") or "")
            score = 0
            if ctitle == target:
                score += 100
            cyear = c.get("publication_year")
            if year and cyear:
                try:
                    score += max(0, 10 - abs(int(cyear) - int(year)))
                except Exception:
                    pass
            # author overlap
            c_auths = { (a.get("author", {}) or {}).get("display_name", "").lower() for a in (c.get("authorships") or []) }
            score += len(norm_auth & c_auths)
            if score > best_score:
                best_score = score
                best = c
        return best or (candidates[0] if candidates else None)

    def _select_best_s2_candidate(self, title: str, authors: List[str], year: Optional[int], candidates: List[Dict[str, Any]]):
        target = self._normalize_title(title)
        norm_auth = {a.lower() for a in authors}
        best = None
        best_score = -1
        for c in candidates:
            ctitle = self._normalize_title(c.get("title") or "")
            score = 0
            if ctitle == target:
                score += 100
            cyear = c.get("year")
            if year and cyear:
                try:
                    score += max(0, 10 - abs(int(cyear) - int(year)))
                except Exception:
                    pass
            c_auths = { a.get("name", "").lower() for a in (c.get("authors") or []) }
            score += len(norm_auth & c_auths)
            if score > best_score:
                best_score = score
                best = c
        return best or (candidates[0] if candidates else None)

    # Crossref DOI resolver (best-effort)
    def _resolve_doi_crossref(self, title: str, authors: List[str], year: Optional[int]) -> Optional[str]:
        if requests is None:
            return None
        try:
            base = "https://api.crossref.org/works"
            q = title
            if authors:
                q += " " + authors[0]
            params = {"query.bibliographic": q, "rows": 5}
            headers = {"User-Agent": os.getenv("CROSSREF_UA", "acl-search/0.1 (+mailto:you@example.com)")}
            r = requests.get(base, params=params, headers=headers, timeout=self.timeout)
            if r.status_code != 200:
                return None
            j = r.json() or {}
            items = ((j.get("message") or {}).get("items") or [])
            if not items:
                return None
            # pick by title similarity and year proximity
            target = self._normalize_title(title)
            best = None
            best_score = -1
            for it in items:
                it_title = self._normalize_title(" ".join(it.get("title") or []) )
                score = 0
                if it_title == target:
                    score += 100
                if year and it.get("issued") and (it.get("issued", {}).get("date-parts")):
                    try:
                        y = int(it["issued"]["date-parts"][0][0])
                        score += max(0, 10 - abs(int(year) - y))
                    except Exception:
                        pass
                if score > best_score:
                    best_score = score
                    best = it
            return (best or {}).get("DOI")
        except Exception:
            return None

    # --- Crossref ---
    def _fetch_crossref(self, *, doi: Optional[str], title: Optional[str], authors: List[str], year: Optional[int],
                        max_related: int) -> Dict[str, Any]:
        base = "https://api.crossref.org/works"
        headers = {"User-Agent": os.getenv("CROSSREF_UA", "acl-search/0.1 (+mailto:you@example.com)")}

        # Crossref can be slower, use longer timeout (bibliographic searches can take 16+ seconds)
        crossref_timeout = max(30.0, self.timeout * 3)

        # Resolve work
        work = None
        source_url = None
        if doi:
            url = f"{base}/{doi}"
            r = requests.get(url, timeout=crossref_timeout, headers=headers)
            if r.status_code == 200:
                j = r.json()
                work = (j or {}).get("message")
                source_url = url
        if work is None and title:
            # Search by title with author and year
            q = title
            if authors:
                q += " " + authors[0]
            params = {"query.bibliographic": q, "rows": 5}
            if year:
                params["filter"] = f"from-pub-date:{year},until-pub-date:{year}"
            r = requests.get(base, params=params, headers=headers, timeout=crossref_timeout)
            if r.status_code == 200:
                j = r.json()
                candidates = ((j or {}).get("message", {}).get("items") or [])
                if candidates:
                    work = self._select_best_crossref_candidate(title, authors, year, candidates)
                    source_url = r.url

        if not isinstance(work, dict):
            raise RuntimeError("Crossref: work not found")

        cr_doi = work.get("DOI") or doi
        title_found = " ".join(work.get("title") or [])

        # Citation counts from Crossref
        citations_count = work.get("is-referenced-by-count")
        references_count = len(work.get("reference") or [])

        # Get related works via references (limited)
        related: List[Dict[str, Any]] = []
        note_parts: List[str] = []
        references = work.get("reference", [])
        if references:
            # Take first few references that have DOIs
            ref_dois = []
            for ref in references[:max_related * 2]:  # Get more to account for failures
                ref_doi = ref.get("DOI")
                if ref_doi and len(ref_dois) < max_related:
                    ref_dois.append(ref_doi)

            # Fetch metadata for referenced works
            for ref_doi in ref_dois:
                try:
                    ref_url = f"{base}/{ref_doi}"
                    rr = requests.get(ref_url, timeout=crossref_timeout, headers=headers)
                    if rr.status_code == 200:
                        ref_work = rr.json().get("message", {})
                        ref_authors = []
                        for author in (ref_work.get("author") or []):
                            given = author.get("given", "")
                            family = author.get("family", "")
                            if given and family:
                                ref_authors.append(f"{given} {family}")
                            elif family:
                                ref_authors.append(family)

                        ref_year = None
                        if ref_work.get("issued") and ref_work["issued"].get("date-parts"):
                            try:
                                ref_year = int(ref_work["issued"]["date-parts"][0][0])
                            except Exception:
                                pass

                        related.append({
                            "title": " ".join(ref_work.get("title") or []),
                            "year": ref_year,
                            "authors": ref_authors,
                            "url": ref_work.get("URL"),
                            "doi": ref_work.get("DOI"),
                        })
                except Exception:
                    continue

            if related:
                note_parts.append("references")

        # Note: Crossref doesn't have a direct citing works API
        # Related works come only from references for now

        return {
            "provider": "crossref",
            "citations_count": citations_count,
            "references_count": references_count,
            "doi": cr_doi,
            "openalex_id": None,
            "s2_paper_id": None,
            "related_works": related[:max_related],
            "source_url": source_url,
            "fetched_at": int(time.time()),
            "note": "crossref:" + ",".join(note_parts) if note_parts else None,
        }

    def _select_best_crossref_candidate(self, title: str, authors: List[str], year: Optional[int], candidates: List[Dict[str, Any]]):
        target = self._normalize_title(title)
        norm_auth = {a.lower() for a in authors}
        best = None
        best_score = -1
        for c in candidates:
            ctitle = self._normalize_title(" ".join(c.get("title") or []))
            score = 0
            if ctitle == target:
                score += 100
            # Year match
            if year and c.get("issued") and c["issued"].get("date-parts"):
                try:
                    cyear = int(c["issued"]["date-parts"][0][0])
                    score += max(0, 10 - abs(int(year) - cyear))
                except Exception:
                    pass
            # Author overlap
            c_auths = set()
            for author in (c.get("author") or []):
                given = author.get("given", "")
                family = author.get("family", "")
                if given and family:
                    c_auths.add(f"{given} {family}".lower())
                elif family:
                    c_auths.add(family.lower())
            score += len(norm_auth & c_auths)
            if score > best_score:
                best_score = score
                best = c
        return best or (candidates[0] if candidates else None)
