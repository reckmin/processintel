# Contributing Guidelines

Thank you for your interest in contributing to this project!

This project is primarily developed by **students as part of their bachelor theses**.  
The goal is to maintain a **high-quality, well-tested, well-documented, and secure academic codebase**, suitable for **research, reproducibility, and long-term maintenance** in the field of **process mining**.

Please read and follow these guidelines carefully.

---

## General Principles

- Keep changes **small, focused, and reviewable**
- Maintain **high code quality**
- Write **tests for all relevant code**
- Document your work clearly and precisely
- Follow established software engineering and academic best practices
- These rules apply to **all contributors**, including thesis students

---

## Required Setup

Before contributing, you must complete the following one-time setup steps.
These requirements apply to all contributors, including thesis students.

### SSH Keys

SSH is used to securely authenticate all access to the repository. All interactions with the repository must use SSH. HTTPS access is not allowed.  

You must generate an SSH key and add it to your Forgejo account.

How to generate and add an SSH key:  
See [SETUP.md](SETUP.md#ssh-key-setup) for step-by-step instructions.

### GPG Keys & Signed Commits

GPG is used to cryptographically sign commits and verify authorship. All commits must be signed using GPG.  

Your public GPG key must be added to your Forgejo profile.    

Enable commit signing:
```bash
git config --global commit.gpgsign true
git config --global user.signingkey YOUR_KEY_ID
```

How to generate and add a GPG key:  
See [SETUP.md](SETUP.md#gpg-key-setup) for detailed instructions.

### Forking the Repository

You must work in your own fork. The main repository is read-only for contributors. 
Direct commits to the main repository are not allowed.  

Create and clone your fork:

```bash
git clone ssh://git@code.swisdata.eu:your-username/processintel.git
```

Add the upstream repository:
```bash
git remote add upstream ssh://git@code.swisdata.eu:SWISDATA/processintel.git
```

## Repository Workflow

All development must be performed in a personal fork of the main repository. Contributions are integrated into the main repository exclusively via Pull Requests (PRs).  

Direct commits to the main repository are not allowed.

**Workflow Overview**

1. Fork the main repository on Forgejo
2. Clone your fork locally
3. Create a dedicated branch for your change
4. Implement, document, and test your changes
5. Push the branch to your fork
6. Open a Pull Request
---

## Branch Guidelines

- Every change must be made in its own branch.
- Never commit directly to main. 
- Branches must be short-lived and focused. 
- One branch contains one logical change.  

### Branch Naming Convention

Use descriptive names:

- add-xes-support
- fix-event-log-parser
- refactor-miner-interface
- update-documentation

---

## Commit Message Guidelines

Required Format:
```
<module>.[<submodule>]: short description
```

### Rules

- Use the imperative mood ("add", "fix", "refactor")
- Keep the description concise and specific
- One logical change per commit
- Do not mix unrelated changes

### Examples
- parser.xes: add support for xes format
- miner.inductive: fix recursion depth issue
- docs.architecture: clarify MVC responsibilities

---

## Pull Request Guidelines

All contributions must be submitted via a Pull Request from a fork.
Each Pull Request must address exactly one concern.

Allowed:
- One feature
- One bug fix
- One refactor

Not allowed:
- Mixing unrelated changes
- Combining features and fixes
- Large, unfocused cleanup PRs

Split work into multiple PRs if necessary.

Never ever create merge commits. Rebase + fast forward  only.  
Thus never pull without `--ff-only`. Better `git fetch` + `git rebase …`

When adding changes to pull request, keep the commits clean. Never ever add unecessary fix commits.  
Squash your commits with an interactive rebase:  
`git rebase -i HEAD~5` (for editing the last 5 commits).

### Pull Request Requirements

Each Pull Request must:
- Be opened from a fork and a dedicated branch
- Target the main branch of the upstream repository
- Include a clear description of:
     - What was changed
     - What sections were tested
- Pass all automated checks
- Include required documentation and tests

---

## Code Formatting

This project **requires** the use of the **Black** code formatter.

- All Python code must be formatted with Black
- Formatting is not optional

Install and run:

```bash
pip install black
black .
```
---

## Docstring Guidelines

### Docstring Rules

- Use **NumPy docstring format**
- Be precise and explicit
- All parameters and return values must be documented

### Required structure

```python
"""Short summary of the function.

Parameters 
---------- 
param_name : type
     Description of the parameter. 
optional_param : type, optional
     Description, by default VALUE
       
Returns 
------- 
return_type
     Description of the return value.
     
Raises 
------ 
ExceptionType
     Description of when this exception is raised. 
"""
```

---

## Testing Guildines

Testing is a core requirement for correctness, reproducibility, and validity.

### Framework

- Python's built-in unittest framework is used exclusively
- Do not introduce alternative testing frameworks

### Requirements

- New functionality must include new tests
- Tests must be deterministic and reproducible
- Tests must not rely on external state or network access

### Structure

- Tests must be placed in the `tests` directory
- Test files must be named `<module>/<name>_test.py`
- Use descriptive test class and method names
- Each test should validate one specific behavior

---

## Review Process

- All Pull Requests require review
- Feedback is part of the learning process
- Maintainers have final merge authority
- Changes may be requested for correctness or clarity

---

## Extending the Project

Guidelines for extending the project architecture (UI pages, views, algorithms, models, and data formats) are documented separately.

Before implementing new features, contributors **should read**:

- [EXTENDING.md](docs/EXTENDING.md) - Architecture and extension guidelines

All extensions are expected to follow the documented MVC structure and existing templates.

---

## Questions

If something is unclear, open an issue or contact your supervisor.  
Do not hesitate to ask questions

---

Thank you for contributing to a **high-quality and secure** open source process mining project.