# rfam-batch-search

The Rfam Batch Search can be used to submit a sequence to the Job Dispatcher
service that runs the Infernal cmscan software

## Manual deployment in production

**Requirements**

- [Terraform](https://www.terraform.io)
- [Ansible](https://www.ansible.com/)

1. Create `terraform/providers.tf` using the `providers.tf.template` file.
2. Generate `rfam_rsa` key: `cd terraform && ssh-keygen -t rsa -b 4096`
3. Run `terraform init && terraform apply` to create the infrastructure
4. Run `ansible-playbook -i hosts rfam_batch_search.yml` to install and configure the service
5. The service will be available at `45.88.81.27:8000`
