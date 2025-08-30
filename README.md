# What is net-checker

The `net-checker` is a set of tools (ansible runner and python report parser) to perform
network performance tests (iperf3) and generate report diagrams. It also collects
all important system information before and after test like:

* interface statistics
* sysctl values
* atop logs

# Usage

## Prepare ansible inventory

For example we have 2 compute hosts and 4 VMs running on
them. We would like to test the following connectivity scenarios:

* hostA -> hostB performance between compute hosts
* vmA1 (hostA) --> vmA2 (hostA) performance between VMs on same compute
* vmA1 (hostA) --> vmB1 (hostB) performance between VMs on different computes.
```
---
all:
  vars:
    ansible_ssh_private_key_file: /home/ubuntu/bootstrap/dev/ssh_key
    ansible_user: mcc-user
  hosts:
    localhost:
      ansible_host: localhost
      ansible_connection: local
    hostA:
      ansible_host: 172.16.56.94
    hostB:
      ansible_host: 172.16.56.93
    vmA1:
     ansible_host: 192.168.15.108
    vmA2:
     ansible_host: 192.168.15.147
    vmB1:
      ansible_host: 192.168.15.205

  children:
    iperfs:
      hosts:
        hostA:
          iperf_targets:
            - 172.16.56.93
        vmA1:
          iperf_targets:
            - 192.168.15.147
            - 192.168.15.205
```

## Run performance tests
```
# Install requirements
pip3 install -r requirements.txt

ansible-playbook -i ansible/inventory.yaml ansible/perf.yaml

# Save performance tests in reports directory
mkdir ./net_checker_reports
mv /tmp/net_checker_reports/ ./net_checker_reports/01_default

# Change some parameters, in for example add bond transmit policy.
# Run tests one more time
ansible-playbook -i ansible/inventory.yaml ansible/perf.yaml
mv /tmp/net_checker_reports/ ./net_checker_reports/02_bond_hash
```

## Create report graphs
```
python3 generate_report.py
```

# Example of reports
<img alt="" src="docs/examples/reports/tcp_hostA_172.16.56.93.svg" width="50%" height="50%">
<img alt="" src="docs/examples/reports/udp_hostA_172.16.56.93.svg" width="50%" height="50%">
