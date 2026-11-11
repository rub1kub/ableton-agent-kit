# Evidence: audio, transport and uncertainty

Separate four things: source-file analysis, rendered Live audio, subjective listening through an audio-capable tool, and physical speaker/headphone checks. Report which actually happened. ASR and meters alone are not listening.

## Decode and inspect

`audio-analyze` preserves source rate and amplitude. It reports integrated LUFS, sample peak, a 4× oversampled peak **estimate**, crest, stereo correlation, mono RMS change, gap candidates, energy transients and optional section measurements. Reports sanitize silence/non-finite statistics to JSON null where appropriate. No target LUFS is an automatic artistic requirement.

`audio-plot` creates a waveform, spectrogram and left/right energy overview. These reveal events and spectral changes, not lyrics, chords or emotional intent. A quiet interval can be a deliberate beat interruption. Use the original beat as a reference before attributing mono cancellation or tonal changes to the vocal mix.

The beat-grid diagnostic assumes the supplied BPM; it does not establish it. Check corresponding attacks near the beginning, middle and end. A quarter is `60/BPM`, an eighth `30/BPM`, dotted eighth `45/BPM`, sixteenth `15/BPM`. Swung and syncopated attacks need musical interpretation.

## Pitch and words

`key` ranks chroma/profile hypotheses; neighboring sections may have different bass notes without a key change. Inspect the melody and harmonic phrase. `pitch` uses pYIN on a monophonic excerpt up to 60 seconds and retains high-confidence voiced frames. It can still fail on harmonies, distortion, breath, octave shifts or rap. Confidence thresholds are not proof of accuracy.

`transcribe` requires a local faster-whisper model. Supplied lyrics are text authority. ASR is a tentative alignment aid, especially unreliable for exaggerated tuning and Russian slang. Inspect word boundaries in the waveform and rendered phrase; never edit based on one low-confidence token.

## Capture actual processing

On supported Windows, passive `capture --pid ...` records the process tree at 44.1 kHz PCM16 and logs packet discontinuities. This is not the native export resolution. It does not move transport or verify the start position. Silence may mean an unsupported audio path (including some ASIO routes), not a silent project.

For an authorized automated playback test:

1. Verify recording is off and preserve current selection/transport settings.
2. Start transport, allow it to settle, then seek and read back while playing. Some installations start from the Arrangement insertion cursor rather than the previously assigned song time.
3. Record timestamped transport samples around/during the capture. `transport_check` rejects stops, jumps and implausible wall-time differences; use a tolerance justified by measured request latency.
4. Align against a known source section. `audio.align` gives a global delay and correlation, but repeated phrases can create false matches. Verify a second independent region and check drift. Do not hand-place capture offsets from intuition.
5. Stop transport and restore temporary state in `finally`. If the user touches transport, invalidate the measurement and coordinate a fresh pass instead of fighting their controls.

A brief passive capture can validate the backend. It does not establish that every section played, the mix is correct or the user has listened.

## Compare changes

Use matching excerpts and equal perceived loudness. `audio-compare` reports the candidate gain needed to match integrated LUFS; it does not apply gain, align files or decide which is better. For tiny effects, inspect isolated wet audio plus the full mix. Keep protected sections unchanged or quantify any unavoidable bus interaction.

Store hashes, parameters, timing uncertainty and report paths locally. Refresh analysis when the relevant files or routing change. Repeated full-track analyses without a changed question waste time and context.
