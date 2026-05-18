# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Koro Kaiwa AI** is a conversational AI system designed for Japanese language learning and practice. The system enables users to have natural voice-based conversations in Japanese, with AI-powered transcription, response generation, and text-to-speech synthesis. The system also provides learning aids like Furigana (kanji reading guides), Romaji (Latin transliteration), and translations.

**License:** MIT (2026, Dinh Truong Phan)

## Architecture

The system follows a modular, component-based architecture with clear separation of concerns through abstract base classes and dependency injection.

### Core Data Flow (MVP - Phase 1)

```
Input (Voice) → ASR → Text A → LLM → Text B → TTS → Output (Voice)
                                        ↓
                                    NLP (Async)
                                  [Furigana, Romaji, Translation]
```

**Phase 1 (MVP):** Sequential pipeline with asynchronous NLP processing for learning aids.
**Phase 2 (Future):** End-to-end Speech-to-Speech model with pronunciation assessment and intelligent tutoring feedback.

### Component Architecture

The system is organized around four main abstract components, all defined in `src/core/interfaces.py`:

1. **BaseASR (Automatic Speech Recognition)**
   - Input: Audio bytes
   - Output: Transcribed text (Text A)
   - Converts user voice to Japanese text
   - Dummy implementation returns fixed Japanese strings

2. **BaseLLM (Large Language Model)**
   - Input: Conversation context (list of Message objects with history)
   - Output: Response text (Text B)
   - Maintains conversation context and generates contextually relevant responses
   - Dummy implementation returns context-aware Japanese responses

3. **BaseTTS (Text-to-Speech)**
   - Input: Text (Text B)
   - Output: Audio bytes
   - Converts AI response back to voice
   - Dummy implementation returns fake audio stream

4. **BaseNLP (Natural Language Processing - Auxiliary)**
   - Input: Text (Text B)
   - Output: NLPResult (furigana, romaji, translation)
   - Runs asynchronously to provide learning aids
   - Dummy implementation returns mock linguistic data

### Data Models

All data structures are in `src/core/schemas.py`:

- **Message:** Represents a single conversational turn (role: str, content: str)
- **NLPResult:** Contains learning aid data (furigana, romaji, translation)
- **Session:** Manages conversation state with session_id and history list, provides context management via `get_context()`

### Engine Orchestration

`src/engine.py` contains **KaiwaEngine**, which orchestrates the complete interaction flow:

1. Takes user audio and converts to text via ASR
2. Adds user text to session history
3. Generates AI response from context via LLM
4. Adds AI response to session history
5. Synthesizes response audio via TTS
6. Processes response for learning aids via NLP (currently synchronous in MVP)
7. Returns combined result (text_input, text_output, audio_output, nlp metadata)

### Current Implementation

The MVP uses dummy implementations in `src/components/dummies.py` to verify data flow without external dependencies. These are concrete implementations of the base classes that return fixed or context-aware mock data.

## Directory Structure

```
koro-kaiwa-ai/
├── main.py              # Entry point for MVP testing
├── src/
│   ├── engine.py        # KaiwaEngine orchestration
│   ├── core/
│   │   ├── interfaces.py  # Abstract base classes (BaseASR, BaseLLM, BaseTTS, BaseNLP)
│   │   └── schemas.py     # Data models (Message, NLPResult, Session)
│   └── components/
│       └── dummies.py     # Dummy implementations for testing
├── docs/
│   ├── architecture.md    # System architecture and data flow
│   ├── roadmap.md         # Development phases and timeline
│   ├── phase1/
│   │   └── implementation_guide.md  # Phase 1 technical specifications
│   └── phase2/
│       └── research_and_development.md  # Phase 2 advanced features
├── README.md            # Project overview (in Vietnamese)
├── LICENSE              # MIT License
└── .gitignore          # Standard Python gitignore

```

## Running and Testing

### Run the MVP

```bash
python main.py
```

This runs a single interaction cycle with dummy implementations to verify the data flow. Output includes:
- Transcribed user input (Text A)
- AI response (Text B)
- Learning aids (Furigana, Romaji, Translation)
- Mock audio output

### Testing Strategy

Currently, there are no automated tests. The MVP uses manual testing through `main.py`. For future testing:

- Use pytest for unit tests (conventional: `tests/` directory or `test_*.py` files)
- Test each component independently against its interface
- Mock external API calls (real ASR, LLM, TTS providers)
- Integration tests should verify the complete engine flow with different session histories

## Dependencies

The project currently has **no external dependencies beyond Python standard library**. The dummy implementations use only built-in types.

**Phase 1 will require:** (See `docs/phase1/implementation_guide.md`)
- ASR: OpenAI Whisper or Google Cloud Speech-to-Text
- LLM: OpenAI API, Google Gemini, or Anthropic Claude
- TTS: Voicevox or OpenAI TTS
- NLP/Translation: MeCab, Kuroshiro, pykakasi, or Google Translate API

## Key Design Patterns

1. **Abstract Base Classes:** All major components inherit from abstract interfaces to enable easy swapping of implementations (strategy pattern).

2. **Dependency Injection:** KaiwaEngine receives all components as constructor arguments, making it testable and flexible.

3. **Session-Based Context:** Conversation history is managed through Session objects, allowing multiple concurrent conversations and proper context management within LLM's token limits.

4. **Asynchronous Processing:** NLP (learning aids) runs separately from the main response flow to avoid blocking user experience (though currently synchronous in MVP).

5. **Modular Data Flow:** Clear separation between main pipeline (ASR → LLM → TTS) and auxiliary processing (NLP).

## Configuration and Language

- All user-facing text and docstrings are in **Vietnamese**
- Code structure and variable names follow English conventions
- The system is designed to work with both Japanese and Vietnamese input/output

## Development Notes

- The project is in **early MVP stage** - focus is on verifying data flow and architecture, not full feature implementation
- All current implementations are dummy/mock versions
- The architecture is designed to be production-ready once real component implementations are integrated
- Session management will need enhancement for production (currently in-memory only)
- Asynchronous NLP processing should use proper async/await patterns and background task queues in Phase 1

## Documentation

Primary architecture and design decisions are documented in `docs/`. Key files:
- `docs/architecture.md` - Main data flow and system design
- `docs/roadmap.md` - Development phases (MVP → Advanced AI features)
- `docs/phase1/implementation_guide.md` - Specific technologies and backend architecture recommendations
- `docs/phase2/research_and_development.md` - Advanced features like pronunciation assessment and S2S models
