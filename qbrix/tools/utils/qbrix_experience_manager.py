import os
import re

from cumulusci.core.utils import process_list_of_pairs_dict_arg
from cumulusci.tasks.salesforce import BaseSalesforceApiTask

from qbrix.tools.shared.qbrix_console_utils import run_command


class ExperienceManager(BaseSalesforceApiTask):

    """Class for working with Experience Cloud sites in Qbrix"""

    task_options = {
        "org": {"description": "Org Alias for the target org", "required": False},
        "experience_site_name": {
            "description": "Name/label for the Experience Cloud site",
            "required": True,
        },
        "featured_topics": {
            "description": "Dictionary of featured topics with related image file path",
            "required": False,
        },
        "topic_assignments": {
            "description": "Dictionary of topics with a list of related knowledge article titles",
            "required": False,
        },
        "collaboration_groups": {
            "description": "List of collaboration groups to link to site",
            "required": False,
        },
    }

    task_docs = ""

    def _init_options(self, kwargs):
        super(ExperienceManager, self)._init_options(kwargs)
        self.topic_assignments = (
            process_list_of_pairs_dict_arg(self.options["topic_assignments"])
            if "topic_assignments" in self.options
            else None
        )
        self.featured_topics = (
            process_list_of_pairs_dict_arg(self.options["featured_topics"])
            if "featured_topics" in self.options
            else None
        )
        self.experience_site_name = self.options["experience_site_name"]
        self.collaboration_groups = (
            self.options["collaboration_groups"]
            if "collaboration_groups" in self.options
            else None
        )
        self.network_id = None

    def _process_collaboration_groups(self):
        for collaboration_group in self.collaboration_groups:
            cg_lookup = self.sf.query(
                f"select id from CollaborationGroup Where Name = '{collaboration_group}' and NetworkId = '{self.network_id}' LIMIT 1"
            )

            if cg_lookup["totalSize"] == 0:
                group_id = self.sf.CollaborationGroup.create(
                    {
                        "Name": collaboration_group,
                        "CollaborationType": "Public",
                        "NetworkId": self.network_id,
                    }
                )
                if group_id and group_id["id"]:
                    self.logger.info(
                        f"Created new Collaboration Group '{collaboration_group}'  for experience cloud site '{self.experience_site_name}' with id '{group_id['id']}'"
                    )
            else:
                self.logger.info(
                    f"Collaboration Group '{collaboration_group}' was already created"
                )

    def _lookup_topic_id(self, topic_name):
        topic_lookup = self.sf.query(
            f"select id,Name from Topic Where Name = '{topic_name}' LIMIT 1"
        )

        if topic_lookup["totalSize"] > 0:
            return topic_lookup["records"][0]["Id"]
        return None

    def _lookup_article_id(self, article_title):
        knowledge_lookup = self.sf.query(
            f"Select id from Knowledge__kav Where Title =  '{article_title}' LIMIT 1"
        )

        if knowledge_lookup["totalSize"] > 0:
            return knowledge_lookup["records"][0]["Id"]
        return None

    def _process_topic_assignments(self):
        for topic, kb_articles in self.topic_assignments.items():
            topic_name = topic
            if not topic_name:
                self.logger.info("Topic name not found. Skipping...")
                continue
            topic_id = self._lookup_topic_id(topic_name)
            if not topic_id:
                self.logger.info(
                    f"Topic with name '{topic_name}' not found. Skipping..."
                )
                continue

            for article in kb_articles:
                knowledge_title = article.replace("'", "\\'")
                if not knowledge_title:
                    self.logger.info("Knowledge Article title not found. Skipping...")
                    continue
                knowledge_article_id = self._lookup_article_id(knowledge_title)
                if not knowledge_article_id:
                    self.logger.info(
                        f"Knowledge Article with title '{knowledge_title}' not found. Skipping..."
                    )
                    continue

                kb_lookup = self.sf.query(
                    f"select id from TopicAssignment Where TopicId = '{topic_id}' and NetworkId = '{self.network_id}' and EntityId = '{knowledge_article_id}' LIMIT 1"
                )

                if kb_lookup["totalSize"] == 0:
                    topic_assignment_id = self.sf.TopicAssignment.create(
                        {
                            "EntityId": knowledge_article_id,
                            "NetworkId": self.network_id,
                            "TopicId": topic_id,
                        }
                    )

                    if topic_assignment_id and topic_assignment_id.get("id"):
                        self.logger.info(
                            f"Created new Topic Assignment for experience cloud site {self.experience_site_name} with id {topic_assignment_id['id']}"
                        )
                    else:
                        self.logger.error("Topic failed to create:")
                        self.logger.info(topic_assignment_id)

                else:
                    self.logger.info(
                        f"Topic Assignment already created for article '{article}' and topic '{topic}' "
                    )

    def _process_featured_topic(self):
        os.makedirs(".qbrix/feature_topic_uploads", exist_ok=True)

        robot_file = "*** Settings ***\nResource\t../../qbrix/robot/QRobot.resource\nSuite Setup\tRun keyword\tQRobot.Open Q Browser\nSuite Teardown\tQRobot.Close Q Browser\n*** Test Cases ***\nUpload Featured Topic Images"

        first_record = True
        for topic, topic_details in self.featured_topics.items():
            if first_record:
                robot_file += f"\tUpload Featured Topic Image\n\t...\t{topic_details.get('file')}\n\t...\t{topic}\n\t...\t{self.experience_site_name}\n\t...\t${{True}}\n\n"
                first_record = False
            else:
                robot_file += f"\tUpload Featured Topic Image\n\t...\t{topic_details.get('file')}\n\t...\t{topic}\n\t...\t{self.experience_site_name}\n\t...\t${{False}}\n\n"

        with open(
            ".qbrix/feature_topic_uploads/temp_robot_topics_upload.robot",
            "w",
            encoding="utf-8",
        ) as upload_file:
            upload_file.write(robot_file)

        run_command(
            f"cci task run robot --org {self.org_config.name} --suites .qbrix/feature_topic_uploads/temp_robot_topics_upload.robot --vars 'browser:headlesschrome'"
        )

        os.remove(".qbrix/feature_topic_uploads/temp_robot_topics_upload.robot")

    def _run_task(self):
        self.logger.info("Starting Experience Cloud Manager\n")

        # Get Experience Cloud Site ID
        site_lookup = self.sf.query(
            f"SELECT Id,Name From Network WHERE Name = '{self.experience_site_name}' LIMIT 1"
        )

        if site_lookup["totalSize"] > 0:
            self.network_id = site_lookup["records"][0]["Id"]
            self.logger.info(
                f"\nWorking with Experience Site ({self.experience_site_name}) - ID: ({self.network_id})"
            )
        else:
            self.logger.error("Experience Cloud Site not found in org.")
            return

        # Process Collaboration Groups
        if self.collaboration_groups and len(self.collaboration_groups) > 0:
            self.logger.info("\n-> Processing Collaboration Groups")
            self._process_collaboration_groups()

        # Process Topic Assignments
        if self.topic_assignments:
            self.logger.info("\n-> Processing Topic Assignments")
            self._process_topic_assignments()

        # Process Featured Topic
        if self.featured_topics:
            self.logger.info("\n-> Processing Featured Topic Assignments")
            self._process_featured_topic()


