from __future__ import annotations

from typing import Dict

import torch


class BCSmallPolicy(torch.nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 64, n_actions: int = 4):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(int(input_dim), int(hidden_dim)),
            torch.nn.ReLU(),
            torch.nn.Linear(int(hidden_dim), int(n_actions)),
        )

    def forward(self, obs):
        return self.net(obs)


def train_bc(
    obs_tensor,
    action_tensor,
    hidden_dim: int = 64,
    epochs: int = 20,
    lr: float = 1e-3,
):
    if obs_tensor.ndim != 2:
        raise ValueError("obs_tensor must be 2D")

    if obs_tensor.shape[0] != action_tensor.shape[0]:
        raise ValueError("obs/action batch size mismatch")

    obs = obs_tensor.float()
    actions = action_tensor.long()

    model = BCSmallPolicy(input_dim=obs.shape[1], hidden_dim=hidden_dim)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(lr))
    criterion = torch.nn.CrossEntropyLoss()

    for _ in range(int(epochs)):
        logits = model(obs)
        loss = criterion(logits, actions)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    state: Dict[str, torch.Tensor] = {
        key: value.detach().cpu().clone() for key, value in model.state_dict().items()
    }
    return state
