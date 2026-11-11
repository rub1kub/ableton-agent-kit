# Third-party boundaries

The original code and documentation in this repository use the MIT license. No Ableton binaries, devices, presets, LiveMCP upstream server source, user recordings, ASR models or FFmpeg executables are redistributed here.

The diagnostic and reference-loop workflow in `skills/ableton-mix/references/diagnosis.md` is adapted and substantially revised from `glincker/ableton-skills` (`mixer-doctor`, commit `347cd7dc4c9b53a42fcc39b332b972c687cf9fdc`) and `CanArslanDev/ableton-live-mcp` (`mix-and-master`, commit `e65141b411746841746b553e3e8dbd6ab44442e8`). Their MIT notices are preserved in `LICENSES/` and inside the distributable skill. See `docs/research.md` for the exact retained concepts and corrected assumptions. No other upstream skill is installed as an authoritative instruction source.

Dependencies are installed separately and retain their respective licenses. Consult the installed versions' license metadata, especially FFmpeg build configuration and codec distribution conditions when redistributing a packaged environment. This repository does not relicense those dependencies.

The additive extension was written against the observed interface `get_all_write_handlers()` and main-thread dispatcher of an installed LiveMCP variant. Its upstream identity/license was not established; consequently this package ships only original extension code and a local staging script. The staged copy remains local and must not be published without establishing upstream redistribution rights.

Ableton and Live are trademarks of Ableton AG. This project is independent and not endorsed by Ableton.

Official technical references used:

- [Live 12 audio effects, including Auto Shift](https://www.ableton.com/en/live-manual/12/live-audio-effect-reference/)
- [Live Object Model: Song](https://docs.cycling74.com/apiref/lom/song/)
- [Live Object Model: Track](https://docs.cycling74.com/apiref/lom/track/)
- [Live Object Model: DeviceParameter](https://docs.cycling74.com/apiref/lom/deviceparameter/)
- [Microsoft application loopback capture](https://learn.microsoft.com/en-us/samples/microsoft/windows-classic-samples/applicationloopbackaudio-sample/)
- [Microsoft process loopback parameters](https://learn.microsoft.com/en-us/windows/win32/api/audioclientactivationparams/ns-audioclientactivationparams-audioclient_process_loopback_params)
- [SciPy polyphase resampling](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.resample_poly.html)
- [librosa pYIN](https://librosa.org/doc/latest/generated/librosa.pyin.html)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

Links document API concepts, not a claim that every installed Live edition or Remote Script behaves identically. Short implementation guidance is original; manuals are not bundled.

The optional `plugins` extra installs Spotify's [Pedalboard](https://github.com/spotify/pedalboard), GPL-3.0, as a separate dependency. No external plugin binaries, installers or factory presets are bundled; their sources and license categories are listed in [docs/free-plugins.md](docs/free-plugins.md).
