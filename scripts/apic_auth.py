import requests
import json
import yaml
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#Script global variables
# Directory variables
working_dir = os.path.abspath(os.getcwd())
repo_abs_path = os.path.abspath(os.path.join(working_dir, ".."))
switch_config_dir = os.path.join(repo_abs_path, "config")

def apic_extract_login_info():
    """
    Extracts APIC info from config YAML files
    :return:
    """
    with open(f"{switch_config_dir}/config.yaml", 'r') as f:
        valuesYaml = yaml.load(f, Loader=yaml.FullLoader)
    apic_ip = valuesYaml['apic_ip']

    with open(f"{switch_config_dir}/auth.yaml", 'r') as f:
        authYaml = yaml.load(f, Loader=yaml.FullLoader)
    apic_username = authYaml['username']
    apic_password = authYaml['password']

    return apic_ip, apic_username, apic_password


def apic_connectivity_check(apic_ip_address: str):
    """
    Check IP connectivity to APIC using ping
    :return:
    """
    apic_connection_flag = False
    ping_response = os.system("ping -c 2 " + apic_ip_address)
    if ping_response == 0:
        print(f"Connection to APIC with IP address {apic_ip_address} is OK!")
        apic_connection_flag = True
    else:
        print(f"Connection to APIC with IP address {apic_ip_address} FAILED!")
        apic_connection_flag = False

    return apic_connection_flag

def apic_auth_token(data: str):
    """
    Retrieves Cisco APIC authentication token
    :param data:
    :return:
    """
    login_url = "aaaLogin.json"
    apic_auth_url = f"https://{apic_extract_login_info()[0]}/api/{login_url}"

    try:
        post_auth_response = requests.post(apic_auth_url, json=data, verify=False)

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
    except ConnectionError:
        print('Cannot login to Cisco APIC due to connectivity issue')

    auth_response = json.loads(post_auth_response.text)
    apic_auth_token = auth_response["imdata"][0]["aaaLogin"]["attributes"]["token"]
    apic_cookie = {'APIC-cookie': apic_auth_token}

    return apic_cookie


def main():
    # APIC variables
    apic_ip, apic_username, apic_password = apic_extract_login_info()[0], apic_extract_login_info()[1], apic_extract_login_info()[2]
    apic_login_data_json = {"aaaUser": {"attributes": {"name": apic_username, "pwd": apic_password}}}

    # Generate file "token_file" containing APIC authentication token
    if apic_connectivity_check(apic_ip):
        with open(f"{switch_config_dir}/token_file.yaml", 'w') as output_file:
            yaml.dump(apic_auth_token(apic_login_data_json), output_file, default_flow_style=False)
            print(f"Token file {output_file.name} has been generated.")
    else:
        exit()


if __name__ == "__main__":
    main()


