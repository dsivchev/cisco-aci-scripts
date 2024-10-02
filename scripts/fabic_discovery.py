from string import Template
import requests
import json
import yaml
import os
import pprint
import apic_auth
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


#Script global variables
# Directory variables
working_dir = os.path.abspath(os.getcwd())
repo_abs_path = os.path.abspath(os.path.join(working_dir, ".."))
switch_config_dir = os.path.join(repo_abs_path, "config")
switch_inventory_dir = os.path.join(repo_abs_path, "inventory")


def apic_login_info():
    """
    Extracts APIC info from config YAML files
    :return:
    """
    try:
        with open(f"{switch_config_dir}/config.yaml", 'r') as f:
            valuesYaml = yaml.load(f, Loader=yaml.FullLoader)
        apic_ip = valuesYaml['apic_ip']
    except FileNotFoundError:
        print('Token file not found!')
        exit()

    try:
        with open(f"{switch_config_dir}/token_file.yaml", 'r') as f:
            valuesYaml = yaml.load(f, Loader=yaml.FullLoader)
        apic_cookie = valuesYaml["APIC-cookie"]
    except ConnectionError:
        print('Cannot login to Cisco APIC due to connectivity issue')
        exit()
    except FileNotFoundError:
        print('Token file not found!')
        exit()

    if apic_cookie is None:
        print("APIC Token file empty, or invalid token")
        exit()

    return apic_ip, apic_cookie

def fabric_check_nodes():
    #APIC variables and URLs
    fabric_class_name = "fabricNode.json"
    dhcp_class_name = "dhcpClient.json"
    apic_ip = apic_login_info()[0]
    apic_cookie = {"APIC-cookie": apic_login_info()[1]}
    base_url = f"https://{apic_ip}/api/node/class/"
    request_registered_nodes_filter = 'query-target-filter=ne(fabricNode.role,"controller")'
    #request_unregistered_nodes_filter = 'query-target-filter=or(eq(fabricNode.fabricSt,"incomplete"),eq(fabricNode.fabricSt,"unregistered"))'
    request_registered_nodes_url = base_url + fabric_class_name + "?" + request_registered_nodes_filter
    request_unregistered_nodes_url = base_url + dhcp_class_name #+ "?" + request_unregistered_nodes_filter

    #Other variables
    unregistered_nodes = {}

    try:
        get_fabric_response_reg = requests.get(request_registered_nodes_url, cookies=apic_cookie, verify=False)
        get_fabric_response_reg_json = get_fabric_response_reg.json()
        #pprint.pprint(get_fabric_response_reg_json)

        if get_fabric_response_reg_json["totalCount"] != "0":
            print(f"There are {eval(get_fabric_response_reg_json["totalCount"])} registered fabric devices discovered by APIC(s), script will exit!")
            exit()
        elif get_fabric_response_reg_json["totalCount"] == "0":
            print("No fabric devices discovered by APIC(s) yet, we are good to go...")

            get_fabric_response_unreg = requests.get(request_unregistered_nodes_url, cookies=apic_cookie, verify=False)
            get_response_dict = json.loads(get_fabric_response_unreg.text)
            #pprint.pprint(get_response_dict)

            for dhcp_clients in get_response_dict["imdata"][0].values():
                unregistered_nodes = {
                    attributes_value["id"]: {
                        "model":attributes_value["model"],
                        "role": attributes_value["nodeRole"],
                        "pod": attributes_value["podId"],
                    }
                    for attributes_value in dhcp_clients.values()
                }

            print()
            print("Devices to be registered:")
            print('serial_number switch_model  pod_number switch_role')
            for sn_key, values in unregistered_nodes.items():
                print("{:13} {:^12} {:^4} {:^19}".format(sn_key, values["model"], values["pod"], values["role"]))
            print()


    except ConnectionError:
        print('Cannot login to Cisco APIC due to connectivity issue')


def fabric_nodes_registration():
    """

    :return:
    """
    #APIC info
    cookie = {'APIC-cookie': apic_login_info()[1]}
    apic_ip_address = apic_login_info()[0]

    # APIC RESP API URL
    fabric_reg_class = "nodeidentpol.json"
    base_url = "api/node/mo/uni/controller/"
    apic_fab_url = f"https://{apic_ip_address}/{base_url}/{fabric_reg_class}"

    #REST API constructs
    post_headers = {"Content-Type": "application/json"}

    post_req_body = json.dumps({
    "fabricNodeIdentP": {
        "attributes":{
            #"nodeType":"$nodeType",
            "podId":"$podId",
            "serial":"$serial",
            "name":"$name",
            "nodeId":"$nodeId",
            }
        }
    })

    post_req_body_template = Template(post_req_body)

    try:
        with open(f"{switch_inventory_dir}/fabric_nodes.yaml", "r") as f:
            device_dict = yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError:
        print('Fabric nodes YAML file not found!')
        exit()

    for fabric_dev in device_dict["aci_metadata"]:
        post_req_body_str = post_req_body_template.substitute(
            name = fabric_dev["name"],
            nodeType = fabric_dev["nodeType"],
            podId = fabric_dev["podId"],
            serial = fabric_dev["serial"],
            nodeId = fabric_dev["nodeId"]
        )
        print(post_req_body_str)


        try:
            fabric_register_post = requests.post(apic_fab_url, json=post_headers, data=post_req_body_str, cookies=cookie, verify=False)
            fabric_register_post.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(e.response.json())
        except requests.exceptions.Timeout:
            print("Timeout Error:")
        except requests.exceptions.ConnectionError:
            print("Error Connecting:")
        except requests.exceptions.TooManyRedirects:
            print("Bad URL, please check if correct URL is supplied")
        except requests.exceptions.RequestException as err:
            print("Catastrophic error, exiting...")
            raise SystemExit(err)


def main():
    apic_ip_address = apic_login_info()[0]
    if apic_auth.apic_connectivity_check(apic_ip_address):
        fabric_check_nodes()
        fabric_nodes_registration()
    else:
        exit()


if __name__ == "__main__":
    main()

