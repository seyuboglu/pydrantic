import sys
import yaml

from dataclasses import dataclass

from typing import Optional, Union
from pydrantic.config import BaseConfig, RunConfig
import pydrantic.parser



import importlib
from datetime import datetime
import os
import importlib.util
from typing import List, Optional

import click
import pandas as pd 
from tqdm import tqdm

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
        for key in arg_path.split("."):
            next_node = getattr(child, key)
            if isinstance(next_node, BaseConfig):
                parent = child
                child = next_node
                relation = key
        if parent is None:
            config = child.model_validate({**child.to_dict(), key: value})
        else:
            setattr(parent, relation, child.model_validate({**child.to_dict(), key: value}))
    return config



# @click.option("-p", "--parallelize", is_flag=True)
# @click.option("--log-to-driver", is_flag=True)
# @click.option("--gpus", default=None, type=str)
# @click.option("--updates", "-u", type=str, multiple=True, help="Update config with these key=value pairs.")
def main(
    configs: Union[RunConfig, List[RunConfig]], 
    parallelize: bool=True, 
    log_to_driver: bool=False,
    gpus: str=None, 
    updates: List[str]=[],
    output_dir: Optional[str] = None
):
    if isinstance(configs, RunConfig):
        configs = [configs]

    if gpus is not None:
        print(gpus)
        os.environ["CUDA_VISIBLE_DEVICES"] = gpus

    # # update output_dir if not provided
    # if output_dir is None:
    #     if hasattr(config_module, "output_dir"):
    #         output_dir = config_module.output_dir

    launch_ids = []
    time_tag = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    for idx, config in enumerate(configs):
        # if output_dir is None:
        #     assert config.output_dir is not None, "output_dir not found in config file or HAYSTACKS_OUTPUT_DIR environment variable"
        #     output_dir = config.output_dir
        
        config = _update_config(config, updates)
        configs[idx] = config
        # if config.sweep_id is None:
        #     config.sweep_id = python_file.split("/")[-1].replace(".py", "")
        # sweep_id = config.sweep_id
        
        # if config.run_id is None:
        #     # use a unique run_id if not provided
        #     from uuid import uuid4
        #     config.run_id = str(uuid4())

        # config.launch_id =  f"{time_tag}-{sweep_id}"
        # launch_ids.append(config.launch_id)
        # config.run_dir = os.path.join(output_dir, config.launch_id, config.run_id)
        # os.makedirs(config.run_dir, exist_ok=True)
        # config.to_yaml(os.path.join(config.run_dir, "config.yaml"))

    # launch_ids = set(launch_ids)

    use_ray = parallelize and len(configs) > 0
    if use_ray:
        import ray
        # SE(03/02): ray was killing workers due to OOM, but it didn't seem to be necessary 
        os.environ["RAY_memory_monitor_refresh_ms"] = "0"
        ray.init(ignore_reinit_error=True, log_to_driver=log_to_driver, _temp_dir="/home/sabri/tmp")

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
            ray.remote(num_gpus=1)(execute_config).remote(config) 
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
                    results.append((output, config, error))
                    
            print(f"Completed: {completed} ({completed / total:0.1%} -- {failed} failed) | Total: {total}")

        ray.shutdown()

    # write outputs to disk
    # for launch_id in launch_ids:
    #     data = []
    #     for (output, config, error) in results:
    #         if config.launch_id != launch_id: 
    #             continue

    #         if error is not None:
    #             continue

    #         if isinstance(output, dict):
    #             data.append(output)
    #         elif isinstance(output, list):
    #             data.extend(output)
    #         elif output is not None: 
    #             raise ValueError(f"Invalid output type {type(output)}")
        
    #     df = pd.DataFrame(data)
    #     path = os.path.join(output_dir, launch_id, f"results.feather")
    #     os.makedirs(os.path.dirname(path), exist_ok=True)
    #     df.to_feather(path)
    #     print(f"Saved results to {path}")



# def main(configs: Union[RunConfig, List[RunConfig]]):
#     """
#     Run a pydrantic config. 
#     """
#     if not isinstance(configs, list):
#         configs = [configs]
    

#     args = sys.argv[1:]
#     for config in configs:
#         show = apply_overrides(config, args, finalize=True)

#     if show:
#         config.print()
#         return

#     return config.run()


# @dataclass
# class Alias:
#     name: str


# def assign(obj, key: str, value, assert_exists: bool = True):
#     split_dots = key.split(".")

#     obj_path = [obj]
#     for i, k in enumerate(split_dots):
#         cur_obj = obj_path[-1]

#         if isinstance(cur_obj, dict):
#             has_func = lambda o, k: k in o
#             get_func = lambda o, k: o[k]
#             set_func = lambda o, k, v: o.update({k: v})
#         else:
#             has_func = hasattr
#             get_func = getattr
#             set_func = setattr

#         if has_func(cur_obj, k):
#             next_obj = get_func(cur_obj, k)
#             if isinstance(next_obj, Alias):
#                 k = next_obj.name

#         # at our destination
#         if i == len(split_dots) - 1:
#             if assert_exists and not has_func(cur_obj, k):
#                 raise AttributeError(f"Config does not have attribute {key}")

#             set_func(cur_obj, k, value)
#         else:
#             if not assert_exists and not has_func(cur_obj, k):
#                 set_func(cur_obj, k, {})
#             new_obj = get_func(cur_obj, k)
#             obj_path.append(new_obj)


def apply_overrides(
    config: BaseConfig,
    args: list[str],
    enforce_required: bool = True,
    finalize: bool = True,
) -> bool:

    parsed_args = pydrantic.parser.parse(args)

    for command in parsed_args.commands:
        if isinstance(command, pydrantic.parser.Assignment):
            assign(
                config,
                command.kv_pair.key,
                command.kv_pair.value,
                assert_exists=command.assert_exists,
            )
        elif isinstance(command, pydrantic.parser.MethodCall):
            getattr(config, command.method_name)(*command.args, **command.kwargs)
        else:
            raise ValueError(f"Unknown command type {command}")

    return parsed_args.show
