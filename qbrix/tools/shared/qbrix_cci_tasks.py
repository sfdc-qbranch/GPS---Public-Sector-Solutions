import os
import shutil

from cumulusci.cli.runtime import CliRuntime
from cumulusci.core.exceptions import TaskOptionsError
from cumulusci.core.tasks import CURRENT_TASK
from cumulusci.core.utils import import_global

from qbrix.tools.shared.qbrix_console_utils import init_logger


def rebuild_cci_cache(
    cci_project_cache_directory: str = None, rebuild_flow: str = None
) -> bool:
    """
    Rebuilds the CCI projects Cache folder using the dev_org flow from CCI

    Args:
        cci_project_cache_directory (str): Relative File Path to the CCI Projects Directory
        rebuild_flow (str): (Optional) Name of the flow from the Q Brix to use to get all relevant sources. Defaults to deploy_qbrix

    Returns:
        bool: True when complete
    """
    logger = init_logger()

    if not cci_project_cache_directory:
        cci_project_cache_directory = os.path.normpath(".cci/projects")

    # Cleanup Current Directory
    if os.path.exists(cci_project_cache_directory):
        shutil.rmtree(cci_project_cache_directory)

    # Get deploy_qbrix flow to rebuild cache
    if not rebuild_flow:
        rebuild_flow = "deploy_qbrix"

    logger.info("Rebuilding Cache using flow called [%s]...", rebuild_flow)
    CliRuntime().get_flow(rebuild_flow)
    logger.info("Cache Rebuilt!")
    # Return True to confirm completion
    return True


def _init_task(class_path, options, task_config, org_config=None):
    task_class = import_global(class_path)
    task_config = _parse_task_options(options, task_class, task_config)

    if org_config:
        task = task_class(
            task_config.project_config, task_config, org_config=org_config
        )
    else:
        task = task_class(task_config.project_config, task_config)
    return task


def _parse_task_options(options, task_class, task_config):
    """
    Task Option Parser
    """

    if "options" not in task_config.config:
        task_config.config["options"] = {}
    # Parse options and add to task config
    if options:
        for name, value in options.items():
            # Validate the option
            if name not in task_class.task_options:
                raise TaskOptionsError(
                    'Option "{}" is not available for task {}'.format(name, task_class)
                )

            # Override the option in the task config
            task_config.config["options"][name] = value

    return task_config


def _run_task(task):
    task()
    return task.return_values


def run_cci_task(task_name: str, org_name: str = None, **options) -> bool:
    """
    Runs a given task using the name of the task.

    Args:
        task_name (str): The name of the task to run
        org_name (str): The optional alias for the org, this defaults to "dev"
        options: Additional options for the task that you want to provide, for example the 'deploy' task has an option for path, so you can define path='my/path/here'

    Example Usage:

    run_cci_task('deploy', 'dev', path='force-app')
    """

    _org = None
    _project_config = None

    logger = init_logger()

    if not org_name:
        logger.debug("No Org name was provided. Defaulting to 'dev' alias.")
        org_name = "dev"

    logger.info(
        "Running task with name [%s] against target org [%s]", task_name, org_name
    )

    try:
        if (
            getattr(CURRENT_TASK, "stack", None)
            and CURRENT_TASK.stack[0].project_config
        ):
            _project_config = CURRENT_TASK.stack[0].project_config
        else:
            _project_config = CliRuntime().project_config

        if getattr(CURRENT_TASK, "stack", None) and CURRENT_TASK.stack[0].org_config:
            _org = CURRENT_TASK.stack[0].org_config
        else:
            _org = CliRuntime().project_config.keychain.get_org(org_name)

        task_config = CliRuntime().project_config.get_task(task_name)
        task_class = import_global(task_config.class_path)
        task_config = _parse_task_options(options, task_class, task_config)
        task = task_class(
            task_config.project_config or _project_config,
            task_config,
            org_config=_org,
        )

        logger.info(" -> Task parameters generated. Running task...")

        _run_task(task)

        logger.info(" -> Task Complete!")
        return True
    except Exception as e:
        raise Exception(f"Task Runner Failed. Error details: {e}")


def run_cci_flow(flow_name: str, org_name: str = None, **options) -> bool:
    """
    Runs a given flow using the flow name and optional org name along with optional options.

    Args:
        flow_name (str): The name of the flow to run, for example deploy_qbrix
        org_name (str): Optional alias for the org. This defaults to "dev"

    Returns:
        bool: True if the flow has executed without error

    Example Usage:
        run_cci_flow('deploy_qbrix', 'dev')
    """

    logger = init_logger()

    if not org_name:
        logger.debug("No Org name was provided. Defaulting to 'dev' alias.")
        org_name = "dev"

    logger.info("Starting flow [%s] against target org [%s]", flow_name, org_name)

    org_config = CliRuntime().project_config.keychain.get_org(org_name)

    if not org_config:
        raise ValueError(
            f"Unable to get target Salesforce org configuration for provided alias [{org_name}]"
        )

    flow_coordinator = CliRuntime().get_flow(flow_name, options=options)

    if not flow_coordinator:
        raise ValueError(
            f"Unable to get find a flow configuration for the name provided [{flow_name}]"
        )

    flow_coordinator.run(org_config)

    logger.info("Flow completed!")

    return True
