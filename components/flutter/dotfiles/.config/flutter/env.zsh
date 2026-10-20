# Optional Flutter component. SDK files live in the shared home; tools run in dev.
if [[ ${CONTAINER_ID:-} == dev ]]; then
    export FLUTTER_HOME="${FLUTTER_DEV_HOME:-$HOME/.local/share/flutter-dev}/flutter"
    export ANDROID_HOME="${FLUTTER_DEV_HOME:-$HOME/.local/share/flutter-dev}/android-sdk"
    export ANDROID_SDK_ROOT="$ANDROID_HOME"
    export ANDROID_AVD_HOME="${ANDROID_AVD_HOME:-${XDG_CONFIG_HOME:-$HOME/.config}/.android/avd}"
    [[ -d /usr/lib/jvm/java-21-openjdk ]] && export JAVA_HOME=/usr/lib/jvm/java-21-openjdk
fi
