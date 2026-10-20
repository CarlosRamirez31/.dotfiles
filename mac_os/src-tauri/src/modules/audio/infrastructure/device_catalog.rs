use super::core_audio::VIRTUAL_DEVICE_NAME;
use crate::commons::Result;
use crate::modules::audio::{
    application::{DeviceCatalog, audio_error},
    domain::{Devices, Input},
};
use cpal::traits::{DeviceTrait, HostTrait};
pub struct CoreAudioDeviceCatalog;
impl DeviceCatalog for CoreAudioDeviceCatalog {
    fn list(&self) -> Result<Devices> {
        let host = cpal::default_host();
        let mut inputs = Vec::new();
        let mut blackhole_available = false;
        for device in host.devices().map_err(|_| audio_error())? {
            let description = device.description().map_err(|_| audio_error())?;
            let name = description.name().to_owned();
            if name == VIRTUAL_DEVICE_NAME {
                blackhole_available = device.supports_output();
            } else if device.supports_input() {
                inputs.push(Input {
                    id: device.id().map_err(|_| audio_error())?.to_string(),
                    name,
                });
            }
        }
        Ok(Devices {
            inputs,
            blackhole_available,
        })
    }
}
