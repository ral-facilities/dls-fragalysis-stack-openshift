# Fraglysis Ansible OpenShift Deployment
To run the playbook you will need to create a `vault-pass.txt` file that
contains the password used to create the vault passwords used in this project.
    
The run the playbook with the command: -

    ansible-playbook -i localhost, \
        --vault-password-file vault-pass.txt \
        site.yaml

And, to also install the backup process...

    ansible-playbook -i localhost, \
        --extra-vars "deploy_backup=true" \
        --vault-password-file vault-pass.txt \
        site.yaml

And, to also install the Jun2018 Graph database...

    ansible-playbook -i localhost, \
        --extra-vars "deploy_jun2018_graph=true" \
        --vault-password-file vault-pass.txt \
        site.yaml

## Creating encrypted secrets
If you have the ansible vault password you can encrypt strings
for the `secrets.yaml` file by running something like this: -

    ansible-vault encrypt_string <string> \
        --name <string name> --ask-vault-pass