# Free plugin palette and agent support

Checked 2026-11-11. Downloads were obtained from the developers' sites or their linked GitHub releases. These are free editions/open-source releases, not trials. Binaries, factory presets, private paths and installer backups are not distributed here.

| Product/version | Official source | License category |
|---|---|---|
| TDR Nova 2.2.3 | [Tokyo Dawn](https://www.tokyodawn.net/tdr-nova/) | Proprietary freeware; GE is a separate paid edition |
| TDR Kotelnikov 1.6.7 | [Tokyo Dawn](https://www.tokyodawn.net/tdr-kotelnikov/) | Proprietary freeware; GE is a separate paid edition |
| Dragonfly Reverb suite 3.2.10 | [Official release](https://github.com/michaelwillis/dragonfly-reverb/releases/tag/3.2.10) | Open source, GPL-3.0 |
| Chow Tape Model 2.11.4 | [Official release](https://github.com/jatinchowdhury18/AnalogTapeModel/releases/tag/v2.11.4) | Open source, GPL-3.0 |
| ChowMatrix 1.3.0 | [Official release](https://github.com/Chowdhury-DSP/ChowMatrix/releases/tag/v1.3.0) | Open source, BSD-3-Clause |
| Surge XT and Surge XT Effects 1.3.4 | [Official release](https://github.com/surge-synthesizer/releases-xt/releases/tag/1.3.4) | Open source, GPL-3.0; retain bundled asset notices |
| Voxengo SPAN 3.24 | [Voxengo](https://www.voxengo.com/product/span/) | Proprietary freeware; SPAN Plus is a separate paid product |
| Pedalboard 0.9.26, optional agent host | [Spotify documentation](https://spotify.github.io/pedalboard/reference/pedalboard.html) | GPL-3.0; installed separately as an optional dependency |

The host is an additional way to inspect a plugin, not a replacement for Live. `pip install -e ".[plugins]"` enables `ableton-agent plugin-probe PATH --out REPORT`. The command launches a separate process, fingerprints installed files, lists host-visible parameters and processes a one-second synthetic signal. It does not play sound, capture a microphone, change audio drivers, edit the Live set, or import a Live device's current state.

## Installation boundaries

The local installation uses a dedicated user VST3 folder. Existing system plugins are preserved. Select this folder as Live's VST3 Custom Folder and keep the System Folder enabled if it contains existing devices. Use only the 64-bit VST3 variants; do not mix duplicate VST2/VST3 versions in the same set. Preserve Surge's portable factory data layout/search path and verify presets after loading.

The optional `-_PluginAutoPopulateThreshold=128` line follows [Ableton's Options.txt documentation](https://help.ableton.com/hc/en-us/articles/6003224107292-Options-txt-file). It is experimental and requires restart. It exposes at most 128 parameters; advanced synths and dynamic effect graphs need selected controls/macros and fresh mappings. [Ableton's Windows plugin guide](https://help.ableton.com/hc/en-us/articles/209071729-Using-VST-plug-ins-on-Windows) explains folder selection; [Configure/defaults guidance](https://help.ableton.com/hc/en-us/articles/209073089-Saving-plug-in-parameter-configurations) explains native parameter exposure.

## Verification scope

All eleven VST3 entries loaded and produced finite stereo output in Pedalboard 0.9.26 at 48 kHz, with factory/default state; the instrument received a generated MIDI note. This is a small functional smoke test. It does not prove musical quality, long-tail behavior, all presets, tempo sync, CPU stability or Live compatibility. Native Live plugin activation/loading remained pending after Computer Use was stopped. The Ableton MCP connection itself had already passed its separate native check.

The initial offline scan rejected Windows directory bundles; resolving their contained x64 module fixed all eight bundle scans. Both directory and single-file VST3 layouts are now handled. Parameter counts observed by the offline host are recorded in the [skill reference](../skills/ableton-mix/references/plugins.md). In particular, SPAN's three host parameters do not expose its spectrum or loudness measurements as machine-readable data.
