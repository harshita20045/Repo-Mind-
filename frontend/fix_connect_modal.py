import re

file_path = 'frontend/src/pages/RepositoriesPage.jsx'
with open(file_path, 'r') as f:
    content = f.read()

# Remove the PAT field from initial state
content = content.replace("github_owner: '', github_name: '', default_branch: 'main', pat: ''", "github_owner: '', github_name: '', default_branch: 'main'")

# Replace the PAT input in the form with a connect button logic if needed
pat_field = """<Field
            label="Personal Access Token (PAT)"
            hint="Requires 'repo' scope. Encrypted immediately — never stored in plaintext."
          >
            <TextInput
              type="password"
              value={repoForm.pat}
              onChange={(e) => setRepoForm({ ...repoForm, pat: e.target.value })}
              placeholder="ghp_xxxxxxxxxxxx"
              autoComplete="new-password"
            />
          </Field>"""

# Replace the pat field with nothing, since we use OAuth now
content = content.replace(pat_field, "")

# Modify the connect repo button disabled condition
content = content.replace("!repoForm.github_owner || !repoForm.github_name || !repoForm.pat", "!repoForm.github_owner || !repoForm.github_name")

# Also, add an OAuth login button in the modal if there's an error containing 'connect your GitHub account'
error_block = """{errorMsg && (
          <div className="mb-4 p-3 bg-danger/8 border border-danger/20 text-danger text-sm rounded-lg" role="alert">
            {errorMsg}
          </div>
        )}"""

new_error_block = """{errorMsg && (
          <div className="mb-4 p-3 bg-danger/8 border border-danger/20 text-danger text-sm rounded-lg flex flex-col gap-2" role="alert">
            <div>{errorMsg}</div>
            {errorMsg.includes('connect your GitHub account') && (
              <Button
                variant="primary"
                size="xs"
                onClick={() => window.location.href = '/api/github/oauth/login'}
                className="self-start mt-1"
              >
                Connect GitHub Account
              </Button>
            )}
          </div>
        )}"""

content = content.replace(error_block, new_error_block)

with open(file_path, 'w') as f:
    f.write(content)
