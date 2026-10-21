// Read-only development probe. No capture and no device changes.
#include <CoreAudio/CoreAudio.h>
#include <stdio.h>
#include <stdlib.h>

static OSStatus read_property(AudioObjectID object,
                              AudioObjectPropertySelector selector,
                              AudioObjectPropertyScope scope, UInt32 *size,
                              void *value) {
  AudioObjectPropertyAddress address = {selector, scope,
                                        kAudioObjectPropertyElementMain};
  return AudioObjectGetPropertyData(object, &address, 0, NULL, size, value);
}

static void print_devices(AudioObjectID object, AudioObjectPropertyScope scope,
                          const char *label) {
  AudioObjectID devices[64];
  UInt32 size = sizeof(devices);
  OSStatus status = read_property(object, kAudioProcessPropertyDevices, scope,
                                  &size, devices);
  printf(" %s(status=%d)=", label, (int)status);
  if (status == noErr) {
    for (unsigned index = 0; index < size / sizeof(*devices); index++) {
      printf("%u,", devices[index]);
    }
  }
}

static int print_process(AudioObjectID object) {
  pid_t pid = 0;
  UInt32 size = sizeof(pid), input = 0, output = 0;
  if (read_property(object, kAudioProcessPropertyPID,
                    kAudioObjectPropertyScopeGlobal, &size, &pid) != noErr) {
    return 1;
  }
  size = sizeof(input);
  OSStatus input_status =
      read_property(object, kAudioProcessPropertyIsRunningInput,
                    kAudioObjectPropertyScopeGlobal, &size, &input);
  size = sizeof(output);
  OSStatus output_status =
      read_property(object, kAudioProcessPropertyIsRunningOutput,
                    kAudioObjectPropertyScopeGlobal, &size, &output);
  if (input_status != noErr || output_status != noErr) {
    fprintf(stderr, "Unknown state for process %d\n", pid);
    return 1;
  }
  if (input == 0 && output == 0) {
    return 0;
  }
  printf("pid=%d input=%u output=%u", pid, input, output);
  print_devices(object, kAudioObjectPropertyScopeInput, "inputs");
  print_devices(object, kAudioObjectPropertyScopeOutput, "outputs");
  puts("");
  return 0;
}

int main(void) {
  AudioObjectPropertyAddress address = {kAudioHardwarePropertyProcessObjectList,
                                        kAudioObjectPropertyScopeGlobal,
                                        kAudioObjectPropertyElementMain};
  UInt32 size = 0;
  if (AudioObjectGetPropertyDataSize(kAudioObjectSystemObject, &address, 0,
                                     NULL, &size) != noErr) {
    return 1;
  }
  AudioObjectID *objects = malloc(size);
  if (objects == NULL) {
    return 2;
  }
  if (AudioObjectGetPropertyData(kAudioObjectSystemObject, &address, 0, NULL,
                                 &size, objects) != noErr) {
    free(objects);
    return 3;
  }
  int failed = 0;
  for (unsigned index = 0; index < size / sizeof(*objects); index++) {
    failed |= print_process(objects[index]);
  }
  free(objects);
  return failed;
}
