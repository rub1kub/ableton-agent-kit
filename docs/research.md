# What was reused, what was rejected, and why

Research snapshot: 2026-11-11. Repository revisions are pinned below; forum statements are practice reports, not experimental proof. Technical behavior is checked against source/manuals. Listening research informs comparisons and arrangement hypotheses, not a promise of universal pleasure.

## Existing skills and MCP projects

| Source | Useful material adopted or adapted | Improvements in this kit |
|---|---|---|
| [glincker/ableton-skills, `347cd7d`](https://github.com/glincker/ableton-skills/tree/347cd7dc4c9b53a42fcc39b332b972c687cf9fdc) — MIT | Diagnostic triage from `mixer-doctor`; separate reference aspects; role-focused workflows | Frequency ranges become hypotheses, not diagnoses. No mandatory high-pass, no blanket normalized parameter values, no automatic -14 LUFS target, no approval loop after every authorized knob move |
| [CanArslanDev/ableton-live-mcp, `e65141b`](https://github.com/CanArslanDev/ableton-live-mcp/tree/e65141b411746841746b553e3e8dbd6ab44442e8) — MIT | Adapted section → snapshot → measure → change → compare workflow; distinction between meter inspection and rendered evidence | Explicit version gates, state restoration, uncertain key/peak estimates, protected creative choices, no claim that all streaming services use the same target |
| [wstierhout/ableton-live-mcp, `55abd3a`](https://github.com/wstierhout/ableton-live-mcp/tree/55abd3a38a74c39f6f2fc0d1d90107d06ec5f952) — MIT | Toolset filtering, typed operations, native read scheduling, state identity/diff concepts | Backend-neutral skill; additive legacy compatibility; actual file analysis and cheaper report access |
| [dreamrec/LivePilot](https://github.com/dreamrec/LivePilot) | Relevant mixing skill found during discovery | Not copied: GitHub license identification was `NOASSERTION`; license clarity is required before incorporating its code/text |
| [ahujasid/ableton-mcp](https://github.com/ahujasid/ableton-mcp) — MIT | Original lineage and baseline capabilities | Do not confuse original, modern forks and the local legacy variant |

Substantive adapted workflow material is attributed in [THIRD_PARTY.md](../THIRD_PARTY.md); original license notices are included in `LICENSES/`. We did not import whole skills as authoritative instructions. Their operational assumptions sometimes conflict with the actual device APIs and the user's established authorization.

## Perception and musical decisions

| Evidence | What it supports | Practical consequence and limit |
|---|---|---|
| [Croghan, Arehart & Kates 2012, JASA](https://pubmed.ncbi.nlm.nih.gov/22894236/) | Compression preference depends partly on loudness comparison; strongest compression harmed quality in the tested material | Make level-matched A/B copies before choosing “more powerful.” Does not establish one compression setting for rap |
| [Campbell et al. 2017, JAES](https://repository.uwl.ac.uk/id/eprint/3324/) | Preference depends on compression configuration, not merely whether compression is present | Compare track, bus and master changes separately; do not equate “more compression” with either good or bad |
| [Witek et al. 2014](https://ora.ox.ac.uk/objects/uuid%3A48a24a75-5f4f-44ce-ad7e-26a011dffc44) | In tested funk breaks, intermediate syncopation elicited greater movement/pleasure ratings | Preserve readable pulse and some space; avoid quantizing every articulation or filling every gap. A population result is not a recipe for an individual's song |
| [Cheung et al. 2019, Current Biology](https://www.sciencedirect.com/science/article/pii/S0960982219312588) | Harmonic pleasure varied with interacting uncertainty and surprise | A recurring vocal signature with selected variations is a reasonable creative hypothesis. The study does not prescribe FX counts or guarantee dopamine/virality |
| [Naturalistic-listening study, Frontiers 2023](https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2023.1209398/full) | Naturalistic listening links expectancy, liking and reward-related activity | Evaluate context and transitions, not only isolated sound effects; listener familiarity remains relevant |
| [AES loudness basics](https://aes.org/resources/audio-topics/loudness-project/loudness-basics/) | Loudness includes frequency, intensity and duration; normalization is distinct from internal dynamics | Preserve section contrast while matching comparison playback. Avoid peak normalization as a substitute for equal perceived loudness |
| [ITU-R BS.1116-3](https://www.itu.int/rec/R-REC-BS.1116-3-201502-I) | Controlled subjective comparison requires managed listening conditions | The kit's blinded A/B is a practical aid, not an ITU-compliant listening experiment |
| [AES masked-to-unmasked ratio study](https://aes.org/publications/elibrary/elibrary-page/?id=15811) | Masking assessment requires an auditory model and listening validation | Label our band-energy overlap as a proxy; never report it as measured intelligibility or an automatic EQ prescription |

## Forums and practitioner evidence

Read practice discussions about [ducking vocal FX on Allen & Heath](https://forums.allen-heath.com/t/ducking-vocal-effects-channels/13203), [H-Reverb ducking on Waves](https://forum.waves.com/t/h-reverb-ducking-question/682), and [sidechain behavior on Steinberg](https://forums.steinberg.net/t/cant-understand-what-side-chain-compression-does/115085). These corroborate a useful practical distinction: the wet effect can move around the dry vocal rather than requiring the whole voice to become quieter. Particular attack/release numbers are not universal and were not adopted as defaults.

The relevant routing mechanism is documented by [Ableton's audio-effect reference](https://www.ableton.com/en/live-manual/12/live-audio-effect-reference/) and illustrated by the processor manufacturer's [iZotope ducking guide](https://www.izotope.com/community/blog/what-is-audio-ducking). Forum claims are used to generate tests, not to override observed behavior.

## Implemented consequences

- `ab-pack`: randomized A/B identity with loudness matching and common headroom attenuation; original audio unchanged.
- `masking-proxy`: time/band competition candidates for aligned stems, explicitly not a perceptual threshold model.
- Content-addressed analysis cache includes file hash, options, analysis code hash and library versions.
- `backend-plan`: choose from observed tools rather than guessing capabilities from a brand name.
- The skill's diagnostic reference turns complaints into evidence questions and reversible moves; it avoids missing-plugin diagnoses.
- Progressive references, paginated queries and file-backed reports keep the agent focused on the current decision.

Success is assessed with the user: clearer words, stronger intended groove, coherent depth and memorable effects at an acceptable level. None of the cited research supports claiming an objectively perfect mix or guaranteed commercial success.
