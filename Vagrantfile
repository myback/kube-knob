boxes = [
    "ubuntu/focal64",
    "generic/centos8"
]

# "mihailutasu/fedora-coreos-stable"

master_count = 3
worker_count = 2

subnet = "172.17.8"

inventory_path_generated = ENV['PWD'] + "/.vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory"
inventory_path = ENV['PWD'] + "/inventory/vagrant.ini"

host_vars = {}
cluster = {}
grp_master = []
grp_worker = []

(1..master_count).each do |i|
    ip = "#{subnet}.#{50+i}"
    vm_name = "master%d" % i

    grp_master.push(vm_name)

    cluster[vm_name] = {
        :ip => ip,
        :cpus => 2,
        :mem => 2048,
        :box => boxes[0]
    }

    host_vars[vm_name] = {
        :ansible_host => ip,
        :ansible_port => 22
    }
end

(1..worker_count).each do |i|
    ip = "#{subnet}.#{100+i}"
    vm_name = "worker%d" % i

    grp_worker.push(vm_name)

    cluster[vm_name] = {
        :ip => ip,
        :cpus => 2,
        :mem => 2048,
        :box => boxes[0]
    }

    host_vars[vm_name] = {
        :ansible_host => ip,
        :ansible_port => 22
    }
end

Vagrant.configure("2") do |config|
    # config.vm.network :public_network, :bridge => 'en0: Wi-Fi (Wireless)'

    config.vm.provider :virtualbox do |v|
        v.linked_clone = true
    end

    config.vm.provision "shell" do |s|
    ssh_pub_key = File.readlines("#{Dir.home}/.ssh/id_rsa.pub").first.strip
    s.inline = <<-SHELL
      mkdir -p /root/.ssh
      chmod 700 /root/.ssh
      echo #{ssh_pub_key} >> /home/vagrant/.ssh/authorized_keys
      echo #{ssh_pub_key} >> /root/.ssh/authorized_keys
      chmod 600 /root/.ssh/authorized_keys
    SHELL
    end

    cluster.each_with_index do |(hostname, info), index|
        config.vm.define hostname do |cfg|
            cfg.vm.provider :virtualbox do |vb, override|
                override.vm.box = "#{info[:box]}"
                override.vm.network :private_network, ip: "#{info[:ip]}"
                override.vm.hostname = hostname
                override.vm.disk :disk, size: "10GB", primary: true
        
                vb.name = hostname
                vb.memory = info[:mem]
                vb.cpus = info[:cpus]
            end

            if index == cluster.size #- 1
                # FileUtils::ln_sf inventory_path_generated, inventory_path

                # cfg.trigger.before :destroy do |trigger|
                #     trigger.info = "Delete symlink to inventory file"
                #     trigger.run = {inline: "rm -f #{inventory_path}"}
                # end


                cfg.vm.provision :ansible do |ansible|
                    ansible.playbook = "cluster.yml"
                    ansible.limit = 'k8s'
                    ansible.host_vars = host_vars
                    ansible.become = true
                    ansible.host_key_checking = false
                    # ansible.raw_arguments = ["--flush-cache --inventory=#{inventory_path}", "--forks=#{master_count + worker_count}", "--flush-cache", "-e ansible_become_pass=vagrant"]
                    ansible.raw_arguments = ["--flush-cache --forks=#{master_count + worker_count}", "--flush-cache", "-e ansible_become_pass=vagrant"]
                    ansible.groups = {
                        :bastion => [],
                        :k8s => cluster.keys,
                        :cache => grp_worker[0],
                        "k8s:children" => "cache",
                        "k8s-master" => grp_master,
                        "k8s-worker" => grp_worker,
                    }
                end
            end
        end
    end
end
