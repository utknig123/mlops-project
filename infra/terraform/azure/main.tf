terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.9"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

variable "subscription_id" {
  type        = string
  description = "Azure subscription. Set this before apply. Validate does not call Azure."
  default     = "00000000-0000-0000-0000-000000000000"
}

variable "location" {
  type    = string
  default = "centralindia"
}

variable "image" {
  type        = string
  description = "Streamlit image published by GitHub Actions."
  default     = "ghcr.io/utknig123/mlops-project-streamlit:latest"
}

variable "api_url" {
  type        = string
  description = "API the Azure Streamlit container calls."
  default     = "http://localhost:8000"
}

resource "azurerm_resource_group" "stockgod" {
  name     = "rg-stockgod-mlops"
  location = var.location
}

resource "azurerm_log_analytics_workspace" "stockgod" {
  name                = "log-stockgod-mlops"
  location            = azurerm_resource_group.stockgod.location
  resource_group_name = azurerm_resource_group.stockgod.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_container_app_environment" "stockgod" {
  name                       = "cae-stockgod"
  location                   = azurerm_resource_group.stockgod.location
  resource_group_name        = azurerm_resource_group.stockgod.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.stockgod.id
}

resource "azurerm_container_app" "streamlit" {
  name                         = "ca-stockgod-streamlit"
  container_app_environment_id = azurerm_container_app_environment.stockgod.id
  resource_group_name          = azurerm_resource_group.stockgod.name
  revision_mode                = "Single"

  template {
    container {
      name   = "streamlit"
      image  = var.image
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "API_URL"
        value = var.api_url
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8501
    transport        = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }
}

output "streamlit_url" {
  value = "https://${azurerm_container_app.streamlit.ingress[0].fqdn}"
}
