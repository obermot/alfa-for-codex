#!/usr/bin/env bash
set -uo pipefail
task_tools="$GITHUB_WORKSPACE/infra/alpha3"
mkdir -p alpha3-evidence
failure=0
adb logcat -b all -v threadtime > alpha3-evidence/android-logcat-live.txt 2>&1 &
log_pid=$!
collect() {
  local target="$1"
  mkdir -p "alpha3-evidence/$target"
  adb shell -n wm size > "alpha3-evidence/$target/display.txt" 2>&1
  adb shell -n wm density >> "alpha3-evidence/$target/display.txt" 2>&1
  adb shell -n settings get system font_scale >> "alpha3-evidence/$target/display.txt" 2>&1
  adb shell -n getprop > "alpha3-evidence/$target/device-properties.txt" 2>&1
  adb shell -n dumpsys window > "alpha3-evidence/$target/windows.txt" 2>&1
  if adb pull /sdcard/Android/data/com.nezabudka.preview/files/device-evidence "alpha3-evidence/$target/" > "alpha3-evidence/$target/pull.txt" 2>&1; then
    printf 'OK\n' > "alpha3-evidence/$target/pull-status.txt"
  else
    printf 'FAILED\n' > "alpha3-evidence/$target/pull-status.txt"
    failure=1
  fi
}
finish() {
  local status=$?
  trap - EXIT INT TERM
  collect final-device
  adb logcat -b all -d > alpha3-evidence/android-logcat-final.txt 2>&1
  adb shell -n wm size reset
  adb shell -n wm density reset
  adb shell -n settings put system font_scale 1.0
  adb shell -n cmd uimode night no
  kill "$log_pid" 2>/dev/null || :
  wait "$log_pid" 2>/dev/null || :
  python3 "$task_tools/inventory.py" || failure=1
  if (( status!=0 || failure!=0 )); then exit 1; fi
}
trap finish EXIT
trap 'exit 130' INT TERM

# The full baseline is not filtered by individual original methods. Only the NEW diagnostic class is separate.
gradle :app:connectedDebugAndroidTest --stacktrace \
  -Pandroid.injected.androidTest.leaveApksInstalledAfterRun=true \
  -Pandroid.testInstrumentationRunnerArguments.notClass=com.nezabudka.testharness.Alpha3DiagnosticDeviceTest \
  2>&1 | tee alpha3-evidence/baseline-android-gradle.txt
baseline_status=${PIPESTATUS[0]}
if (( baseline_status!=0 )); then failure=1; fi
collect baseline-device
if [[ -d app/build/outputs/androidTest-results ]]; then
  cp -a app/build/outputs/androidTest-results alpha3-evidence/baseline-android-results
fi
python3 "$task_tools/verify-results.py" --source . --suite android \
  --results alpha3-evidence/baseline-android-results --output alpha3-evidence/baseline-android-coverage.json || failure=1

adb shell -n pm path com.nezabudka.preview > alpha3-evidence/installed-app.txt 2>&1
adb shell -n pm list instrumentation > alpha3-evidence/installed-runners.txt 2>&1
if ! grep -Fq 'com.nezabudka.preview.test/androidx.test.runner.AndroidJUnitRunner' alpha3-evidence/installed-runners.txt; then
  printf 'Instrumentation disappeared after baseline; diagnostics cannot execute.\n' >&2
  failure=1
fi
python3 "$task_tools/instrument.py" --profile unresolved --expected 6 \
  --tests com.nezabudka.testharness.Alpha3DiagnosticDeviceTest || failure=1
collect unresolved-device

# Synthetic profiles vary size, aspect, density, fontScale, night mode and system navigation.
# They are NOT described as a physical Motorola reproduction.
adb shell -n cmd overlay list > alpha3-evidence/available-overlays.txt
while read -r profile dimensions dpi font night navigation <&3; do
  adb shell -n am force-stop com.nezabudka.preview
  mkdir -p "alpha3-evidence/$profile"
  adb shell -n wm size "$dimensions" || failure=1
  adb shell -n wm density "$dpi" || failure=1
  adb shell -n settings put system font_scale "$font" || failure=1
  adb shell -n cmd uimode night "$night" || failure=1
  if grep -Fq "$navigation" alpha3-evidence/available-overlays.txt; then
    adb shell -n cmd overlay enable-exclusive --category "$navigation" > "alpha3-evidence/$profile/navigation.txt" 2>&1 || failure=1
  else
    printf 'Requested navigation overlay is unavailable: %s\n' "$navigation" > "alpha3-evidence/$profile/navigation.txt"
    failure=1
  fi
  python3 "$task_tools/instrument.py" --profile "$profile" --expected 2 \
    --tests 'com.nezabudka.testharness.Alpha3DiagnosticDeviceTest#geometryImeAndTheme,com.nezabudka.testharness.FinalEditorDeviceTest#calendarAndTextEditorKeepTheSameScaleBeforeAndDuringIme' || failure=1
  collect "$profile-device"
done 3<<'PROFILES'
short-owner 1080x2060 420 1.0 no com.android.internal.systemui.navbar.threebutton
compact-font 720x1600 320 1.3 no com.android.internal.systemui.navbar.gestural
short-large-font-dark-system 1080x1920 480 1.5 yes com.android.internal.systemui.navbar.threebutton
tall-dense 1440x2560 560 1.0 no com.android.internal.systemui.navbar.gestural
PROFILES

exit "$failure"
