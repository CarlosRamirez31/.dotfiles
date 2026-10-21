#define kNumber_Of_Channels 2
#define kDevice_HasInput true
#define kDevice_HasOutput false
#define kDevice2_HasInput false
#define kDevice2_HasOutput true
#define kDevice2_IsHidden true
#ifndef MIC_DRIVER_SOURCE
#error "Provide the verified upstream source with MIC_DRIVER_SOURCE"
#endif
#include MIC_DRIVER_SOURCE
#include <assert.h>
#include <stdio.h>
int main(void) {
  assert(BlackHole_StartIO(gAudioServerPlugInDriverRef, kObjectID_Device2, 1) ==
         0);
  assert(gDevice_IOIsRunning == 0 && gDevice2_IOIsRunning == 1);
  assert(BlackHole_StartIO(gAudioServerPlugInDriverRef, kObjectID_Device, 2) ==
         0);
  assert(BlackHole_StartIO(gAudioServerPlugInDriverRef, kObjectID_Device, 3) ==
         0);
  assert(gDevice_IOIsRunning == 2 && gDevice2_IOIsRunning == 1);
  assert(BlackHole_StopIO(gAudioServerPlugInDriverRef, kObjectID_Device, 2) ==
         0);
  assert(gDevice_IOIsRunning == 1);
  assert(BlackHole_StopIO(gAudioServerPlugInDriverRef, kObjectID_Device, 3) ==
         0);
  assert(gDevice_IOIsRunning == 0 && gDevice2_IOIsRunning == 1);
  assert(BlackHole_StopIO(gAudioServerPlugInDriverRef, kObjectID_Device2, 1) ==
         0);
  assert(gDevice_IOIsRunning == 0 && gDevice2_IOIsRunning == 0);
  puts("PASS split-device internal counters 0/1/2/1/0; no installed driver "
       "tested");
}
