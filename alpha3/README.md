# Alpha №3: launch and evidence contract

Application: `obermot/nezabudka-for-codex` at **140fb1cf91afc83f4d2f74eee6cad734ace3866c**.
All tracked non-Kotlin-test files, including application code, resources, signing input, PDF87 and approved PNG references, are fingerprinted before preparation and verified after execution.

This branch changes test infrastructure only. It does not commit anything to the application repository. `prepare-tests.py` first validates SHA-256 and every exact replacement context for all 11 changed original test files; it refuses a changed source or a second application. The CI gate compiles both unit and Android Kotlin test suites before the full runs. `--fixture` is local partial-source validation only and is never used by the workflow.

## Baseline coverage

`expected-tests.json` lists all **731 unit + 78 Android** identities taken from Alpha №2 JUnit XML. No original methods are removed, renamed or disabled. The Android baseline excludes only the newly added `Alpha3DiagnosticDeviceTest`, which runs separately. Post-run verification fails on any missing, duplicated or skipped original identity. Failures remain failures.

## Audit mapping

| Group | Preparation |
|---|---|
| T10 | Both fixtures drain the real asynchronous session writer, remove AtomicFile base/backup/new files, and verify removal before launch. Room and preferences are reset as before. This fixes an isolation defect; it does not declare the suspected cascade proven for every original failure. |
| T02 | Six failing scenarios have explicit ACKNOWLEDGED assertions, acknowledged timestamp and stopped audio checks. The previously blocked compact-to-full scenario has the same reviewed correction. The screen-off test retains FIRING. Acknowledged-window snoozing uses the same explicit runtime option as the actual Activity. |
| T01 | Relative checked output directory; scale screenshots are uploaded. |
| T05 | Date and time are verified separately; navigation uses the actual clickable When heading. Four occurrences are repaired, including cases blocked earlier by isolation. |
| T03 | Assert the approved literal list 0/5/15/30; test its three repeat indices and terminal completion. The original method identity containing “sevenStages” is retained for baseline traceability. |
| T04 | Navigate through the explicit Repeat heading, not an ambiguous Daily summary. |
| T06 | Verify return to Home according to the single-editor navigation rule. |
| T09 | Measure the card through actual layout ancestors and select its separate switch hit target. The real 196-source-pixel card height is used, not an assumed 200. |
| T07 | Verify DEFERRED_ELAPSED while retaining no-replay checks. |
| T08 | Use owner-approved full-alarm gray #43595E; preserve strict lower #A3A38C check. |
| E01 | Schedule a real one-shot event through the production service/AlarmManager/foreground presentation path. Keep original retained-file and six-second cue checks. No audio-focus bypass and no direct-player test workaround. |
| U01–U05 | Original strict checks stay. Additional F01/F03/F11/F28/F37 diagnostics retain screenshots, Android hierarchy, Compose semantics, window/activity focus, audio, alarms, icon raster/palette/safe area, and startup video. |

U04/U05 remain product questions if the approved original is absent or contradicts existing expectations. Diagnostic data must not be interpreted as owner approval for new icon/startup colours.

## Visual and device evidence

The main unit run verifies the existing PDF87 references. Separate record-mode executions write Russian actual images and Ukrainian candidates **only into build output directories**, never the approved reference directory. Russian reference/actual pairs and per-pixel differences are exported. Ukrainian candidates are not automatically accepted as approved baselines.

The original Android suite runs on Pixel 6 API35 at its default 1080×2400/dpi420 setting. Extra targeted runs use 1080×2060/dpi420/font1, 720×1600/dpi320/font1.3, 1080×1920/dpi480/font1.5/system-dark, 1440×2560/dpi560/font1; gesture and three-button navigation vary where the emulator supplies those overlays. These are **synthetic profiles**, not a claim of testing a physical Motorola. The actual hardware model, window insets, density and fontScale are saved with each phase.

The approved application has an active light theme and an inactive Dark menu entry until dark layouts are approved (§59). Tests verify that rule and the application under Android system-night mode; no dark application UI is invented.

The official Vosk 0.22 model from the same vendor URL used by the existing installer is included in the **test APK only**, enabling the existing offline voice fixture to extract it if needed. Its SHA-256 is recorded. The application APK and functional source are unchanged by that addition.

General logcat starts while the emulator is alive; the test overlay removes both prior `logcat -c` calls. EXIT/INT/TERM collection runs before emulator shutdown. Full-size per-test screenshots, hierarchy and diagnostics are pulled from the target application's `device-evidence` directory. Pull/capture failures are recorded and fail evidence verification. Original XML, individual logcat, HTML, exact APKs and their SHA-256, source/infrastructure commits and an evidence inventory are uploaded even on test failure.

## Launch

The workflow supports manual dispatch and a narrowly scoped push trigger: only a change to `alpha3/launch.json` on branch `alpha-3`. Preparing or reporting commits do not trigger new runs. A launch marker identifies the reviewed preparation commit; the actual infrastructure commit is recorded from `GITHUB_SHA` in every job. Never push a marker while an earlier authorized run is still active.

No successful test result or Kotlin compilation is claimed before CI produces it. Compilation gate failure prevents spending emulator time on uncompilable tests; the preflight artifact preserves the precise compiler messages. New work must continue from those messages and this branch, without modifying application functionality.
