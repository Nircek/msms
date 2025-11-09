---
applyTo: '.github/prompts/*.md'
description: 'Prompt authoring guidelines'
---
- Keep prompts focused on the task, referencing instructions instead of duplicating them.
- Define the task to achieve, including specific requirements, constraints, and success criteria.
- Reuse and reference instructions files to keep them clean and focused, and to avoid duplicating instructions.

## Collaboration Guidelines
- **Complete all tasks:** Never use phrases like "Given the volume, let me focus on the most important ones" — always execute commands fully
- **Systematic approach:** Work through all files methodically, not selectively
- **No shortcuts:** When asked to "find all X", actually find and process ALL instances
- **Update instructions:** Always update relevant instruction files after completing systematic changes

## Prompt file examples

The following examples demonstrate how to use prompt files.

```markdown
---
mode: 'agent'
model: GPT-4o
tools: ['githubRepo', 'search/codebase']
description: 'Generate a new React form component'
---
Your goal is to generate a new React form component based on the templates in #githubRepo contoso/react-templates.

Ask for the form name and fields if not provided.

Requirements for the form:
* Use the approved design system components referenced in project docs
* Use `react-hook-form` for form state management:
* Always define TypeScript types for your form data
* Prefer *uncontrolled* components using register
* Use `defaultValues` to prevent unnecessary rerenders
* Use `yup` for validation:
* Create reusable validation schemas in separate files
* Use TypeScript types to ensure type safety
* Customize UX-friendly validation rules
```


```markdown
---
mode: 'ask'
model: Claude Sonnet 4
description: 'Perform a REST API security review'
---
Perform a REST API security review and provide a TODO list of security issues to address.

* Ensure all endpoints are protected by authentication and authorization
* Validate all user inputs and sanitize data
* Implement rate limiting and throttling
* Implement logging and monitoring for security events

Return the TODO list in a Markdown format, grouped by priority and issue type.
```


## Prompt file format

Prompt files are Markdown files and use the `.prompt.md` extension and have this structure:

* **Header** (optional): YAML frontmatter including `description`
    * `description`: Short description of the prompt
    * `mode`: Chat mode used for running the prompt: `ask`, `edit`, or `agent` (default).
    * `model`: Language model used when running the prompt. If not specified, the currently selected model in model picker is used.
    * `tools`: Array of tool (set) names that can be used. Select **Configure Tools** to select the tools from the list of available tools in your workspace. If a given tool (set) is not available when running the prompt, it is ignored.

* **Body**: Prompt instructions in Markdown format

    Reference other workspace files, prompt files, or instruction files by using Markdown links. Use relative paths to reference these files, and ensure that the paths are correct based on the location of the prompt file.

    Within a prompt file, you can reference variables by using the `${variableName}` syntax. You can reference the following variables:

    * Workspace variables - `${workspaceFolder}`, `${workspaceFolderBasename}`
    * Selection variables - `${selection}`, `${selectedText}`
    * File context variables - `${file}`, `${fileBasename}`, `${fileDirname}`, `${fileBasenameNoExtension}`
    * Input variables - `${input:variableName}`, `${input:variableName:placeholder}` (pass values to the prompt from the chat input field)

### Tool list priority

You can specify the list of available tools for both a chat mode and prompt file by using the `tools` metadata field. Prompt files can also reference a chat mode by using the `mode` metadata field.

The list available tools in chat is determined by the following priority order:

1. Tools specified in the prompt file (if any)
2. Tools from the referenced chat mode in the prompt file (if any)
3. Default tools for the selected chat mode

## Tips for defining prompt files

* Clearly describe what the prompt should accomplish and what output format is expected.

* Provide examples of the expected input and output to guide the AI's responses.

* Use Markdown links to reference custom instructions rather than duplicating guidelines in each prompt.

* Take advantage of built-in variables like `${selection}` and input variables to make prompts more flexible.

* Use the editor play button to test your prompts and refine them based on the results.
