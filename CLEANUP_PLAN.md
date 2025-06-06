# Code Cleanup Plan - Enhanced Orchestrator Only

## Overview
This plan details the cleanup process to remove all redundant code and focus exclusively on the Enhanced Orchestrator implementation. The cleanup will be done carefully to ensure no functionality is broken.

## Current Dependencies Analysis

### Enhanced Orchestrator Dependencies:
1. **Direct imports in enhanced_orchestrator.py:**
   - `from models.schemas import Reflection, SearchQuery, SearchQueryList`
   - `from google.adk` packages (agents, tools, events, types)
   - Standard library modules (json, asyncio, datetime)

2. **Required schema models from models/schemas.py:**
   - `SearchQuery` - Used for query generation
   - `SearchQueryList` - Output schema for query generator
   - `Reflection` - Output schema for reflection analyst
   - NOT USED: `WebSearchResult`, `ResearchState`

3. **No dependencies on:**
   - Individual agent files (query_generator.py, web_search.py, etc.)
   - Other orchestrator implementations
   - Utility functions in utils/

## Files to Remove

### 1. Redundant Orchestrator Implementations
- `/adk-backend/agents/orchestrator.py` - Basic orchestrator
- `/adk-backend/agents/sequential_orchestrator.py` - Sequential orchestrator
- `/adk-backend/agents/custom_orchestrator.py` - Custom orchestrator
- `/adk-backend/agents/simplified_research_agent.py` - Simplified agent

### 2. Individual Agent Files (not used by enhanced orchestrator)
- `/adk-backend/agents/query_generator.py`
- `/adk-backend/agents/web_search.py`
- `/adk-backend/agents/reflection.py`
- `/adk-backend/agents/final_answer.py`

### 3. Unused Utility Files
- `/adk-backend/utils/citations.py`
- `/adk-backend/utils/enhanced_citations.py`

## Files to Modify

### 1. `/adk-backend/services/adk_runner.py`
**Changes needed:**
- Remove commented imports (lines 12, 16)
- Remove unused imports (lines 13, 15)
- Clean up import section to only import enhanced_orchestrator
- Remove any references to other orchestrators in comments

### 2. `/adk-backend/models/schemas.py`
**Changes needed:**
- Keep: `SearchQuery`, `SearchQueryList`, `Reflection` classes
- Remove: `WebSearchResult`, `ResearchState` classes (lines 22-57)

### 3. `/adk-backend/app.py`
**Changes needed:**
- Remove commented import (line 25)
- Clean up any references to ResearchState in comments

### 4. `/adk-backend/agents/__init__.py`
**Changes needed:**
- Update to only export enhanced_orchestrator

### 5. `/adk-backend/utils/__init__.py`
**Changes needed:**
- Can be left empty or removed entirely since no utils are used

## Implementation Order

### Phase 1: Update Import Statements
1. Clean up adk_runner.py imports
2. Clean up app.py imports
3. Update agents/__init__.py

### Phase 2: Clean Up Schema Models
1. Remove unused classes from models/schemas.py
2. Verify enhanced_orchestrator still works

### Phase 3: Remove Redundant Files
1. Delete unused orchestrator implementations
2. Delete individual agent files
3. Delete unused utility files

### Phase 4: Final Verification
1. Test the application to ensure it still works
2. Check for any broken imports
3. Verify all functionality is preserved

## Testing Plan

### Pre-cleanup Testing:
1. Run the application and test a simple query
2. Verify reflection loops work
3. Check that all events stream properly

### Post-cleanup Testing:
1. Repeat all pre-cleanup tests
2. Verify no import errors
3. Check logs for any warnings
4. Test with different effort levels (low, medium, high)

## Rollback Plan
- All changes will be made in a new git branch
- Each phase will be a separate commit
- If issues arise, we can rollback to any previous phase

## Success Criteria
- Application runs without errors
- All imports are clean and explicit
- No redundant code remains
- Enhanced orchestrator functionality is fully preserved
- Code is more maintainable and easier to understand