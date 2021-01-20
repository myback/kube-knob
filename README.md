# WIP: Kubernetes with Cilium
Ansible playbook set for deploying a Kubernetes cluster.
### Usage
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r playbooks/requirements.txt
ansible-galaxy collection install -r playbooks/requirements.yml

ansible-playbook plays/k8s/cluster/setup.yml
```
