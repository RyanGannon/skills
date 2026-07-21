---
name: transcript-refinement
description: Refine raw auto-generated transcripts (from YouTube, podcasts, meetings, talks, interviews) into polished, readable Markdown documents. Use this skill whenever the user uploads or pastes a raw transcript and wants it cleaned up, edited, or turned into a readable document. Trigger on phrases like "clean up this transcript", "refine this transcript", "polish this transcript", "edit this transcript", "make this readable", or any mention of a raw/auto-generated transcript paired with a request to improve it. Also trigger when the user uploads a .txt, .srt, .vtt, or .md file that looks like a speech-to-text transcript. Even if the user just says "here's a transcript" with no other instructions, use this skill.
---

# Transcript Refinement

Transform raw auto-generated transcripts into polished, readable Markdown documents that preserve the speaker's authentic voice.

## When you receive a transcript

1. Read the full transcript to understand the speaker, topic, structure, and tone before making any changes.
2. Identify the main topic — you'll use it to create a title.
3. Look for natural topic shifts — these will become section boundaries.
4. Note the speaker's distinctive voice: their favorite phrases, rhetorical style, humor, and emphasis patterns.

## Editing Rules

### Fix transcription errors

- Correct misheard words, names, technical terms, proper nouns, acronyms, and company names. Use surrounding context and your knowledge to infer the right spelling.
- Fix grammar and punctuation lost in speech-to-text conversion.
- If you're unsure about a name or term, make your best guess based on context rather than leaving the error in place. Flag genuinely ambiguous cases with a `[?]` marker so the user can verify.

### Preserve the speaker's voice

This is the most important rule. The output should sound like the speaker wrote it themselves on a very good writing day — not like a ghostwritten article or a corporate blog post.

- Keep their phrasing, sentence rhythms, tone, and personality intact.
- Retain rhetorical devices used intentionally: repetition for emphasis, direct audience address, rhetorical questions, and signature phrases.
- Do not add ideas, arguments, or examples that weren't in the original.
- When smoothing a rough transition, use the speaker's vocabulary, not your own.

### Improve readability

- Remove filler words ("um", "uh", "like", "you know"), false starts, repeated phrases, and verbal stumbles that don't add meaning.
- Smooth transitions between ideas where the spoken version was choppy, but only to the degree needed — don't over-polish.
- Break text into logical paragraphs at natural thought boundaries.
- Add section headers (`## Heading`) where the speaker shifts to a new topic or segment. Headers should reflect what the speaker actually talked about, not generic labels.
- Use **bold** sparingly to highlight the speaker's strongest, most quotable statements — the lines that landed with emphasis when spoken. Don't bold every other sentence.
- Format any lists the speaker rattled off into numbered or bulleted lists for clarity.
- Use em dashes and line breaks to mirror the speaker's natural pauses and cadence.

### Use British English throughout

Always output in British English, regardless of whether the source transcript uses American English.

- **Spelling**: Use British spellings throughout. Common conversions: *-ize* → *-ise* (realise, organise, recognise), *-or* → *-our* (colour, favour, behaviour), *-er* → *-re* (centre, theatre, fibre), *-ense* → *-ence* (defence, licence), *-og* → *-ogue* (catalogue, dialogue), *program* → *programme* (except in computing contexts), *check* → *cheque* (financial), *fulfill* → *fulfil*, *skillful* → *skilful*, *traveling* → *travelling*, *canceled* → *cancelled*.
- **Vocabulary**: Convert common Americanisms where a clear British equivalent exists. For example: *gotten* → *got*, *math* → *maths*, *vacation* → *holiday*, *apartment* → *flat* (only if clearly residential), *truck* → *lorry* (only when clearly a large goods vehicle), *elevator* → *lift*. Use judgement — if the American term is the speaker's natural voice or is an industry term (e.g., "math" in an academic context), prefer preserving voice over converting.
- **Punctuation**: Place punctuation outside quotation marks where British convention applies (e.g., He said "hello". not He said "hello.")
- **Dates and units**: Format dates as day-month-year where context allows. Leave units as spoken unless converting is clearly appropriate.
- **Preserve speaker's voice**: If the speaker is clearly American and uses American idioms and cultural references, do not alter idioms, slang, or cultural references — only apply spelling and vocabulary changes. The goal is a British-English document, not a British speaker.

### Do not

- Change the speaker's opinions, conclusions, or recommendations.
- Add commentary, disclaimers, or editorial notes.
- Over-format with excessive headers, bullets, or bold. Keep it clean.
- Remove promotional sections or calls-to-action at the end — clean them up like the rest of the transcript.
- Strip out personality, humor, or informal language that makes the speaker sound like themselves.

## Output format

Produce a single Markdown file with:

- A `# Title` at the top derived from the main topic of the talk
- `## Section` headers at major topic shifts
- Clean paragraphs, lists, and emphasis as described above
- No front matter, metadata, or editorial notes

Save the output as a `.md` file to `/mnt/user-data/outputs/` with a kebab-case filename derived from the title (e.g., `why-great-products-need-great-stories.md`).

## Handling different transcript formats

- **Plain text dump**: The most common case. Just a wall of text with no speaker labels or timestamps.
- **Timestamped transcripts** (e.g., from YouTube or .srt/.vtt files): Strip the timestamps. They're noise in the final output.
- **Multi-speaker transcripts**: Preserve speaker labels (e.g., "**Host:**", "**Guest:**") and format as a clean dialogue. Each speaker change gets a new paragraph.
- **Partial transcripts or excerpts**: Refine what's there. Don't try to fill in gaps.

## Quality check before delivering

Before saving the final file, scan your output for:

1. Any remaining filler words or verbal stumbles you missed
2. Overly long paragraphs that should be broken up
3. Sections that lost the speaker's voice and sound too "written"
4. Headers that are too generic (e.g., "Introduction" when something more specific fits)
5. Bold text that's overused or applied to unremarkable statements
6. Any American spellings or vocabulary that slipped through (e.g., *-ize*, *-or* endings, *gotten*, *math*, *vacation*)
