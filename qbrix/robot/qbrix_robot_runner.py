
import os
from qbrix.tools.shared.qbrix_console_utils import run_command

def run_robot_task(robot_task_name, robot_work_name, org_alias, **options):

    """Runs a robot task with optional parameters"""

    # Create Temp Folder
    os.makedirs(".qbrix/robot_tasks_temp", exist_ok=True)
    temp_file = f".qbrix/robot_tasks_temp/robot_task_{robot_work_name.lower().replace(' ', '_')}.robot"

    # Build File
    robot_file = f"*** Settings ***\nResource\t../../qbrix/robot/QRobot.resource\nSuite Setup\tRun keyword\tQRobot.Open Q Browser\nSuite Teardown\tQRobot.Close Q Browser\n*** Test Cases ***\n{robot_work_name}\n"

    robot_file += f"\t{robot_task_name}\n"

    for task_option, task_option_value in options.items():
        robot_file += f"\t...\t{task_option}={task_option_value}\n"

    with open(temp_file, 'w', encoding="utf-8") as upload_file:
            upload_file.write(robot_file)

    try:
        if run_command(f"cci task run robot --org {org_alias} --suites {temp_file} --vars 'browser:headlesschrome'") > 0:
            raise Exception("Robot task failed")
    except Exception as e:
        raise e
    finally:
        os.remove(temp_file)
