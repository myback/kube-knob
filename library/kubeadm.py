import re
import yaml

from ansible.module_utils.basic import AnsibleModule


class KubeadmManager:
    def __init__(self, module):
        self.m = module

        self.kubeadm = module.params['kubeadm_bin']
        if self.kubeadm is None:
            self.kubeadm = module.get_bin_path('kubeadm', True)
        self.base_cmd = [self.kubeadm]

        if module.params['log_level']:
            self.base_cmd.append('--v=' + str(module.params['log_level']))

        if module.params['token']:
            create_params = module.params['token']['create']
            self.base_cmd.append('--ttl=' + create_params['ttl'])

            if create_params.get('certificate_key'):
                self.base_cmd.append('--certificate-key=' + create_params['certificate_key'])

        if module.params['cri_socket']:
            self.base_cmd.append('--cri-socket=' + module.params['cri_socket'])

    def _mkcmd(self, cmd):
        return self.base_cmd[:1] + cmd + self.base_cmd[1:]

    def _execute(self, cmd):
        rc, out, err = self.m.run_command(cmd)

        if rc:
            self.m.fail_json(msg="error running (%s) command" % ' '.join(cmd), stdout=out, stderr=err, rc=rc)

        return out

    def cmd_init(self):
        cmd = ['init']

        params = self.m.params['init']
        if params['skip_phases']:
            cmd.append('--skip-phases=' + ",".join(params['skip_phases']))

        if params['kubeadm_config']:
            cmd.append('--config=' + params['kubeadm_config'])
        if params['upload_certs']:
            cmd.append('--upload-certs')

        return True, self._execute(self._mkcmd(cmd))

    def cmd_join(self):
        cmd = ['join']
        cmd.append('--config=' + self.m.params['join']['kubeadm_config'])

        return True, self._execute(self._mkcmd(cmd))

    def cmd_token_list(self):
        cmd = self.base_cmd[:1] + ['token', 'list', '-o', 'yaml']

        o = self._execute(cmd)
        try:
            lst = list(yaml.safe_load_all(o))
        except TypeError:
            return ''

        if not lst:
            return ''

        token = ''
        for t in lst:
            if token:
                break

            if t.get('kind') == 'BootstrapToken':
                if t.get('usages') == ['authentication', 'signing']:
                    token = t['token']

        return token

    def cmd_add_certificate_key(self):
        cmd = self.base_cmd[:1] + ['init', 'phase', 'upload-certs', '--upload-certs',
                                   '--certificate-key=' + self.m.params['token']['create']['certificate_key']]

        self._execute(cmd)

    def cmd_token_create(self):
        cmd = ['token', 'create', '--print-join-command']

        token = self.cmd_token_list()

        changed = False
        if self.m.params['token']['create'].get('certificate_key'):
            self.cmd_add_certificate_key()
            changed = True

        if not token:
            out = self._execute(self._mkcmd(cmd))
            r = re.search(r'[a-z0-9]{6}\.[a-z0-9]{16}', out)
            token = r.group(0)
            changed = True

        return changed, token


def main():
    module = AnsibleModule(
        argument_spec=dict(
            kubeadm_bin=dict(),
            init=dict(type='dict', options=dict(
                kubeadm_config=dict(required=True),
                skip_phases=dict(type='list'),
                upload_certs=dict(default=False, type='bool'),
            )),
            join=dict(type='dict', options=dict(
                kubeadm_config=dict(required=True),
            )),
            token=dict(type='dict', options=dict(
                create=dict(type='dict', options=dict(
                    ttl=dict(required=True),
                    certificate_key=dict(),
                )),
            )),
            cri_socket=dict(),
            log_level=dict(default=0, type='int')
        ),
        required_one_of=[['init', 'join', 'token']]
    )

    manager = KubeadmManager(module)

    if module.params.get('token'):
        changed, out = manager.cmd_token_create()
        if not out:
            module.fail_json(msg="get token failed", stdout=out, stderr='', rc=3)

    elif module.params.get('init'):
        changed, out = manager.cmd_init()

    else:
        changed, out = manager.cmd_join()

    module.exit_json(changed=changed, stdout=out, stderr='', rc=0)


if __name__ == '__main__':
    main()