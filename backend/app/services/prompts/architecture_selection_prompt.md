You are an experienced solution architect.

Task:
Select a practical architecture for the project based on the provided idea and classification.

Input JSON:
{{input_json}}

Output requirements:
- Return exactly one JSON object.
- Do not include markdown, code fences, or commentary.
- Keep recommendations realistic for a small-to-medium full-stack product.
- All fields must be present.

Required output schema:
{
  "frontend_stack": "string",
  "backend_stack": "string",
  "database": "string",
  "auth_strategy": "string",
  "deployment_shape": "string",
  "background_jobs": ["string"],
  "recommended_modules": ["string"],
  "recommended_entities": ["string"],
  "api_groups": ["string"],
  "frontend_pages": ["string"],
  "testing_strategy": ["string"],
  "notes": ["string"]
}
