"""Optional JAX-accelerated neural-network models.

Why here, specifically, and not just for the physics operators: scikit-learn's
`MLPRegressor` trains with a fairly Python-loop-heavy optimizer and cannot use
a GPU at all. Gradient-descent training of a small MLP -- many repeated
forward+backward passes over the *same* computational graph -- is exactly the
workload JAX's JIT compilation (and, on a GPU-equipped machine, `jax.devices()`
automatically including a GPU) is built for. This is a much better fit for
JAX than the physics differential operators in `native_backend`/`jax_backend`,
where the existing C++/OpenMP backend already wins on CPU (see that module's
docstring and `tests/test_jax_physics_backend.py` for the honest numbers).

This module deliberately does not depend on Flax/Optax/etc. to keep the
optional dependency footprint to just `jax`+`jaxlib`: the network and the
Adam optimizer are both the standard textbook formulas, implemented directly
with `jax.grad`/`jax.jit`.

Everything here is optional: if JAX isn't installed, `JAX_AVAILABLE` is
False and callers should fall back to `ml.advanced`'s sklearn-based
classes, which remain the default. Nothing else in the application
requires this module to be usable.
"""
from __future__ import annotations

from functools import partial

import numpy as np

try:
    import jax
    jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp
    JAX_AVAILABLE = True
except ImportError:
    jax = None
    jnp = None
    JAX_AVAILABLE = False

from .core import FeatureSet, MLResult


def require_jax() -> None:
    if not JAX_AVAILABLE:
        raise ImportError(
            "JAX-accelerated models require the 'jax' package. "
            "Install it with `pip install jax` (or `jax[cuda12]` etc. for GPU support)."
        )


def _init_params(key, layer_sizes):
    params = []
    for n_in, n_out in zip(layer_sizes[:-1], layer_sizes[1:]):
        key, wkey, bkey = jax.random.split(key, 3)
        scale = jnp.sqrt(2.0 / n_in)  # He initialization, matches ReLU below
        w = jax.random.normal(wkey, (n_in, n_out)) * scale
        b = jnp.zeros((n_out,))
        params.append((w, b))
    return params


def _forward(params, x):
    for w, b in params[:-1]:
        x = jax.nn.relu(x @ w + b)
    w, b = params[-1]
    return x @ w + b  # linear output layer, standard for regression


def _mse_loss(params, x, y):
    pred = _forward(params, x)
    return jnp.mean((pred - y.reshape(pred.shape)) ** 2)


@partial(jax.jit, static_argnames=("learning_rate",)) if JAX_AVAILABLE else (lambda f: f)
def _adam_step(params, m, v, t, x, y, learning_rate):
    beta1, beta2, eps = 0.9, 0.999, 1e-8
    loss, grads = jax.value_and_grad(_mse_loss)(params, x, y)
    new_params, new_m, new_v = [], [], []
    for (w, b), (gw, gb), (mw, mb), (vw, vb) in zip(params, grads, m, v):
        mw = beta1 * mw + (1 - beta1) * gw; mb = beta1 * mb + (1 - beta1) * gb
        vw = beta2 * vw + (1 - beta2) * gw ** 2; vb = beta2 * vb + (1 - beta2) * gb ** 2
        mw_hat = mw / (1 - beta1 ** t); mb_hat = mb / (1 - beta1 ** t)
        vw_hat = vw / (1 - beta2 ** t); vb_hat = vb / (1 - beta2 ** t)
        w = w - learning_rate * mw_hat / (jnp.sqrt(vw_hat) + eps)
        b = b - learning_rate * mb_hat / (jnp.sqrt(vb_hat) + eps)
        new_params.append((w, b)); new_m.append((mw, mb)); new_v.append((vw, vb))
    return new_params, new_m, new_v, loss


