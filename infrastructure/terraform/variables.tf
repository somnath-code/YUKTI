variable "kubeconfig" {
  type        = string
  description = "Path to the existing cluster kubeconfig."
}

variable "context" {
  type        = string
  description = "Explicit kubeconfig context for the existing cluster."
}

variable "namespace" {
  type        = string
  default     = "yukti-staging"
  description = "Namespace to provision for private YUKTI workloads."
  validation {
    condition     = can(regex("^[a-z]([a-z0-9-]{0,61}[a-z0-9])?$", var.namespace))
    error_message = "Use a valid Kubernetes namespace label."
  }
}
