"""Single-capture original recognition and RNNoise output for personal profiles."""
import ctypes
from collections import deque
from pathlib import Path

import numpy as np

NATIVE_RATE = 48000
NATIVE_FRAME_SAMPLES = 480
NATIVE_FRAME_BYTES = NATIVE_FRAME_SAMPLES * 4


def rnnoise_path():
    for path in (Path('/usr/lib/ladspa/librnnoise_ladspa.so'),
                 Path.home() / '.local/lib/ladspa/librnnoise_ladspa.so'):
        if path.is_file():
            return path
    raise RuntimeError('Falta RNNoise para la salida personal; reinstala voice-isolation.')


class NoiseReducer:
    def __init__(self, path=None):
        self.library = ctypes.CDLL(str(path or rnnoise_path()))
        lib = self.library
        pointer = ctypes.POINTER(ctypes.c_float)
        lib.rnnoise_get_frame_size.argtypes = []
        lib.rnnoise_get_frame_size.restype = ctypes.c_int
        lib.rnnoise_create.argtypes = [ctypes.c_void_p]
        lib.rnnoise_create.restype = ctypes.c_void_p
        lib.rnnoise_destroy.argtypes = [ctypes.c_void_p]
        lib.rnnoise_destroy.restype = None
        lib.rnnoise_process_frame.argtypes = [ctypes.c_void_p, pointer, pointer]
        lib.rnnoise_process_frame.restype = ctypes.c_float
        if lib.rnnoise_get_frame_size() != NATIVE_FRAME_SAMPLES:
            raise RuntimeError('RNNoise usa un tamaño de bloque incompatible.')
        self.state = lib.rnnoise_create(None)
        if not self.state:
            raise RuntimeError('No se pudo preparar RNNoise para la salida personal.')
        try:
            self.delay_samples = self._measure_delay()
        finally:
            self.close()
        # The synthetic probe must not remain in the live denoiser's history.
        self.state = lib.rnnoise_create(None)
        if not self.state:
            raise RuntimeError('No se pudo reiniciar RNNoise tras comprobar su sincronización.')

    def _measure_delay(self):
        samples = np.random.default_rng(2026).normal(0, 0.08, 480 * 48).astype(np.float32)
        samples = np.convolve(samples, np.ones(3) / 3, mode='same').astype(np.float32)
        output = np.concatenate([self.process(samples[start:start + 480])
                                 for start in range(0, len(samples), 480)])
        if float(np.sqrt(np.mean(output ** 2))) < 1e-8:
            raise RuntimeError('No se pudo medir la sincronización de RNNoise personal.')
        size = 1 << (len(samples) * 2 - 1).bit_length()
        correlation = np.fft.irfft(np.fft.rfft(output, size) *
                                   np.conj(np.fft.rfft(samples, size)), size)
        lag = int(np.argmax(correlation[:4800 + 1]))
        frames = round(lag / NATIVE_FRAME_SAMPLES)
        if frames not in (1, 2, 3) or abs(lag - frames * NATIVE_FRAME_SAMPLES) > 8:
            raise RuntimeError('El retardo de RNNoise personal no es compatible; se detuvo la prueba.')
        return frames * NATIVE_FRAME_SAMPLES

    def process(self, samples):
        if not self.state:
            raise RuntimeError('RNNoise personal está cerrado.')
        if np.shape(samples) != (NATIVE_FRAME_SAMPLES,) or not np.isfinite(samples).all():
            raise ValueError('RNNoise personal requiere un frame finito de 480 muestras.')
        # RNNoise accepts float PCM, including headroom above the int16 range.
        # Clamping here would irreversibly flatten peaks before denoising.
        values = np.ascontiguousarray(samples * 32768, dtype=np.float32)
        if not np.isfinite(values).all():
            raise ValueError('La entrada excedió el rango flotante de RNNoise.')
        output = np.empty(NATIVE_FRAME_SAMPLES, dtype=np.float32)
        pointer = ctypes.POINTER(ctypes.c_float)
        self.library.rnnoise_process_frame(self.state, output.ctypes.data_as(pointer),
                                         values.ctypes.data_as(pointer))
        if not np.isfinite(output).all():
            raise RuntimeError('RNNoise personal devolvió audio inválido.')
        return output / 32768

    def close(self):
        if self.state:
            self.library.rnnoise_destroy(self.state)
            self.state = None


class Downsample:
    """Continuous 63-tap low-pass, then 48 -> 16 kHz; preserve history per route."""
    def __init__(self):
        x = np.arange(63, dtype=np.float64) - 31
        self.coefficients = 0.3 * np.sinc(0.3 * x) * np.hanning(63)
        self.coefficients /= np.sum(self.coefficients)
        self.history = np.zeros(62, dtype=np.float32)

    def process(self, samples):
        values = np.concatenate((self.history, samples))
        output = np.convolve(values, self.coefficients, mode='valid')
        self.history = values[-62:].copy()
        return output[2::3].astype(np.float32)


