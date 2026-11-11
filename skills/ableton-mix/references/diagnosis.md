# Diagnostic triage and perceptual comparison

Adapted from the MIT-licensed `mixer-doctor` workflow in glincker/ableton-skills and the MIT-licensed `mix-and-master` workflow in CanArslanDev/ableton-live-mcp. License notices travel with this skill in `references/licenses/`. The diagnostic criteria below are revised: no preset frequency range or absent plugin establishes a fault.

## Symptom → evidence → smallest useful experiment

| User description | Inspect before deciding | A reversible experiment if supported |
|---|---|---|
| Muddy / boomy | Vocal/beat/return contributions to low bands, note lengths, resonances and actual listening | Phrase-specific low-frequency cleanup on the responsible layer; preserve the bass's intended impact |
| Harsh / cutting | Particular consonants, stable vowels, upper-mid transients, saturation and wet sibilance | Dynamic attenuation or a small local ride; compare diction at matched level |
| Thin | Low-cut settings, phase cancellation, pitch/formant changes, source mic tone | Restore body or remove a cancellation-causing layer; do not boost blindly |
| Voice disappears | Mutes/routing first, then relative level and time/band competition | Recover the missing phrase or temporarily reduce a competing layer |
| Flat / unconfident | Performance timing, excessive dynamics control, timbre contrast, lack of intentional phrasing | Adjust stressed syllables, phrase gain or a selected support layer before adding another compressor |
| FX invisible | Native clip presence, track/parent activity, send routing, actual wet level | Restore the path, then match a known approved effect in context |
| Too wet / unclear | Tail timing versus next lyric, wet spectrum, predelay, ducking recovery | Shape wet signal around articulation while retaining the requested depth |
| No groove | Placement of stress, beat interruptions, over-quantization, excessive continuous glitching | Restore a readable pulse and test one timing/motion variation |
| Doesn't connect between sections | Density, level/timbre discontinuity, missing pickup/tail | Reuse a short familiar gesture or smooth a section ride; avoid an unrelated loud sweep |

The band names are search hints, not a diagnosis. `masking-proxy` requires aligned stems and reports overlap candidates, not intelligibility. An absent high-pass, sidechain or bus compressor is not itself a problem.

## Reference loop

Choose a representative section and preserve the approved state. State the symptom and a falsifiable desired change. Measure the relevant signal; then apply the smallest authorized batch that can be compared coherently. Re-measure only the affected evidence and protected neighbors. A full-track check belongs near delivery or after a change affecting the full track.

Use `ab-pack` for short aligned excerpts when user listening is available. Compare at fixed playback level before opening its identity key. Rate diction, groove, harshness, space, signature effects and transition continuity separately. One overall “better” score hides tradeoffs. The copies are loudness matched but not automatically time aligned; this is not a formal scientific listening test.

## Psychology as a design hypothesis

Research on syncopation and musical expectations suggests a useful balance of familiar structure and selective surprise. Apply that as a hypothesis: repeat an approved high-register vocal signature, vary its context, leave some rhythmic gaps, and make the final return meaningful. Do not turn “more FX” into continuous stimulation with no contrast.

Louder audition often changes preference. Match levels before increasing compression or brightness. Short listening passes and a later fresh comparison can reveal fatigue; no numerical metric guarantees that the user's audience will prefer the result.
