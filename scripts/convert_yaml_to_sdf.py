#!/usr/bin/env python

import sys
import os
import re
import argparse
import yaml
from xml.dom.minidom import parseString
import xml.etree.ElementTree as ET


def get_model_path(model_name, ext="yaml"):
    """
    Checks for model file in ED_MODEL_PATH
    :param model_name: name of the model
    :type model_name: str
    :param ext: extension of the file: yaml/sdf
    :type ext: str
    :return: absolute model path or empty string
    :rtype: str
    """
    ed_model_path = os.getenv("ED_MODEL_PATH")
    model_path = ed_model_path + "/{}/model.{}".format(model_name, ext)

    if not os.path.isfile(model_path):
        return ""

    return model_path


def unique_name(name, names):
    """
    Provide a unique name based on name. If name already in names, the name is changed.
    If the name ends with digits, this number is increased. If the name doesn't end with a digit, the name is append
    with '1'. This continues until a unique name is found.
    :param name: name you want to be unique
    :type name: str
    :param names: list of names which are already used
    :type names: list
    :return: unique name
    :rtype: str
    """
    while name in names or not name:
        digits = re.search(r'\d+$', name)
        if name and digits:
            digits = digits.group()
            n_digits = len(digits)
            name = name[:-n_digits] + str(int(digits) + 1)
        else:
            name = name + str(1)
    names.append(name)
    return name


def read_pose(yaml_dict):
    """
    converts pose in yaml dict to string of 6 coordinates.
    :param yaml_dict: dict with possible pose as key on first level in dict
    :type yaml_dict: dict
    :return: string with 6 coordinates
    :rtype: str
    """
    pose = [0, 0, 0, 0, 0, 0]
    if "pose" in yaml_dict:
        # Check if coordinates are in pose, if so overwrite default 0
        options = {"x": 0, "y": 1, "z": 2, "rx": 3, "ry": 4, "rz": 5, "X": 3, "Y": 4, "Z": 5}
        for k, v in options.items():
            if k in yaml_dict["pose"]:
                pose[v] = yaml_dict["pose"][k]

    return " ".join(map(str, pose))


def read_geometry(shape_item):
    """
    Convert a shape item to a SDF geometry. With a possible pose offset. Which should be added to
    visual/collision/virtual_area
    :param shape_item: dict with shape description
    :type shape_item: dict
    :return: tuple of geometry, link_pose and geometry_pose
    :rtype: tuple
    """
    geometry = {}
    link_pose = read_pose(shape_item)
    geometry_pose = None

    if "cylinder" in shape_item:
        yml_cylinder = shape_item["cylinder"]
        geometry["cylinder"] = {"radius": yml_cylinder["radius"], "length": yml_cylinder["height"]}
        if "pose" in yml_cylinder:
            link_pose = read_pose(yml_cylinder)

    elif "box" in shape_item:
        yml_box = shape_item["box"]
        if "size" in yml_box:
            yml_box_size = yml_box["size"]
            box_size_list = [yml_box_size["x"], yml_box_size["y"], yml_box_size["z"]]
            box_size = " ".join(map(str, box_size_list))
            geometry["box"] = {"size": box_size}
        elif "min" in yml_box:
            yml_box_min = yml_box["min"]
            yml_box_max = yml_box["max"]
            size_x = yml_box_max["x"] - yml_box_min["x"]
            size_y = yml_box_max["y"] - yml_box_min["y"]
            size_z = yml_box_max["z"] - yml_box_min["z"]
            box_size_list = [size_x, size_y, size_z]
            box_size = " ".join(map(str, box_size_list))

            pos_x = yml_box_min["x"] + float(size_x)/2
            pos_y = yml_box_min["y"] + float(size_y)/2
            pos_z = yml_box_min["z"] + float(size_z)/2
            box_pose_list = [pos_x, pos_y, pos_z, 0, 0, 0]
            geometry_pose = " ".join(map(str, box_pose_list))

            geometry["box"] = {"size": box_size}

        if "pose" in yml_box:
            link_pose = read_pose(yml_box)

    return geometry, link_pose, geometry_pose


