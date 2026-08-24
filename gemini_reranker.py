import logging
import os
import re
from typing import List, Optional

logger = logging.getLogger(__name__)

def rerank_results_with_gemini(
    query: str,
    top_results: List[dict],
    api_key: Optional[str] = None,
    model_name: str = "gemini-3.5-flash",
) -> List[dict]:
    """
    Reranks top search results using Gemini with strict type safety, 
    regex-based parsing, duplicate prevention, and robust error fallbacks.
    """
    # 1. Early exit if input is empty
    if not top_results:
        return []
    
    # 2. Resolve API key securely from args or environment
    resolved_api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not resolved_api_key:
        logger.warning("GEMINI_API_KEY not found. Skipping Gemini reranking.")
        return top_results

    try:
        from google import genai

        # 3. Initialize Gemini client
        client = genai.Client(api_key=resolved_api_key)
        
        # 4. Format candidates for the prompt payload
        candidates_text = ""
        for idx, res in enumerate(top_results):
            candidates_text += f"ID: {idx} | Video: {res.get('video_id', 'N/A')} | Timestamp: {res.get('timestamp_s', 0.0)}s | OCR: {res.get('ocr_text', 'None')}\n"
        
        prompt = f"""
        You are an AI video search reranker. 
        User Query: "{query}"
        
        Here are the top matching video frames:
        {candidates_text}
        
        Task: Analyze these candidates against the query and return their IDs sorted by relevance (most relevant first).
        CRITICAL INSTRUCTION: Return ONLY a comma-separated list of integer IDs (e.g., 2,0,1,3). Do not include any explanations, markdown, or extra text.
        """
        
        # 5. Invoke Gemini model
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        
        if not response or not getattr(response, 'text', None):
            return top_results
            
        raw_text = response.text.strip()
        
        # 6. Extract integer IDs safely via regex
        found_numbers = re.findall(r'\d+', raw_text)
        if not found_numbers:
            return top_results
            
        parsed_indices = [int(n) for n in found_numbers]
        
        # 7. Reconstruct reranked list with bounds and duplicate checks
        reranked_results = []
        seen = set()
        
        for idx in parsed_indices:
            if idx < len(top_results) and idx not in seen:
                reranked_results.append(top_results[idx])
                seen.add(idx)
        
        # 8. Ensure no missing items are lost (fallback append)
        for idx in range(len(top_results)):
            if idx not in seen:
                reranked_results.append(top_results[idx])
                
        return reranked_results if reranked_results else top_results
            
    except Exception as e:
        logger.warning("Gemini Reranking failed (%s). Falling back to original FAISS results.", e)
        return top_results