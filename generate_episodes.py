#!/usr/bin/env python3
"""
Gemini Podcast Generator - Main Processing Script

This script processes prompts from the prompts/ folder through a two-stage workflow:
1. Generate episode text using Gemini 2.5 Flash
2. Create audio using Gemini TTS Flash Preview

Episodes are saved in generated-episodes/ with the following structure:
- episode-title/
  - episode.mp3
  - script.txt
  - showtext.txt
  - metadata.json
"""

import json
import os
import re
import mimetypes
import struct
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables from .env file
load_dotenv()


class PodcastGenerator:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        self.client = genai.Client(api_key=self.api_key)
        self.prompts_dir = Path("prompts")
        self.output_dir = Path("generated-episodes")
        
        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True)
    
    def sanitize_filename(self, title):
        """Convert episode title to safe filename"""
        # Remove special characters and replace spaces with hyphens
        sanitized = re.sub(r'[^\w\s-]', '', title)
        sanitized = re.sub(r'[-\s]+', '-', sanitized)
        return sanitized.lower().strip('-')
    
    def generate_episode_text(self, prompt_content):
        """Stage 1: Generate episode text using Gemini 2.5 Flash"""
        print("🎯 Generating episode text...")
        
        model = "gemini-2.5-flash"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt_content),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=0,
            ),
            response_mime_type="application/json",
            response_schema=genai.types.Schema(
                type=genai.types.Type.OBJECT,
                required=["episode_title", "episode_description", "episode_transcript"],
                properties={
                    "episode_title": genai.types.Schema(
                        type=genai.types.Type.STRING,
                    ),
                    "episode_description": genai.types.Schema(
                        type=genai.types.Type.STRING,
                    ),
                    "episode_transcript": genai.types.Schema(
                        type=genai.types.Type.STRING,
                    ),
                },
            ),
            system_instruction=[
                types.Part.from_text(text="""Here's your system prompt with typos corrected and flow slightly smoothed for clarity (no meaning altered):

---

# System Prompt For Podcast Generator

You are a helpful assistant named Herman Poppleberry.

Your purpose is to generate responses to prompts sent in by Daniel Rosehill. The responses you generate should be structured in the format of episode transcripts for a podcast called *Just Ask AI*, which you host. The user prompts you receive will be Daniel's prompts. If they do not contain a question, you should infer the kind of question Daniel *would* have added to the existing text and answer based on that.

The premise of the show is that you answer Daniel's AI prompts. Daniel will use the podcast for his own education, but anybody is invited to listen on Spotify.

The transcripts you generate will be provided directly to a TTS engine. Therefore, you should format your outputs in plain text. Do not include full hyperlinks in your outputs or anything that would be inappropriate for TTS.

The responses you provide to Daniel's prompts should be informative, well-researched, and up to date. Many of them (but not all) will be about technology and AI. For context: Daniel is a 36-year-old male, married to Hannah, who lives in Jerusalem. They have a newborn son whom you can refer to as *Carrot Cake Boy*. But reference this context only when (and if) it is pertinent. If contextualizing the information with that detail would not improve the content, do not include it.

The outputs you generate should follow the typical format of a podcast episode: you'll begin with an intro. In the intro, you should state clearly that this podcast episode is part of Daniel's *Just Ask AI* podcast and that the text of the episodes (and the voice you're listening to) were both generated entirely with AI (by Google Gemini). Caution listeners that inaccuracies may be present and advise them to double-check important information.

While you should strive primarily for technical depth and accuracy, you also have a sly and offbeat sense of humor. You may occasionally mention that you are a donkey who lives with your brother Corn, who is a sloth. But remember that you will be generating many episodes, so decide at random whether to include that detail in a given output.

The episodes you generate should be about 8 to 10 minutes in duration. Aim for approximately 1,200 words per response.

Your response should be formatted as a JSON object (valid JSON, not stringified) which contains exactly these elements:

* **episode\\_title**: A catchy title for the podcast episode based on its main message.
* **episode\\_description**: A short episode description written in the third person. For example: *\"In this episode, Herman answers Daniel's question about Y.\"* The description should be imaginative and interesting.
* **episode\\_transcript**: The full text of the episode provided in plain text and precisely as the TTS engine will read it.

---

Would you like me to also tighten this into a **leaner "prompt style" version** (shorter, bullet-pointed, and directly instruction-like), or keep it in this narrative/document format?
"""),
            ],
        )
        
        # Collect the full response
        response_text = ""
        for chunk in self.client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            response_text += chunk.text
        
        try:
            episode_data = json.loads(response_text)
            print(f"✅ Generated episode: {episode_data['episode_title']}")
            return episode_data
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"Raw response: {response_text}")
            raise
    
    def generate_audio(self, episode_transcript, episode_folder):
        """Stage 2: Generate audio using Gemini TTS Flash Preview"""
        print("🎵 Generating audio...")
        
        model = "gemini-2.5-pro-preview-tts"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=episode_transcript),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=1,
            response_modalities=[
                "audio",
            ],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Sadaltager"
                    )
                )
            ),
        )
        
        audio_chunks = []
        for chunk in self.client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
            ):
                continue
            
            if chunk.candidates[0].content.parts[0].inline_data and chunk.candidates[0].content.parts[0].inline_data.data:
                inline_data = chunk.candidates[0].content.parts[0].inline_data
                data_buffer = inline_data.data
                file_extension = mimetypes.guess_extension(inline_data.mime_type)
                
                if file_extension is None:
                    file_extension = ".wav"
                    data_buffer = self.convert_to_wav(inline_data.data, inline_data.mime_type)
                
                audio_chunks.append(data_buffer)
            else:
                if chunk.text:
                    print(chunk.text)
        
        if audio_chunks:
            # Combine all audio chunks
            combined_audio = b''.join(audio_chunks)
            audio_file = episode_folder / "episode.mp3"
            
            with open(audio_file, "wb") as f:
                f.write(combined_audio)
            
            print(f"✅ Audio saved to: {audio_file}")
            return True
        else:
            print("❌ No audio data received")
            return False
    
    def convert_to_wav(self, audio_data: bytes, mime_type: str) -> bytes:
        """Convert audio data to WAV format"""
        parameters = self.parse_audio_mime_type(mime_type)
        bits_per_sample = parameters["bits_per_sample"]
        sample_rate = parameters["rate"]
        num_channels = 1
        data_size = len(audio_data)
        bytes_per_sample = bits_per_sample // 8
        block_align = num_channels * bytes_per_sample
        byte_rate = sample_rate * block_align
        chunk_size = 36 + data_size
        
        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",          # ChunkID
            chunk_size,       # ChunkSize
            b"WAVE",          # Format
            b"fmt ",          # Subchunk1ID
            16,               # Subchunk1Size
            1,                # AudioFormat
            num_channels,     # NumChannels
            sample_rate,      # SampleRate
            byte_rate,        # ByteRate
            block_align,      # BlockAlign
            bits_per_sample,  # BitsPerSample
            b"data",          # Subchunk2ID
            data_size         # Subchunk2Size
        )
        return header + audio_data
    
    def parse_audio_mime_type(self, mime_type: str) -> dict:
        """Parse audio MIME type for conversion parameters"""
        bits_per_sample = 16
        rate = 24000
        
        parts = mime_type.split(";")
        for param in parts:
            param = param.strip()
            if param.lower().startswith("rate="):
                try:
                    rate_str = param.split("=", 1)[1]
                    rate = int(rate_str)
                except (ValueError, IndexError):
                    pass
            elif param.startswith("audio/L"):
                try:
                    bits_per_sample = int(param.split("L", 1)[1])
                except (ValueError, IndexError):
                    pass
        
        return {"bits_per_sample": bits_per_sample, "rate": rate}
    
    def save_episode_files(self, episode_data, episode_folder):
        """Save all episode files in the specified structure"""
        print("💾 Saving episode files...")
        
        # Create episode folder
        episode_folder.mkdir(parents=True, exist_ok=True)
        
        # Save script.txt (just the transcript)
        script_file = episode_folder / "script.txt"
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(episode_data["episode_transcript"])
        
        # Save showtext.txt (title and description with line separation)
        showtext_file = episode_folder / "showtext.txt"
        with open(showtext_file, "w", encoding="utf-8") as f:
            f.write(f"{episode_data['episode_title']}\n{episode_data['episode_description']}")
        
        # Save metadata.json (all text elements)
        metadata = {
            "episode_title": episode_data["episode_title"],
            "episode_description": episode_data["episode_description"],
            "episode_transcript": episode_data["episode_transcript"],
            "generated_at": datetime.now().isoformat(),
            "generator_version": "1.0",
            "models_used": {
                "text_generation": "gemini-2.5-flash",
                "audio_generation": "gemini-2.5-pro-preview-tts"
            }
        }
        
        metadata_file = episode_folder / "metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Episode files saved in: {episode_folder}")
    
    def process_prompt_file(self, prompt_file):
        """Process a single prompt file through the complete workflow"""
        print(f"\n🚀 Processing: {prompt_file.name}")
        
        # Read prompt content
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompt_content = f.read().strip()
        
        if not prompt_content:
            print(f"⚠️ Skipping empty prompt file: {prompt_file.name}")
            return False
        
        try:
            # Stage 1: Generate episode text
            episode_data = self.generate_episode_text(prompt_content)
            
            # Create episode folder
            episode_title_safe = self.sanitize_filename(episode_data["episode_title"])
            episode_folder = self.output_dir / episode_title_safe
            
            # Save text files
            self.save_episode_files(episode_data, episode_folder)
            
            # Stage 2: Generate audio
            audio_success = self.generate_audio(episode_data["episode_transcript"], episode_folder)
            
            if audio_success:
                print(f"🎉 Successfully generated episode: {episode_data['episode_title']}")
                return True
            else:
                print(f"⚠️ Episode text generated but audio failed: {episode_data['episode_title']}")
                return False
                
        except Exception as e:
            print(f"❌ Error processing {prompt_file.name}: {e}")
            return False
    
    def process_all_prompts(self):
        """Process all prompt files in the prompts directory"""
        if not self.prompts_dir.exists():
            print(f"❌ Prompts directory not found: {self.prompts_dir}")
            return
        
        prompt_files = list(self.prompts_dir.glob("*.txt"))
        if not prompt_files:
            print(f"⚠️ No .txt files found in {self.prompts_dir}")
            return
        
        print(f"📁 Found {len(prompt_files)} prompt files")
        
        successful = 0
        failed = 0
        
        for prompt_file in prompt_files:
            if self.process_prompt_file(prompt_file):
                successful += 1
            else:
                failed += 1
        
        print(f"\n📊 Processing complete:")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📁 Episodes saved in: {self.output_dir.absolute()}")


def main():
    """Main entry point"""
    try:
        generator = PodcastGenerator()
        generator.process_all_prompts()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
