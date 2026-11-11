# Saved projects, media and conservative editing

`.als` is gzip-compressed XML, an undocumented application format. Preserve a byte-for-byte original before any offline edit. Compare disk state with the open set; a clean disk hash says nothing about unsaved live edits.

## Available commands

- `als-audit SET --out REPORT`: schema summary, scene/slot consistency, chronological events, target IDs, envelope references, media paths, clips/devices/routing summary.
- `als-revise SOURCE DESTINATION --plan PLAN`: new output only, expected source SHA-256, limited `set_clip_gain_db`, `move_audio_clip`, `set_track_active` operations. No cloning, device authoring, automation editing or invented IDs.
- `als-collect SOURCE NEW_DIRECTORY`: copy referenced audio using content-based names, verify hashes, rewrite local paths. It covers `SampleRef` audio only and reports `native_collect_all_performed=false`.

Example **plan schema**, replace every identity with observed values:

```json
{
  "source_sha256": "SHA256_FROM_AUDIT",
  "operations": [
    {"action": "set_clip_gain_db", "track_id": "5", "expected_track_name": "LEAD", "clip_id": "12", "gain_db": -1.0},
    {"action": "set_track_active", "track_id": "8", "expected_track_name": "FX", "active": true}
  ]
}
```

## Schema hazards that need independent checks

Scene count must agree with ordinary Audio/MIDI track clip-slot lists. Native Group/Return tracks may have empty placeholder lists; do not pad those blindly. Target/pointee IDs and references are not generic XML IDs; different objects have different scopes. Never “deduplicate every Id” globally. `NextPointeeId` must exceed allocated target identifiers. Audio/MIDI events must be sorted by time: Live can silently omit out-of-order events rather than refusing the whole file.

With Warp off, source/loop offsets use seconds while arrangement positions use beats. With Warp on, use the actual piecewise WarpMarkers. `beat_to_source_seconds` rejects unwarped clips and extrapolation; it does not implicitly handle looping, reverse, clip start offsets or tempo automation. Resolve those explicitly before source slicing.

Cloning devices/tracks can duplicate automation targets, inherit mute, add invalid slots or break routing. Obtain a native template, preserve schema and identifiers, and validate loaded state. The toolkit deliberately does not offer a generic clone function that promises safety.

Keep fades around real edit discontinuities without cutting consonants. Source-time edits must preserve the dry file and original complete take. Clip gain changes do not replace phrase-level automation when a word spans several clips or the desired shape is continuous.

## Native acceptance

After opening the candidate in Live, compare **count and positions** of clips per track against the expected saved version. Check devices, take lanes, track activators, missing media and routing. Re-save natively if needed, then audit again. A static pass never substitutes for this step.

For delivery use native Collect All and Save when available and transfer the whole project folder. Plugin samples, packs and external libraries are outside the collector's scope. Keep an archive of the old project; do not erase it merely because a new version loads.
