# Also intentionally messy so fmt -check fails clearly.

output "example_name" {
  value       = local.example_name
  description = "Example local for fmt PoC"
}

output "region" {
  value       = var.region
  description = "Region variable echo"
}
