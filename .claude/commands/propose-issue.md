Analyze the GitHub issue and propose concrete code changes to implement it.

## Steps

1. Fetch the issue details:
   ```
   gh issue view $ARGUMENTS --json number,title,body,labels,assignees,comments
   ```

2. Read the relevant source files based on the issue description. Focus on:
   - `bonbon-lambda/hello_world/app.py` for Lambda handler changes
   - `bonbon-lambda/template.yaml` for infrastructure changes
   - `bonbon-lambda/tests/` for test changes

3. Propose a minimal, targeted diff that addresses the issue. Show:
   - Which files to change
   - The exact code additions/removals (unified diff format)
   - Why each change is needed

4. List any test changes required alongside the implementation changes.

Do NOT implement the changes — only propose them. End with a summary sentence of what the change does and its scope.
