from __future__ import annotations

import numpy as np

from ..core.data import Dataset
from .statistics import statistics
from .series import SimulationSeries


class AIAnalysisEngine:
    """Deterministic scientific-analysis service for one frame or an entire simulation series."""

    def analyze(self, dataset: Dataset) -> dict:
        data = np.asarray(dataset.data)
        finite = data[np.isfinite(data)]
        if finite.size == 0:
            raise ValueError("The selected dataset contains no finite numerical values.")
        stats = statistics(data)
        return {
            "scope": "frame",
            "n_frames": 1,
            "summary": self._summary(dataset, finite, stats),
            "statistics": stats,
            "physics": self._physics_suggestions(dataset),
            "recommendations": self._recommendations(dataset, finite),
        }

    def analyze_series(self, files=None, quantity=None, folder=None, reduction="mean", max_frames=None) -> dict:
        if folder:
            series = SimulationSeries.from_folder(folder, quantity=quantity)
        elif files:
            series = SimulationSeries(files, quantity=quantity)
        else:
            raise ValueError("Provide a simulation folder or a list of HDF5 files")
        frames = series.discover()
        if max_frames and len(frames) > max_frames:
            # Keep the full metadata inventory but sample evenly for expensive statistics.
            ids = np.linspace(0, len(frames) - 1, max_frames, dtype=int)
            sampled = [frames[i] for i in ids]
            sampled_series = SimulationSeries([x[0] for x in sampled], quantity=series.quantity)
            sampled_series._frames = sampled
            analysis_series = sampled_series
        else:
            analysis_series = series

        times, iterations, values = analysis_series.temporal_reduction(reduction)
        finite_values = values[np.isfinite(values)]
        if not finite_values.size:
            raise ValueError("The simulation series contains no finite values for the requested reduction")
        temporal_stats = {
            "frames_discovered": len(frames),
            "frames_analyzed": len(analysis_series.frames),
            "time_start": float(times.min()),
            "time_end": float(times.max()),
            "value_min": float(finite_values.min()),
            "value_max": float(finite_values.max()),
            "value_mean": float(finite_values.mean()),
            "value_rms": float(np.sqrt(np.mean(finite_values ** 2))),
        }
        frequency = None
        if len(times) >= 4:
            try:
                _, _, _, spec = analysis_series.temporal_frequency(reduction)
                power = np.asarray(spec.power).reshape(-1)
                freq = np.asarray(spec.frequencies).reshape(-1)
                idx = int(np.argmax(power[1:]) + 1) if power.size > 1 else 0
                frequency = {"peak_frequency": float(freq[idx]), "peak_power": float(power[idx])}
            except ValueError:
                frequency = {"status": "temporal spacing is not uniform; FFT skipped"}

        first_ds = analysis_series.load(0)
        last_ds = analysis_series.load(len(analysis_series.frames) - 1)
        change = np.asarray(last_ds.data, dtype=float) - np.asarray(first_ds.data, dtype=float)
        finite_change = change[np.isfinite(change)]
        return {
            "scope": "simulation_series",
            "quantity": series.quantity,
            "n_files_discovered": len(series.files),
            "n_frames": len(frames),
            "n_frames_analyzed": len(analysis_series.frames),
            "files": [f[0] for f in frames],
            "times": times,
            "iterations": iterations,
            "reduced_values": values,
            "temporal_statistics": temporal_stats,
            "temporal_frequency": frequency,
            "field_change": {
                "delta_min": float(np.nanmin(finite_change)),
                "delta_max": float(np.nanmax(finite_change)),
                "delta_rms": float(np.sqrt(np.nanmean(finite_change ** 2))),
            },
            "summary": (
                f"{series.quantity}: analyzed {len(analysis_series.frames)} of {len(frames)} discovered frames "
                f"from t={times.min():.6g} to {times.max():.6g}. "
                f"{reduction} over space ranges from {finite_values.min():.6g} to {finite_values.max():.6g}."
            ),
            "recommendations": self._series_recommendations(first_ds, times, values, frequency),
        }

    def _summary(self, ds, finite, stats):
        return (
            f"{ds.name}: {ds.ndim}D {ds.shape}, units={ds.units or 'not specified'}. "
            f"Finite range [{finite.min():.6g}, {finite.max():.6g}], "
            f"mean={stats['mean']:.6g}, RMS={stats['rms']:.6g}."
        )

    def _physics_suggestions(self, ds):
        axes = set(ds.axes)
        suggestions = []
        if ds.ndim >= 1:
            suggestions.append("Inspect coordinate-aware gradients along the available physical axes.")
        if ds.ndim >= 2:
            suggestions.append("Inspect lineouts and spatial averages to identify localized structure.")
        lower = ds.name.lower()
        if lower.startswith(("e", "electric")):
            suggestions.append("If E1/E2/E3 are available, evaluate |E|, E², divergence, and related derived quantities.")
        if lower.startswith(("b", "magnetic")):
            suggestions.append("If B1/B2/B3 are available, evaluate |B|, B², curl, and related derived quantities.")
        if axes:
            suggestions.append("Use physical coordinates for derivatives, integrals, and spectral wavenumbers.")
        return suggestions

    def _series_recommendations(self, ds, times, values, frequency):
        recs = [
            "Use the complete frame inventory for temporal statistics rather than analyzing only the displayed frame.",
            "Compare field evolution against simulation iteration and physical time before training a surrogate model.",
        ]
        if frequency and "peak_frequency" in frequency and frequency["peak_frequency"] > 0:
            recs.append(f"A temporal spectral peak was detected near {frequency['peak_frequency']:.6g} cycles per time unit; inspect its stability across the run.")
        if ds.ndim >= 2:
            recs.append("Run spatial FFT/wavenumber analysis and k-ω analysis when the spatial and temporal coordinates are uniform.")
        if np.ptp(values) > 0:
            recs.append("Use normalized temporal features and coordinate-aware spatial features for ML/surrogate training.")
        return recs

    def _recommendations(self, ds, finite):
        p01, p99 = np.percentile(finite, [1, 99])
        recs = []
        if np.min(finite) <= 0 < np.max(finite):
            recs.append("A diverging colormap or symmetric limits may be appropriate because the field crosses zero.")
        elif p99 / max(abs(p01), 1e-30) > 100:
            recs.append("The dynamic range is large; percentile clipping or logarithmic normalization may improve visualization.")
        if ds.ndim >= 2 and finite.size > 1000:
            recs.append("For ML, start with coordinate-aware features and bounded spatial sampling before training.")
        return recs
