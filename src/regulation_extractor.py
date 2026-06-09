"""Extract relevant regulations/articles from full text based on relevance."""

import re
from typing import List, Tuple


def extract_articles_by_pattern(text: str) -> List[Tuple[str, str]]:
    """Extract articles with clear patterns like '第X条'.
    
    Returns list of tuples: (article_number, article_content)
    """
    # Pattern for "第X条" format (e.g., 第四十五条、第45条)
    pattern = r'(第[^\s]+?条)[^\n]*\n((?:(?!第[^\s]+?条).)*?)(?=\n(?:第[^\s]+?条)|$)'
    
    matches = re.finditer(pattern, text, re.DOTALL)
    articles = []
    
    for match in matches:
        article_num = match.group(1).strip()
        article_content = match.group(2).strip()
        if article_content:  # Only add if there's actual content
            articles.append((article_num, article_content))
    
    return articles


def _identify_source(text: str) -> str:
    """Identify the source document from content."""
    first_1000 = text[:1000].lower()
    if "顺丰" in first_1000:
        return "顺丰条款"
    elif "韵达" in first_1000:
        return "韵达条款"
    elif "邮政" in first_1000:
        return "邮政规定"
    elif "sf express" in first_1000 or "spx" in first_1000:
        return "快递条款"
    else:
        return "相关条款"


def extract_relevant_articles(full_text: str, query: str = "", max_articles: int = 3) -> List[Tuple[str, str]]:
    """Extract relevant articles from the retrieved text.
    
    Args:
        full_text: The full text retrieved from vector store
        query: The original query (used for filtering if needed)
        max_articles: Maximum number of articles to extract
        
    Returns:
        List of tuples: (article_identifier, article_content)
    """
    # First try pattern-based extraction for "第X条" format
    articles = extract_articles_by_pattern(full_text)
    
    if articles:
        # Found numbered articles
        if len(articles) <= max_articles:
            return articles
        return articles[:max_articles]
    
    # No numbered articles - format the whole document as relevant context
    # Take the relevant parts (skip very long blocks)
    text_preview = full_text[:1500]  # Take reasonable amount for display
    
    # Try to identify the source
    source = _identify_source(full_text)
    
    return [(source, text_preview)]


def format_articles_for_output(articles: List[Tuple[str, str]]) -> str:
    """Format articles for user-friendly output."""
    if not articles:
        return ""
    
    formatted = []
    for article_num, article_content in articles:
        formatted.append(f"\n【{article_num}】\n{article_content}")
    
    return "\n".join(formatted)


def format_articles_for_llm(articles: List[Tuple[str, str]]) -> str:
    """Format articles for LLM to use as context."""
    if not articles:
        return ""
    
    formatted = []
    for article_num, article_content in articles:
        formatted.append(f"{article_num}\n{article_content}")
    
    return "\n\n".join(formatted)
