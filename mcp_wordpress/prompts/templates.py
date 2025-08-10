"""MCP Prompts for content creation templates."""

from fastmcp import FastMCP


def register_content_prompts(mcp: FastMCP):
    """Register all content creation prompts with the MCP server."""
    
    @mcp.prompt()
    async def article_template(
        topic: str,
        target_audience: str = "general readers"
    ) -> str:
        """Generate article template with best practices.
        
        Args:
            topic: Article topic or subject
            target_audience: Target audience for the article (optional)
        """
        template = f"""# Article Template: {topic}

## Target Audience
{target_audience}

## Article Structure

### 1. Compelling Headline
Create an attention-grabbing headline that:
- Clearly states the main benefit or value proposition
- Includes relevant keywords for SEO
- Is under 60 characters for optimal display

### 2. Introduction (100-150 words)
- Hook the reader with an interesting fact, question, or statistic
- Clearly state what the article will cover
- Explain why this topic matters to your audience
- Preview the main points or benefits

### 3. Main Content Sections
Break your content into 3-5 main sections:

#### Section 1: [Primary Point]
- Start with your most important point
- Use subheadings to organize information
- Include relevant examples or case studies
- Add bullet points for easy scanning

#### Section 2: [Supporting Information]
- Provide detailed explanations
- Use data and evidence to support your claims
- Include quotes from experts or relevant sources
- Add visuals if applicable (images, charts, etc.)

#### Section 3: [Practical Application]
- Show how readers can apply this information
- Provide step-by-step instructions when relevant
- Include tips and best practices
- Address common challenges or misconceptions

### 4. Conclusion (75-100 words)
- Summarize the key takeaways
- Reinforce the main benefit or value
- Include a clear call-to-action
- Encourage engagement (comments, shares, etc.)

## SEO Best Practices
- Use the focus keyword in the title, first paragraph, and throughout the content naturally
- Include related keywords and synonyms
- Write meta description (150-160 characters)
- Use proper heading structure (H1, H2, H3)
- Add internal and external links where relevant

## Content Guidelines
- Write in active voice when possible
- Use short paragraphs (2-3 sentences)
- Include transition words for flow
- Maintain consistent tone throughout
- Proofread for grammar and clarity

---

**Topic**: {topic}
**Target Audience**: {target_audience}
**Recommended Length**: 800-1500 words
**Tone**: Professional, informative, engaging"""

        return template
    
    @mcp.prompt()
    async def review_checklist(content_type: str) -> str:
        """Generate review checklist for content quality.
        
        Args:
            content_type: Type of content being reviewed
        """
        base_checklist = f"""# Content Review Checklist: {content_type}

## Content Quality
- [ ] **Accuracy**: All facts and information are accurate and up-to-date
- [ ] **Completeness**: Content covers the topic comprehensively
- [ ] **Clarity**: Writing is clear, concise, and easy to understand
- [ ] **Value**: Content provides genuine value to the target audience
- [ ] **Originality**: Content is original and not plagiarized

## Technical Requirements
- [ ] **Grammar**: No grammatical errors or typos
- [ ] **Formatting**: Proper use of headings, bullet points, and formatting
- [ ] **Length**: Appropriate length for the content type and topic
- [ ] **Links**: All links are working and relevant
- [ ] **Images**: Images are properly attributed and optimized

## SEO Optimization
- [ ] **Keywords**: Focus keywords are naturally integrated
- [ ] **Headings**: Proper heading structure (H1, H2, H3)
- [ ] **Meta Elements**: Title and description are SEO-friendly
- [ ] **Internal Links**: Relevant internal links are included
- [ ] **Readability**: Content is easy to read and scan

## WordPress Compliance
- [ ] **Categories**: Appropriate category is assigned
- [ ] **Tags**: Relevant tags are added (3-8 tags recommended)
- [ ] **Featured Image**: Featured image is set if required
- [ ] **Excerpt**: Custom excerpt is written if needed
- [ ] **Publication Status**: Ready for immediate publication

## Brand Consistency
- [ ] **Tone**: Matches brand voice and style guidelines
- [ ] **Messaging**: Aligns with brand values and messaging
- [ ] **Style**: Follows editorial style guide
- [ ] **Legal**: No copyright or legal issues
- [ ] **Compliance**: Meets industry and regulatory requirements

## Final Review
- [ ] **Proofreading**: Content has been thoroughly proofread
- [ ] **Fact-checking**: All claims and statistics are verified
- [ ] **Approval**: Content is approved for publication
- [ ] **Scheduling**: Publication timing is appropriate

## Reviewer Notes
**Reviewer**: [Name]
**Review Date**: [Date]
**Overall Rating**: [1-5 stars]
**Recommendation**: [Approve/Reject/Revise]

### Comments:
[Detailed feedback and suggestions]

### Required Changes (if any):
[List specific changes needed before approval]"""

        # Add content-type specific checks
        if content_type.lower() in ["blog", "article", "post"]:
            specific_checks = """

## Blog-Specific Checks
- [ ] **Engagement**: Content encourages reader interaction
- [ ] **Social Sharing**: Content is optimized for social media sharing
- [ ] **Call-to-Action**: Clear next steps for readers
- [ ] **Related Content**: Links to related articles are included"""
            
        elif content_type.lower() in ["tutorial", "guide", "how-to"]:
            specific_checks = """

## Tutorial-Specific Checks
- [ ] **Step-by-Step**: Instructions are clear and sequential
- [ ] **Prerequisites**: Required knowledge or tools are listed
- [ ] **Examples**: Concrete examples are provided
- [ ] **Troubleshooting**: Common issues and solutions are addressed"""
            
        elif content_type.lower() in ["review", "comparison"]:
            specific_checks = """

## Review-Specific Checks
- [ ] **Objectivity**: Review is fair and unbiased
- [ ] **Criteria**: Evaluation criteria are clearly stated
- [ ] **Evidence**: Claims are supported by evidence
- [ ] **Conclusion**: Clear recommendation is provided"""
        else:
            specific_checks = ""
        
        return base_checklist + specific_checks
    
    @mcp.prompt()
    async def wordpress_formatting() -> str:
        """Generate WordPress formatting guide and best practices."""
        return """# WordPress Formatting Guide

## Content Structure

### Headings Hierarchy
- **H1**: Article title (automatically generated from title field)
- **H2**: Main section headings
- **H3**: Subsection headings
- **H4-H6**: Use sparingly for deep hierarchies

Example:
```markdown
# Main Title (H1 - WordPress generates this)
## Introduction (H2)
### Key Concepts (H3)
#### Implementation Details (H4)
```

### Paragraph Structure
- Keep paragraphs short (2-4 sentences)
- Use line breaks between paragraphs
- Start with topic sentences
- End with transition sentences when needed

## Text Formatting

### Emphasis
- **Bold** for important terms and key points
- *Italic* for emphasis and foreign words
- `Code` for technical terms and commands
- ~~Strikethrough~~ for corrections or deprecated information

### Lists
**Unordered Lists:**
- Use for non-sequential items
- Keep items parallel in structure
- Limit to 7±2 items for readability

**Ordered Lists:**
1. Use for sequential steps
2. Number items consecutively
3. Use sub-lists when needed

### Code Blocks
Use fenced code blocks with language specification:

```python
def example_function():
    return "Hello, WordPress!"
```

```javascript
const greeting = () => {
    console.log("Hello, WordPress!");
};
```

## Links and References

### Internal Links
- Link to related content on your site
- Use descriptive anchor text
- Avoid "click here" or "read more"
- Example: [WordPress security best practices](internal-link)

### External Links
- Link to authoritative sources
- Open in new tab for external sites (WordPress handles this)
- Use rel="nofollow" for untrusted sources
- Example: [Official WordPress documentation](https://wordpress.org/documentation/)

## Images and Media

### Image Guidelines
- Use descriptive alt text for accessibility
- Optimize images for web (WebP format preferred)
- Include captions when helpful
- Maintain consistent aspect ratios

### WordPress Image Syntax
```markdown
![Alt text description](image-url "Optional caption")
```

## Special WordPress Features

### Shortcodes
WordPress supports shortcodes for special functionality:
- `[gallery]` for image galleries
- `[caption]` for image captions
- `[embed]` for media embeds

### Blocks (Gutenberg)
When using Gutenberg editor, content will be converted to blocks:
- Paragraphs become paragraph blocks
- Headings become heading blocks
- Code blocks become code blocks
- Lists become list blocks

## SEO Optimization

### Keyword Usage
- Include focus keyword in first paragraph
- Use keywords naturally throughout content
- Include related keywords and synonyms
- Avoid keyword stuffing

### Meta Information
- Write compelling meta descriptions (150-160 characters)
- Use focus keyword in meta description
- Include publication date and author information

## Content Categories and Tags

### Categories
- Use 1-2 primary categories
- Choose existing categories when possible
- Create new categories sparingly

### Tags
- Use 3-8 relevant tags
- Mix broad and specific tags
- Include both topic and format tags
- Examples: "tutorial", "wordpress", "beginners", "advanced"

## Accessibility

### Screen Reader Friendly
- Use proper heading hierarchy
- Include alt text for images
- Use descriptive link text
- Maintain good color contrast

### Mobile Optimization
- Keep paragraphs short for mobile reading
- Use responsive images
- Ensure touch targets are adequate
- Test on mobile devices

## WordPress-Specific Markdown Extensions

### Table of Contents
```markdown
[TOC]
```

### WordPress Blocks
```markdown
<!-- wp:heading {"level":2} -->
## Section Title
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Paragraph content here.</p>
<!-- /wp:paragraph -->
```

## Quality Checklist

Before publishing, ensure:
- [ ] Content follows proper heading hierarchy
- [ ] All links are working and relevant
- [ ] Images have alt text and are optimized
- [ ] Grammar and spelling are correct
- [ ] Content is properly categorized and tagged
- [ ] SEO elements are optimized
- [ ] Content is mobile-friendly
- [ ] Accessibility guidelines are followed

## Common Mistakes to Avoid

1. **Poor heading structure**: Skipping heading levels (H2 to H4)
2. **Wall of text**: Long paragraphs without breaks
3. **Missing alt text**: Images without accessibility descriptions
4. **Weak links**: Using "click here" instead of descriptive text
5. **Over-optimization**: Keyword stuffing and unnatural language
6. **Inconsistent formatting**: Mixed styles throughout the article
7. **Missing categories**: Publishing without proper categorization

---

*This guide ensures your content is optimized for WordPress, SEO, and user experience.*"""