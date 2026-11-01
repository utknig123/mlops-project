terraform {
  required_version = ">= 1.5.0"

  required_providers {
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = "~> 1.14"
    }
  }
}

provider "kubectl" {
  config_path = pathexpand(var.kubeconfig)
}

variable "kubeconfig" {
  type        = string
  description = "Kubeconfig used to apply the StockGod manifests."
  default     = "~/.kube/config"
}

data "kubectl_path_documents" "manifests" {
  pattern = "${path.module}/../../k8s/*.yaml"
}

resource "kubectl_manifest" "stockgod" {
  for_each  = data.kubectl_path_documents.manifests.manifests
  yaml_body = each.value
}

output "applied_manifests" {
  value = length(data.kubectl_path_documents.manifests.manifests)
}
