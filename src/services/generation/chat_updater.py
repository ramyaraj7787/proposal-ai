"""Service for updating generated proposals based on user chat instructions."""

import json
from services.llm.ollama_factory import build_chat_model
from langchain_core.prompts import PromptTemplate

UPDATE_PROMPT = PromptTemplate(
    template="""You are an expert proposal consultant.
The user wants to update their current proposal based on some chat instructions.
You must return the updated proposal sections in valid JSON format.
Each section must have a "title" and "content" key.

### CURRENT PROPOSAL SECTIONS
{current_sections}

### CHAT HISTORY & INSTRUCTIONS
{chat_history}

Please apply the instructions to the current proposal sections.
IMPORTANT: Do not output the entire proposal again. Instead, output a list of specific "actions" to apply.
Actions can be "add" (add a new section to the end), "modify" (completely replace the content of an existing section by matching its title), or "delete" (remove an existing section by title).
Return ONLY a valid JSON object matching this schema:
{{
  "message": "A conversational response telling the user what you changed.",
  "actions": [
    {{
      "type": "add",
      "title": "New Slide Title",
      "content": "Content of the new slide..."
    }},
    {{
      "type": "modify",
      "title": "Existing Slide Title",
      "content": "Completely new content for the existing slide..."
    }},
    {{
      "type": "delete",
      "title": "Slide Title to Delete"
    }}
  ]
}}
""",
    input_variables=["current_sections", "chat_history"]
)

def update_proposal_via_chat(
    current_sections: list[dict],
    chat_history: list[dict],
    settings
) -> list[dict]:
    """Applies user chat instructions to the current proposal sections."""
    llm = build_chat_model(settings)
    
    sections_json = json.dumps(current_sections, indent=2)
    history_str = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in chat_history])
    
    prompt = UPDATE_PROMPT.format(
        current_sections=sections_json,
        chat_history=history_str
    )
    
    response = llm.invoke(prompt)
    content = str(response.content).strip()
    
    # Try to extract the JSON object using regex
    import re
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        json_str = match.group(0)
    else:
        json_str = content
        
    try:
        parsed = json.loads(json_str)
        actions = parsed.get("actions", [])
        ai_message = parsed.get("message", "I have updated the proposal based on your instructions.")
        
        updated_sections = list(current_sections)
        for action in actions:
            action_type = action.get("type")
            title = action.get("title", "")
            content = action.get("content", "")
            
            if action_type == "add":
                updated_sections.append({"title": title, "content": content})
            elif action_type == "modify":
                for sec in updated_sections:
                    if sec["title"].lower() == title.lower():
                        sec["content"] = content
                        break
            elif action_type == "delete":
                updated_sections = [sec for sec in updated_sections if sec["title"].lower() != title.lower()]
                
        return updated_sections, ai_message
    except Exception as e:
        print(f"Error parsing updated sections: {e}")
        print(f"Raw output: {content}")
        return current_sections, "I encountered an error while processing your request. Please try again."
