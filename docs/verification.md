# Verification scope

This file distinguishes software verification from musical and application verification.

## Recorded local results (2026-11-11)

- Main suite: 53 tests passed after the final project-collection changes; Ruff passed. The wheel and source distribution built successfully. Check CI for the exact published commit.
- The built wheel was installed into a separate target directory and its CLI successfully ran `doctor`.
- Public GitHub Actions [run 43082752346](https://github.com/rub1kub/ableton-agent-kit/actions/runs/43082752346) could not start any job: GitHub reported an account billing lock. The Windows/Linux, Python 3.11/3.13 matrix is configured but **not verified**. Local suite results above are from Windows, Python 3.12.10; they do not establish the entire matrix.
- Real stdio MCP initialization, seven-tool listing, echo planning and disabled-write rejection passed.
- Windows process-loopback smoke: a generated 0.3-second 1 kHz tone was captured at peak 0.005005, with zero reported packet discontinuities. This validates the local process capture path, **not** Ableton's driver path.
- Optional pitch smoke: generated 440 Hz tone yielded median voiced estimate 439.80 Hz. Key candidates and plotting commands executed; the plot was visually inspected. A single tone cannot prove key detection quality.
- A previously native-saved real set was audited locally without modification: ordinary-track slot semantics, 31 track/return elements and 29 referenced audio files passed. Its names, paths, audio and XML are not published.
- Third-party comparison: five selected wstierhout dispatcher/session-identity tests passed; 22 CanArslanDev audio/mix-analysis tests passed in a separate SDK-2 environment. These are narrow source-level checks, **not** a live-server benchmark.
- The first expanded-backend test attempt in the SDK-1 toolkit environment failed at import; using its declared SDK-2 dependency in a separate environment resolved that mismatch. This is why the setup guide requires isolation.
- Skill frontmatter validation passed. The skill was installed locally and its runtime wrapper successfully ran `doctor`. The extension was staged from the actual installed legacy layout without changing the installed source.

The synthetic context-size experiment is reproducible with `benchmarks/context_cost.py` and recorded in [context-benchmark.json](context-benchmark.json). It compares information selection, not model billing or total mixing cost.

## Automated suite

Tests generate their own signals and XML. They cover valid/invalid ALS structures, media resolution and copied hashes, immutable source revisions, piecewise warp mapping, finite audio metrics, stereo cancellation, gap detection, echo fit/overlap policy, local TCP framing, write gating, response limits, extension group/return handling, pagination, stale identity/value rejection, automation protection, rollback and parameter readback.

CLI smoke tests exercise report output and packaging. The CI matrix runs Python 3.11 and 3.13 on Linux and Windows. Optional external dependencies and Windows process capture need additional platform checks; see the release's actual Actions result rather than treating this paragraph as a pass certificate.

## Native Ableton acceptance gate

Follow-up installation on 2026-11-11: wstierhout 1.8.1 was installed into a separate environment, its matching Remote Script was selected in Live 12.2.2 Suite, and its doctor returned `ok: true`. A real stdio MCP session listed 138 tools from eight selected groups and read session state, track inventory, returns and Reverb parameters. In an empty test set, a batch changed Return A Reverb Dry/Wet from 100% to 99%; readback confirmed the change, native Undo restored 100%, all Reverb parameters matched their original values and the session snapshot was unchanged. Transport remained stopped. This is a narrow native acceptance check, not validation of every tool, audio capture, rack editing or project export. The legacy extension below remains separately unverified in Live.

The initial extension targets the observed dispatcher layout of a LiveMCP installation used with Live 12.2.2 Suite. At development preflight its TCP endpoint was unavailable. Therefore initial automated results do **not** prove native extension loading, device parameter writes, project opening, edition compatibility or real playback capture. No active Live installation is modified by the staging command.

Before using a new Live/LiveMCP version for paid or irreplaceable work:

1. Save a disposable test set, preserve the original, stage/install the extension with Live closed.
2. Query capabilities, a group, return, master, clip page and parameter page.
3. Change one nonautomated native device parameter with expected identity/value; verify readback and Undo.
4. Try an expired or stale plan and verify no value changes.
5. Capture or export a known test tone and silence. Check source process, channels, rate, amplitude and transport alignment.
6. Reopen an edited copy of a set and compare exact loaded clip positions, devices and media availability with the offline audit. Save natively and repeat the inventory comparison.

Keep the evidence local; record versions and failures. A mock is not Live, a static XML pass is not a native load, meters are not a listening session, and a four-times oversampled sample peak is not a certified true-peak implementation.

## Musical acceptance

Use equal-loudness comparison of matching sections. Preserve user-approved sections and tails. Check diction, groove, transitions and mono in rendered audio; request specific user feedback where the agent cannot hear the result. Do not claim testing on physical speakers/headphones unless that actually occurred. No numerical test establishes that a song is a hit or that further artistic changes would be worse.
