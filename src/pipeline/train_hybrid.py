from __future__ import annotations



def train_buy_model(config):
    return {
        "model_path": f"{config.get('output_dir', 'data/models')}/buy_model.cbm",
        "threshold": 0.5,
    }


def build_sell_env(config, buy_artifact):
    return {"env": "sell_env", "buy": buy_artifact}


def run_bc_warmstart(config, env):
    return {"weights": f"{config.get('output_dir', 'data/models')}/bc.pt"}


def run_ppo_finetune(config, env, bc_artifact):
    return {"policy_path": f"{config.get('output_dir', 'data/models')}/sell_policy.zip"}


def run_ab_evaluation(config, buy_artifact, ppo_artifact):
    return {
        "maxdd_delta": 0.0,
        "sortino_delta": 0.0,
        "net_return_delta": 0.0,
    }


def run_hybrid_training(config):
    buy_artifact = train_buy_model(config)
    env = build_sell_env(config, buy_artifact)
    bc_artifact = run_bc_warmstart(config, env)
    ppo_artifact = run_ppo_finetune(config, env, bc_artifact)
    evaluation = run_ab_evaluation(config, buy_artifact, ppo_artifact)

    return {
        "artifacts": {
            "buy_model": buy_artifact,
            "sell_policy": ppo_artifact,
            "bc_warmstart": bc_artifact,
        },
        "evaluation": evaluation,
    }
