# CLAUDE EXECUTION CONTRACT

## 1. PURPOSE
You are building the CourtDominion frontend based ONLY on:
- CLAUDE_COMPLETE_REQUIREMENTS.md

## 2. ALLOWED MODES
✔ Execute instructions  
✔ Generate code  
✔ Follow structure EXACTLY  

## 3. FORBIDDEN MODES
✘ Asking questions  
✘ Suggesting improvements  
✘ Inventing features  
✘ Changing file locations  
✘ Reinterpreting requirements  
✘ Hardcoding text  

## 4. PRIORITY RULES
If a conflict appears:  
1. CLAUDE_COMPLETE_REQUIREMENTS.md  
2. SHORT_ANSWERS_FOR_CLAUDE.md  
3. User’s newest message  
4. Fallback to local JSON  

## 5. OUTPUT REQUIREMENTS
- ALL CODE MUST BE COMPLETE  
- NO hardcoded UI text  
- MUST follow folder structure exactly  

## 6. SESSION LOSS HANDLING
If you lose context:
→ Reload EVERYTHING from attached files  
→ Continue without questions  
