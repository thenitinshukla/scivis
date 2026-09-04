from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class SpectrumResult:
    frequencies: np.ndarray
    power: np.ndarray
    amplitude: np.ndarray
    axis: str = ""
    units: str = ""


def _uniform_spacing(values, *, name="coordinate", rtol=1e-6, atol=1e-12):
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or x.size < 2:
        raise ValueError(f"{name} needs at least two coordinates for spectral analysis")
    d = np.diff(x)
    if not np.all(np.isfinite(d)) or np.any(d == 0):
        raise ValueError(f"{name} contains invalid or repeated coordinates")
    ref = float(np.mean(d))
    if not np.allclose(d, ref, rtol=rtol, atol=atol):
        raise ValueError(f"{name} is non-uniform; FFT requires uniform spacing. Resample explicitly first.")
    return ref


def fft_1d(data, coordinate, axis=-1, *, use_rfft=True):
    spacing = _uniform_spacing(coordinate)
    arr = np.asarray(data)
    if use_rfft:
        spec = np.fft.rfft(arr, axis=axis)
        freq = np.fft.rfftfreq(arr.shape[axis], d=abs(spacing))
    else:
        spec = np.fft.fft(arr, axis=axis)
        freq = np.fft.fftfreq(arr.shape[axis], d=abs(spacing))
    amp = np.abs(spec)
    power = amp ** 2
    return SpectrumResult(freq, power, amp)


def fft_nd(data, coordinates, axes=None, *, use_rfftn=True):
    arr = np.asarray(data)
    if axes is None:
        axes = tuple(range(arr.ndim))
    axes = tuple(axes)
    spacings = [_uniform_spacing(coordinates[i], name=f"axis {i}") for i in axes]
    if use_rfftn:
        spec = np.fft.rfftn(arr, axes=axes)
        freq_axes = [np.fft.fftfreq(arr.shape[i], d=abs(spacings[j])) for j, i in enumerate(axes[:-1])]
        freq_axes.append(np.fft.rfftfreq(arr.shape[axes[-1]], d=abs(spacings[-1])))
    else:
        spec = np.fft.fftn(arr, axes=axes)
        freq_axes = [np.fft.fftfreq(arr.shape[i], d=abs(spacings[j])) for j, i in enumerate(axes)]
    return tuple(freq_axes), np.abs(spec), np.abs(spec) ** 2


def power_spectrum_1d(data, coordinate, axis=-1):
    return fft_1d(data, coordinate, axis=axis)


def wavenumber_spectrum(data, coordinate, axis=-1):
    result = fft_1d(data, coordinate, axis=axis)
    k = 2 * np.pi * result.frequencies
    return SpectrumResult(k, result.power, result.amplitude, axis="k")


def temporal_spectrum(values, times, axis=0):
    return fft_1d(values, times, axis=axis)


def k_omega(values, x, times, spatial_axis=-1, time_axis=0):
    arr = np.asarray(values)
    dt = _uniform_spacing(times, name="time")
    dx = _uniform_spacing(x, name="spatial coordinate")
    if time_axis != 0:
        arr = np.moveaxis(arr, time_axis, 0)
    if spatial_axis != arr.ndim - 1:
        spatial_axis = spatial_axis if spatial_axis >= 0 else arr.ndim + spatial_axis
        arr = np.moveaxis(arr, spatial_axis, -1)
    spec = np.fft.rfft2(arr, axes=(0, arr.ndim - 1))
    omega = 2 * np.pi * np.fft.fftfreq(arr.shape[0], d=abs(dt))
    k = 2 * np.pi * np.fft.rfftfreq(arr.shape[-1], d=abs(dx))
    return omega, k, np.abs(spec) ** 2
