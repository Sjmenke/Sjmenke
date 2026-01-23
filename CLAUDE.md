# CLAUDE.md - AI Assistant Guide for Sjmenke/Sjmenke Repository

## Repository Overview

This is a **GitHub profile repository** (special repository where the repository name matches the username). The README.md file in this repository automatically appears on the GitHub profile page at https://github.com/Sjmenke.

### Repository Purpose
- Display professional profile information on GitHub
- Showcase interests, skills, and current learning journey
- Provide contact information and collaboration opportunities

### Owner Profile
- **Name**: Sjmenke
- **Background**: Accountant transitioning into data science and Python development
- **Industry**: Big data manufacturing
- **Current Learning**: Python, data science, Oracle Fusion, SQL
- **Interests**: Accounting automation, data analysis, enterprise systems

## Codebase Structure

```
/home/user/Sjmenke/
├── .git/               # Git version control
├── README.md           # Profile page content (visible on GitHub profile)
└── CLAUDE.md           # This file - AI assistant documentation
```

### Key Files

#### README.md
- **Purpose**: Main profile content displayed on GitHub
- **Format**: GitHub-flavored Markdown
- **Audience**: Public viewers of the GitHub profile
- **Content**: Personal introduction, interests, skills, contact info

#### CLAUDE.md
- **Purpose**: Documentation for AI assistants working with this repository
- **Format**: Markdown
- **Audience**: AI assistants (Claude, etc.)
- **Content**: Repository context, conventions, workflows

## Development Workflows

### Branch Strategy
- **Main Branch**: `main` (default branch for profile display)
- **Feature Branches**: Use `claude/` prefix for AI-assisted work
  - Pattern: `claude/<description>-<session-id>`
  - Example: `claude/add-claude-documentation-oTI0r`

### Making Changes to README.md

When updating the profile README:

1. **Read Current Content**: Always read README.md before making changes
2. **Understand Context**: This is a professional profile - maintain professional tone
3. **Preserve Structure**: Keep the existing format with emoji indicators
4. **Update Relevant Sections**: Only modify sections that need changes
5. **Test Locally**: Ensure markdown renders correctly
6. **Commit with Clear Messages**: Describe what was updated
7. **Push to Feature Branch**: Use `git push -u origin <branch-name>`

### Adding New Content

For adding projects, skills, or sections:

1. **Maintain Professional Tone**: Balance personality with professionalism
2. **Use GitHub Markdown Features**:
   - Emoji for visual interest (existing style uses emoji bullets)
   - Headers for organization
   - Links to projects/resources
   - Code blocks for technical examples
3. **Keep it Concise**: Profile should be scannable
4. **Update Progressively**: Reflect current skills and interests

## Key Conventions for AI Assistants

### Content Guidelines

1. **Professional but Personal**: This is an individual's profile, not corporate documentation
2. **Accounting + Tech Focus**: Highlight intersection of accounting and data science
3. **Learning Journey**: Emphasize growth and current learning (user is transitioning careers)
4. **Collaboration Ready**: Make it clear what collaboration opportunities exist

### Technical Conventions

1. **Markdown Style**:
   - Use emoji bullets (👋, 👀, 🌱, 💞️, 📫) for main points
   - Keep lines readable (no excessive length)
   - Use proper markdown syntax for links and formatting

2. **Git Practices**:
   - Always work on feature branches (never commit directly to main)
   - Use descriptive commit messages
   - Include session URLs in commits: `https://claude.ai/code/session_<id>`

3. **Privacy**:
   - DO NOT add personal contact information without explicit permission
   - Keep "How to reach me" as TBD unless user provides contact info
   - Avoid adding sensitive information (email, phone, address)

### Common Tasks

#### Updating Skills/Technologies
When adding new skills the user has learned:
- Add to the "I'm currently learning" section
- Consider moving from "learning" to "experienced with" if appropriate
- Maintain parallel structure with existing items

#### Adding Projects
If the user wants to showcase projects:
- Create a new "Projects" section with header
- Use links to project repositories
- Brief description (1-2 sentences per project)
- Highlight accounting/data science applications

#### Updating Collaboration Interests
When modifying collaboration section:
- Keep specific to accounting/data domains
- Mention relevant technologies (Python, SQL, Oracle Fusion)
- Be clear about what type of collaboration is sought

## Repository-Specific Notes

### This is a Profile Repository
- Changes to README.md are immediately visible on the GitHub profile
- This is PUBLIC - all content is visible to anyone
- Focus on professional presentation

### Current State (2026-01-23)
- Repository is minimal (README only)
- Profile describes learning journey in Python/data science
- Accounting background with big data manufacturing context
- No contact information provided yet (marked TBD)

### Potential Enhancements
Consider suggesting these if relevant:

1. **GitHub Stats**: Add GitHub stats widgets/badges
2. **Tech Stack Section**: Visual representation of technologies
3. **Project Showcase**: Links to notable repositories
4. **Blog/Articles**: Links to technical writing if applicable
5. **Certifications**: Accounting or data science certifications
6. **LinkedIn/Professional Links**: When user is ready to share

## Working with This Repository

### Before Making Changes
1. Read README.md to understand current state
2. Understand the user's intent
3. Check if changes align with professional profile goals

### After Making Changes
1. Commit with descriptive message
2. Push to appropriate branch
3. Be ready to create PR if requested
4. Summarize changes made

### Git Commands Reference
```bash
# Check current status
git status

# Create and switch to feature branch
git checkout -b claude/description-sessionId

# Stage changes
git add README.md

# Commit with message
git commit -m "Update profile: description

https://claude.ai/code/session_<id>"

# Push to feature branch
git push -u origin claude/description-sessionId
```

## Best Practices for AI Assistants

1. **Respect the Learning Journey**: User is actively learning - be encouraging
2. **Accounting Context Matters**: Understand that solutions should apply to accounting/finance domains
3. **Professional Development Focus**: This profile supports career transition
4. **Keep it Updated**: Profile should reflect current, not outdated, information
5. **Ask Before Adding Contact Info**: Privacy is important
6. **Maintain Consistency**: Match existing tone and style
7. **Test Suggestions**: Ensure markdown renders correctly

## Questions to Ask User

When uncertain, consider asking:
- "Would you like to add any completed projects to your profile?"
- "Have you moved from learning to comfortable with any technologies?"
- "Are you ready to add contact information?"
- "Would you like to add any certifications or credentials?"
- "Should we highlight any specific accounting or data science achievements?"

## Resources

- [GitHub Profile README Guide](https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-github-profile/customizing-your-profile/managing-your-profile-readme)
- [Markdown Guide](https://www.markdownguide.org/)
- [Emoji Cheat Sheet](https://github.com/ikatyang/emoji-cheat-sheet)

---

**Last Updated**: 2026-01-23
**Repository**: Sjmenke/Sjmenke (GitHub Profile Repository)
**Primary Language**: Markdown
**Purpose**: Professional GitHub profile display
