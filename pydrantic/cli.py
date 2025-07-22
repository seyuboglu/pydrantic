import os
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Union, List

from pydrantic.config import BaseConfig, RunConfig


def execute_config(config: RunConfig):
    # os.makedirs(config.run_dir, exist_ok=True)
    try: 
        output = config.run()
    except Exception as e:
        return None, config, e
    return output, config, None


def _update_config(config: BaseConfig, updates: List[str]) -> BaseConfig:
    # perform nested updates in place
    for update in updates:
        arg_path, value = update.split("=")

        child, parent, relation = config, None, None
        ancestors = []
        for key in arg_path.split("."):
            next_node = getattr(child, key)
            if isinstance(next_node, BaseConfig):
                parent = child
                child = next_node
                ancestors.append((parent, key))

        # NOTE: we use strict=False so that it coerces the strings from the cli into the 
        # correct types
        # we also are careful not to use model_dump() because it will also serialize
        # the nested configs
        data = {**{k: getattr(child, k) for k in child.model_fields}, key: value}
        if child._variables is not None:
            data.update(child._variables)
        config = child.model_validate(data, strict=False)
    
        for (parent, key) in reversed(ancestors):
            data = {** {k: getattr(parent, k) for k in parent.model_fields}, key: config}
            if parent._variables is not None:
                data.update(parent._variables)
            config = parent.model_validate(data, strict=False)

    return config


import argparse
from pathlib import Path

def main(
    configs: Union[RunConfig, List[RunConfig]], 
):
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--parallelize", action="store_true", default=False, help="Run configs in parallel")
    parser.add_argument("--gpus-per-config", type=int, default=1, help="Number of GPUs to use per config")
    parser.add_argument("--log-to-driver", action="store_true", default=False, help="Log to driver")
    parser.add_argument("--devices", type=str, default=None, help="Specify GPUs to use")
    args, updates = parser.parse_known_args()

    if isinstance(configs, RunConfig):
        configs = [configs]

    if args.devices is not None:
        print(args.devices)
        os.environ["CUDA_VISIBLE_DEVICES"] = args.devices

    time_tag = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    for idx, config in enumerate(configs):
        config: RunConfig = _update_config(config, updates)
        configs[idx] = config
        if config.script_id is None:
            import sys
            main_file = sys.modules['__main__'].__file__
            config.script_id = Path(main_file).stem
        
        if config.run_id is None:
            # use a unique run_id if not provided
            from uuid import uuid4
            config.run_id = str(uuid4())
        else:
            config.run_id = f"{config.run_id}-{idx}"

        config.launch_id = f"{time_tag}-{config.script_id}"
        if config.output_dir is not None:
            config.run_dir = os.path.join(config.output_dir, config.launch_id, config.run_id) 
            os.makedirs(config.run_dir, exist_ok=True)
            config.to_yaml(os.path.join(config.run_dir, "config.yaml"))

    use_ray = args.parallelize and len(configs) > 0
    if use_ray:
        import ray
        # SE(03/02): ray was killing workers due to OOM, but it didn't seem to be necessary 
        os.environ["RAY_memory_monitor_refresh_ms"] = "0"
        ray.init(ignore_reinit_error=True, log_to_driver=args.log_to_driver) #, _temp_dir="/home/sabri/tmp")

    print(f"Running {len(configs)} configs")

    # Run each script in parallel using Ray
    results = []
    if not use_ray:
        for config in configs: 
            out = config.run()
            results.append((out, config, None))
    else:
        completed = 0
        failed = 0
        total = len(configs)
        print(f"Completed: {completed} ({completed / total:0.1%}) | Total: {total}")

        # we set the number of gpus required by each remote equal to the number of
        # gpus required by each config
        futures = [
            ray.remote(num_gpus=args.gpus_per_config)(execute_config).remote(config) 
            for config in configs
        ]
        
        while futures:
            complete, futures = ray.wait(futures)
            for output, config, error in ray.get(complete):
                completed += 1
                if error is not None:
                    failed += 1
                    config.print()
                    print(error)
                else: 
                    print(f"Run {config.run_id} (status: completed) (run_dir: {config.run_dir})")
                    results.append((output, config, error))
                    
            print(f"Completed: {completed} ({completed / total:0.1%} -- {failed} failed) | Total: {total}")

        ray.shutdown()
