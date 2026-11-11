# Demonstrated failure patterns

| Symptom | Evidence to inspect | Useful next action |
|---|---|---|
| Sample Offline | SampleRef paths, existence, hash, original recording location | Relink exact files, collect into a new project, verify native reload |
| Slot count mismatch | Scene count versus each ClipSlotList | Restore a native-valid version; repair only with understood schema |
| Clip exists in XML but not Live | Ordered Events, loaded count/positions | Sort chronological events in a copy and reopen; do not trust XML count alone |
| New FX is completely inaudible | Track activator, parent, solo, sends, routing, device, meters | Restore the intended path before increasing gain |
| Group inspection throws Arm error | Upstream handler's unguarded `track.arm` access | Use extension snapshot/track queries with `can_be_armed` guard |
| Echo arrives after the next lyric | Source word bounds and actual gap | Move/shorten repeats, remove late answers or use simultaneous width |
| Echo overlaps verse but user likes it | User approval and actual diction | Preserve the overlap; adjust only a demonstrated competing detail |
| Word is half normal, half pitched | Pitch automation boundaries, duplicated clips, source context | Process/capture the complete approved word consistently |
| Shortened transition disappears | Wet layer's native activity and level in mix | Compare approved texture; shorten decay without unintentionally hiding onset |
| Reverb stops abruptly | Clip end, return automation, gate, duck release, feedback | Restore smooth decay; distinguish hold from repeated syllables |
| Verse feels louder/serious than hook | Beat level change and vocal timbre, not just peaks | Follow beat with phrase rides; preserve approved hook as reference |
| Stereo motion not heard | Rate, depth, actual layer level, channel envelopes | Make movement clear in context; do not equate faster with harsher |
| Playback test starts at wrong time | Insertion cursor, playing seek readback | Verify transport after starting; align recorded audio with source |
| Timeout during write | Journal + actual parameter readback | Outcome is uncertain; inspect before retrying |
| Captured silence | Correct PID, packet count, audio driver path | Use native export if process loopback cannot see the render path |
| Pitch detector returns absurd notes | Monophony, voiced confidence, distortion, octave ambiguity | Inspect stable vowels and source key; never tune blind from one frame |

Use these as diagnoses to test, not blanket assumptions. If the cause differs, follow the actual evidence. If accessibility inspection destabilizes a particular Live setup, stop using that method there and use supported APIs or screenshot-only interaction.