class ExperienceFileAssetManager(BaseSalesforceApiTask):
    task_docs = """
        Class for working with File Assets in Experience Cloud sites in Qbrix
    """

    task_options = {
        "org": {"description": "Org Alias for the target org", "required": False},
    }

    # Constants
    EXPERIENCE_AURA_PATH = "force-app/main/default/experiences"
    EXPERIENCE_LWR_PATH = "force-app/main/default/digitalExperiences/site"
    REGEX_FILE_ASSET = r"/file-asset/(\w+)(\?v=(\d+))?"

    def _init_options(self, kwargs):
        super(ExperienceFileAssetManager, self)._init_options(kwargs)

    def read_file_content(self, filepath):
        """
        Read a file
        """
        file = open(filepath, "r", encoding="utf-8")
        file_content = file.read()
        file.close()
        return file_content

    def find_file_assets(self, path):
        """
        Loop through all the json files in a given directory and search for the references to file assets (e.g. /file-asset/file.png?v=1)
        """
        if not os.path.exists(path):
            self.logger.error(f'Experience path "{path}" does not exist.')
            return []

        file_assets = []

        for root, _, files in os.walk(path, topdown=True):
            for name in files:
                current_file = os.path.join(root, name)

                if current_file.endswith(".json"):
                    file_content = self.read_file_content(current_file)
                    matches = re.findall(self.REGEX_FILE_ASSET, file_content)
                    if len(matches) > 0:
                        self.logger.info(
                            f"{len(matches)} asset file(s) found in {current_file}:"
                        )
                        for match in matches:
                            file_assets.append(match[0])
                            self.logger.info(f"  - {match[0]}")

        return file_assets

    def _run_task(self):
        file_assets = []
        file_assets += self.find_file_assets(self.EXPERIENCE_AURA_PATH)
        file_assets += self.find_file_assets(self.EXPERIENCE_LWR_PATH)

        if len(file_assets) == 0:
            self.logger.info("Could not find any file assets in the current workspace.")
            return

        # Set the default output directory path
        output_dir = os.path.join("datasets", "community_files")

        filenames = ",".join(file_assets)
        command = f'cci task run qbrix_download_files --org {self.org_config.name} --filenames "{filenames}" --path "{output_dir}"'

        run_command(command)
