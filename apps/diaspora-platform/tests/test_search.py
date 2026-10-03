"""
Integration tests for Diaspora search.

Tests community search using shared_search.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "packages"))
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDiasporaSearch:
    """Test Diaspora community search."""
    
    def test_import(self):
        """Test importing community search."""
        from search.community_search import DiasporaCommunitySearch
        
        assert DiasporaCommunitySearch is not None
    
    def test_requires_faiss(self):
        """Test that search requires FAISS."""
        from shared_search import FAISS_AVAILABLE
        
        if FAISS_AVAILABLE:
            pytest.skip("FAISS is available")
        
        from search.community_search import DiasporaCommunitySearch
        
        # Should raise ImportError without FAISS
        with pytest.raises(ImportError):
            DiasporaCommunitySearch()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
