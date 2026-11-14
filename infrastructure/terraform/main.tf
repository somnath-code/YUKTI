resource "kubernetes_namespace_v1" "yukti" {
  metadata {
    name = var.namespace
    labels = {
      "pod-security.kubernetes.io/enforce" = "restricted"
      "pod-security.kubernetes.io/warn"    = "restricted"
    }
  }
}

resource "kubernetes_resource_quota_v1" "yukti" {
  metadata {
    name      = "yukti-limits"
    namespace = kubernetes_namespace_v1.yukti.metadata[0].name
  }
  spec {
    hard = {
      pods              = "12"
      "requests.cpu"    = "6"
      "requests.memory" = "8Gi"
      "limits.cpu"      = "12"
      "limits.memory"   = "16Gi"
    }
  }
}

output "namespace" {
  value = kubernetes_namespace_v1.yukti.metadata[0].name
}
