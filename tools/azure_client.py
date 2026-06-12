from config.settings import Settings


class AzureClient:
    """
    Fetches real Azure environment context for agent analysis.
    Falls back to demo data if credentials are not configured.
    """

    def __init__(self):
        self.subscription_id = Settings.AZURE_SUBSCRIPTION_ID
        self._credential = None

    def _get_credential(self):
        if self._credential:
            return self._credential
        from azure.identity import DefaultAzureCredential, ClientSecretCredential
        if Settings.AZURE_CLIENT_ID and Settings.AZURE_CLIENT_SECRET:
            self._credential = ClientSecretCredential(
                tenant_id=Settings.AZURE_TENANT_ID,
                client_id=Settings.AZURE_CLIENT_ID,
                client_secret=Settings.AZURE_CLIENT_SECRET,
            )
        else:
            self._credential = DefaultAzureCredential()
        return self._credential

    def get_environment_context(self) -> dict:
        """Build environment context dict for agent analysis."""
        if Settings.DEMO_MODE:
            return self._demo_context()
        try:
            from azure.mgmt.resource import ResourceManagementClient
            cred = self._get_credential()
            resource_client = ResourceManagementClient(cred, self.subscription_id)
            resources = list(resource_client.resources.list())
            return {
                "subscription_id": self.subscription_id,
                "subscription_name": "Production",
                "landing_zone": "Enterprise Scale",
                "resource_count": len(resources),
                "resource_types": list({r.type for r in resources}),
                "identity_count": 0,
            }
        except Exception as e:
            print(f"[WARNING] Azure client error: {e}. Using demo context.")
            return self._demo_context()

    def _demo_context(self) -> dict:
        return {
            "subscription_id": "00000000-demo-0000-0000-000000000000",
            "subscription_name": "Contoso - Production",
            "landing_zone": "Enterprise Scale",
            "resource_count": 187,
            "identity_count": 89,
            "resource_types": [
                "Microsoft.Compute/virtualMachines",
                "Microsoft.Storage/storageAccounts",
                "Microsoft.Network/virtualNetworks",
                "Microsoft.KeyVault/vaults",
                "Microsoft.Sql/servers",
            ],
        }
