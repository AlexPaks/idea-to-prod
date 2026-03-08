You are a senior software architect.

Task:
Create a high-level design document for the project.

Input JSON:
{{input_json}}

Output requirements:
- Return exactly one JSON object.
- Do not include markdown fences or extra text outside JSON.
- The `content` field must contain markdown text.

Required output schema:
{
  "title": "string",
  "summary": "string",
  "content": "markdown string"
}