def read_shape_item(shape_item, link_names, color):
    """
    Convert shape item to a link with collision and visual elements
    :param shape_item: dict of one shape item
    :type shape_item: dict
    :param link_names: list of link names already used
    :type link_names: list
    :param color: None or dict of rgb values (0-1.0)
    :type color: dict
    :return: dict of SDF link element
    :rtype: dict
    """
    sdf_link_item = {}

    # name
    name = ""
    if "#" in shape_item:
        name = shape_item["#"]
    # Unique name should be known here
    name = unique_name(name, link_names)
    sdf_link_item["name"] = name

    geometry, link_pose, geometry_pose = read_geometry(shape_item)

    # Maybe have a default name for collision and visual instead of link name
    sdf_link_item["collision"] = {"name": name, "geometry": geometry}
    sdf_link_item["visual"] = {"name": name, "geometry": geometry}
    if geometry_pose:
        sdf_link_item["collision"]["pose"] = geometry_pose
        sdf_link_item["visual"]["pose"] = geometry_pose
    if color:
        color_str = " ".join(map(str, color.values()+[1]))
        sdf_link_item["visual"]["material"] = {"ambient": color_str}

    # pose
    sdf_link_item["pose"] = link_pose

    return sdf_link_item


def read_shape(shape, link_names, color):
    """
    Convert (array of) shape(s) to list of SDF links
    :param shape: shape dict
    :type shape: dict
    :param link_names: list of link names already used
    :type link_names: list
    :param color: None or dict of rgb values (0-1.0)
    :type color: dict
    :return: list of link elements
    :rtype: list
    """
    sdf_link = []
    # Check if compound type has name (inserted as comment in yaml)
    if "compound" in shape:
        for item in shape["compound"]:
            sdf_link.append(read_shape_item(item, link_names, color))
    else:
        sdf_link.append(read_shape_item(shape, link_names, color))

    return sdf_link


def read_areas(areas, link_names):
    """
    Convert areas to links with a virtual area
    :param areas: list of areas
    :type areas: list
    :param link_names: list of link names already used
    :type link_names: list
    :return: list of links with a virtual area child element
    :rtype: list
    """
    sdf_link = []
    if not isinstance(areas, list):
        print("areas should be a list")
        return sdf_link

    area_names = []
    for area in areas:
        name = area["name"]
        if name == "near":
            continue

        uname = unique_name(name, link_names)
        if not uname == name:
            print("Name of area has changed from '{}' to '{}'".format(name, uname))
        sdf_link_item = {"name": uname}

        for shape_item in area["shape"]:
            geometry, link_pose, geometry_pose = read_geometry(shape_item)
            shape_name = unique_name(uname, area_names)
            sdf_link_item["virtual_area"] = {"name": shape_name, "geometry": geometry}
            if geometry_pose:
                sdf_link_item["virtual_area"]["pose"] = geometry_pose

            sdf_link.append(sdf_link_item)

    return sdf_link


def parse_to_xml(xml, item, list_name=""):
    """
    Extend XML with elements from a dict, list or a string
    :param xml: xml element
    :type xml: xml.etree.ElementTree.Element
    :param item: dict, list or str
    :type item: dict or list or str
    :param list_name: name of list, needs to be passed on by parent for each element
    :type list_name: str
    """
    if isinstance(item, list):
        if not list_name:
            print("list_name should be passed on by parent in case of a list")
            return -1
        for v in item:
            child = ET.SubElement(xml, list_name)
            parse_to_xml(child, v)
    elif isinstance(item, dict):
        for k, v in item.items():
            # attributes
            if k == "name" or k == "version":
                xml.set(k, v)
                continue

            if isinstance(v, list):
                parse_to_xml(xml, v, k)
            else:
                child = ET.SubElement(xml, k)
                parse_to_xml(child, v)
    elif isinstance(item, str) or isinstance(item, float) or isinstance(item, int):
        xml.text = str(item)
    else:
        print("Cannot not parse object type: '{}'".format(type(item)))