def linear_source_volume(source):
    """Read the existing virtual-source gain without changing any system volume."""
    channels = source.get('volume', {}).values()
    volumes = [channel['value'] for channel in channels]
    if not volumes:
        return 1.0
    pulse = ctypes.CDLL('libpulse.so.0')
    pulse.pa_sw_volume_to_linear.argtypes = [ctypes.c_uint32]
    pulse.pa_sw_volume_to_linear.restype = ctypes.c_double
    return sum(pulse.pa_sw_volume_to_linear(value) for value in volumes) / len(volumes)


def prepare_enrollment(samples):
    if len(samples) < 16000 * 14 or not np.isfinite(samples).all():
        raise ValueError('La grabación fue corta o inválida. Vuelve a registrar tu voz.')
    absolute = np.abs(samples.astype(np.float64))
    peak = float(np.max(absolute))
    if float(np.sqrt(np.mean(absolute ** 2))) < 0.002:
        raise ValueError('Llegó muy poco audio. Habla a volumen normal y vuelve a registrar tu voz.')
    flat = float(np.mean(absolute >= peak * 0.999999)) if peak > 0.05 else 0.0
    if flat > 0.01:
        raise ValueError('Hay posibles picos recortados antes del reconocimiento. Revisa la entrada y repite el registro.')
    gain = min(1.0, 0.9 / peak)
    return (samples * gain).astype(np.float32), gain


class PersonalAudio:
    """Paired recognition and cleaned audio; optionally retain native output rate."""
    def __init__(self, gain, output_gain=1.0, denoiser=None, fullband=False):
        if type(gain) not in (int, float) or not np.isfinite(gain) or not 0 < gain <= 1:
            raise ValueError('El perfil tiene un factor de reconocimiento inválido.')
        if not np.isfinite(output_gain) or output_gain < 0:
            raise ValueError('La salida tiene un volumen inválido.')
        self.gain = gain
        self.output_gain = output_gain
        self.fullband = fullband
        self.levels = {'input_peak': 0.0, 'output_peak': 0.0,
                       'output_over_range_samples': 0, 'output_samples': 0}
        self.denoiser = denoiser or NoiseReducer()
        delay_frames = self.denoiser.delay_samples // NATIVE_FRAME_SAMPLES
        self.delay_seconds = self.denoiser.delay_samples / NATIVE_RATE
        self.original_downsample = Downsample()
        self.clean_downsample = Downsample()
        self.previous = deque(np.zeros(NATIVE_FRAME_SAMPLES, dtype=np.float32)
                              for _ in range(delay_frames))

    def process(self, raw):
        values = np.frombuffer(raw, dtype='<f4')
        if len(values) != NATIVE_FRAME_SAMPLES or not np.isfinite(values).all():
            raise RuntimeError('La captura original entregó un frame inválido.')
        scaled = (values * self.gain).astype(np.float32)
        # Enrollment gain belongs to recognition, not the nonlinear denoiser.
        # Native output uses the physical signal level, like the normal filter.
        cleaned = self.denoiser.process(values if self.fullband else scaled)
        # Delay the original branch by the denoiser's measured algorithmic delay.
        # Both branches come from one capture; never compare
        # a decision about one capture with filtered audio from another capture.
        original16 = self.original_downsample.process(self.previous.popleft())
        # Retain the enrollment scale in recognition and preserve source volume
        # on output. Only the older 16 kHz route compensates enrollment gain.
        self.previous.append(scaled.copy())
        if self.fullband:
            # Pack three native output samples beside each recognition sample.
            # Only recognition is downsampled; preserve all cleaned output samples.
            output48 = cleaned * self.output_gain
            previous_levels = self.levels
            self.levels = {
                'input_peak': max(previous_levels['input_peak'], float(np.max(np.abs(values)))),
                'output_peak': max(previous_levels['output_peak'], float(np.max(np.abs(output48)))),
                'output_over_range_samples': previous_levels['output_over_range_samples'] +
                    int(np.count_nonzero((output48 < -1) | (output48 > 32767 / 32768))),
                'output_samples': previous_levels['output_samples'] + len(output48),
            }
            return np.column_stack((original16, output48.reshape(-1, 3))).astype('<f4').tobytes()
        cleaned16 = self.clean_downsample.process(cleaned) * (self.output_gain / self.gain)
        return np.column_stack((original16, cleaned16)).astype('<f4').tobytes()

    def close(self):
        self.denoiser.close()
