# Intentionally misformatted for detect/heal PoC testing.
# After heal runs terraform fmt, indentation/spacing should normalize.

locals {
            example_name = "poc-fmt-test"
            tags = {
              Environment = "dev"
              Project     = "agentic-ai-poc"
              Owner       = "terraform-team"
            }
}

variable "region" {
  default     = "eu-west-1"
  type        = string
  description = "AWS region placeholder — no apply in this PoC"
}