def write_xml_to_file(xml_element, path):
    """
    write xml element to a file
    :param xml_element: xml element
    :type xml_element: xml.etree.ElementTree.Element
    :param path: full path of file, which to write
    :type path: str
    """
    # generate xml string with indentation
    xml_dom = parseString(ET.tostring(xml_element, encoding="utf-8"))
    pretty_xml_string = xml_dom.toprettyxml(indent="  ")

    with open(path, "w") as f:
        f.write(pretty_xml_string)


def main(model_name, recursive=False):
    # get model path
    model_path = get_model_path(model_name, "yaml")
    if not model_path:
        print ("no model path found for model: {}".format(model_name))
        return -1

    # declare sdf dict including sdf version
    sdf = {"version": "1.6"}

    # read yaml file
    with open(model_path, "r") as stream:
        try:
            yml = yaml.load(stream)
        except yaml.YAMLError as e:
            raise e

    # determine file_type
    if "composition" in yml:
        file_type = "world"
    else:
        file_type = "model"

    if file_type == "world":
        sdf["world"] = {"name": model_name, "include": []}
        sdf_include = sdf["world"]["include"]
        if not isinstance(yml["composition"], list):
            print("composition should be a list")
            return -1
        for item in yml["composition"]:
            if not isinstance(item, dict):
                print("items in composition should be a dict")
                return -1
            include = {"name": item["id"]}
            if "type" in item:
                if recursive:
                    # Todo: If there are multiple objects of the same type, then this type's SDF is created for every
                    #       instance of the type (for instance ids: table1 and table2 are both type TableA, so it will
                    #       recreate the SDF and config for TableA twice)
                    main(item["type"], recursive=recursive)
                include["uri"] = "model://{}".format(item["type"])
            include["pose"] = read_pose(item)
            sdf_include.append(include)

    elif file_type == "model":
        sdf["model"] = {"name": model_name, "static": "true", "link": []}  # All default parameters should be added here
        color = {}
        if "color" in yml:
            color["red"] = yml["color"]["red"]
            color["green"] = yml["color"]["green"]
            color["blue"] = yml["color"]["blue"]

        link_names = []
        if "shape" in yml:
            sdf["model"]["link"].extend(read_shape(yml["shape"], link_names, color))

        if "areas" in yml:
            sdf["model"]["link"].extend(read_areas(yml["areas"], link_names))

    # convert combination of dicts and lists to ET Elements
    xml = ET.Element("sdf")
    parse_to_xml(xml, sdf)

    # write to sdf file
    model_sdf_path = os.path.dirname(model_path) + "/model.sdf"
    write_xml_to_file(xml, model_sdf_path)

    ##
    # Generate model.config
    test_model_path = get_model_path("test_sdf", "sdf")
    if not test_model_path:
        print("Can't find 'test_sdf' model. Which is used for generation of 'model.config'")
        print("model.config not generated. Gazebo will not be able to find the model: '{}'".format(model_name))
        return -1

    test_config_path = os.path.dirname(test_model_path) + "/model.config"
    if not os.path.exists(test_config_path):
        print("model.config path: '{}' doesn't exist")
        print("model.config not generated. Gazebo will not be able to find the model: '{}'".format(model_name))
        return -1

    # xml parsing doesn't ignore whitespace, so reading the file manually
    with open(test_config_path, "r") as f:
        config_string = "".join(line.strip() for line in f)

    config_root = ET.fromstring(config_string)

    # set name and description
    config_root.find("name").text = model_name
    config_root.find("description").text = model_name

    # write model.config
    model_config_path = os.path.dirname(model_path) + "/model.config"
    write_xml_to_file(config_root, model_config_path)

    print("Successfully converted model '{}' to SDF".format(model_name))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert custom ED YAML model to SDF")
    parser.add_argument("model", type=str)
    parser.add_argument("--recursive", default=False, action="store_true")
    arguments = parser.parse_args()
    model = arguments.model
    recursive = arguments.recursive

    sys.exit(main(model, recursive=recursive))
