# rfam-batch-search

The Rfam Batch Search can be used to submit a sequence to the Job Dispatcher
service that runs the Infernal cmscan software

## Manual deployment in production

**Requirements**

- [kubectl](https://kubernetes.io/docs/reference/kubectl/)
- [helm](https://helm.sh/docs/intro/install/)

```
# Make sure you are using the correct namespace
% kubectl config current-context
rfam

# List helm charts
% helm list --all
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS          CHART           APP VERSION
batch-search    rfam            1               2024-05-10 11:04:58.920023 +0100 BST    deployed        helm-0.1.0      1.16.0

# Uninstall chart
% helm uninstall batch-search
release "batch-search" uninstalled

# Install chart. It is possible to set some variables here,
# but the main one is the branch.
% cd kubernetes/helm
% helm install batch-search . --set branch=dev
NAME: batch-search
LAST DEPLOYED: Fri May 10 11:04:58 2024
NAMESPACE: rfam
STATUS: deployed
REVISION: 1
TEST SUITE: None

# Follow the pods creation by running the command below
% kubectl get pod
NAME                                 READY   STATUS              RESTARTS   AGE
nginx-5dbfc595db-dndt2               1/1     Running             0          3s
nginx-5dbfc595db-smhwm               1/1     Running             0          3s
rfam-batch-search-59657595ff-6lrhp   0/1     ContainerCreating   0          3s
rfam-batch-search-59657595ff-qdgjp   0/1     ContainerCreating   0          3s
rfam-batch-search-59657595ff-t4vs7   0/1     ContainerCreating   0          3s
rfam-batch-search-59657595ff-t8m5p   0/1     ContainerCreating   0          3s
```
