WAF_PILLARS = {
    "reliability": {
        "name": "Reliability",
        "description": "Ensure workloads are resilient and available. Includes DR, HA, backup, and fault tolerance.",
        "reference": "https://learn.microsoft.com/azure/well-architected/reliability/",
        "icon": "🛡️",
        "weight_boost": ["RELIABILITY"],
    },
    "security": {
        "name": "Security",
        "description": "Protect applications and data from threats. Includes identity, access, data protection.",
        "reference": "https://learn.microsoft.com/azure/well-architected/security/",
        "icon": "🔐",
        "weight_boost": ["SECURITY", "IDENTITY"],
    },
    "cost": {
        "name": "Cost Optimization",
        "description": "Manage costs to maximize value. Includes rightsizing, reservations, and shutdown schedules.",
        "reference": "https://learn.microsoft.com/azure/well-architected/cost-optimization/",
        "icon": "💰",
        "weight_boost": ["COST"],
    },
    "operational_excellence": {
        "name": "Operational Excellence",
        "description": "Operate and monitor workloads effectively. Includes DevOps, observability, automation.",
        "reference": "https://learn.microsoft.com/azure/well-architected/operational-excellence/",
        "icon": "⚙️",
        "weight_boost": ["RELIABILITY"],
    },
    "performance": {
        "name": "Performance Efficiency",
        "description": "Scale workloads efficiently to meet demand without over-provisioning.",
        "reference": "https://learn.microsoft.com/azure/well-architected/performance-efficiency/",
        "icon": "⚡",
        "weight_boost": ["COST", "RELIABILITY"],
    },
}
