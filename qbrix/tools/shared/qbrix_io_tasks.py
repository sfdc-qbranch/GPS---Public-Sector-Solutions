import os
import shutil

from qbrix.tools.shared.qbrix_console_utils import init_logger


class QbrixFileTask:

    """Provides general functions and security for working with files in Q brix"""

    def __init__(self, file_location: str):
        self.logger = init_logger()
        self.file_path = os.path.normpath(file_location)
        self.new_file_mode = bool(not os.path.exists(self.file_path))

        if not self.new_file_mode:
            self.check_file()

    def delete_file(self) -> bool:

        """ Deletes a given file """

        if self.new_file_mode:
            self.logger.info("'%s' does not exist or has already been deleted.", self.file_path)
            return True

        os.remove(self.file_path)

        return True

    def _is_within_project_directory(self):

        """Checks to ensure that given file path is not outwith the current project"""

        current_dir = os.path.realpath('.')
        common_prefix = os.path.commonprefix([os.path.realpath(self.file_path), current_dir])
        if common_prefix != current_dir:
            raise ValueError(f"Cannot modify or read file outside of current project: {self.file_path}")
        return True

    def check_file(self):

        """Carries out checks on the file to ensure we can proceed with other operations"""

        if not os.path.exists(self.file_path):
             raise FileNotFoundError("File does not exist")

        if not os.path.isfile(self.file_path):
            raise FileNotFoundError("File provided is not a File")

        self._is_within_project_directory()

    def get_file_contents(self):

        """Returns the file contents of a given file"""

        with open(self.file_path, "r", encoding="utf-8") as tmpFile:
            tmpFile.seek(0)
            file_contents = tmpFile.read()
        return file_contents

    def _upsert_file(self, file_contents):
        try:
            with open(self.file_path, "w", encoding="utf-8") as updated_file:
                updated_file.seek(0)
                updated_file.write(file_contents)
            return True
        except Exception as e:
            self.logger.error(e)
            return False

    def update_file(self, updated_file_contents) -> bool:

        """Updates an existing file with the given updated_file_contents with raise exception if file does not exist"""

        if self.new_file_mode:
            self.logger.error("File does not exist and cannot be updated.")
            return

        return self._upsert_file(updated_file_contents)

    def write_file(self, new_file_contents, overwrite_existing_file: bool = False):

        """
        Creates a new file using the given content. Raises an exception if file already exists and the overwrite_existing_file is False.

        Args:
            new_file_contents: The contents for the given file.
            overwrite_existing_file (bool): (Optional) Set to True when you want to allow method to overwrite an existing file. False (Default) if not.

        """
        if not self.new_file_mode and not overwrite_existing_file:
            self.logger.error("File already exists. Write new file method was called but file already exists.")
            return

        self.update_file(new_file_contents)


class QBrixDirectoryTask:

    """Provides general functions and security for working with directories in Q brix"""

    def __init__(self, directory_location: str):
        self.logger = init_logger()
        self.location = os.path.normpath(directory_location)

        if os.path.exists(self.location):
            self.check_dir()
        else:
            if self._is_within_project_directory():
                os.makedirs(self.location, exist_ok=True)

    def _is_within_project_directory(self):

        """Checks to ensure that the directory is within the current project"""

        current_dir = os.path.realpath('.')
        common_prefix = os.path.commonprefix([os.path.realpath(self.location), current_dir])
        if common_prefix != current_dir:
            raise ValueError(f"Cannot read or modify directory outside of current project: {self.location}")

    def check_dir(self):

        """Runs several checks on the directory to ensure we can proceed with other operations"""

        if not os.path.exists(self.location):
            raise FileNotFoundError("Directory already appears to have been removed or does not exist.")

        if not os.path.isdir(self.location):
            raise FileNotFoundError(f"Directory provided '{self.location}' is not a directory, stopping additional processing.")

        self._is_within_project_directory()

    def delete_directory(self) -> bool:

        """Deletes a given directory along with all sub-directories and files for a given parent directory"""

        if not os.path.exists(self.location):
            self.logger.info("'%s' has already been removed.", self.location)
            return True

        shutil.rmtree(self.location)
        return True
