import logging
import shlex
import os
import subprocess
import textwrap
from abc import ABC

from cumulusci.tasks.command import Command
from cumulusci.cli.logger import init_logger as cci_init_logger

def init_logger():

    """
    Initiates cumulusci logger for static methods

    Usage:
        from qbrix.tools.shared.qbrix_console_utils import init_logger

        def test_func():
            logger = init_logger()
            logger.info("hey")

    """

    cci_init_logger(False)
    logger = logging.getLogger('cumulusci')
    return logger
class CreateBanner(Command, ABC):
    task_docs = """Creates a full width banner in the console with the provided text"""

    task_options = {
        "text": {
            "description": "Text you want to show in a banner. If you leave this blank it will show the current Q Brix details.",
            "required": False
        }
    }

    def _init_options(self, kwargs):
        super(CreateBanner, self)._init_options(kwargs)
        self.text = ""
        if "text" in self.options:
            self.text = self.options["text"]
        else:
            self.text = f"{self.project_config.project__name}\n\nAPI VERSION: {self.project_config.project__package__api_version}\nREPO URL:    {self.project_config.project__git__repo_url}"

        self.width = None
        self.text_box = None
        self.max_width = None
        self.border_char = '*'
        self.min_width = None
        self.env = self._get_env()

    def _banner_string(self):
        # if we are running in a headless runner- tty will not be there.
        if self.width == 0:
            return

        output_string = self.border_char * self.width + "\n"
        for text_line in self.text_box:
            output_string += self.border_char + " " + text_line + " " + self.border_char + "\n"
        output_string += self.border_char * self.width
        return output_string

    def _generate_list(self):

        # if we are running in a headless runner- tty will not be there.
        if self.width == 0:
            return []
        # Split the input text into separate paragraphs before formatting the
        # length.
        box_width = self.width - 4
        paragraph_list = self.text.split("\n")
        text_list = []
        for paragraph in paragraph_list:
            text_list += textwrap.fill(paragraph, box_width, replace_whitespace=False).split("\n")
        text_list = [line.ljust(box_width) for line in text_list]
        return text_list

    def _run_task(self):
        self.width = get_terminal_width()
        self.text_box = self._generate_list()
        print(self._banner_string())


def get_terminal_width():
    # if we are running in a headless runner- tty will not be there.
    try:
        return int(subprocess.check_output(['stty', 'size']).split()[1])
    except Exception as e:
        print(e)
    return 0


def run_command(command: str, cwd=None) -> int:
    """
    Runs a command as a subprocess and returns the result code

    Args:
        command (str): string command statement
        cwd (str): (Optional) Current Working Directory override

    Returns:
        (int) code (0 = success, 1 or above = error/failure)
    """

    log = init_logger()

    # Check Command
    if command:

        # Blacklisted Command Keywords
        blacklisted_keywords = {
            'rm', 'shutdown', 'reboot', 'dd', 'mkfs', 'fdisk',  # Linux/Unix commands
            'del', 'format', 'rmdir', 'rd', 'sfc', 'chkdsk', 'move', 'attrib',  # Windows commands
            'mv', 'chmod', 'chown', 'sudo', 'kill', 'killall', 'iptables'  # More Linux/Unix commands
        }

        # Check if any blacklisted keyword is in the command
        if any(keyword in command.split() for keyword in blacklisted_keywords):
            raise ValueError(f"Dangerous command detected: {command}")

    else:
        raise ValueError("No command was passed to the run_command function. Stopping script.")

    # Check Current Working Directory
    if not cwd:
        cwd = "."
    cwd = os.path.normpath(cwd)

    log.info("Running Command: '%s' in directory '%s'...", command, cwd)

    try:
        with subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', text=True) as proc:
            errs = []
            for line in proc.stdout:
                if line:
                    log.info(line)
            for line in proc.stderr:
                if line:
                    errs.append(line)
            stdout, _ = proc.communicate()
        result = subprocess.CompletedProcess(command, proc.returncode, stdout, "\n".join(errs))
    except subprocess.TimeoutExpired:
        proc.kill()
        log.error(" -X Subprocess Timeout. Killing Process")
    except Exception as e:
        proc.kill()
        log.error(" -X Subprocess Failed. Error details: %s", e)

    return result.returncode