def _train(X, y, hidden_layers, max_iter, learning_rate, random_state, X_val=None, y_val=None,
           early_stopping=True, patience=15, chunk_size=20):
    """Train with `jax.lax.scan` over chunks of steps, not a plain Python
    loop. A naive Python `for` loop calling a jitted single-step function
    forces a host<->device round-trip on every iteration (to read the loss
    back for the loss curve / early-stopping check), which dominates
    runtime for a small MLP and erases JAX's advantage entirely -- an
    earlier version of this module did exactly that and was measured to
    be *both* slower and less accurate than sklearn's MLPRegressor for
    this reason. Scanning `chunk_size` steps at a time inside a single
    compiled call cuts the number of host round-trips by that same
    factor, while still checking validation loss between chunks for
    (approximate) early stopping."""
    require_jax()
    n_features = X.shape[1]
    n_out = 1 if y.ndim == 1 else y.shape[1]
    layer_sizes = [n_features, *hidden_layers, n_out]
    key = jax.random.PRNGKey(int(random_state))
    params = _init_params(key, layer_sizes)
    m = [(jnp.zeros_like(w), jnp.zeros_like(b)) for w, b in params]
    v = [(jnp.zeros_like(w), jnp.zeros_like(b)) for w, b in params]

    Xj = jnp.asarray(X, dtype=jnp.float64)
    yj = jnp.asarray(y, dtype=jnp.float64)
    Xv = jnp.asarray(X_val, dtype=jnp.float64) if X_val is not None else None
    yv = jnp.asarray(y_val, dtype=jnp.float64) if y_val is not None else None

    def scan_body(carry, t):
        params, m, v = carry
        params, m, v, loss = _adam_step(params, m, v, t, Xj, yj, learning_rate)
        return (params, m, v), loss

    loss_curve = []
    best_val = np.inf
    best_params = params
    stall = 0
    step = 0
    while step < max_iter:
        n_steps = min(chunk_size, max_iter - step)
        ts = jnp.arange(step + 1, step + n_steps + 1, dtype=jnp.float64)
        (params, m, v), losses = jax.lax.scan(scan_body, (params, m, v), ts)
        loss_curve.extend(np.asarray(losses).tolist())
        step += n_steps
        if early_stopping and Xv is not None:
            val_loss = float(_mse_loss(params, Xv, yv))
            if val_loss < best_val - 1e-9:
                best_val = val_loss; best_params = params; stall = 0
            else:
                stall += n_steps
                if stall >= patience:
                    break
    return (best_params if early_stopping and X_val is not None else params), loss_curve


