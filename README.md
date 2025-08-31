# Gemini Podcast Generator: Idea & Implementation

![alt text](banner.webp)

This AI agent (WIP) is an offshoot of an N8N workflow that I've been using for the past few weeks to generate [a podcast](https://open.spotify.com/show/4RlBls1ZQxs4ciREOR8vpU?si=34F4kvIzRVCHo5ehvNYI2w) for my own listening. It has been an enjoyable experiment!

![alt text](graphics/workflow-1.png)

## Table of Contents

- [Sample Episode](#sample-episode)
- [Personal AI-Generated Podcast – The Idea / Motivation](#personal-ai-generated-podcast--the-idea--motivation)
- [Key Elements: Search and a Pleasant Voice!](#key-elements-search-and-a-pleasant-voice)
- [Deployment Workflows](#deployment-workflows)
- [Getting Started](#getting-started)

## Use Case & AI Ethics Note

I love sending quite specific prompts to AI and using its responses to learn about things (see: `example-prompt`). My personal use-case is, therefore, probably best described as "self-directed learning."

I love using AI for purposes like this and am sharing it for others who wish to create similar implementations. This was never built with the intention of creating a commercial podcast.

There is an argument in favor of sharing AI-produced content like this with the internet-at-large. But I believe it is only ethical to do so under limited circumstances: that content is offered freely; it is made very clear to listeners that it was generated with AI; no terms of service are violated in the process. 

For those who are similarly interested in using this pattern for learning, here are some variations on the workflow that I have validated and which are appropriate:

- Save generated episodes to Google Drive and use a podcast app that pulls directly from it to listen 
- Self-host a podcast server 
- Free / publicly available podcast on third party hosting 

The "frontend" to initiate this workflow could be a webhook payload or a Google Form collector or a web UI. This worked well under all these models in N8N with the exception that the structured output parsing (as usual) was hit-and-miss which is why I created this implementation.

## Sample Episode

**"The Gatekeepers of Your Digital Castle: How Firewalls Filter the Web"**

This sample episode demonstrates the full capabilities of the Gemini Podcast Generator. Herman Poppleberry explains how firewalls manage network security while allowing legitimate internet traffic.

| Element | Link | Details |
|---------|------|---------|
| **🎧 Audio Episode** | [episode.mp3](generated-episodes/the-gatekeepers-of-your-digital-castle-how-firewalls-filter-the-web/episode.mp3) | **Duration:** 7m 51s |
| **📝 Episode Script** | [script.txt](generated-episodes/the-gatekeepers-of-your-digital-castle-how-firewalls-filter-the-web/script.txt) | Full transcript with AI-generated content |
| **📋 Episode Metadata** | [metadata.json](generated-episodes/the-gatekeepers-of-your-digital-castle-how-firewalls-filter-the-web/metadata.json) | Generation details, models used, timestamps |
| **💭 Original Prompt** | [prompt.txt](generated-episodes/the-gatekeepers-of-your-digital-castle-how-firewalls-filter-the-web/prompt.txt) | User's original question about firewalls |

**Generation Details:**
- **Text Model:** gemini-2.5-flash
- **Audio Model:** gemini-2.5-pro-preview-tts  
- **Generated:** 2025-08-31T15:15:27
- **Generation Time:** ~2-3 minutes (estimated)

## Personal AI-Generated Podcast – The Idea / Motivation

About a year ago, I discovered the wonderful world of speech-to-text (STT) via Whisper.

Since then, I’ve been using STT to capture most of my AI prompts. (This was before the ChatGPT–Whisper integration worked reliably. Even now that it does, capturing prompts separately has the added benefit of building up your own prompt library over time.)

A workflow I’ve naturally fallen into as a result of adopting this process looks something like this:

* When I’m feeling curious, I record a few prompts — often in the middle of the workday when I don’t have time to give the generations proper attention.
* Later, when I want something interesting to listen to (at the gym, on public transit), I can play them back.

I’ve long advocated for saving AI outputs. Even if AI-generated content is, to some degree, unreliable and ephemeral, outputs (like prompts) may contain contextual data about yourself that is useful — if not now, then in a few years’ time. If outputs *are* useful, you’ll want to store them somewhere other than a vendor’s chat UI. Today, however, solutions for that are thin.

Through N8N, I began building workflows that satisfied my need for AI output storage: prompts go to an agent, outputs and prompts are saved in a database, and the content is written to a wiki. The podcast idea was a natural extension of that: why not run the outputs through a TTS API so that you can not only *read* them, but also *listen* to them if you feel inclined?

## Key Elements: Search and a Pleasant Voice!

I validated the workflow using Qwen, OpenAI, and Lemonfox. But a few things quickly became apparent:

* Unless you want to build a lot of tooling, you need an LLM with a fairly recent knowledge cutoff or strong search capabilities.
* You need a TTS voice that isn’t painful to listen to — ideally, one that’s actually enjoyable.
* If, like me, you may send dozens of prompts to AI on a busy day, you also need a model that can generate completions without bankrupting you.

11Labs has the best voices but is prohibitively expensive. Qwen lagged on knowledge freshness. OpenAI has affordable endpoints (like GPT-4o-mini and GPT-3.5 variants) but the voices aren’t great.

Turning to Google, however, I found an option that ticked all the boxes while keeping the workflow inside one ecosystem:

* Gemini models are relatively up to date, affordable, and benefit from Google’s strategic advantage as the western world’s long-dominant search engine.
* Gemini recently rolled out a very interesting [TTS layer](https://ai.google.dev/gemini-api/docs/speech-generation) that goes beyond “classic” TTS: you can prompt not only the text to be read but also stylistic instructions.

This engineering makes Gemini quite an ideal platform for podcast generation. Instead of forcing lengthy instructions into the LLM (for example: *"the text you generate must be readable by a TTS tool; therefore, don't read out full hyperlinks"*), you can move these rules to the TTS stage — or use both, with the latter functioning as a safety mechanism.

## Deployment Workflows

### Recommended Deployment Options

#### 1. Google Drive Integration
Perfect for personal use and easy sharing:

```bash
# Install Google Drive CLI (gdrive)
# Upload generated episodes to Drive
gdrive upload generated-episodes/*/episode.mp3
gdrive upload generated-episodes/*/metadata.json
gdrive upload generated-episodes/*/script.txt
```

**Benefits:**
- Automatic syncing across devices
- Easy sharing with specific people
- Built-in version history
- Free 15GB storage

#### 2. AWS S3 Bucket Storage
Ideal for scalable, production deployments:

```bash
# Install AWS CLI and configure credentials
aws s3 sync generated-episodes/ s3://your-podcast-bucket/episodes/
aws s3 cp generated-episodes/*/episode.mp3 s3://your-podcast-bucket/audio/ --recursive
```

**Benefits:**
- Highly scalable and reliable
- CDN integration with CloudFront
- Programmatic access via API
- Cost-effective for large volumes

#### 3. Hybrid Approach
Combine both for maximum flexibility:

1. **Local Generation** → Store episodes locally first
2. **Google Drive** → Personal backup and mobile access  
3. **S3** → Public distribution and podcast RSS feeds
4. **Metadata Tracking** → Keep JSON files in both locations

### Automation Scripts

The repository includes helper scripts for common deployment scenarios:

- `scripts/deploy-to-drive.py` - Automated Google Drive uploads
- `scripts/deploy-to-s3.py` - AWS S3 batch uploads with metadata
- `scripts/generate-rss.py` - Create podcast RSS feeds from metadata

## Getting Started

1. **Clone the repository**
2. **Install dependencies:** `pip install -r requirements.txt`
3. **Configure API keys** in `.env` (see `.env.example`)
4. **Run episode generation:** `python generate_episodes.py`
5. **Deploy using your preferred workflow** (see above)

For detailed setup instructions, see the [workflow documentation](workflow.md).