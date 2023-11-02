
import os
import xml
import xml.etree.ElementTree as ET


def find_value_in_sfdx_file(file_path, entry_key):

    """Returns the value for a given element key within a SFDX format XML file"""

    if not os.path.exists(file_path):
        return None

    ET.register_namespace('', "http://soap.sforce.com/2006/04/metadata")
    existing_tree = xml.etree.ElementTree.parse(file_path)
    salesforce_namespace_map = {'': "http://soap.sforce.com/2006/04/metadata"}
    located_element = existing_tree.find('.//'+entry_key, namespaces=salesforce_namespace_map)
    if located_element is not None:
        xml_value = located_element.text
        return xml_value
    return None
