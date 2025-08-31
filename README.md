# Gemini Podcast Generator: Idea & Implementation

![alt text](banner.webp)

This AI agent (WIP) is an offshoot of an N8N workflow that I’ve been using for the past few weeks to generate [a podcast](https://open.spotify.com/show/4RlBls1ZQxs4ciREOR8vpU?si=34F4kvIzRVCHo5ehvNYI2w) for my own listening. It has been an enjoyable experiment!

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

This engineering makes Gemini quite an ideal platform for podcast generation. Instead of forcing lengthy instructions into the LLM (for example: *“the text you generate must be readable by a TTS tool; therefore, don’t read out full hyperlinks”*), you can move these rules to the TTS stage — or use both, with the latter functioning as a safety mechanism.
 