# Intro
This is a collection of Cisco ACI scripts

# Installation
Clone repository using:
```bash
git clone <repo_url>
``` 
Then use python package manager to install 'requirements.txt' file:

```bash
pip install -r requirements.txt
```

# Description
Directory structure of the current repository is following:
```bash
├── README.md
├── ansible
├── config
│   ├── auth.yaml
│   ├── config.yaml
│   └── token_file.yaml
├── inventory
│   └── fabric_nodes.yaml
├── requirements.txt
└── scripts
    ├── apic_auth.py
    └── fabic_discovery.py
```

## *Directories description:*

**'ansible'** - contains all Ansible code
**'config'** - config files relevant to all Python scripts. All attribute values in YAML files are provided manually! 
**'inventory'** - files describing ACI insfrastructure, used only by Python scripts 
**'scripts'** - contains all Python scripts

## *Scripts description:*
### *Python scripts*
All Python scripts are located in _*'scripts'*_ directory.

_**apic_auth.py**_ - generates an APIC authentication token. Generated token is stored in _../config/token_file.yaml_file.
_**fabric_discovery**_ - provisions all fabric network devices (that is excluding APICs) in ACI fabric for fabric discovery. Uses devices info stored in _../inventory/fabric_nodes.yaml_ file.

# Usage
## *Python scripts*
### **Notes**:

**- Python scripts must be executed from '**scripts**' folder!**

```bash
command: pwd | awk -F'/' '{print $(NF-1),"/",$NF}'
output: aci_scripts / scripts
```
**- Python 3.7 is lowest supported Python version.** 

### **Execution**:
_**apic_auth.py**_ - execute to generate APIC authentication token for the user specified in _../config/auth.yaml_ file.
```bash
python apic_auth.py
```

_**fabric_discovery**_ - provisions all fabric network devices (that is excluding APICs) in ACI fabric for fabric discovery. Reads ACI fabric devices info stored in _../inventory/fabric_nodes.yaml_ file.

# Roadmap