class JaxMLPRegressor:
    """JAX/Adam-trained MLP regressor. Same external contract (`fit_predict`
    returning an `MLResult` with the same metadata keys) as
    `ml.advanced.NeuralNetworkRegressorAnalyzer`, so the GUI/ML tab can
    offer this as a drop-in alternative backend."""

    def __init__(self, hidden_layers=(128, 64), max_iter=300, learning_rate_init=1e-3,
                 early_stopping=True, random_state=42):
        require_jax()
        self.hidden_layers = tuple(int(v) for v in hidden_layers)
        self.max_iter = int(max_iter)
        self.learning_rate_init = float(learning_rate_init)
        self.early_stopping = bool(early_stopping)
        self.random_state = int(random_state)

    def fit_predict(self, features: FeatureSet, target, test_size=0.2, cv_folds=0) -> MLResult:
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        from sklearn.model_selection import train_test_split, KFold

        y = np.asarray(target, dtype=float).reshape(-1)
        if y.size != features.values.shape[0]:
            raise ValueError("Regression target must contain one value per sample")

        X_train, X_test, y_train, y_test = train_test_split(
            features.values, y, test_size=test_size, random_state=self.random_state
        )
        mu, sigma = X_train.mean(axis=0), X_train.std(axis=0) + 1e-12
        X_train_s = (X_train - mu) / sigma
        X_test_s = (X_test - mu) / sigma

        # Hold out a validation slice from the training data for early stopping,
        # matching sklearn MLPRegressor's own early_stopping behavior.
        if self.early_stopping and len(X_train_s) >= 10:
            X_fit, X_val, y_fit, y_val = train_test_split(X_train_s, y_train, test_size=0.1, random_state=self.random_state)
        else:
            X_fit, y_fit, X_val, y_val = X_train_s, y_train, None, None

        params, loss_curve = _train(
            X_fit, y_fit, self.hidden_layers, self.max_iter, self.learning_rate_init,
            self.random_state, X_val, y_val, early_stopping=self.early_stopping,
        )
        pred = np.asarray(_forward(params, jnp.asarray(X_test_s))).reshape(-1)
        metrics = {
            "r2": float(r2_score(y_test, pred)),
            "mae": float(mean_absolute_error(y_test, pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, pred))),
        }

        cv = None
        if int(cv_folds) >= 2:
            folds = min(int(cv_folds), max(2, len(y) // 5))
            scores = []
            for train_idx, test_idx in KFold(n_splits=folds, shuffle=True, random_state=self.random_state).split(features.values):
                Xtr, Xte = features.values[train_idx], features.values[test_idx]
                ytr, yte = y[train_idx], y[test_idx]
                mu_k, sigma_k = Xtr.mean(axis=0), Xtr.std(axis=0) + 1e-12
                p_k, _ = _train((Xtr - mu_k) / sigma_k, ytr, self.hidden_layers, self.max_iter,
                                 self.learning_rate_init, self.random_state, early_stopping=False)
                pred_k = np.asarray(_forward(p_k, jnp.asarray((Xte - mu_k) / sigma_k))).reshape(-1)
                scores.append(r2_score(yte, pred_k))
            scores = np.asarray(scores)
            cv = {"folds": int(folds), "scores": scores.tolist(),
                  "mean_r2": float(np.mean(scores)), "std_r2": float(np.std(scores))}

        model = {"params": params, "mu": mu, "sigma": sigma, "predict": lambda X: np.asarray(
            _forward(params, jnp.asarray((np.asarray(X) - mu) / sigma))).reshape(-1)}
        metadata = {
            "metrics": metrics, "y_test": y_test, "predicted": pred,
            "loss_curve": loss_curve, "cv": cv, "hidden_layers": self.hidden_layers,
            "backend": "jax",
        }
        return MLResult("Neural Network Regression (JAX)", pred, model, features, metadata)


class JaxAutoencoder:
    """JAX/Adam-trained autoencoder, mirroring `ml.advanced.AutoencoderAnalyzer`."""

    def __init__(self, bottleneck=8, max_iter=250, random_state=42, learning_rate_init=1e-3):
        require_jax()
        self.bottleneck = max(2, int(bottleneck))
        self.max_iter = int(max_iter)
        self.random_state = int(random_state)
        self.learning_rate_init = float(learning_rate_init)

    def fit_transform(self, features: FeatureSet) -> MLResult:
        X = np.asarray(features.values, dtype=float)
        mu, sigma = X.mean(axis=0), X.std(axis=0) + 1e-12
        Xs = (X - mu) / sigma
        hidden = (max(self.bottleneck * 4, 16), self.bottleneck, max(self.bottleneck * 4, 16))

        n = len(Xs)
        if n >= 10:
            idx = np.random.RandomState(self.random_state).permutation(n)
            n_val = max(1, n // 10)
            val_idx, fit_idx = idx[:n_val], idx[n_val:]
            X_val = Xs[val_idx]
        else:
            fit_idx, X_val = np.arange(n), None

        params, loss_curve = _train(
            Xs[fit_idx], Xs[fit_idx], hidden, self.max_iter, self.learning_rate_init,
            self.random_state, X_val, X_val, early_stopping=X_val is not None,
        )
        reconstructed_s = np.asarray(_forward(params, jnp.asarray(Xs)))
        reconstructed = reconstructed_s * sigma + mu
        errors = np.mean((X - reconstructed) ** 2, axis=1)
        model = {"params": params, "mu": mu, "sigma": sigma}
        return MLResult(
            "Neural Autoencoder (JAX)", reconstructed, model, features,
            {"reconstruction_error": errors, "loss_curve": loss_curve,
             "bottleneck": self.bottleneck, "hidden_layers": hidden, "backend": "jax"}
        )
