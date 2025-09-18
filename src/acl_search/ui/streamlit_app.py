"""
Streamlit app for searching ACL Anthology papers
"""
import streamlit as st
import pandas as pd
from acl_search.core.search_engine import BooleanSearchEngine, SearchResult
from acl_search.providers.metadata_providers import ExternalMetadataProvider
from typing import List, Dict, Any
import time


# Configure page
st.set_page_config(
    page_title="ACL Anthology Search",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
        border-bottom: 2px solid #f0f2f6;
        margin-bottom: 2rem;
    }
    .search-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .result-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .result-title {
        color: #1f77b4;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .result-meta {
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    .match-indicator {
        background: #e8f4f8;
        color: #1f77b4;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        display: inline-block;
        margin: 0.2rem;
    }
    .stats-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .filter-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_search_engine():
    """Load and cache the search engine"""
    return BooleanSearchEngine()


@st.cache_resource
def get_metadata_provider():
    """Create and cache the external metadata provider"""
    try:
        return ExternalMetadataProvider()
    except Exception:
        return None


def format_authors(authors: List[str], max_display: int = 5) -> str:
    """Format authors list for display"""
    if not authors:
        return "Unknown"
    
    if len(authors) <= max_display:
        return ", ".join(authors)
    else:
        return f"{', '.join(authors[:max_display])} et al. ({len(authors)} total)"


def display_search_result(result: SearchResult, show_abstract: bool = True, index: int = 1, metadata: dict | None = None):
    """Display a single search result with improved styling"""
    
    # Result card container
    st.markdown(f'''
    <div class="result-card">
        <div class="result-title">
            <a href="{result.url}" target="_blank" style="text-decoration: none; color: inherit;">
                {index}. {result.title}
            </a>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Metadata in columns
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.markdown(f"**👥 Authors:** {format_authors(result.authors)}")
    
    with col2:
        st.markdown(f"**📅 Year:** {result.year}")
    
    with col3:
        if result.venue:
            venue_str = ', '.join(result.venue[:2])
            if len(result.venue) > 2:
                venue_str += f" +{len(result.venue)-2}"
            st.markdown(f"**📍 Venue:** {venue_str}")
    
    # Match indicators
    if result.match_fields:
        st.markdown("**🔍 Matches:** " + "".join([
            f'<span class="match-indicator">{field}</span>' 
            for field in result.match_fields
        ]), unsafe_allow_html=True)

    # External metadata (citations/related)
    if metadata:
        meta_cols = st.columns([1, 2])
        with meta_cols[0]:
            cc = metadata.get("citations_count")
            rc = metadata.get("references_count")
            st.markdown(f"**📈 Citations:** {cc if cc is not None else 'N/A'}")
            if rc is not None:
                st.markdown(f"**🔗 References:** {rc}")
        with meta_cols[1]:
            rel = metadata.get("related_works") or []
            if rel:
                st.markdown("**🧭 Related works:**")
                for rw in rel[:3]:
                    title = rw.get("title") or "Untitled"
                    url = rw.get("url") or ""
                    year = rw.get("year")
                    suffix = f" ({year})" if year else ""
                    if url:
                        st.markdown(f"- [{title}]({url}){suffix}")
                    else:
                        st.markdown(f"- {title}{suffix}")
    
    # Abstract toggle
    if show_abstract and result.abstract:
        with st.expander("📄 View Abstract", expanded=False):
            st.markdown(f"<div style='text-align: justify; line-height: 1.6;'>{result.abstract}</div>", 
                       unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)


def create_filters_sidebar(search_engine: BooleanSearchEngine) -> Dict[str, Any]:
    """Create the filters sidebar"""
    st.sidebar.markdown("## 🎛️ Search Configuration")
    
    filters = {}
    
    # Field selection with better styling
    with st.sidebar.container():
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        st.markdown("### 🔍 Search Fields")
        search_fields = st.multiselect(
            "Select fields to search in:",
            options=["title", "abstract", "authors"],
            default=["title", "abstract", "authors"],
            help="Choose which fields to search in"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Year range filter
    with st.sidebar.container():
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        st.markdown("### 📅 Publication Year")
        try:
            min_year, max_year = search_engine.get_year_range()
            year_range = st.slider(
                "Select year range:",
                min_value=min_year,
                max_value=max_year,
                value=(min_year, max_year),
                help=f"Filter papers by publication year ({min_year}-{max_year})"
            )
            if year_range != (min_year, max_year):
                filters["year_range"] = year_range
        except Exception as e:
            st.error(f"Error loading year range: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Venue filter
    with st.sidebar.container():
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        st.markdown("### 🏛️ Conferences & Venues")
        try:
            all_venues = sorted(list(search_engine.get_available_venues()))
            
            # Show top venues by default, with option to see all
            show_all_venues = st.checkbox("Show all venues", value=False)
            
            if show_all_venues:
                display_venues = all_venues
            else:
                # Show most common venues
                common_venues = ["acl", "emnlp", "naacl", "eacl", "coling", "conll", 
                               "findings", "semeval", "ws", "demos"]
                display_venues = [v for v in all_venues if any(cv in v for cv in common_venues)]
                display_venues = display_venues[:20]  # Limit to 20 for UI
            
            selected_venues = st.multiselect(
                "Select venues:",
                options=display_venues,
                help="Filter papers by venue/conference"
            )
            
            if selected_venues:
                filters["venues"] = selected_venues
                
        except Exception as e:
            st.error(f"Error loading venues: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Results limit
    with st.sidebar.container():
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        st.markdown("### 📊 Display Options")
        results_limit = st.selectbox(
            "Maximum results:",
            options=[50, 100, 200, 500, 1000],
            index=2,
            help="Limit the number of search results"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # Fuzzy matching toggle
    with st.sidebar.container():
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        fuzzy_match = st.checkbox(
            "Enable fuzzy matching",
            value=False,
            help="Allow approximate matches using RapidFuzz"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    return {
        "search_fields": search_fields,
        "filters": filters,
        "limit": results_limit,
        "fuzzy_match": fuzzy_match
    }


def create_search_help():
    """Create search help section"""
    with st.expander("ℹ️ Search Help & Examples"):
        st.markdown("""
        ### Boolean Search Syntax
        
        **Basic Search:**
        - `attention mechanism` - Find papers containing both words
        - `"neural machine translation"` - Find exact phrase (quotes required)
        
        **Boolean Operators:**
        - `attention AND mechanism` - Both terms must be present
        - `attention OR mechanism` - Either term can be present  
        - `attention NOT model` - Must contain 'attention' but not 'model'
        
        **Example Queries:**
        - `"transformer architecture" AND attention`
        - `BERT OR GPT OR T5`
        - `machine translation AND (attention OR transformer)`
        - `"question answering" NOT conversational`
        
        **Search Fields:**
        Use the sidebar to choose whether to search in:
        - **Title**: Paper titles only
        - **Abstract**: Paper abstracts only
        - **Authors**: Author names only
        - **All fields**: Search across all selected fields
        
        **Tips:**
        - Use quotes for exact phrases
        - Combine terms with AND, OR, NOT
        - Use filters to narrow results by year or venue
        - Boolean operators are case-insensitive
        """)


def main():
    """Main Streamlit app"""
    
    # Header with styling
    st.markdown("""
    <div class="main-header">
        <h1>🔍 ACL Anthology Search</h1>
        <p style="font-size: 1.2rem; color: #666; margin-top: 0.5rem;">
            Search 113,000+ computational linguistics and NLP papers with advanced boolean queries
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load search engine
    with st.spinner("🚀 Loading ACL Anthology data..."):
        search_engine = load_search_engine()
    
    # Create sidebar filters
    filter_config = create_filters_sidebar(search_engine)
    
    # Main search interface with container styling
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    
    # Search input
    query = st.text_input(
        "🔍 Enter your search query:",
        placeholder="e.g., attention mechanism AND transformer",
        help="Use boolean operators (AND, OR, NOT) and quotes for exact phrases",
        label_visibility="collapsed"
    )
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_button = st.button("🚀 Search Papers", type="primary", use_container_width=True)
    
    with col2:
        clear_button = st.button("🗑️ Clear", use_container_width=True)
        if clear_button:
            st.rerun()
    
    with col3:
        help_expander = st.button("❓ Help", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Search help (show if help button clicked or always collapsed)
    if help_expander or "show_help" not in st.session_state:
        create_search_help()
    
    # Perform search
    if (search_button or query) and query.strip():
        if not filter_config["search_fields"]:
            st.error("Please select at least one field to search in.")
            return
            
        with st.spinner("Searching..."):
            start_time = time.time()
            
            try:
                results = search_engine.search(
                    query=query,
                    fields=filter_config["search_fields"],
                    filters=filter_config["filters"],
                    limit=filter_config["limit"],
                    fuzzy=filter_config["fuzzy_match"]
                )
                
                search_time = time.time() - start_time
                
                # Results summary with styling
                if results:
                    # Stats container with gradient background
                    years = [r.year for r in results if r.year]
                    venues = set()
                    authors = set()
                    for r in results:
                        venues.update(r.venue)
                        authors.update(r.authors)
                    
                    st.markdown(f"""
                    <div class="stats-container">
                        <h3 style="margin-top: 0;">📊 Search Results Summary</h3>
                        <div style="display: flex; justify-content: space-around; margin-top: 1rem;">
                            <div style="text-align: center;">
                                <h2 style="margin: 0; font-size: 2rem;">{len(results)}</h2>
                                <p style="margin: 0;">Papers Found</p>
                            </div>
                            <div style="text-align: center;">
                                <h2 style="margin: 0; font-size: 2rem;">{search_time:.2f}s</h2>
                                <p style="margin: 0;">Search Time</p>
                            </div>
                            <div style="text-align: center;">
                                <h2 style="margin: 0; font-size: 2rem;">{len(venues)}</h2>
                                <p style="margin: 0;">Venues</p>
                            </div>
                            <div style="text-align: center;">
                                <h2 style="margin: 0; font-size: 2rem;">{f"{min(years)}-{max(years)}" if years else "N/A"}</h2>
                                <p style="margin: 0;">Year Range</p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display options
                    col1, col2, col3 = st.columns([1, 1, 1])
                    
                    with col1:
                        show_abstracts = st.checkbox("📄 Show abstracts", value=False)
                    
                    with col2:
                        # Download results as CSV
                        df = pd.DataFrame([
                            {
                                "ID": r.paper_id,
                                "Title": r.title,
                                "Authors": "; ".join(r.authors),
                                "Year": r.year,
                                "Venue": "; ".join(r.venue),
                                "URL": r.url,
                                "Abstract": r.abstract or ""
                            }
                            for r in results
                        ])
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name=f"acl_search_results_{int(time.time())}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    
                    with col3:
                        st.metric("👥 Authors", f"{len(authors):,}")

                    # Optional metadata enrichment (can be slower)
                    enrich_md = st.checkbox("📈 Show citation counts and related works (slower)", value=False)
                    
                    st.markdown("---")
                    
                    # Display results with improved styling
                    st.markdown("## 📋 Search Results")
                    provider = get_metadata_provider() if enrich_md else None
                    max_enrich = 10
                    for i, result in enumerate(results, 1):
                        md = None
                        if enrich_md and provider and i <= max_enrich:
                            try:
                                md = provider.fetch(
                                    doi=getattr(result, 'doi', None),
                                    title=result.title,
                                    authors=result.authors,
                                    year=int(result.year) if str(result.year).isdigit() else None,
                                    max_related=3,
                                )
                            except Exception as e:
                                md = {"error": str(e)}
                        display_search_result(result, show_abstracts, i, metadata=md)
                
                else:
                    st.markdown("""
                    <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 1.5rem; margin: 2rem 0;">
                        <h4 style="color: #856404; margin-top: 0;">🔍 No Results Found</h4>
                        <p style="color: #856404; margin-bottom: 1rem;">Your search didn't return any papers. Here are some suggestions:</p>
                        <ul style="color: #856404; margin: 0;">
                            <li>Try using different or more general keywords</li>
                            <li>Remove some filters (year range, venues)</li>
                            <li>Use OR instead of AND to broaden your search</li>
                            <li>Check your spelling or try synonyms</li>
                            <li>Search in more fields (title, abstract, authors)</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"Search error: {e}")
                st.exception(e)
    
    elif not query.strip() and search_button:
        st.warning("Please enter a search query.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center'>
    <p>Data from <a href='https://aclanthology.org/'>ACL Anthology</a> | 
    Built with <a href='https://streamlit.io/'>Streamlit</a></p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
